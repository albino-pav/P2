# Andrés Sánchez Alcántara


PAV - P2: detección de actividad vocal (VAD)
============================================

Esta práctica se distribuye a través del repositorio GitHub [Práctica 2](https://github.com/albino-pav/P2),
y una parte de su gestión se realizará mediante esta web de trabajo colaborativo.  Al contrario que Git,
GitHub se gestiona completamente desde un entorno gráfico bastante intuitivo. Además, está razonablemente
documentado, tanto internamente, mediante sus [Guías de GitHub](https://guides.github.com/), como
externamente, mediante infinidad de tutoriales, guías y vídeos disponibles gratuitamente en internet.


Inicialización del repositorio de la práctica.
----------------------------------------------

Para cargar los ficheros en su ordenador personal debe seguir los pasos siguientes:

*  Abra una cuenta GitHub para gestionar esta y el resto de prácticas del curso.
*  Cree un repositorio GitHub con el contenido inicial de la práctica (sólo debe hacerlo uno de los
  integrantes del grupo de laboratorio, cuya página GitHub actuará de repositorio central del grupo):
  -  Acceda la página de la [Práctica 2](https://github.com/albino-pav/P2).
  -  En la parte superior derecha encontrará el botón **`Fork`**. Apriételo y, después de unos segundos,
    se creará en su cuenta GitHub un proyecto con el mismo nombre (**P2**). Si ya tuviera uno con ese 
    nombre, se utilizará el nombre **P2-1**, y así sucesivamente.
*  Habilite al resto de miembros del grupo como *colaboradores* del proyecto; de este modo, podrán
  subir sus modificaciones al repositorio central:
  -  En la página principal del repositorio, en la pestaña **:gear:`Settings`**, escoja la opción 
    **Collaborators** y añada a su compañero de prácticas.
  -  Éste recibirá un email solicitándole confirmación. Una vez confirmado, tanto él como el
    propietario podrán gestionar el repositorio, por ejemplo: crear ramas en él o subir las
    modificaciones de su directorio local de trabajo al repositorio GitHub.
*  En la página principal del repositorio, localice el botón **Branch: master** y úselo para crear
  una rama nueva con los primeros apellidos de los integrantes del equipo de prácticas separados por
  guion (**fulano-mengano**).
*  Todos los miembros del grupo deben realizar su copia local en su ordenador personal.
  -  Copie la dirección de su copia del repositorio apretando en el botón **Clone or download**.
    Asegúrese de usar *Clone with HTTPS*.
  -  Abra una sesión de Bash en su ordenador personal y vaya al directorio **PAV**. Desde ahí, ejecute:

    ```.sh
    git clone dirección-del-fork-de-la-práctica
    ```

  -  Vaya al directorio de la práctica `cd P2`.

  -  Cambie a la rama **fulano-mengano** con la orden:

    ```.sh
    git checkout fulano-mengano
    ```

*  A partir de este momento, todos los miembros del grupo de prácticas pueden trabajar en su directorio
  local del modo habitual, usando el repositorio remoto en GitHub como repositorio central para el trabajo colaborativo
  de los distintos miembros del grupo de prácticas o como copia de seguridad.
  -  Puede *confirmar* versiones del proyecto en su directorio local con las órdenes siguientes:

    ```.sh
    git add .
    git commit -m "Mensaje del commit"
    ```

  -  Las versiones confirmadas, y sólo ellas, se almacenan en el repositorio y pueden ser accedidas en cualquier momento.

*  Para interactuar con el contenido remoto en GitHub es necesario que los cambios en el directorio local estén confirmados.

  -  Puede comprobar si el directorio está *limpio* (es decir, si la versión actual está confirmada) usando el comando
    `git status`.

  -  La versión actual del directorio local se sube al repositorio remoto con la orden:

    ```.sh
    git push
    ```

    *  Si el repositorio remoto contiene cambios no presentes en el directorio local, `git` puede negarse
      a subir el nuevo contenido.

      -  En ese caso, lo primero que deberemos hacer es incorporar los cambios presentes en el repositorio
        GitHub con la orden `git pull`.

      -  Es posible que, al hacer el `git pull` aparezcan *conflictos*; es decir, ficheros que se han modificado
        tanto en el directorio local como en el repositorio GitHub y que `git` no sabe cómo combinar.

      -  Los conflictos aparecen marcados con cadenas del estilo `>>>>`, `<<<<` y `====`. Los ficheros correspondientes
        deben ser editados para decidir qué versión preferimos conservar. Un editor avanzado, del estilo de Microsoft
        Visual Studio Code, puede resultar muy útil para localizar los conflictos y resolverlos.

      -  Tras resolver los conflictos, se ha de confirmar los cambios con `git commit` y ya estaremos en condiciones
        de subir la nueva versión a GitHub con el comando `git push`.


  -  Para bajar al directorio local el contenido del repositorio GitHub hay que ejecutar la orden:

    ```.sh
    git pull
    ```
  
    *  Si el repositorio local contiene cambios no presentes en el directorio remoto, `git` puede negarse a bajar
      el contenido de este último.

      -  La resolución de los posibles conflictos se realiza como se explica más arriba para
        la subida del contenido local con el comando `git push`.



*  Al final de la práctica, la rama **fulano-mengano** del repositorio GitHub servirá para remitir la
  práctica para su evaluación utilizando el mecanismo *pull request*.
  -  Vaya a la página principal de la copia del repositorio y asegúrese de estar en la rama
    **fulano-mengano**.
  -  Pulse en el botón **New pull request**, y siga las instrucciones de GitHub.


Entrega de la práctica.
-----------------------

Responda, en este mismo documento (README.md), los ejercicios indicados a continuación. Este documento es
un fichero de texto escrito con un formato denominado _**markdown**_. La principal característica de este
formato es que, manteniendo la legibilidad cuando se visualiza con herramientas en modo texto (`more`,
`less`, editores varios, ...), permite amplias posibilidades de visualización con formato en una amplia
gama de aplicaciones; muy notablemente, **GitHub**, **Doxygen** y **Facebook** (ciertamente, :eyes:).

En GitHub. cuando existe un fichero denominado README.md en el directorio raíz de un repositorio, se
interpreta y muestra al entrar en el repositorio.

Debe redactar las respuestas a los ejercicios usando Markdown. Puede encontrar información acerca de su
sintáxis en la página web [Sintaxis de Markdown](https://daringfireball.net/projects/markdown/syntax).
También puede consultar el documento adjunto [MARKDOWN.md](MARKDOWN.md), en el que se enumeran los
elementos más relevantes para completar la redacción de esta práctica.

Recuerde realizar el *pull request* una vez completada la práctica.

Ejercicios
----------

### Etiquetado manual de los segmentos de voz y silencio

- Grabe una señal de voz en la que haya distintos segmentos de voz y silencio. La señal debe ser de un
  solo canal (monofónica), grabada con una frecuencia de muestreo de 16 kHz y codificada con PCM lineal
  de 16 bits.

  Nombre a la señal como `pav_GGP#.wav`, donde GG es el grupo de clase (por ejemplo, 21 o 41), P es el
  número del puesto de trabajo y # es el número de señal (si sólo se entrega una señal, este número es
  1).

  > NOTA: es habitual que las grabaciones empiecen con un segmento de silencio de potencia extremadamente
  > bajo; mucho más bajo que el nivel de ruido normal durante el resto de la señal. Si esto ocurre, la
  > detección usando como nivel de referencia para el silencio el segmento inicial se ve seriamente
  > dificultada. Puede detectar esta situación visualizando el nivel de potencia estimado por el propio
  > `wavesurfer` y corregirla usando la herramienta de corte (:scissors:).

- Etiquete manualmente los segmentos de voz y silencio del fichero grabado al efecto. Inserte, a
  continuación, una captura de `wavesurfer` en la que se vea con claridad la señal temporal, el contorno de
  potencia y la tasa de cruces por cero, junto con el etiquetado manual de los segmentos.

- A la vista de la gráfica, indique qué valores considera adecuados para las magnitudes siguientes:

  * Incremento del nivel potencia en dB, respecto al nivel correspondiente al silencio inicial, para
    estar seguros de que un segmento de señal se corresponde con voz.

  * Duración mínima razonable de los segmentos de voz y silencio.

  * ¿Es capaz de sacar alguna conclusión a partir de la evolución de la tasa de cruces por cero?



**Grabación y etiquetado manual**

Se ha utilizado una grabación propia en formato WAV, monofónica, con una frecuencia de muestreo de 16 kHz y codificación PCM lineal de 16 bits.

**Nota sobre la nomenclatura de los archivos**

El grupo de clase es el **41**. Debido a que no he podido confirmar mi número de puesto de laboratorio, he utilizado el identificador `pav_41_andres_sanchez` en lugar del formato `pav_GGP#` indicado en el enunciado.

Los archivos correspondientes a la grabación definitiva son:

- `pav_41_andres_sanchez.wav`: señal de voz recortada, de 9,361375 segundos.
- `pav_41_andres_sanchez.lab`: etiquetado manual de voz y silencio.
- `pav_41_andres_sanchez.vad`: etiquetado generado automáticamente por el detector.

Los tres archivos corresponden a la misma señal. Se ha incluido el grupo y el nombre del estudiante para permitir su identificación.

Al analizarla en WaveSurfer se observó que el silencio tenía una potencia demasiado baja justo en el momento inicial. Se recortó ese fragmento inicial para mejorar la estimación del nivel de referencia del silencio.

Los segmentos de voz (`V`) y silencio (`S`) se etiquetaron manualmente mediante la escucha y la observación de la forma de onda y la potencia. Las etiquetas se guardaron en `pav_41_andres_sanchez.lab`.

La siguiente captura muestra la forma de onda, la potencia, la ZCR, las etiquetas manuales y la detección automática:

![Forma de onda, potencia, ZCR y etiquetado](img/comparacion_vad.png)

**1. Incremento de potencia respecto al silencio inicial**

En la gráfica se observa que los fragmentos de voz presentan, en general, una potencia claramente superior a la del silencio. Para identificar visualmente los segmentos de voz más evidentes, un incremento de varias decenas de dB permite distinguirlos del ruido de fondo, aunque los límites de algunos segmentos tienen una potencia menor.

En una primera versión del detector se seleccionó un umbral de 5,1 dB, obteniendo una puntuación global del 90,845 % sobre `db.v4`. Posteriormente, al incorporar un mecanismo de confirmación temporal del silencio y optimizar sus parámetros, se seleccionó un umbral de 9,5 dB con un hangover de 100 ms. Esta configuración obtuvo un 93,933 % en la misma base de datos.

**2. Duración mínima razonable de los segmentos de voz y silencio**

Dado que el análisis se realiza en tramas de 10 ms, se considera razonable proponer una duración mínima inicial de **50 ms para voz y 50 ms para silencio**, con el objetivo de evitar cambios de estado provocados por fluctuaciones muy breves de la potencia.

No obstante, en la grabación etiquetada aparece una pausa real de aproximadamente 65 ms. Por tanto, utilizar duraciones mínimas demasiado elevadas podría eliminar pausas auténticas.

En la versión final se ha implementado un mecanismo de hangover de 100 ms para confirmar el paso de voz a silencio. No se ha implementado una duración mínima equivalente para confirmar la entrada en voz. Los 50 ms planteados anteriormente eran una estimación inicial a partir de la señal, mientras que los 100 ms se seleccionaron después mediante pruebas experimentales sobre `db.v4`.

**3. Conclusiones sobre la tasa de cruces por cero (ZCR)**

La ZCR presenta variaciones a lo largo de la grabación y picos destacados en algunos fragmentos de voz. Sin embargo, también se observan cruces por cero durante los silencios y segmentos de voz con valores relativamente bajos.

Esto es coherente con el hecho de que los sonidos sonoros, habitualmente más periódicos, pueden presentar menos cruces por cero que los sonidos sordos o ciertos tipos de ruido.

Por tanto, la ZCR es una característica complementaria a la potencia, pero no es suficiente por sí sola para distinguir de manera fiable entre voz y silencio.




### Desarrollo del detector de actividad vocal

- Complete el código de los ficheros de la práctica para implementar un detector de actividad vocal en
  tiempo real tan exacto como sea posible. Tome como objetivo la maximización de la puntuación-F `TOTAL`.

- Inserte una gráfica en la que se vea con claridad la señal temporal, el etiquetado manual y la detección
  automática conseguida para el fichero grabado al efecto. 

- Explique, si existen. las discrepancias entre el etiquetado manual y la detección automática.

- Evalúe los resultados sobre la base de datos `db.v4` con el script `vad_evaluation.pl` e inserte a 
  continuación las tasas de sensibilidad (*recall*) y precisión para el conjunto de la base de datos (sólo
  el resumen).





**Implementación del detector de actividad vocal**

Se ha implementado un detector VAD basado en la potencia de la señal, trabajando con tramas de 10 ms. Para cada trama se calcula la potencia mediante `compute_power()` de `pav_analysis.c`, reutilizando las funciones desarrolladas en la P1.

El detector utiliza tres estados principales:

- `ST_INIT`: almacena la potencia de la primera trama como referencia inicial del ruido.
- `ST_SILENCE`: permanece en silencio hasta que la potencia supera el umbral.
- `ST_VOICE`: permanece en voz hasta confirmar que la potencia se ha mantenido por debajo del umbral durante un número determinado de tramas consecutivas.

Inicialmente se utilizaba un único umbral de potencia, sin ningún mecanismo para evitar cambios rápidos de estado.

Posteriormente se añadió un mecanismo de *hangover*, mediante un contador de tramas consecutivas de baja potencia. Si la potencia vuelve a superar el umbral antes de alcanzar el número mínimo de tramas, el contador se reinicia y el detector permanece en voz.

Se probaron diferentes duraciones de *hangover* y distintos umbrales sobre `db.v4`, utilizando como criterio la maximización de la puntuación `TOTAL`.

La configuración final seleccionada fue:

- **Umbral relativo:** 9,5 dB.
- **Hangover:** 10 tramas consecutivas, equivalentes a 100 ms.

Esta mejora reduce la fragmentación de los segmentos de voz provocada por caídas breves de potencia. Como contrapartida, también puede prolongar las detecciones de voz dentro de algunos intervalos de silencio.

**Comparación entre el etiquetado manual y el automático**

La siguiente captura muestra la señal temporal, la potencia, la ZCR, el etiquetado manual y la detección automática de la grabación recortada:

![Comparación entre etiquetado manual y detección automática](img/comparacion_vad.png)

El detector identifica correctamente los principales fragmentos de voz, pero presenta algunas discrepancias durante los silencios. Estas se deben a fluctuaciones de potencia que pueden superar el umbral y al tiempo adicional que el algoritmo espera antes de pasar de voz a silencio.

También se observó que la grabación original comenzaba con un silencio de potencia anormalmente baja. Siguiendo la recomendación del enunciado, se recortó ese fragmento inicial antes de realizar el etiquetado y la evaluación definitiva.

**Evaluación sobre la grabación propia**

Con la nueva configuración de 9,5 dB y 100 ms de *hangover*, los resultados fueron:

- Recall de voz: 100,00 %
- Precisión de voz: 73,81 %
- Recall de silencio: 64,31 %
- Precisión de silencio: 100,00 %
- **TOTAL: 91,674 %**

La primera versión del detector había obtenido un 92,857 % sobre esta grabación recortada. Por tanto, aunque la nueva configuración mejora los resultados globales sobre `db.v4`, empeora ligeramente la puntuación de esta grabación concreta.

**Evaluación sobre la base de datos `db.v4`**

Se ha evaluado la versión mejorada utilizando el script `vad_evaluation.pl`, con un umbral de 9,5 dB y un *hangover* de 100 ms.

El resumen global obtenido fue:

- Recall V: 97,83 %
- Precision V: 88,23 %
- F-score V (2): 95,75 %
- Recall S: 79,63 %
- Precision S: 95,93 %
- F-score S (1/2): 92,15 %
- **TOTAL: 93,933 %**

La versión inicial obtenía un 90,845 %, por lo que la mejora conseguida es de **3,088 puntos porcentuales**.

Los resultados muestran una mejora importante en la detección de voz, aunque el detector sigue teniendo dificultades para distinguir algunos intervalos silenciosos.

Como posibles mejoras futuras podrían incorporarse histéresis entre los umbrales de entrada y salida de voz, una duración mínima para entrar en estado de voz o una estimación adaptativa del ruido. Estas funcionalidades no están implementadas en la versión actual.



### Trabajos de ampliación

#### Cancelación del ruido en los segmentos de silencio

- Si ha desarrollado el algoritmo para la cancelación de los segmentos de silencio, inserte una gráfica en
  la que se vea con claridad la señal antes y después de la cancelación (puede que `wavesurfer` no sea la
  mejor opción para esto, ya que no es capaz de visualizar varias señales al mismo tiempo).

#### Gestión de las opciones del programa usando `docopt_c`

- Si ha usado `docopt_c` para realizar la gestión de las opciones y argumentos del programa `vad`, inserte
  una captura de pantalla en la que se vea el mensaje de ayuda del programa.

**Ampliación realizada**

Se ha utilizado la biblioteca `docopt_c` para gestionar las opciones y argumentos del programa `vad`.

El programa permite especificar el archivo de audio de entrada, el archivo de etiquetas de salida y el umbral de detección mediante argumentos de la línea de comandos.

Se ha establecido un umbral predeterminado de 9,5 dB, seleccionado experimentalmente mediante la evaluación sobre `db.v4`. De esta forma, el detector puede ejecutarse sin indicar explícitamente el umbral.

La siguiente captura muestra el mensaje de ayuda generado mediante `docopt_c`:

![Ayuda del programa VAD con docopt_c](img/ayuda_docopt.png)

### Contribuciones adicionales y/o comentarios acerca de la práctica

- Indique a continuación si ha realizado algún tipo de aportación suplementaria (algoritmos de detección o 
  parámetros alternativos, etc.).

- Si lo desea, puede realizar también algún comentario acerca de la realización de la práctica que
  considere de interés de cara a su evaluación.

Como contribución adicional se han realizado diferentes pruebas para optimizar los parámetros del detector de actividad vocal.

Primero se estudió el efecto del umbral de potencia. Después se incorporó un mecanismo de *hangover* para evitar cambios de estado provocados por caídas breves de potencia.

Se realizaron varios barridos de valores, combinando umbrales de potencia y duraciones de *hangover*. La mejor configuración entre las probadas fue de 9,5 dB y 100 ms, con una puntuación `TOTAL` del 93,933 % sobre `db.v4`.

El proceso permitió comprobar que aumentar la duración del *hangover* mejora la detección de algunos fragmentos de voz, pero también puede aumentar la cantidad de silencio clasificado como voz. Por ello, fue necesario ajustar conjuntamente ambos parámetros.


### Antes de entregar la práctica

Recuerde comprobar que el repositorio cuenta con los códigos correctos y en condiciones de ser 
correctamente compilados con la orden `meson bin; ninja -C bin`. El programa generado (`bin/vad`) será
el usado, sin más opciones, para realizar la evaluación *ciega* del sistema.
