"""Casos petits per a les idees pendents."""
from pathlib import Path
import subprocess
import tempfile
import numpy as np
import soundfile as sf

root=Path(__file__).resolve().parent.parent
checks=[]
with tempfile.TemporaryDirectory(prefix='p2-pendents-') as name:
    temp=Path(name)
    for rate in (8000,16000,48000):
        n=rate//100
        def blocks(values):
            x=np.repeat(np.array(values,dtype=float),n);x[1::2]*=-1
            return x
        def run(x,flags=()):
            sf.write(temp/'test.wav',x,rate,subtype='PCM_16')
            output=subprocess.run([str(root/'bin/vad'),'-i',str(temp/'test.wav'),'-o',str(temp/'test.vad'),'-v',*flags],check=True,capture_output=True,text=True).stdout
            segments=[(float(a),float(b),c) for a,b,c in (line.split() for line in (temp/'test.vad').read_text().splitlines())]
            thresholds=[float(line.split()[-1]) for line in output.splitlines()]
            return segments,thresholds
        falling=blocks([.002]*20+[.001]*30)
        _,normal=run(falling,['--alfa=.02'])
        _,asymmetric=run(falling,['--alfa=.02','--soroll-asimetric','--factor-baixada=4'])
        assert asymmetric[-1]<normal[-1]-1.5
        rising=blocks([.001]*20+[.0015]*30)
        _,normal=run(rising,['--alfa=.02'])
        _,asymmetric=run(rising,['--alfa=.02','--soroll-asimetric','--factor-baixada=4'])
        assert asymmetric==normal
        checks.append(f'OK: {rate} Hz: segueixo les baixades més ràpid i les pujades al mateix ritme.')
        x=blocks([0.]*20+[.1]*30+[0.]*30+[.0003]*30)
        plain,_=run(x,['--alfa=0'])
        limited,threshold=run(x,['--alfa=0','--terra-soroll','--rang-soroll=40'])
        assert any(a>=.8 and c=='V' for a,b,c in plain),plain
        assert not any(a>=.8 and c=='V' for a,b,c in limited),limited
        assert threshold[-1]>-80,threshold[-1]
        checks.append(f'OK: {rate} Hz: el límit segons la veu evita un soroll estimat massa baix.')
        x=blocks([.001]*20+[.1]+[.001]*30)
        plain,_=run(x)
        direct,_=run(x,['--entrada-directa'])
        assert all(c=='S' for _,_,c in plain)
        assert [(a,b) for a,b,c in direct if c=='V']==[(.2,.21)],direct
        checks.append(f'OK: {rate} Hz: l’entrada directa accepta el pic que abans es descartava.')
        for ms in (5,10,20,30,40,120):
            length=int(rate*1.2345)
            segments,_=run(np.zeros(length),[f'--frame-ms={ms}'])
            assert segments==[(0.,round(length/rate,6),'S')],(ms,segments)
        checks.append(f'OK: {rate} Hz: sis durades de bloc i final incomplet conservat.')
    for flag in ('--frame-ms=0','--frame-ms=121','--frame-ms=nan','--factor-baixada=.5','--rang-soroll=0'):
        result=subprocess.run([str(root/'bin/vad'),'-i',str(temp/'test.wav'),'-o',str(temp/'bad.vad'),flag],capture_output=True)
        assert result.returncode!=0,flag
    checks.append('OK: opcions invàlides rebutjades.')
(root/'resultats/pendents').mkdir(exist_ok=True)
(root/'resultats/pendents/comprovacions.txt').write_text('\n'.join(checks)+'\n')
print('\n'.join(checks))
