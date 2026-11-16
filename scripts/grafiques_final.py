from pathlib import Path
import subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv
import tempfile
import atexit
import shutil
temporary=Path(tempfile.mkdtemp(prefix="p2-figures-"))
atexit.register(shutil.rmtree, temporary)
r=Path(__file__).resolve().parent.parent
helptext=subprocess.check_output([str(r/'bin/vad'),'--help'],text=True)
example=subprocess.check_output([str(r/'bin/vad'),'-v','-i',str(r/'pav_41XX1.wav'),'-o',str(temporary/'example.vad'),'-l','5.94'],text=True).splitlines()
text='$ bin/vad --help\n'+helptext+'\n$ bin/vad -v -i pav_41XX1.wav -o prova.vad -l 5.94\n'+'\n'.join(example[8:13])
fig=plt.figure(figsize=(12,7),facecolor='#18212b');fig.text(.025,.97,text.expandtabs(10),va='top',fontfamily='monospace',fontsize=10,color='#e1e9f0');plt.savefig(r/'img/opcions.png',dpi=150,facecolor=fig.get_facecolor());plt.close()
rows=list(csv.DictReader((r/'resultats/optimitzacio_final.csv').open()))
chosen=[row for row in rows if int(row['init_frames'])==9 and int(row['min_voice'])==8 and int(row['min_silence'])==17 and abs(float(row['noise_alpha'])-.00615)<1e-8]
chosen.sort(key=lambda row:float(row['margin_db']))
fig,ax=plt.subplots(figsize=(8,4));ax.plot([float(x['margin_db']) for x in chosen],[float(x['total']) for x in chosen]);ax.scatter([5.94],[95.829317],color='tab:red',label='5,94 dB: 95,829 %');ax.set(xlabel='Marge sobre el soroll (dB)',ylabel='TOTAL (%)',title='Afinament final: inicialització 90 ms, veu 80 ms, silenci 170 ms, alfa 0,00615');ax.legend();ax.grid(alpha=.25);fig.tight_layout();fig.savefig(r/'img/optimitzacio_final.png',dpi=160);plt.close()
