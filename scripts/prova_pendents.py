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
from cerca_pendents import search

ROOT = Path(__file__).resolve().parent.parent
NEW_METHODS = ['soroll_asimetric', 'terra_soroll', 'entrada_directa']
EXTRA_PARAMS = ['factor_baixada', 'rang_soroll', 'frame_ms']
BASE_METHODS = (1,1,1,0,0,1,1,1,1,1,0)
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


def old_arguments(config):
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


def arguments(config):
    args = old_arguments(config[:18])
    for active, flag in zip(config[18:21], ['--soroll-asimetric','--terra-soroll','--entrada-directa']):
        if active: args.append(flag)
    args += [f'--factor-baixada={config[21]:.9g}',f'--rang-soroll={config[22]:.9g}',f'--frame-ms={config[23]:.9g}']
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


def run(database, verify, frame_ms):
    files = sorted(database.glob('*/*.wav'))
    if len(files) != 115:
        raise SystemExit('Cal db.v4 amb les 115 gravacions.')
    results = ROOT / 'resultats/pendents' / f'{frame_ms:g}ms'
    results.mkdir(parents=True, exist_ok=True)
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
#include <math.h>
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
        d->asymmetric_noise=(int)cfg[18]; d->floor_noise=(int)cfg[19]; d->direct_voice=(int)cfg[20];
        d->down_factor=(float)cfg[21]; d->voice_range=(float)cfg[22];
        d->frame_length=(unsigned int)(16000*(float)cfg[23]/1000.0f);
        d->voice_alpha=1.0f-powf(0.9f,(float)cfg[23]/10.0f);
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
            frame = int(rate*frame_ms/1000.0)
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
            if config[1] == 1 and not config[11] and not config[20]: config[7] = 0
            if config[1] == 1 and config[2] == 1 and not config[11] and not config[20]: config[9] = 1
            config = tuple(config)
            if config not in cache:
                out = np.zeros(4)
                lib.evaluate(raw, centered, zcrs, voices, silences, ends, len(files), np.array(config, dtype=np.float64), out)
                cache[config] = metrics(out)
            return cache[config]

        rows, trace_rows, configurations = [], [], []
        for additions in itertools.product((0,1),repeat=3):
            best, trace, limited = search(BASE_METHODS, additions, frame_ms, evaluate)
            configurations.append(best)
            row = dict(zip(NEW_METHODS,additions), frame_ms=frame_ms,
                       **dict(zip(PARAMS,best[:18])), factor_baixada=best[21],rang_soroll=best[22],
                       **dict(zip(METRICS,evaluate(best))), inicis_limitats=limited)
            rows.append(row)
            for step in trace:
                trace_rows.append(dict(zip(NEW_METHODS,additions),inici=step['inici_cerca'],volta=step['volta'],
                                       accio=step['accio'],total=step['total'],configuracio=json.dumps(step['config'])))
            print(f'{frame_ms:g} ms {additions}: {evaluate(best)[0]:.3f} %',flush=True)
        rows.sort(key=lambda row:row['total'],reverse=True)
        fields=NEW_METHODS+EXTRA_PARAMS+PARAMS+METRICS+['inicis_limitats']
        write_csv(results/'resultats.csv',fields,rows)
        write_csv(results/'recorregut.csv',NEW_METHODS+['inici','volta','accio','total','configuracio'],trace_rows)
        (results/'resum.json').write_text(json.dumps({'proves':len(cache),'configuracions':[dict(configuracio=c,arguments=arguments(c),resultat=evaluate(c)) for c in configurations]},indent=2)+'\n')
        if verify:
            verified=[]
            for index,cfg in enumerate(configurations):
                folder=temp/'native';folder.mkdir(exist_ok=True);refs=[]
                for wav in files:
                    ref=folder/wav.parent.name/wav.with_suffix('.lab').name
                    ref.parent.mkdir(exist_ok=True)
                    ref.write_bytes(wav.with_suffix('.lab').read_bytes())
                    subprocess.run([str(ROOT/'bin/vad'),'-i',str(wav),'-o',str(ref.with_suffix('.vad')),*arguments(cfg)],check=True,capture_output=True)
                    refs.append(str(ref.relative_to(folder)))
                output=subprocess.run(['perl',str(ROOT/'scripts/vad_evaluation.pl'),*refs],cwd=folder,check=True,capture_output=True,text=True).stdout
                total=float(output.split('===> TOTAL: ')[-1].split('%')[0])
                assert abs(total-evaluate(cfg)[0])<=.000501,(cfg,total,evaluate(cfg))
                verified.append(dict(zip(NEW_METHODS,cfg[18:21]),total_perl=total,total_rapid=evaluate(cfg)[0]))
                (results/f'avaluacio_{index}.txt').write_text(output.rstrip()+'\n')
            write_csv(results/'verificacio.csv',NEW_METHODS+['total_perl','total_rapid'],verified)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database',nargs='?',type=Path,default=ROOT/'db.v4')
    parser.add_argument('--verifica',action='store_true')
    parser.add_argument('--blocs',type=float,nargs='+',choices=[5,10,20,30,40,120],default=[5,10,20,30,40,120])
    args=parser.parse_args()
    for frame_ms in args.blocs:
        if not 2<=frame_ms<=120: raise SystemExit('Blocs entre 2 i 120 ms.')
        run(args.database.resolve(),args.verifica,frame_ms)

    from actualitza_pendents import actualitza
    actualitza()
