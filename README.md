# P2 — Proves que quedaven pendents

Jordi Albareda Fortuny · Grup 41 · Lloc 05

En aquesta branca provo les idees que vaig trobar als PR nous: soroll a dues velocitats, límit del soroll segons la veu, entrada directa i altres durades de bloc.

És `jordi-albareda-proves-pendents`. L’explicació, l’origen de cada idea i les taules són a [IDEES.md](IDEES.md#proves-que-quedaven-pendents).

## Què he provat

He mantingut els onze interruptors de la combinació que donava 96,186 %. A sobre d’aquesta faig les vuit barreges de les tres regles noves amb blocs de 5, 10, 20, 30, 40 i 120 ms: **48 casos**.

En cada cas torno a buscar els valors amb tres inicis genèrics. El pas es va fent petit quan el resultat deixa de millorar. Els temps es passen a blocs sencers segons la durada que estigui provant. També adapto alfa per poder comparar velocitats semblants.

Això és una prova centrada en la millor combinació anterior. No he tornat a provar totes les barreges de les catorze regles.

## Resultats

| Bloc | Millor TOTAL |
|---|---:|
| 5 ms | 96,417 % |
| 10 ms | 96,838 % |
| 20 ms | **96,910 %** |
| 30 ms | 96,775 % |
| 40 ms | 96,847 % |
| 120 ms | 95,737 % |

La millor prova fa servir les dues velocitats del soroll i el límit segons la veu. L’entrada directa queda apagada. Amb blocs de 10 ms també millora el resultat anterior de 96,186 %.

He provat **42.790 configuracions** i he comprovat els 48 casos amb el programa normal i el Perl. No he canviat les marques de referència. Amb les opcions noves apagades, la configuració anterior dona les mateixes 115 sortides.

## D’on surten les idees

- Les tres regles noves s’inspiren en [Martínez–Urioste, PR #8](https://github.com/albino-pav/P2/pull/8).
- Variar el bloc surt de [Pascual–Sánchez, PR #9](https://github.com/albino-pav/P2/pull/9).

He adaptat les idees al meu detector. Les tres regles estan apagades per defecte i el bloc continua sent de 10 ms.

## Compilar i executar

```sh
meson setup bin
ninja -C bin
```

Per repetir el 96,910 %:

```sh
bin/vad -i pav_41XX1.wav -o prova.vad \
    --inici=1 --veu=5 --silenci=8 -l7 \
    --alfa=0.0023082305 --histeresi=0 --permet-baixada --treu-dc \
    --rescat-zcr --confirma-alt --zcr=1750 --rebaixa-zcr=3.625 \
    --pujada=6 --espera=15 --marge-soroll=2 --soroll-asimetric \
    --terra-soroll --factor-baixada=9.25 --rang-soroll=41.25 --frame-ms=20
```

`--inici`, `--veu`, `--silenci` i `--espera` són nombres de blocs. En aquesta comanda cada bloc dura 20 ms: per exemple, `--veu=5` són 100 ms i `--silenci=8` són 160 ms. Alfa és el pes de cada bloc; l’script ja ha fet la conversió per a cada durada.

## Repetir les proves

Necessito un compilador C, Meson, Ninja, libsndfile, Python, NumPy i SoundFile.

```sh
python3 scripts/prova_pendents.py /cami/a/db.v4 --verifica
python3 scripts/comprova_pendents.py
```

Si `db.v4` és dins de P2, no cal posar el camí. Puc repetir una part de la prova amb `--blocs 10 20`. Les taules s’actualitzen al final.

Per regenerar només les taules amb els CSV que ja tinc:

```sh
python3 scripts/actualitza_pendents.py
```

## Fitxers

- [Matriu dels 48 casos i valors trobats](resultats/pendents/matriu.csv).
- [Resum i arguments de la millor prova](resultats/pendents/resum.json).
- [Avaluació completa del millor resultat](resultats/pendents/avaluacio_millor.txt).
- [Comprovacions amb àudios petits](resultats/pendents/comprovacions.txt).

A cada carpeta `5ms`, `10ms`, etc., hi ha els resultats, la comprovació amb el Perl i el recorregut de la cerca.

Són resultats amb `db.v4`, que ja havia fet servir per ajustar el detector. Caldrien àudios nous per saber si la millora també es manté fora d’aquesta base.
