"""Poso les 256 combinacions i les seves puntuacions a IDEES.md."""
from pathlib import Path
import csv
import itertools

ROOT = Path(__file__).resolve().parent.parent
METHODS = ['veu_minima', 'silenci_minim', 'seguiment_soroll', 'histeresi',
           'treu_pic', 'baixada', 'treu_dc', 'retroces']
START = '<!-- inici-matriu-combinacions -->'
END = '<!-- final-matriu-combinacions -->'


def actualitza():
    folder = ROOT / 'resultats/combinacions'
    with (folder/'combinacions_amb_valors_fixos.csv').open() as stream:
        fixed = {tuple(int(row[key]) for key in METHODS): row
                 for row in csv.DictReader(stream) if row['perfil'] == 'base_actual'}
    with (folder/'combinacions_ajustades.csv').open() as stream:
        adjusted = {tuple(int(row[key]) for key in METHODS): row for row in csv.DictReader(stream)}
    with (folder/'combinacions_abans_afinament.csv').open() as stream:
        previous = {tuple(int(row[key]) for key in METHODS): row for row in csv.DictReader(stream)}
    combinations = list(itertools.product((0, 1), repeat=8))
    if any(set(table) != set(combinations) for table in (fixed, adjusted, previous)):
        raise ValueError('Cal tenir exactament les 256 combinacions a les dues taules.')
    best = max(float(row['total']) for row in adjusted.values())
    base_number = combinations.index((1, 1, 1, 0, 0, 0, 0, 1))
    best_codes = [f'**C{i:03d}**' for i, switches in enumerate(combinations)
                  if abs(float(adjusted[switches]['total'])-best) < 1e-9]
    lines = [START, '## Matriu de totes les combinacions', '',
             'Cada fila és una combinació. **✓** vol dir activat i **—** vol dir desactivat.', '',
             '**Veu** i **Sil.** són les esperes de veu i silenci; **Sor.** és el seguiment del soroll; '
             '**Hist.** són els dos llindars; **Pic** deixa fora el pic inicial; '
             '**Baix.** permet una baixada; **DC** treu la mitjana; **Ret.** torna al primer bloc pendent.', '',
             '**Fix** és el TOTAL amb els valors de la base actual. Si activo la histèresi, separo els llindars 1 dB. '
             '**Ajust curt** és el resultat de la primera cerca. **Ajust fi** és el millor TOTAL trobat després de provar valors més propers. '
             'Per tant, les columnes ajustades poden fer servir paràmetres diferents a cada fila. '
             'Els tres resultats són sobre les 115 gravacions de `db.v4`.', '',
             f'La **C{base_number:03d}** és la combinació de la base actual. El millor ajust és a '+', '.join(best_codes)+'. '
             'El número identifica els vuit interruptors en l’ordre de les columnes; les files van de C000 a C255.', '',
             '| Combinació | Veu | Sil. | Sor. | Hist. | Pic | Baix. | DC | Ret. | Fix (%) | Ajust curt (%) | Ajust fi (%) |',
             '|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---:|---:|---:|']
    for number, switches in enumerate(combinations):
        label = f'C{number:03d}'
        if number == base_number:
            label = f'**C{number:03d} · base**'
        elif abs(float(adjusted[switches]['total'])-best) < 1e-9:
            label = f'**C{number:03d} · millor ajust**'
        score_fixed = f"{float(fixed[switches]['total']):.3f}".replace('.', ',')
        score_previous = f"{float(previous[switches]['total']):.3f}".replace('.', ',')
        score_adjusted = f"{float(adjusted[switches]['total']):.3f}".replace('.', ',')
        if abs(float(adjusted[switches]['total'])-best) < 1e-9:
            score_adjusted = '**'+score_adjusted+'**'
        ticks = ['✓' if enabled else '—' for enabled in switches]
        lines.append('| '+' | '.join([label, *ticks, score_fixed, score_previous, score_adjusted])+' |')
    lines.extend(['', 'Els paràmetres concrets de cada ajust són al '
                  '[CSV de combinacions ajustades](https://github.com/victor836768/P2/blob/jordi-albareda-combinacions/resultats/combinacions/combinacions_ajustades.csv). '
                  'Algunes files donen el mateix perquè hi ha idees que no fan res si una altra està desactivada.', END])
    block = '\n'.join(lines)
    path = ROOT / 'IDEES.md'
    text = path.read_text()
    if START in text:
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        text = before+block+after
    else:
        text = text.replace('## Com ho he comprovat', block+'\n\n## Com ho he comprovat', 1)
    path.write_text(text)
    print('IDEES.md: matriu actualitzada amb les 256 combinacions.')


if __name__ == '__main__':
    actualitza()
