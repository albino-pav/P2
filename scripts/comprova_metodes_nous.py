"""Proves petites per comprovar les tres idees noves abans de comparar puntuacions."""
from pathlib import Path
import subprocess
import tempfile
import numpy as np
import soundfile as sf

root = Path(__file__).resolve().parent.parent
checks = []
with tempfile.TemporaryDirectory(prefix='p2-nous-') as name:
    temp = Path(name)
    for rate in (8000, 16000, 48000):
        size = rate//100
        def blocks(values):
            x = np.repeat(np.array(values, dtype=float), size)
            x[1::2] *= -1
            return x
        def run(x, flags=()):
            audio, labels = temp/'test.wav', temp/'test.vad'
            sf.write(audio, x, rate, subtype='PCM_16')
            result = subprocess.run([str(root/'bin/vad'), '-i', str(audio), '-o', str(labels), '-v', *flags],
                                    check=True, capture_output=True, text=True)
            segments = [(float(a), float(b), c) for a,b,c in (line.split() for line in labels.read_text().splitlines())]
            return segments, result.stdout
        weak = blocks([.001]*20+[.0018]*30+[.001]*30)
        labels, _ = run(weak, ['--alfa=0'])
        assert all(c=='S' for _,_,c in labels)
        labels, _ = run(weak, ['--alfa=0', '--rescat-zcr', '--rebaixa-zcr=2'])
        assert [(a,b) for a,b,c in labels if c=='V']==[(.2,.5)],labels
        labels, _ = run(blocks([.001]*20+[.0012]*30+[.001]*30), ['--alfa=0', '--rescat-zcr', '--rebaixa-zcr=2'])
        assert all(c=='S' for _,_,c in labels)
        low_zcr = weak.copy()
        t = np.arange(30*size)/rate
        low_zcr[20*size:50*size] = np.sqrt(2)*.0018*np.sin(2*np.pi*200*t)
        labels, _ = run(low_zcr, ['--alfa=0', '--rescat-zcr', '--rebaixa-zcr=2'])
        assert all(c=='S' for _,_,c in labels)
        checks.append(f'OK: {rate} Hz: el ZCR rescata veu fluixa, però no energia insuficient ni ZCR baix.')
        flags=['--alfa=0', '--confirma-alt', '--pujada=3', '--espera=12']
        labels, _ = run(blocks([.001]*20+[.0025]*40+[.001]*30), flags)
        assert all(c=='S' for _,_,c in labels)
        labels, _ = run(blocks([.001]*20+[.0025]*15+[.01]*10+[.001]*30), flags)
        assert [(a,b) for a,b,c in labels if c=='V']==[(.32,.45)],labels
        labels, _ = run(blocks([.001]*20+[.1]+[.001]*30), flags)
        assert all(c=='S' for _,_,c in labels)
        checks.append(f'OK: {rate} Hz: confirmació alta, límit d’espera i rebuig d’un pic curt.')
        x=blocks([.001]*20+[.0015]*30)
        _, guarded = run(x, ['--alfa=.1', '--limita-soroll', '--marge-soroll=2'])
        _, ordinary = run(x, ['--alfa=.1'])
        a=[float(row.split()[-1]) for row in guarded.splitlines()]
        b=[float(row.split()[-1]) for row in ordinary.splitlines()]
        assert a[-1]==a[8] and b[-1]>a[-1]+2,(a[-1],b[-1])
        checks.append(f'OK: {rate} Hz: el límit impedeix incorporar blocs massa alts al soroll.')
        labels, _ = run(np.zeros(rate//2), ['--rescat-zcr', '--confirma-alt', '--limita-soroll', '--treu-pic', '--treu-dc', '--permet-baixada'])
        assert labels==[(0.,.5,'S')]
    for flags in (['--rescat-zcr','--rebaixa-zcr=99'], ['--confirma-alt','--espera=2'],
                  ['--zcr=nan'], ['--pujada=-1'], ['--marge-soroll=-1']):
        result=subprocess.run([str(root/'bin/vad'), '-i', str(temp/'test.wav'), '-o', str(temp/'bad.vad'), *flags],capture_output=True)
        assert result.returncode!=0,flags
    checks.append('OK: opcions invàlides rebutjades.')
(root/'resultats/combinacions/comprovacions_nous.txt').write_text('\n'.join(checks)+'\n')
print('\n'.join(checks))
