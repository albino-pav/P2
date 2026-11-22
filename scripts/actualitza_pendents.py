"""Ajunto les proves pendents i les poso a IDEES.md."""
from pathlib import Path
import csv
import json

ROOT=Path(__file__).resolve().parent.parent
START='<!-- inici-proves-pendents -->'
END='<!-- final-proves-pendents -->'


def actualitza():
    folder=ROOT/'resultats/pendents'
    rows=[];configs=[];trials=0;limited=0
    for ms in (5,10,20,30,40,120):
        part=folder/f'{ms}ms'
        with (part/'resultats.csv').open() as f: rows.extend(csv.DictReader(f))
        meta=json.loads((part/'resum.json').read_text())
        trials+=meta['proves'];configs.extend(meta['configuracions'])
    assert len(rows)==48
    limited=sum(int(row['inicis_limitats']) for row in rows)
    best=max(configs,key=lambda row:row['resultat'][0])
    with (folder/'matriu.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(sorted(rows,key=lambda r:float(r['total']),reverse=True))
    summary={'casos':48,'configuracions_provades':trials,'inicis_limitats':limited,'millor':best}
    (folder/'resum.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    cfg=best['configuracio']
    enabled=[label for value,label in zip(cfg[18:21],['soroll a dues velocitats','límit segons la veu','entrada directa']) if value]
    description=f"La millor prova fa servir blocs de {cfg[23]:g} ms. Les regles noves actives són: "+(' i '.join(enabled) if enabled else 'cap')+'.'
    if cfg[18]: description+=f" El factor de baixada és {cfg[21]:g}."
    if cfg[19]: description+=f" La diferència màxima entre veu i soroll és {cfg[22]:g} dB."
    best_index=int(cfg[18])*4+int(cfg[19])*2+int(cfg[20])
    (folder/'avaluacio_millor.txt').write_bytes((folder/f'{cfg[23]:g}ms'/f'avaluacio_{best_index}.txt').read_bytes())
    fmt=lambda value:f'{float(value):.3f}'.replace('.',',')
    lines=[START,'## Proves que quedaven pendents','',
           'Després de mirar els PR nous he provat quatre idees més a '
           '[jordi-albareda-proves-pendents](https://github.com/victor836768/P2/tree/jordi-albareda-proves-pendents).','',
           '- **Soroll a dues velocitats:** quan la potència baixa, el soroll es mou més ràpid. Quan puja, mantinc el ritme normal.',
           '- **Límit del soroll segons la veu:** també estimo el nivell de veu i evito que el soroll quedi massa per sota seu.',
           '- **Entrada directa:** si arriba un bloc molt fort, puc confirmar veu sense esperar tota la duració mínima. També pot acceptar un cop curt.',
           '- **Altres durades de bloc:** 5, 10, 20, 30, 40 i 120 ms. Les esperes es converteixen a blocs de la durada corresponent.','',
           'Les tres regles s’inspiren en [Martínez–Urioste, PR #8](https://github.com/albino-pav/P2/pull/8). '
           'Variar el bloc surt de [Pascual–Sánchez, PR #9](https://github.com/albino-pav/P2/pull/9). '
           'He adaptat les idees al meu programa; els valors es tornen a buscar.','',
           'En aquesta prova mantinc els onze interruptors de la combinació que donava 96,186 %. '
           'Provo les vuit barreges de les tres regles noves amb sis durades de bloc: **48 casos**. '
           'No és una cerca de totes les barreges possibles de les catorze regles.','',
           'Per a cada cas torno a ajustar els valors amb tres inicis genèrics. Els temps es busquen en mil·lisegons i es passen a blocs sencers. '
           'També ajusto el factor de baixada del soroll i la diferència màxima entre veu i soroll. '
           'El primer va d’1 a 15 i el segon de 30 a 80 dB. El pas es va reduint fins a 0,1 i 0,5 dB.','',
           'Quan canvio la durada del bloc, també adapto alfa per mantenir una velocitat comparable. '
           'El nivell de veu fa una mitjana suau dels blocs confirmats com a veu o pendents de silenci. '
           'Les quatre opcions noves estan apagades per defecte i el bloc continua sent de 10 ms.','',
           f'He provat **{trials:,} configuracions** i he comprovat els **48 casos** amb el binari normal i el Perl. '.replace(',','.')+
           ('Cap inici ha esgotat el límit de voltes.' if not limited else f'{limited} inicis han esgotat el límit de voltes.'),'',
           '| Bloc | Millor TOTAL |','|---:|---:|']
    for ms in (5,10,20,30,40,120):
        score=max(float(r['total']) for r in rows if float(r['frame_ms'])==ms)
        lines.append(f'| {ms} ms | {fmt(score)} % |')
    lines+=['',f'El millor resultat és **{fmt(best["resultat"][0])} %**, davant del 96,186 % anterior. '+
            description,'',
            'El bloc de 120 ms dona un resultat pitjor. Les esperes no es poden ajustar amb gaire detall si cada bloc ja dura tant. '
            'En aquest estudi no he agafat les 24 trames del PR com si fossin 240 ms: sempre faig la conversió amb la durada real.','',
            '### Matriu de les 48 proves','',
            '✓ vol dir activat. A cada fila hi ha el millor ajust trobat per a aquella barreja.','',
            '| Bloc | Dues velocitats | Límit segons veu | Entrada directa | TOTAL |',
            '|---:|:---:|:---:|:---:|---:|']
    for row in sorted(rows,key=lambda r:(float(r['frame_ms']),r['soroll_asimetric'],r['terra_soroll'],r['entrada_directa'])):
        ticks=['✓' if row[key]=='1' else '—' for key in ('soroll_asimetric','terra_soroll','entrada_directa')]
        lines.append('| '+' | '.join([f"{float(row['frame_ms']):g} ms",*ticks,fmt(row['total'])+' %'])+' |')
    lines+=['','Els valors exactes són al [CSV de les proves pendents](https://github.com/victor836768/P2/blob/jordi-albareda-proves-pendents/resultats/pendents/matriu.csv). '
            'Els resultats continuen sent de `db.v4`; falta veure com va amb àudios nous.',END]
    text=(ROOT/'IDEES.md').read_text();block='\n'.join(lines)
    if START in text:
        before,rest=text.split(START,1);_,after=rest.split(END,1);text=before+block+after
    else:
        text=text.replace('## On són les proves',block+'\n\n## On són les proves',1)
    (ROOT/'IDEES.md').write_text(text)
    print('IDEES.md: 48 proves pendents actualitzades.')


if __name__=='__main__': actualitza()
