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

ROOT = Path(__file__).resolve().parent.parent
METHODS = ['veu_minima', 'silenci_minim', 'seguiment_soroll', 'histeresi',
           'treu_pic', 'baixada', 'treu_dc', 'retroces']
PARAMS = ['inici', 'veu', 'silenci', 'marge', 'alfa', 'diferencia',
          'treu_pic', 'baixada', 'treu_dc', 'retroces']
METRICS = ['total', 'recall_v', 'precision_v', 'recall_s', 'precision_s']
PROFILES = {
    'primer_ajust': (20, 5, 15, 8., .02),
    'base_6': (10, 8, 15, 6., .02),
    'marge_6_63': (10, 8, 15, 6.63, .02),
    'base_actual': (9, 8, 17, 5.94, .00615),
}


def arguments(config):
    init, voice, silence, margin, alpha, gap, trim, dip, dc, backdate = config
    args = [f'--inici={int(init)}', f'--veu={int(voice)}', f'--silenci={int(silence)}',
            f'-l{margin:g}', f'--alfa={alpha:g}', f'--histeresi={gap:g}']
    for enabled, flag in [(trim, '--treu-pic'), (dip, '--permet-baixada'),
                          (dc, '--treu-dc'), (not backdate, '--sense-retroces')]:
        if enabled:
            args.append(flag)
    return args


def initial_config(methods, profile):
    voice_on, silence_on, adapt, hysteresis, trim, dip, dc, backdate = methods
    init, voice, silence, margin, alpha = profile
    return (init, voice if voice_on else 1, silence if silence_on else 1,
            margin, alpha if adapt else 0., 1. if hysteresis else 0.,
            trim, dip, dc, backdate)


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
        source = source.replace(old, 'extern float cached_power; float power = cached_power;')
        (temp / 'vad.c').write_text(source)
        (temp / 'runner.c').write_text('''
#include "vad.h"
float cached_power;
void evaluate(float *raw, float *dc, double *v, double *s, int *ends,
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
        int pending=start, last=ST_SILENCE;
        for (int i=start; i<ends[f]; i++) {
            cached_power=d->remove_dc ? dc[i] : raw[i];
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
        lib.evaluate.argtypes = [fp, fp, dp, dp, ip, C.c_int, dp, dp]
        for func in (lib.compute_power, lib.compute_power_centered):
            func.argtypes = [fp, C.c_uint]
            func.restype = C.c_float
        raw, centered, voices, silences, ends = [], [], [], [], []
        for wav in files:
            x, rate = sf.read(wav, dtype='float32')
            frame = int(rate*.01)
            count = len(x)//frame
            if count == 0:
                raise ValueError('La prova ràpida necessita almenys un bloc complet: '+str(wav))
            raw.extend(lib.compute_power(x[i*frame:(i+1)*frame], frame) for i in range(count))
            centered.extend(lib.compute_power_centered(x[i*frame:(i+1)*frame], frame) for i in range(count))
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
        voices, silences = np.array(voices), np.array(silences)
        ends = np.array(ends, dtype=np.int32)
        cache = {}

        def evaluate(config):
            config = tuple(config)
            if config not in cache:
                out = np.zeros(4)
                lib.evaluate(raw, centered, voices, silences, ends, len(files), np.array(config, dtype=np.float64), out)
                cache[config] = metrics(out)
            return cache[config]

        # Comprovo que la prova ràpida reprodueix els quatre resultats que ja coneixem.
        baseline = (1, 1, 1, 0, 0, 0, 0, 1)
        reference = initial_config(baseline, PROFILES['base_actual'])
        for index, known in [(None, 95.829), (6, 95.669), (7, 95.791), (8, 95.771)]:
            config = list(reference)
            if index is not None:
                config[index] = 1
            assert round(evaluate(config)[0], 3) == known, (config, evaluate(config))
        fixed_rows, best_rows, best_configs = [], [], []
        for number, methods in enumerate(itertools.product((0, 1), repeat=len(METHODS))):
            choices = []
            for name, profile in PROFILES.items():
                config = initial_config(methods, profile)
                score = evaluate(config)
                fixed_rows.append(dict(zip(METHODS, methods), perfil=name, **dict(zip(PARAMS[:6], config[:6])),
                                       **dict(zip(METRICS, score))))
                choices.append(config)
            best = max(choices, key=lambda c: evaluate(c)[0])
            # La mateixa cerca petita per a cada grup de mètodes.
            grids = [(0, [5, 9, 10, 15, 20]),
                     (1, [5, 8, 10, 12] if methods[0] else [1]),
                     (2, [10, 15, 17, 20, 25] if methods[1] else [1]),
                     (3, [4., 5., 5.94, 6.63, 7., 8., 9.]),
                     (4, [.003, .00615, .01, .02, .04] if methods[2] else [0.]),
                     (5, [.5, 1., 1.5, 2.] if methods[3] else [0.])]
            for _ in range(2):
                for dimension, values in grids:
                    candidates = [best]
                    for value in values:
                        c = list(best); c[dimension] = value
                        if c[5] < c[3]:
                            candidates.append(tuple(c))
                    best = max(candidates, key=lambda c: evaluate(c)[0])
            # Un afinament curt, igual per a totes les combinacions.
            for dimension in range(6):
                value = best[dimension]
                if dimension in (0, 1, 2):
                    values = [max(2 if dimension==0 else 1, value-1), value, value+1]
                    if dimension in (1, 2) and not methods[dimension-1]:
                        values = [1]
                    elif dimension in (1, 2):
                        values = [max(2, x) for x in values]
                elif dimension==3:
                    values = [round(value + delta, 4) for delta in (-.2, -.1, 0, .1, .2)]
                elif dimension==4:
                    values = [round(value*factor, 7) for factor in (.75, 1., 1.25)] if methods[2] else [0.]
                else:
                    values = [max(.1, value-.25), value, value+.25] if methods[3] else [0.]
                candidates = [best]
                for value in values:
                    c = list(best); c[dimension] = value
                    if c[5] < c[3]:
                        candidates.append(tuple(c))
                best = max(candidates, key=lambda c: evaluate(c)[0])
            best_configs.append((methods, best))
            best_rows.append(dict(zip(METHODS, methods), **dict(zip(PARAMS[:6], best[:6])),
                                  **dict(zip(METRICS, evaluate(best)))))
            if number % 16 == 15:
                winner = max(best_configs, key=lambda item: evaluate(item[1])[0])
                print(f'{number+1}/256 grups; millor TOTAL {evaluate(winner[1])[0]:.3f} %', flush=True)
        best_rows.sort(key=lambda row: row['total'], reverse=True)
        fields = METHODS + PARAMS[:6] + METRICS
        write_csv(results/'combinacions_amb_valors_fixos.csv', METHODS+['perfil']+PARAMS[:6]+METRICS, fixed_rows)
        write_csv(results/'combinacions_ajustades.csv', fields, best_rows)
        write_csv(results/'canvis_per_parelles.csv', ['perfil', 'metode', 'abans', 'despres', 'total_sense', 'total_amb', 'diferencia'], paired_effects(fixed_rows))
        best_configs.sort(key=lambda item: evaluate(item[1])[0], reverse=True)
        winner = best_configs[0][1]
        summary = {'metodes': METHODS, 'grups': len(best_configs), 'proves_diferents': len(cache),
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
