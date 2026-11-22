"""Poso totes les combinacions i les seves puntuacions a IDEES.md."""
from pathlib import Path
import csv
import itertools

ROOT = Path(__file__).resolve().parent.parent
METHODS = ['veu_minima', 'silenci_minim', 'seguiment_soroll', 'histeresi',
           'treu_pic', 'baixada', 'treu_dc', 'retroces', 'rescat_zcr', 'confirma_alt', 'limita_soroll']
START = '<!-- inici-matriu-combinacions -->'
END = '<!-- final-matriu-combinacions -->'


def actualitza():
    folder = ROOT/'resultats/combinacions'
    with (folder/'combinacions_amb_valors_fixos.csv').open() as stream:
        fixed = {tuple(int(row[key]) for key in METHODS): row for row in csv.DictReader(stream) if row['perfil']=='base_actual'}
    with (folder/'combinacions_ajustades.csv').open() as stream:
        adjusted = {tuple(int(row[key]) for key in METHODS): row for row in csv.DictReader(stream)}
    with (folder/'combinacions_vuit_metodes.csv').open() as stream:
        previous = {tuple(int(row[key]) for key in METHODS[:8]): row for row in csv.DictReader(stream)}
    combinations = list(itertools.product((0,1), repeat=len(METHODS)))
    if set(fixed)!=set(combinations) or set(adjusted)!=set(combinations):
        raise ValueError('Falten combinacions a les taules de resultats.')
    best = max(float(row['total']) for row in adjusted.values())
    baseline=(1,1,1,0,0,0,0,1,0,0,0)
    base_number=combinations.index(baseline)
    best_codes=[f'**C{i:04d}**' for i,c in enumerate(combinations) if abs(float(adjusted[c]['total'])-best)<1e-9]
    lines=[START, '## Matriu de totes les combinacions', '',
           'Cada fila és una combinació. **✓** vol dir activat i **—** vol dir desactivat.', '',
           '**Veu** i **Sil.** són les esperes; **Sor.** és el seguiment del soroll; **Hist.** són els dos llindars; '
           '**Pic** deixa fora el pic inicial; **Baix.** permet una baixada; **DC** treu la mitjana; **Ret.** torna al primer bloc pendent. '
           '**ZCR** rescata veu fluixa; **Conf.** exigeix arribar al llindar alt a temps; **Lím.** limita quins blocs actualitzen el soroll.', '',
           '**Fix** fa servir els valors de la base i els valors inicials dels mètodes nous. '
           '**Anterior** és la cerca amb vuit idees; només hi ha resultat quan les tres noves estan apagades. '
           '**Adaptativa** és la cerca amb les onze idees. Els ajustos poden ser diferents a cada fila. '
           'Tots els resultats són sobre les mateixes 115 gravacions de `db.v4`.', '',
           f'La **C{base_number:04d}** és la base. La millor cerca nova és a '+', '.join(best_codes)+'. '
           'Amb onze interruptors hi ha 2.048 files, de C0000 a C2047. Els números de l’estudi de vuit idees ja no són els mateixos.', '',
           '| Combinació | Veu | Sil. | Sor. | Hist. | Pic | Baix. | DC | Ret. | ZCR | Conf. | Lím. | Fix (%) | Anterior (%) | Adaptativa (%) |',
           '|---|'+':---:|'*11+'---:|---:|---:|']
    for number,c in enumerate(combinations):
        label=f'C{number:04d}'
        if c==baseline: label=f'**{label} · base**'
        elif abs(float(adjusted[c]['total'])-best)<1e-9: label=f'**{label} · millor cerca**'
        scores=[f"{float(fixed[c]['total']):.3f}".replace('.',','),
                f"{float(previous[c[:8]]['total']):.3f}".replace('.',',') if not any(c[8:]) else '—',
                f"{float(adjusted[c]['total']):.3f}".replace('.',',')]
        if abs(float(adjusted[c]['total'])-best)<1e-9: scores[-1]='**'+scores[-1]+'**'
        lines.append('| '+' | '.join([label,*['✓' if x else '—' for x in c],*scores])+' |')
    lines+=['', 'Els valors exactes de cada fila són al '
            '[CSV de combinacions ajustades](https://github.com/victor836768/P2/blob/jordi-albareda-combinacions/resultats/combinacions/combinacions_ajustades.csv). '
            'Hi ha files repetides perquè algunes idees no fan res quan una altra està apagada.', END]
    text=(ROOT/'IDEES.md').read_text()
    before,rest=text.split(START,1);_,after=rest.split(END,1)
    (ROOT/'IDEES.md').write_text(before+'\n'.join(lines)+after)
    print('IDEES.md: matriu actualitzada amb 2.048 combinacions.')


if __name__=='__main__':
    actualitza()
