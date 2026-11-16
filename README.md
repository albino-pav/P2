# P2 — Prova de totes les idees juntes

Jordi Albareda Fortuny · Grup 41 · Lloc XX

Aquesta branca és `jordi-albareda-combinacions`. Aquí provo les idees antigues i les noves, juntes i per separat. La versió d’entrega continua a `jordi-albareda`.

Les idees i els resultats estan explicats amb paraules senzilles a [IDEES.md](IDEES.md). També hi ha la [matriu de les 256 combinacions](IDEES.md#matriu-de-totes-les-combinacions).

## Què he provat

- Esperar abans de confirmar la veu.
- Esperar abans de confirmar el silenci.
- Anar actualitzant el soroll.
- Fer servir dos llindars, és a dir, histèresi.
- Tornar al primer bloc pendent quan confirmo un canvi.
- Treure el bloc inicial més fort.
- Permetre una baixada curta mentre confirmo veu.
- Treure la mitjana abans de calcular la potència.

També canvio el temps inicial, el marge, les duracions mínimes, alfa i la diferència entre llindars.

Hi ha 256 combinacions d’interruptors. Les provo amb quatre grups de valors i faig una cerca adaptativa per a cadascuna, a partir de tres inicis genèrics. Els perfils històrics només es calculen per comparar. Quan un canvi millora el TOTAL, hi moc el centre. Quan s’encalla, redueixo el pas. No afegeixo valors específics ni importo els guanyadors anteriors com a punt de partida.

## Resultat

| Versió | TOTAL |
|---|---:|
| Base actual, també per defecte en aquesta branca | 95,829 % |
| Totes les idees activades amb els mateixos valors | 95,223 % |
| Millor de la cerca anterior | 95,871 % |
| Millor de la cerca adaptativa | **95,891 %** |

La millor combinació manté les esperes, el seguiment del soroll i el retorn al primer bloc pendent. També activa histèresi i permet una baixada. No treu el pic inicial ni la mitjana.

La cerca adaptativa arriba a 95,891 %. Són uns 0,020 punts més que la cerca anterior i 0,062 punts més que la base d’entrega. Guardo aquesta prova separada; els valors per defecte continuen sent els de la base.

## Compilar i executar

Necessito Meson, Ninja i libsndfile.

```sh
meson setup bin
ninja -C bin
bin/vad -i pav_41XX1.wav -o prova.vad
```

Sense opcions noves, el resultat continua sent el de la base. Per provar la millor configuració trobada:

```sh
bin/vad -i pav_41XX1.wav -o prova.vad --veu=7 -l 7.885 --alfa=0.0040213789 --histeresi=2.09375 --permet-baixada
```

Per provar les idees a mà:

```sh
bin/vad --help
bin/vad -i pav_41XX1.wav -o prova.vad --histeresi=1 --permet-baixada
bin/vad -i pav_41XX1.wav -o prova.vad --veu=1 --silenci=1 --alfa=0
```

`--veu=1` i `--silenci=1` volen dir sense espera. `--alfa=0` vol dir soroll fix. Els nombres de `--inici`, `--veu` i `--silenci` són blocs de 10 ms. `--sense-retroces` evita tornar al primer bloc pendent.

## Repetir les proves

Necessito també un compilador C, Python, NumPy i SoundFile. La base de dades no es puja al repositori.

```sh
python3 scripts/prova_combinacions.py /cami/a/db.v4 --verifica
python3 scripts/comprova_metodes.py
```

Si `db.v4` és dins de P2, no cal passar el camí. La primera ordre calcula les combinacions i comprova 27 configuracions amb el programa normal i el Perl. La segona comprova casos petits a 8, 16 i 48 kHz.

Per tornar a posar la matriu a `IDEES.md` a partir dels CSV, sense repetir les proves:

```sh
python3 scripts/actualitza_matriu.py
```

La cerca comença amb passos grans i els va reduint segons els resultats. En total són 46.888 configuracions diferents. Els 768 inicis han acabat pel pas mínim i la falta de millora, sense esgotar el límit de voltes. El detall és a [IDEES.md](IDEES.md#com-es-va-acostant-als-valors-bons).

## Fitxers de resultats

- [Combinacions amb valors fixos](resultats/combinacions/combinacions_amb_valors_fixos.csv).
- [Parelles on només canvia una idea](resultats/combinacions/canvis_per_parelles.csv).
- [Resultats de la cerca anterior](resultats/combinacions/combinacions_afinament_anterior.csv).
- [Millor ajust trobat per a cada combinació](resultats/combinacions/combinacions_ajustades.csv).
- [Recorregut de la cerca adaptativa](resultats/combinacions/recorregut_cerca.csv).
- [Verificació amb el programa normal i el Perl](resultats/combinacions/verificacio.csv).
- [Avaluació completa del millor resultat](resultats/combinacions/avaluacio_millor.txt).
- [Comprovacions amb àudios petits](resultats/combinacions/comprovacions.txt).

La gravació personal no es fa servir per triar la millor combinació. La puntuació de la taula és sobre les 115 gravacions de `db.v4`. Aquests àudios ja s’havien fet servir per ajustar la base; caldrien àudios nous per saber com funciona fora d’aquest conjunt.

Els altres resultats i figures ja venien de les proves anteriors. No són els resultats d’aquest estudi.
