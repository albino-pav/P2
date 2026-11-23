from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

root=Path(__file__).resolve().parent.parent
original,rate=sf.read(root/'pav_4151.wav')
output,_=sf.read(root/'pav_4151_sense_soroll.wav')
time=np.arange(len(original))/rate
fig,axes=plt.subplots(2,1,figsize=(11,5),sharex=True,sharey=True)
for ax,signal,title in zip(axes,[original,output],['Original','Sortida: silencis a zero']):
    ax.plot(time,signal,linewidth=.5)
    ax.set_ylabel('Amplitud')
    ax.set_title(title)
    ax.set_xlim(0,len(original)/rate)
axes[-1].set_xlabel('Temps (s)')
fig.tight_layout()
fig.savefig(root/'img/cancelacio_silenci.png',dpi=160)
plt.close(fig)
