Berta Martínez i Alejandro Urioste
============================================ 

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
  continuación, una captura de `wavesurfer` en la que se vea con claridad la señal temporal, el contorno de potencia y la tasa de cruces por cero, junto con el etiquetado manual de los segmentos.

![Etiquetado manual en WaveSurfer](img/grafica_classificacio.png)


> **Respuesta:** En la captura se muestran los distintos paneles de WaveSurfer para la grabación `pav_4061.wav`, de unos 22 segundos y muestreada a 16 kHz. Podemos ver la forma de onda, la evolución de la potencia, la tasa de cruces por cero (ZCR) y el etiquetado manual que hemos realizado, donde `V` corresponde a voz y `S` a silencio.


- A la vista de la gráfica, indique qué valores considera adecuados para las magnitudes siguientes:

  * Incremento del nivel potencia en dB, respecto al nivel correspondiente al silencio inicial, para estar seguros de que un segmento de señal se corresponde con voz.



> **Respuesta:** En los tramos de silencio vemos que la potencia suele estar entre -25 dB y -10 dB, mientras que cuando hay voz aumenta bastante, llegando a unos 40–65 dB en las vocales. Algunas consonantes tienen menos energía y pueden quedarse cerca de los 30 dB.
>
> Por eso, consideramos que un incremento de unos 10–15 dB respecto al ruido de fondo sería suficiente para detectar voz sin confundirla con pequeñas variaciones del ruido. Además, el umbral no sería tan alto como para perder las consonantes más débiles.


Por eso, usaríamos un umbral de unos $10\text{--}15\text{ dB}$ por encima del ruido de fondo. Así evitamos detectar pequeñas variaciones del ruido como voz sin exigir una potencia tan alta que perdamos las consonantes más débiles. El umbral concreto depende del nivel de silencio que se tome como referencia.
  * Duración mínima razonable de los segmentos de voz y silencio.



> **Respuesta:**
>
> - **Voz (V):** La palabra más corta que hemos grabado, "Hola", dura aproximadamente 280 ms. Como trabajamos con tramas de 10 ms, creemos que con unas 3–5 tramas seguidas (30–50 ms) ya podemos confirmar que hay voz y evitar detectar ruidos muy puntuales.
>
> - **Silencio (S):** La pausa más corta que hemos etiquetado dura unos 180 ms. También hay que tener en cuenta que algunas consonantes, como la /p/, /t/ o /k/, pueden provocar caídas breves de potencia sin que realmente termine la palabra. Por eso, consideramos razonable exigir unos 150–200 ms para confirmar un silencio. En la implementación hemos acabado utilizando 120 ms para no alargar demasiado los finales de voz.

  * ¿Es capaz de sacar alguna conclusión a partir de la evolución de la tasa de cruces por cero?


> **Respuesta:** Sí, vemos que la ZCR cambia bastante según el tipo de sonido. En las vocales, que tienen una señal más periódica, la ZCR suele ser baja y bastante estable. En cambio, las consonantes fricativas sordas, como la /s/ o la /f/, tienen menos potencia pero presentan picos de ZCR mucho más altos, que en nuestra grabación llegan aproximadamente a 2500–4500 Hz.
>
> En los silencios la ZCR suele ser baja, aunque puede variar debido al ruido de fondo. Por tanto, no podemos utilizarla por sí sola para detectar voz, pero sí que nos ayuda a identificar consonantes que podrían pasar desapercibidas si solo mirásemos la potencia.


### Desarrollo del detector de actividad vocal

- Complete el código de los ficheros de la práctica para implementar un detector de actividad vocal en tiempo real tan exacto como sea posible. Tome como objetivo la maximización de la puntuación-F `TOTAL`.

- Inserte una gráfica en la que se vea con claridad la señal temporal, el etiquetado manual y la detección automática conseguida para el fichero grabado al efecto. 

![Detección automática frente a etiquetado manual](img/grafica_vad.png)


> **Respuesta:** En la gráfica comparamos el etiquetado manual (`pav_4061.lab`) con el generado por nuestro detector (`pav_4061_auto.lab`) para la grabación `pav_4061.wav`. La detección automática se ha realizado utilizando el umbral por defecto de 12 dB.
>
> Podemos ver que los segmentos detectados coinciden bastante bien con los que habíamos marcado manualmente, aunque hay algunas diferencias en los instantes de inicio y final de la voz.


- Explique, si existen. las discrepancias entre el etiquetado manual y la detección automática.


> **Respuesta:** El detector consigue identificar los mismos 7 segmentos de voz y 8 de silencio que habíamos etiquetado manualmente. Las principales diferencias están en los instantes en los que empieza o termina cada segmento.
>
> - **Finales de voz:** En algunos casos, el detector tarda un poco más en volver al estado de silencio. Por ejemplo, hay un segmento que termina manualmente en 15,59 s y automáticamente en 15,86 s. Esto ocurre en parte porque hemos añadido un tiempo de espera de 120 ms antes de confirmar el silencio, para evitar cortar palabras cuando hay pequeñas caídas de potencia. El resto de la diferencia puede deberse a cómo se detecta el final de la señal de voz.
>
> - **Inicios de voz:** En la primera palabra, "Hola", el detector empieza a marcar voz en 0,080 s, mientras que manualmente la habíamos marcado en 0,125 s. Es posible que esté detectando algún sonido débil anterior al inicio de la vocal.
>
> En general, estamos bastante satisfechos con el resultado, ya que el detector encuentra los mismos segmentos y las diferencias se concentran principalmente en sus límites.

- Evalúe los resultados sobre la base de datos `db.v4` con el script `vad_evaluation.pl` e inserte a continuación las tasas de sensibilidad (*recall*) y precisión para el conjunto de la base de datos (sólo
  el resumen).


> **Respuesta:** Hemos evaluado el detector sobre la base de datos `db.v4` utilizando el umbral por defecto de 12 dB. La puntuación-F total obtenida es del **93,952 %**.
>
> ```text
> **************** Summary ****************
> Recall V:606.47/625.02 97.03%   Precision V:606.47/671.64 90.30%   F-score V (2)  : 95.61%
> Recall S:335.29/400.47 83.73%   Precision S:335.29/353.84 94.76%   F-score S (1/2): 92.33%
> ===> TOTAL: 93.952%
> ```



### Trabajos de ampliación

#### Cancelación del ruido en los segmentos de silencio

- Si ha desarrollado el algoritmo para la cancelación de los segmentos de silencio, inserte una gráfica en
  la que se vea con claridad la señal antes y después de la cancelación (puede que `wavesurfer` no sea la
  mejor opción para esto, ya que no es capaz de visualizar varias señales al mismo tiempo).

#### Gestión de las opciones del programa usando `docopt_c`

- Si ha usado `docopt_c` para realizar la gestión de las opciones y argumentos del programa `vad`, inserte
  una captura de pantalla en la que se vea el mensaje de ayuda del programa.


### Contribuciones adicionales y/o comentarios acerca de la práctica

- Indique a continuación si ha realizado algún tipo de aportación suplementaria (algoritmos de detección o parámetros alternativos, etc.).

- Indique a continuación si ha realizado algún tipo de aportación suplementaria (algoritmos de detección o parámetros alternativos, etc.).


> **Respuesta:** Hemos añadido algunas modificaciones al detector inicial para mejorar la detección y evitar que cambie constantemente entre voz y silencio cuando hay ruidos o pausas cortas.
>
> - **Estados intermedios:** Hemos utilizado los estados `ST_MAYBE_VOICE` y `ST_MAYBE_SILENCE` para no cambiar de estado directamente por una sola trama. Para confirmar el inicio de voz esperamos 3 tramas (30 ms), excepto cuando la potencia aumenta mucho de golpe. Para volver a silencio esperamos 12 tramas (120 ms), evitando así cortar palabras por pequeñas caídas de potencia.
>
> - **Uso de la ZCR:** Como vimos en WaveSurfer, algunas consonantes como la /s/ o la /f/ tienen poca potencia pero una ZCR elevada. Por eso, cuando la ZCR supera los 2500 Hz y la potencia está algo por encima del ruido de fondo, también consideramos que puede haber voz. Esto ayuda a no perder algunas consonantes al principio o al final de las palabras.
>
> - **Actualización del ruido de fondo:** Inicialmente el ruido se calculaba con las 5 primeras tramas y se mantenía fijo. Lo hemos modificado para que se vaya actualizando cuando el detector está en `ST_SILENCE`. Si la potencia actual es menor que la estimada, la actualizamos con un peso del 15 %. Si es mayor, utilizamos solo un 2 % para que el umbral no aumente demasiado por un ruido puntual.
>
> - **Límite inferior del ruido:** También hemos tenido en cuenta que algunas grabaciones empiezan con un silencio casi digital, con una potencia mucho menor que el ruido habitual de la sala. Para evitar que esto afecte al detector, estimamos la potencia de voz (`potencia_veu`) y limitamos la diferencia entre esta y `potencia_soroll` a 55 dB.
>
> Con estos cambios conseguimos que el detector sea más estable y se adapte mejor a las variaciones de potencia y ruido durante la grabación.


- Si lo desea, puede realizar también algún comentario acerca de la realización de la práctica que
  considere de interés de cara a su evaluación.


### Antes de entregar la práctica

Recuerde comprobar que el repositorio cuenta con los códigos correctos y en condiciones de ser 
correctamente compilados con la orden `meson bin; ninja -C bin`. El programa generado (`bin/vad`) será
el usado, sin más opciones, para realizar la evaluación *ciega* del sistema.
