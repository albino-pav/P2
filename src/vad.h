#ifndef _VAD_H
#define _VAD_H
#include <stdio.h>

/* Estats de l'autòmat */
typedef enum {ST_UNDEF=0, ST_SILENCE, ST_VOICE, ST_INIT,
              ST_MAYBE_VOICE, ST_MAYBE_SILENCE} VAD_STATE;

/* Return a string label associated to each state */
const char *state2str(VAD_STATE st);

typedef struct {
  VAD_STATE state;
  float sampling_rate;
  unsigned int frame_length;
  float last_feature;      /* for debugging purposes */

  /* Estimació del soroll de fons */
  unsigned int n_init;     /* trames llegides durant la inicialització */
  double suma_pot_init;    /* suma de potència (lineal) de les trames inicials */
  float k0;                /* nivell de soroll (dB) */
  float k1;                /* llindar per entrar a veu  (k0 + alfa1) */
  float k2;                /* llindar per tornar a silenci (k0 + alfa2) */

  /* Comptador de trames en un estat dubtós */
  unsigned int n_maybe;
} VAD_DATA;

VAD_DATA *vad_open(float sampling_rate);
unsigned int vad_frame_size(VAD_DATA *);

/* Retorna ST_SILENCE, ST_VOICE o ST_UNDEF (encara no es pot decidir) */
VAD_STATE vad(VAD_DATA *vad_data, float *x, float llindar);

VAD_STATE vad_close(VAD_DATA *vad_data);
void vad_show_state(const VAD_DATA *vad_data, FILE *out, float llindar);

#endif
