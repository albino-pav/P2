"""Ajust fora de línia de l’autòmat amb potències calculades pel mateix codi C.

Requereix cc, NumPy i SoundFile. Les referències només intervenen en la puntuació.
"""
from pathlib import Path
import ctypes as C, subprocess, tempfile, itertools, csv, json
import numpy as np
import soundfile as sf
root=Path(__file__).resolve().parent.parent
import atexit, shutil
tmp=Path(tempfile.mkdtemp(prefix='p2-tuning-'))
atexit.register(shutil.rmtree, tmp)
source=(root/'src/vad.c').read_text()
for typ,name in [('int','INIT_FRAMES'),('int','MIN_VOICE'),('int','MIN_SILENCE'),('float','NOISE_ALPHA')]:
    source=source.replace('const '+typ+' '+name,typ+' '+name)
source=source.replace('float power = compute_power(x, data->frame_length);','extern float cached_power; float power = cached_power;')
(tmp/'vad.c').write_text(source)
(tmp/'runner.c').write_text('''
#include "vad.h"
extern int INIT_FRAMES, MIN_VOICE, MIN_SILENCE;
extern float NOISE_ALPHA;
float cached_power;
void evaluate(float *p, double *v, double *s, int *ends, int files,
              int init, int voice, int silence, float margin, float alpha, double *out) {
 INIT_FRAMES=init; MIN_VOICE=voice; MIN_SILENCE=silence; NOISE_ALPHA=alpha;
 for(int j=0;j<4;j++)out[j]=0;
 int start=0;
 for(int f=0;f<files;f++){
   VAD_DATA *d=vad_open(16000); d->margin_db=margin;
   int pending=start, last=ST_SILENCE;
   for(int i=start;i<ends[f];i++){
     cached_power=p[i]; int state=vad(d,0);
     if(state==ST_UNDEF)continue;
     last=state;
     for(int k=pending;k<=i;k++){
       out[state==ST_VOICE?0:2]+=v[k];
       out[state==ST_VOICE?1:3]+=s[k];
     }
     pending=i+1;
   }
   for(int k=pending;k<ends[f];k++){
     out[last==ST_VOICE?0:2]+=v[k];out[last==ST_VOICE?1:3]+=s[k];
   }
   vad_close(d);start=ends[f];
 }
}
''')
subprocess.run(['cc','-O2','-shared','-fPIC','-I'+str(root/'src'),str(tmp/'vad.c'),str(tmp/'runner.c'),'-lm','-o',str(tmp/'tune.dylib')],check=True)
# Use the same float accumulation and logarithm as the detector.
subprocess.run(['cc','-O2','-shared','-fPIC',str(root/'src/pav_analysis.c'),'-lm','-o',str(tmp/'power.dylib')],check=True)
lib=C.CDLL(str(tmp/'tune.dylib')); power=C.CDLL(str(tmp/'power.dylib')).compute_power
fp=np.ctypeslib.ndpointer(dtype=np.float32,flags='C_CONTIGUOUS'); dp=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS'); ip=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS')
power.argtypes=[fp,C.c_uint]; power.restype=C.c_float
lib.evaluate.argtypes=[fp,dp,dp,ip,C.c_int,C.c_int,C.c_int,C.c_int,C.c_float,C.c_float,dp]
ps=[]; vs=[]; ss=[]; ends=[]
for wav in sorted((root/'db.v4').glob('*/*.wav')):
 x,rate=sf.read(wav,dtype='float32'); n=int(rate*.01); count=len(x)//n; duration=round(len(x)/rate,6)
 p=np.array([power(x[i*n:(i+1)*n],n) for i in range(count)],dtype=np.float32)
 bounds=np.arange(count+1)*n/rate; bounds[-1]=duration
 v=np.zeros(count); s=np.zeros(count)
 ref=[line.split() for line in wav.with_suffix('.lab').read_text().splitlines() if line.strip()]
 if float(ref[-1][1])<duration*.99:ref.append([ref[-1][1],str(duration),'S'])
 for a,b,label in ref:
  weights=np.maximum(0,np.minimum(bounds[1:],float(b))-np.maximum(bounds[:-1],float(a)))
  (v if label=='V' else s)[:]+=weights
 ps.extend(p); vs.extend(v); ss.extend(s); ends.append(len(ps))
p=np.array(ps,dtype=np.float32); v=np.array(vs); s=np.array(ss); ends=np.array(ends,dtype=np.int32)
seen={}
def evaluate(config):
 config=tuple(config)
 if config in seen:return seen[config]
 out=np.zeros(4); lib.evaluate(p,v,s,ends,len(ends),*config,out)
 vv,sv,vs,ss=out
 rv=vv/(vv+vs); pv=vv/(vv+sv); rs=ss/(ss+sv); ps=ss/(ss+vs)
 score=100*np.sqrt((5*rv*pv/(rv+4*pv))*(1.25*rs*ps/(rs+.25*ps)))
 seen[config]=(score,100*rv,100*pv,100*rs,100*ps)
 return seen[config]
for init in [5,8,10,15,20]:
 for config in itertools.product([init],[3,5,7,8,9,10,12,15],[8,10,12,15,17,20,23,27],[4,5,6,7,8,9,10],[.001,.003,.006,.01,.02,.04]):evaluate(config)
 best=max(seen,key=lambda c:seen[c][0]);print(init,best,evaluate(best),flush=True)
for _ in range(3):
 for dimension,values in [(3,np.round(np.arange(best[3]-.7,best[3]+.701,.01),2)),(4,np.round(np.linspace(max(.0001,best[4]*.5),best[4]*1.5,41),6)),(0,range(2,41)),(1,range(2,21)),(2,range(5,36))]:
  for value in values:evaluate(tuple(value if j==dimension else best[j] for j in range(5)))
  best=max(seen,key=lambda c:seen[c][0])
 print('fine',best,evaluate(best),flush=True)
with (root/'resultats/optimitzacio_final.csv').open('w') as f:
 writer=csv.writer(f,lineterminator='\n')
 writer.writerow(['init_frames','min_voice','min_silence','margin_db','noise_alpha','total','recall_v','precision_v','recall_s','precision_s'])
 for config,metrics in sorted(seen.items(),key=lambda item:item[1][0],reverse=True):writer.writerow([*config,*metrics])
print('BEST',best,evaluate(best),'trials',len(seen),flush=True)
