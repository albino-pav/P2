# P2: Detector de actividad vocal

## Objetivo

La práctica consiste en marcar qué partes de una grabación contienen voz y cuáles son silencio. El detector analiza la potencia en tramas cortas y cambia de estado cuando se mantienen las condiciones durante cierto tiempo.

## 1. Grabación y etiquetado manual

Para el etiquetado manual se utilizó `pav_411.wav`, una grabación mono a 16 kHz con muestras PCM de 16 bits. Se trabajó con WaveSurfer y se recortó el silencio inicial de potencia muy baja antes de marcar los tramos.

En la escala de potencia de WaveSurfer, el ruido de fondo está aproximadamente entre 20 y 25 dB y la voz suele superar los 40 dB. Son valores orientativos. Para las etiquetas manuales se marcaron como silencio las pausas claras, sin separar las interrupciones breves que forman parte de las palabras.

El ZCR cuenta los cambios de signo de la señal. Ayuda a describir algunos sonidos, aunque el ruido también puede tener un ZCR alto. Por eso se calcula y se muestra, pero el detector decide usando la potencia.

La imagen corresponde a una prueba de la variante adaptativa, que obtuvo 94,291 % en `db.v4`. El primer panel muestra el ZCR y el segundo la potencia. Las etiquetas manuales aparecen en magenta y las automáticas en amarillo, debajo se ve la señal ampliada y la vista general.

![Pav_411 con ZCR, potencia, señal y etiquetas manuales y automáticas](captura_411_completa.png)

## 2. Detector

El programa procesa el audio en tramas de 10 ms. Para cada trama calcula tres medidas:

- **Potencia:** calcula el promedio de las muestras al cuadrado y lo expresa en decibelios. La potencia indica el nivel de energía de la trama y es la medida que utiliza el detector para clasificarla.
- **Amplitud media:** calcula el promedio de los valores absolutos de las muestras. Está disponible en el código, pero no se usa para decidir si hay voz.
- **ZCR:** cuenta los cambios de signo de la señal y los relaciona con el tiempo de la trama. Se muestra en las gráficas y en la depuración, pero no interviene en la clasificación. Un ZCR alto por sí solo no distingue la voz del ruido.

### Parámetros principales

| Parámetro | Valor predeterminado | Función |
|---|---:|---|
| Longitud de trama | 10 ms | Duración de cada fragmento analizado. |
| Calibración inicial | 10 tramas (100 ms) | Estima el nivel de ruido al comienzo del audio. |
| Margen de entrada a voz (`-u`) | 5,49 dB | Se suma al nivel de ruido estimado para fijar el umbral de voz. |
| Histéresis (`--histeresis`) | 2 dB | El umbral de salida a silencio queda 2 dB por debajo del de entrada. |
| Margen de voz clara (`--margen-claro`) | 3 dB | Diferencia sobre el umbral para considerar clara una posible entrada en voz. |
| Confirmación de voz clara o dudosa | 30 ms para cada caso | Tiempo que debe mantenerse la potencia sobre el umbral para confirmar voz. |
| Confirmación de silencio | 100 ms | Tiempo por debajo del umbral de salida para confirmar el silencio. |
| Percentil de ruido (`--percentil-ruido`) | 0 (desactivado) | Admite 1–99. Un valor mayor que 0 estima el nivel inicial con ese percentil de las potencias de todo el archivo. |
| Actualización de ruido (`--adaptacion-ruido`) | 0 (desactivada) | Admite valores de 0 a 1; por ejemplo, 0,01 ajusta lentamente la referencia durante el silencio firme. |

La calibración predeterminada supone que las primeras 10 tramas representan el ruido de fondo, por lo que se presupone que ese inicio no contiene voz relevante. El umbral de entrada a voz es el nivel de ruido más el margen de 5,49 dB. Para salir de voz se usa el umbral de entrada menos la histéresis. Esta diferencia evita que pequeñas variaciones hagan alternar continuamente entre voz y silencio.

El detector usa estados intermedios: espera a confirmar la voz (`MAYBE_VOICE`) o el silencio (`MAYBE_SILENCE`) antes de cambiar de estado. Si confirma una transición, corrige su límite hasta la primera trama candidata para reducir el retraso introducido por la espera.

Las dos opciones actúan en momentos distintos y se pueden usar por separado o juntas. `--percentil-ruido 20` activa una pasada inicial por todo el archivo y toma como referencia el percentil 20 de la potencia de sus tramas. `--adaptacion-ruido 0.01` actualiza después esa referencia con un paso del 1 % hacia la potencia de cada trama que ya está dentro de un silencio firme. El percentil fija el punto de partida; la adaptación permite seguir cambios lentos del ruido.

Con `-v` se muestran el tiempo, el estado, la potencia, el ZCR, el nivel de ruido y los umbrales de cada trama.

## 3. Evaluación sobre `db.v4`

La mejor ejecución registrada obtuvo **94,843 %** con un umbral de 5,49 dB y la corrección temporal de los límites. El resumen por clases fue:

| Clase | Sensibilidad | Precisión | F-score |
|---|---:|---:|---:|
| Voz | 97,12 % | 92,50 % | 96,16 % (β = 2) |
| Silencio | 87,70 % | 95,13 % | 93,54 % (β = 0,5) |
| **Total** |  |  | **94,843 %** |

### Pruebas de ajustes adicionales

Se probaron alternativas para que la referencia de ruido y los tiempos de decisión respondieran a las características del audio:

| Prueba | Ajustes | Resultado total |
|---|---|---:|
| Estimación por percentil | Percentil 20, actualización 0,01 y confirmación fija de 30 ms | 94,074 % |
| Estimación por percentil y confirmación variable | Los mismos ajustes, con 30 ms para voz clara y 50 ms para voz dudosa | 94,291 % |
| Valores predeterminados restaurados | Calibración inicial y actualización de ruido desactivada | 94,796 % |

Las variantes adaptativas no superaron la mejor medición de 94,843 %. Por eso los valores predeterminados dejan desactivados el percentil y la actualización: se calibra con las primeras 10 tramas y después se mantiene fija la referencia. La última ejecución con esos valores obtuvo 94,796 %, que también se redondea a 94,8 % con una cifra decimal.

También se valoró combinar potencia y ZCR para resolver tramas dudosas, estimar el ruido mediante amplitudes mínimas o aumentar automáticamente el nivel de los audios bajos. Esas reglas no se incorporaron a la evaluación final: el ZCR y la amplitud media no participan en la clasificación, y no se implementó una ganancia automática. La prueba adaptativa realizada estimaba el ruido mediante percentiles de potencia, no mediante el promedio de amplitudes mínimas.

## 4. Revisión auditiva de ejemplos

Se escucharon ejemplos con puntuaciones altas, medias y bajas para identificar qué condiciones podían explicar los aciertos y los errores. La revisión manual de los dos integrantes ayudó a decidir qué audios convenía analizar con más detalle y qué cambios probar.

- En `pav_2171.wav` la voz se distingue con claridad de un ruido suave, parecido a una brisa o interferencia.
- En `pav_2361.wav` las pausas son más largas y separan mejor los tramos de voz y silencio.
- En `pav_2109.wav` hay un ruido de fondo parecido a un petardeo, con un volumen cercano al de la voz.
- En `pav_2121.wav` la grabación tiene poco nivel. Subir el volumen del portátil ayuda a escucharla, pero no cambia la amplitud que procesa el programa.

En `db.v4` hay varias grabaciones con algunos nombres. La tabla muestra el promedio de acierto de cada nombre y el número de grabaciones incluidas:

| Archivo | Grabaciones | Acierto medio |
|---|---:|---:|
| `pav_2109` | 1 | 98,016 % |
| `pav_2171` | 9 | 95,601 % |
| `pav_2121` | 6 | 92,927 % |
| `pav_2361` | 2 | 98,828 % |

La revisión mostró que una misma configuración no obtiene el mismo resultado en todos los audios. Por eso se probaron ajustes para adaptar la referencia de ruido y los tiempos de confirmación. En `db.v4`, esos cambios no superaron la puntuación de la configuración anterior.

## 5. Ampliación

La opción `-w` genera un WAV de salida poniendo a cero los tramos que el detector clasifica como silencio. No aplica una cancelación espectral del ruido.

Los parámetros principales y sus valores predeterminados se describen en la sección 2. Se pueden cambiar al ejecutar el programa; `./bin/vad --help` muestra los nombres y formatos de todas las opciones.

Meson genera la cabecera de `docopt_c` al compilar, a partir de `src/vad.docopt`.

Esta captura muestra la ayuda y los valores predeterminados de la configuración actual:

![Ayuda de vad con los parámetros predeterminados](captura_ayuda.png)

## Compilación y evaluación

Desde la carpeta `P2`:

```sh
meson setup --reconfigure bin
ninja -C bin
scripts/run_vad.sh 5.49
```

Para guardar las etiquetas de voz y silencio:

```sh
./bin/vad -i pav_411.wav -o pav_411_auto.vad
```

## Comentarios finales

La puntuación de `db.v4` permitió escoger los parámetros con mejor resultado en esa base. La escucha de ejemplos concretos ayudó a entender por qué el ruido de fondo, el nivel de grabación y la duración de las pausas pueden cambiar la detección. El comportamiento en audios distintos se tendrá que comprobar con nuevas evaluaciones.