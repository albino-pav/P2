#ifndef _VAD_H
#define _VAD_H
#include <stdio.h>

/* DONE: add the needed states */
typedef enum {ST_UNDEF=0, ST_SILENCE, ST_VOICE, ST_INIT, ST_MAYBE_VOICE, ST_MAYBE_SILENCE} VAD_STATE;

/* Return a string label associated to each state */
const char *state2str(VAD_STATE st);

/* DONE: add the variables needed to control the VAD 
   (counts, thresholds, etc.) */

typedef struct {
   VAD_STATE state;
   float sampling_rate;
   unsigned int frame_length;
   float last_feature; /* potencia en dB */
   float last_zcr;     /* tasa de cruces por cero */

   /* Parámetros y umbrales del FSA */
   float k0;           /* Nivel de referencia de ruido (dB) */
   float k1;           /* Umbral de posible voz: k0 + alpha1 */
   float k2;           /* Umbral de confirmación de voz: k1 + alpha2 */
   float alpha1;
   float alpha2;

   unsigned int n_init;        /* Número de tramas para inicializar ruido */
   unsigned int min_voice;     /* Tramas mínimas para confirmar voz */
   unsigned int min_silence;   /* Tramas mínimas para confirmar silencio */
   unsigned int max_maybe_v;   /* Tiempo máximo en maybe_voice sin superar k2 */

   /* Contadores internos */
   unsigned int count_init;
   unsigned int count_state;
   int high_power_seen;        /* Flag: se ha superado k2 en maybe_voice */
   double sum_power_lin;       /* Acumulador de potencia lineal en ST_INIT */
} VAD_DATA;

/* Call this function before using VAD: 
   It should return allocated and initialized values of vad_data

   sampling_rate: ... the sampling rate */
VAD_DATA *vad_open(float sampling_rate, float alpha1, float alpha2, unsigned int min_voice, unsigned int min_silence, unsigned int n_init);

/* vad works frame by frame.
   This function returns the frame size so that the program knows how
   many samples have to be provided */
unsigned int vad_frame_size(VAD_DATA *);

/* Main function. For each 'time', compute the new state 
   It returns:
    ST_UNDEF   (0) : undefined; it needs more frames to take decission
    ST_SILENCE (1) : silence
    ST_VOICE   (2) : voice

    x: input frame
       It is assumed the length is frame_length */
VAD_STATE vad(VAD_DATA *vad_data, float *x);

/* Free memory
   Returns the state of the last (undecided) states. */
VAD_STATE vad_close(VAD_DATA *vad_data);

/* Print actual state of vad, for debug purposes */
void vad_show_state(const VAD_DATA *, FILE *);

#endif
