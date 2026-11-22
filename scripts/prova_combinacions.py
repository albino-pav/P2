"""Provo les idees del detector juntes i per separat.

Requereix un compilador C, NumPy, SoundFile i db.v4. No modifica els valors
per defecte del programa. Les referències només serveixen per puntuar.
"""
from pathlib import Path
import argparse
import ctypes as C
import csv
import itertools
import json
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from cerca_adaptativa import search

ROOT = Path(__file__).resolve().parent.parent
METHODS = ['veu_minima', 'silenci_minim', 'seguiment_soroll', 'histeresi',
           'treu_pic', 'baixada', 'treu_dc', 'retroces', 'rescat_zcr', 'confirma_alt', 'limita_soroll']
PARAMS = ['inici', 'veu', 'silenci', 'marge', 'alfa', 'diferencia',
          'treu_pic', 'baixada', 'treu_dc', 'retroces', 'rescat_zcr', 'confirma_alt', 'limita_soroll',
          'llindar_zcr', 'rebaixa_zcr', 'pujada_confirmacio', 'max_espera', 'marge_actualitzacio']
NUMERIC = PARAMS[:6] + PARAMS[13:]
METRICS = ['total', 'recall_v', 'precision_v', 'recall_s', 'precision_s']
STEP_FIELDS = ['pas_inici', 'pas_veu', 'pas_silenci', 'pas_marge', 'pas_log10_alfa', 'pas_diferencia', 'pas_zcr', 'pas_rebaixa_zcr', 'pas_pujada', 'pas_espera', 'pas_marge_soroll']
PROFILES = {
    'primer_ajust': (20, 5, 15, 8., .02),
    'base_6': (10, 8, 15, 6., .02),
    'marge_6_63': (10, 8, 15, 6.63, .02),
    'base_actual': (9, 8, 17, 5.94, .00615),
}


def arguments(config):
    init, voice, silence, margin, alpha, gap, trim, dip, dc, backdate, rescue, confirm, guard, zcr, discount, boost, wait, update = config
    args = [f'--inici={int(init)}', f'--veu={int(voice)}', f'--silenci={int(silence)}',
            f'-l{margin:.9g}', f'--alfa={alpha:.9g}', f'--histeresi={gap:.9g}']
    for enabled, flag in [(trim, '--treu-pic'), (dip, '--permet-baixada'),
                          (dc, '--treu-dc'), (not backdate, '--sense-retroces')]:
        if enabled:
            args.append(flag)
    for enabled, flag in [(rescue, '--rescat-zcr'), (confirm, '--confirma-alt'), (guard, '--limita-soroll')]:
        if enabled: args.append(flag)
    args += [f'--zcr={zcr:.9g}', f'--rebaixa-zcr={discount:.9g}', f'--pujada={boost:.9g}',
             f'--espera={int(wait)}', f'--marge-soroll={update:.9g}']
    return args


def initial_config(methods, profile):
    voice_on, silence_on, adapt, hysteresis, trim, dip, dc, backdate, rescue, confirm, guard = methods
    init, voice, silence, margin, alpha = profile
    return (init, voice if voice_on else 1, silence if silence_on else 1,
            margin, alpha if adapt else 0., 1. if hysteresis else 0.,
            trim, dip, dc, backdate, rescue, confirm, guard, 3000., 2., 3., 25, 2.)


def metrics(out):
    vv, sv, vs, ss = out
    eps = 1e-24
    rv, pv = vv / (vv + vs + eps), vv / (vv + sv + eps)
    rs, ps = ss / (ss + sv + eps), ss / (ss + vs + eps)
    fv = 5 * rv * pv / (rv + 4 * pv + eps)
    fs = 1.25 * rs * ps / (rs + .25 * ps + eps)
    return (100 * np.sqrt(fv * fs), 100 * rv, 100 * pv, 100 * rs, 100 * ps)


def write_csv(path, fields, rows):
    with path.open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def paired_effects(rows):
    """Comparo dues files que només es diferencien en una idea."""
    lookup = {(row['perfil'], tuple(int(row[key]) for key in METHODS)): row for row in rows}
    output = []
    for (profile, switches), row in lookup.items():
        for index, method in enumerate(METHODS):
            if switches[index]:
                continue
            enabled = list(switches)
            enabled[index] = 1
            other = lookup[(profile, tuple(enabled))]
            output.append({'perfil': profile, 'metode': method,
                           'abans': ''.join(map(str, switches)), 'despres': ''.join(map(str, enabled)),
                           'total_sense': float(row['total']), 'total_amb': float(other['total']),
                           'diferencia': float(other['total'])-float(row['total'])})
    return output


def run(database, verify):
    files = sorted(database.glob('*/*.wav'))
    if len(files) != 115:
        raise SystemExit('Cal db.v4 amb les 115 gravacions.')
    results = ROOT / 'resultats/combinacions'
    results.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='p2-combinacions-') as temp_name:
        temp = Path(temp_name)
        source = (ROOT / 'src/vad.c').read_text()
        old = 'float power = data->remove_dc ? compute_power_centered(x, data->frame_length) : compute_power(x, data->frame_length);'
        if source.count(old) != 1:
            raise RuntimeError('Ha canviat el càlcul de potència: cal revisar la prova ràpida.')
        source = source.replace(old, 'extern float cached_power, cached_zcr; float power = cached_power;')
        zcr_line = 'float zcr = data->rescue_zcr ? compute_zcr(x, data->frame_length, data->sampling_rate) : 0.0f;'
        assert source.count(zcr_line) == 1
        source = source.replace(zcr_line, 'extern float cached_zcr; float zcr = cached_zcr;')
        (temp / 'vad.c').write_text(source)
        (temp / 'runner.c').write_text('''
#include "vad.h"
float cached_power, cached_zcr;
void evaluate(float *raw, float *dc, float *zcr, double *v, double *s, int *ends,
              int files, double *cfg, double *out) {
    for (int j=0; j<4; j++) out[j]=0;
    int start=0;
    for (int f=0; f<files; f++) {
        VAD_DATA *d=vad_open(16000);
        d->init_frames=(int)cfg[0]; d->min_voice=(int)cfg[1];
        d->min_silence=(int)cfg[2]; d->margin_db=(float)cfg[3];
        d->noise_alpha=(float)cfg[4]; d->silence_gap=(float)cfg[5];
        d->trim_initial=(int)cfg[6]; d->allow_dip=(int)cfg[7];
        d->remove_dc=(int)cfg[8]; d->backdate=(int)cfg[9];
        d->rescue_zcr=(int)cfg[10]; d->confirm_high=(int)cfg[11]; d->guard_noise=(int)cfg[12];
        d->zcr_threshold=(float)cfg[13]; d->zcr_discount=(float)cfg[14];
        d->confirm_boost=(float)cfg[15]; d->max_wait=(int)cfg[16]; d->noise_update_margin=(float)cfg[17];
        int pending=start, last=ST_SILENCE;
        for (int i=start; i<ends[f]; i++) {
            cached_power=d->remove_dc ? dc[i] : raw[i]; cached_zcr=zcr[i];
            int state=vad(d,0);
            if (state==ST_UNDEF) continue;
            for (int k=pending; k<=i; k++) {
                int label=d->backdate || k==i ? state : last;
                out[label==ST_VOICE ? 0 : 2]+=v[k];
                out[label==ST_VOICE ? 1 : 3]+=s[k];
            }
            pending=i+1; last=state;
        }
        for (int k=pending; k<ends[f]; k++) {
            out[last==ST_VOICE ? 0 : 2]+=v[k];
            out[last==ST_VOICE ? 1 : 3]+=s[k];
        }
        vad_close(d); start=ends[f];
    }
}
''')
        subprocess.run(['cc', '-O2', '-shared', '-fPIC', '-I'+str(ROOT/'src'),
                        str(temp/'vad.c'), str(temp/'runner.c'),
                        str(ROOT/'src/pav_analysis.c'), '-lm', '-o', str(temp/'test.so')], check=True)
        lib = C.CDLL(str(temp/'test.so'))
        fp = np.ctypeslib.ndpointer(dtype=np.float32, flags='C_CONTIGUOUS')
        dp = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
        ip = np.ctypeslib.ndpointer(dtype=np.int32, flags='C_CONTIGUOUS')
        lib.evaluate.argtypes = [fp, fp, fp, dp, dp, ip, C.c_int, dp, dp]
        for func in (lib.compute_power, lib.compute_power_centered):
            func.argtypes = [fp, C.c_uint]
            func.restype = C.c_float
        lib.compute_zcr.argtypes = [fp, C.c_uint, C.c_float]
        lib.compute_zcr.restype = C.c_float
        raw, centered, zcrs, voices, silences, ends = [], [], [], [], [], []
        for wav in files:
            x, rate = sf.read(wav, dtype='float32')
            frame = int(rate*.01)
            count = len(x)//frame
            if count == 0:
                raise ValueError('La prova ràpida necessita almenys un bloc complet: '+str(wav))
            raw.extend(lib.compute_power(x[i*frame:(i+1)*frame], frame) for i in range(count))
            centered.extend(lib.compute_power_centered(x[i*frame:(i+1)*frame], frame) for i in range(count))
            zcrs.extend(lib.compute_zcr(x[i*frame:(i+1)*frame], frame, rate) for i in range(count))
            bounds = np.round(np.arange(count+1)*frame/rate, 6)
            bounds[-1] = round(len(x)/rate, 6)
            v, s = np.zeros(count), np.zeros(count)
            refs = [line.split() for line in wav.with_suffix('.lab').read_text().splitlines() if line.strip()]
            if float(refs[-1][1]) < bounds[-1]*.99:
                refs.append([refs[-1][1], str(bounds[-1]), 'S'])
            for a, b, label in refs:
                overlap = np.maximum(0, np.minimum(bounds[1:], float(b))-np.maximum(bounds[:-1], float(a)))
                (v if label=='V' else s)[:] += overlap
            voices.extend(v); silences.extend(s); ends.append(len(raw))
        raw, centered = np.array(raw, dtype=np.float32), np.array(centered, dtype=np.float32)
        zcrs = np.array(zcrs, dtype=np.float32)
        voices, silences = np.array(voices), np.array(silences)
        ends = np.array(ends, dtype=np.int32)
        cache = {}

        def evaluate(config):
            config = list(config)
            # Hi ha interruptors que no fan res si la idea de la qual depenen és apagada.
            if config[4] == 0: config[12], config[17] = 0, 2.
            if config[1] == 1 and not config[11]: config[7] = 0
            if config[1] == 1 and config[2] == 1 and not config[11]: config[9] = 1
            config = tuple(config)
            if config not in cache:
                out = np.zeros(4)
                lib.evaluate(raw, centered, zcrs, voices, silences, ends, len(files), np.array(config, dtype=np.float64), out)
                cache[config] = metrics(out)
            return cache[config]

        # Comprovo que la prova ràpida reprodueix els quatre resultats que ja coneixem.
        baseline = (1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0)
        reference = initial_config(baseline, PROFILES['base_actual'])
        for index, known in [(None, 95.829), (6, 95.669), (7, 95.791), (8, 95.771)]:
            config = list(reference)
            if index is not None:
                config[index] = 1
            assert round(evaluate(config)[0], 3) == known, (config, evaluate(config))
        fixed_rows, best_rows, best_configs = [], [], []
        search_rows = []
        limited_starts = 0
        for number, methods in enumerate(itertools.product((0, 1), repeat=len(METHODS))):
            # Els perfils històrics només serveixen de comparació, no d'inici de cerca.
            for name, profile in PROFILES.items():
                config = initial_config(methods, profile)
                fixed_rows.append(dict(zip(METHODS, methods), perfil=name,
                                       **dict(zip(NUMERIC, config[:6]+config[13:])),
                                       **dict(zip(METRICS, evaluate(config)))))
            best, trace, limited = search(methods, evaluate)
            limited_starts += limited
            for step in trace:
                search_rows.append(dict(zip(METHODS, methods), inici_cerca=step['inici_cerca'],
                                        volta=step['volta'], accio=step['accio'],
                                        **dict(zip(NUMERIC, step['config'][:6]+step['config'][13:])),
                                        **dict(zip(STEP_FIELDS, step['passos'])),
                                        total=step['total']))
            best_configs.append((methods, best))
            best_rows.append(dict(zip(METHODS, methods), **dict(zip(NUMERIC, best[:6]+best[13:])),
                                  **dict(zip(METRICS, evaluate(best)))))
            if number % 16 == 15:
                winner = max(best_configs, key=lambda item: evaluate(item[1])[0])
                print(f'{number+1}/{2**len(METHODS)} grups; millor TOTAL {evaluate(winner[1])[0]:.3f} %', flush=True)
        best_rows.sort(key=lambda row: row['total'], reverse=True)
        fields = METHODS + NUMERIC + METRICS
        write_csv(results/'combinacions_amb_valors_fixos.csv', METHODS+['perfil']+NUMERIC+METRICS, fixed_rows)
        write_csv(results/'combinacions_ajustades.csv', fields, best_rows)
        write_csv(results/'recorregut_cerca.csv', METHODS+['inici_cerca', 'volta', 'accio']+NUMERIC+STEP_FIELDS+['total'], search_rows)
        write_csv(results/'canvis_per_parelles.csv', ['perfil', 'metode', 'abans', 'despres', 'total_sense', 'total_amb', 'diferencia'], paired_effects(fixed_rows))
        best_configs.sort(key=lambda item: evaluate(item[1])[0], reverse=True)
        winner = best_configs[0][1]
        summary = {'metodes': METHODS, 'grups': len(best_configs), 'proves_diferents': len(cache),
                   'voltes_cerca': len(search_rows), 'inicis_aturats_per_limit': limited_starts,
                   'cerca': 'tres inicis generics, moviment segons TOTAL i reduccio del pas',
                   'millor_configuracio': dict(zip(PARAMS, winner)),
                   'millor_resultat': dict(zip(METRICS, evaluate(winner))),
                   'arguments': arguments(winner)}
        (results/'resum.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n')
        print(json.dumps(summary, ensure_ascii=False), flush=True)
        if verify:
            # Verifico les millors, la base, cada mètode sol i cada mètode tret de la base.
            selected = [reference]
            for index in range(len(METHODS)):
                only = [0]*len(METHODS); only[index] = 1
                without = list(baseline); without[index] = 1-without[index]
                selected.extend([initial_config(only, PROFILES['base_actual']),
                                 initial_config(without, PROFILES['base_actual'])])
            selected.extend(config for _, config in best_configs[:10])
            selected = list(dict.fromkeys(selected))
            rows = []
            for index, config in enumerate(selected):
                folder = temp/'native'
                folder.mkdir(exist_ok=True)
                refs = []
                for wav in files:
                    target = folder/wav.parent.name/wav.with_suffix('.lab').name
                    target.parent.mkdir(exist_ok=True)
                    target.write_bytes(wav.with_suffix('.lab').read_bytes())
                    subprocess.run([str(ROOT/'bin/vad'), '-i', str(wav), '-o', str(target.with_suffix('.vad')),
                                    *arguments(config)], check=True, capture_output=True)
                    refs.append(str(target.relative_to(folder)))
                output = subprocess.run(['perl', str(ROOT/'scripts/vad_evaluation.pl'), *refs],
                                        cwd=folder, check=True, capture_output=True, text=True).stdout
                total = float(output.split('===> TOTAL: ')[-1].split('%')[0])
                assert abs(total-evaluate(config)[0]) <= .000501, (config, total, evaluate(config))
                rows.append(dict(zip(PARAMS, config), total_perl=total, total_rapid=evaluate(config)[0]))
                if config==winner:
                    (results/'avaluacio_millor.txt').write_text(output.rstrip()+'\n')
                print(f'Verificació {index+1}/{len(selected)}: {total:.3f} %', flush=True)
            write_csv(results/'verificacio.csv', PARAMS+['total_perl', 'total_rapid'], rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database', nargs='?', type=Path, default=ROOT/'db.v4')
    parser.add_argument('--verifica', action='store_true', help='Comprova també amb el binari i el Perl originals')
    args = parser.parse_args()
    run(args.database.resolve(), args.verifica)
    from actualitza_matriu import actualitza
    actualitza()
