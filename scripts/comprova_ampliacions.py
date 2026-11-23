"""Comprovo que el WAVE de sortida segueixi les etiquetes sense canviar la veu."""
from pathlib import Path
import hashlib
import subprocess
import tempfile
import numpy as np
import soundfile as sf

root=Path(__file__).resolve().parent.parent
checks=[]
with tempfile.TemporaryDirectory(prefix='p2-ampliacions-') as name:
    temp=Path(name)
    def check_audio(audio, description):
        labels=temp/'test.vad';clean=temp/'clean.wav';plain=temp/'plain.vad'
        subprocess.run([str(root/'bin/vad'),'-i',str(audio),'-o',str(labels),'-w',str(clean)],check=True,capture_output=True)
        subprocess.run([str(root/'bin/vad'),'-i',str(audio),'-o',str(plain)],check=True,capture_output=True)
        assert labels.read_bytes()==plain.read_bytes(),description
        info=sf.info(audio);out_info=sf.info(clean)
        assert (info.frames,info.samplerate,info.channels,info.subtype)==(out_info.frames,out_info.samplerate,out_info.channels,out_info.subtype),description
        dtype='float64' if info.subtype in ('FLOAT','DOUBLE') else 'int32'
        original,rate=sf.read(audio,dtype=dtype);output,_=sf.read(clean,dtype=dtype)
        voice=np.zeros(len(original),dtype=bool)
        for line in labels.read_text().splitlines():
            a,b,label=line.split()
            if label=='V':voice[round(float(a)*rate):round(float(b)*rate)]=True
        assert np.array_equal(original[voice],output[voice]),description
        assert np.all(output[~voice]==0),description
    for audio in sorted((root/'db.v4').glob('*/*.wav')):
        check_audio(audio,str(audio))
    checks.append('OK: 115 gravacions: mateixa durada, freqüència i format; veu idèntica i silenci a zero.')
    check_audio(root/'pav_4151.wav','gravació personal')
    for rate in (8000,16000,48000):
        for subtype in ('PCM_U8','PCM_16','PCM_24','PCM_32','FLOAT','DOUBLE'):
            # Soroll, veu i final que no omple un bloc.
            rng=np.random.default_rng(2)
            x=rng.normal(0,.001,rate+13)
            a,b=int(.2*rate),int(.7*rate)
            x[a:b]=.25*np.sin(2*np.pi*200*np.arange(b-a)/rate)
            audio=temp/'synthetic.wav';sf.write(audio,x,rate,subtype=subtype)
            check_audio(audio,f'{rate} Hz {subtype}')
        for length in (1,rate//200,rate//20):
            sf.write(temp/'short.wav',np.zeros(length),rate,subtype='PCM_16')
            check_audio(temp/'short.wav',f'silenci curt {rate} Hz {length}')
    checks.append('OK: 8, 16 i 48 kHz; PCM de 8/16/24/32 bits, float i double; silencis curts i final incomplet.')
    source=temp/'source.wav';source.write_bytes((root/'pav_4151.wav').read_bytes())
    digest=hashlib.sha256(source.read_bytes()).digest()
    cases=[(source,temp/'same.vad',source),(source,source,temp/'other.wav')]
    alias=temp/'alias.wav';alias.symlink_to(source)
    cases.append((source,temp/'alias.vad',alias))
    hard=temp/'hard.wav';hard.hardlink_to(source)
    cases.append((source,temp/'hard.vad',hard))
    same=temp/'both.wav'
    cases.append((source,same,temp/'./both.wav'))
    for audio,labels,output in cases:
        result=subprocess.run([str(root/'bin/vad'),'-i',str(audio),'-o',str(labels),'-w',str(output)],capture_output=True)
        assert result.returncode!=0,(audio,labels,output)
        assert hashlib.sha256(source.read_bytes()).digest()==digest
    result=subprocess.run([str(root/'bin/vad'),'-i',str(source),'-o',str(temp/'fail.vad'),'-w',str(temp/'missing'/'out.wav')],capture_output=True)
    assert result.returncode!=0
    checks.append('OK: rebutjo sortides iguals a l’entrada o a les etiquetes, enllaços i carpetes inexistents.')
(root/'resultats/comprovacio_ampliacions.txt').write_text('\n'.join(checks)+'\n')
print('\n'.join(checks))
