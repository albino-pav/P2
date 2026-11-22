from pathlib import Path
import subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent.parent
helptext = subprocess.check_output([str(root/'bin/vad'), '--help'], text=True)
fig = plt.figure(figsize=(12, 13), facecolor='#18212b')
fig.text(.025, .98, '$ bin/vad --help\n'+helptext, va='top', fontfamily='monospace', fontsize=9, color='#e1e9f0')
fig.savefig(root/'img/opcions.png', dpi=150, facecolor=fig.get_facecolor())
plt.close(fig)

labels = ['Base', 'Ajust de valors', 'Onze idees', 'Límit segons veu\n10 ms', 'Final\n20 ms']
scores = [95.474, 95.829, 96.186, 96.838, 96.910]
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(labels, scores, color=['#9cb3c8']*4+['#367a51'])
ax.set_ylim(95, 97.2)
ax.set_ylabel('TOTAL (%)')
ax.set_title('Resultats de les diferents fases de proves')
for i, score in enumerate(scores):
    ax.text(i, score+.025, f'{score:.3f} %'.replace('.', ','), ha='center', fontsize=10)
fig.tight_layout()
fig.savefig(root/'img/evolucio_total.png', dpi=160)
plt.close(fig)
