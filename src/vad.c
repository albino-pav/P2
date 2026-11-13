#include <math.h>
#include <stdlib.h>
#include <stdio.h>

#include "vad.h"
#include "pav_analysis.h"

const float FRAME_TIME = 10.0F; /* in ms. */

/* Paràmetres de l'autòmat (ajustats sobre db.v4) */
#define N_INIT       10    /* trames per estimar el soroll inicial (100 ms)      */
#define ALFA2        3.0F  /* dB per sobre del soroll per sortir de veu         */
#define MIN_VOICE    4     /* trames mínimes per confirmar veu     (40 ms)     */
#define MIN_SILENCE  15    /* trames mínimes per confirmar silenci (150 ms)    */

const char *state_str[] = {
  "UNDEF", "S", "V", "INIT", "MV", "MS"
};

const char *state2str(VAD_STATE st) {
  return state_str[st];
}

typedef struct {
  float zcr;
  float p;
  float am;
} Features;

Features compute_features(const float *x, int N, float fm) {
  Features feat;
  feat.p   = compute_power(x, N);
  feat.am  = compute_am(x, N);
  feat.zcr = compute_zcr(x, N, fm);
  return feat;
}

VAD_DATA * vad_open(float rate) {
  VAD_DATA *vad_data = malloc(sizeof(VAD_DATA));
  vad_data->state = ST_INIT;
  vad_data->sampling_rate = rate;
  vad_data->frame_length = rate * FRAME_TIME * 1e-3;
  vad_data->last_feature = 0;
  vad_data->n_init = 0;
  vad_data->suma_pot_init = 0;
  vad_data->k0 = vad_data->k1 = vad_data->k2 = 0;
  vad_data->n_maybe = 0;
  return vad_data;
}

VAD_STATE vad_close(VAD_DATA *vad_data) {
  /* Les últimes trames dubtoses es queden amb l'últim estat confirmat */
  VAD_STATE state = vad_data->state;
  if (state == ST_MAYBE_VOICE)   state = ST_SILENCE;
  if (state == ST_MAYBE_SILENCE) state = ST_VOICE;
  if (state == ST_INIT)          state = ST_SILENCE;
  free(vad_data);
  return state;
}

unsigned int vad_frame_size(VAD_DATA *vad_data) {
  return vad_data->frame_length;
}

/*
 * Autòmat d'estats finits:
 *
 *  INIT ──(N_INIT trames)──> SILENCE
 *  SILENCE ──(p > k1)──> MAYBE_VOICE
 *  MAYBE_VOICE ──(p > k2 durant MIN_VOICE trames)──> VOICE
 *  MAYBE_VOICE ──(p < k2)──> SILENCE
 *  VOICE ──(p < k2)──> MAYBE_SILENCE
 *  MAYBE_SILENCE ──(p < k1 durant MIN_SILENCE trames)──> SILENCE
 *  MAYBE_SILENCE ──(p > k1)──> VOICE
 */
VAD_STATE vad(VAD_DATA *vad_data, float *x, float alfa1) {

  Features f = compute_features(x, vad_data->frame_length, vad_data->sampling_rate);
  vad_data->last_feature = f.p;

  switch (vad_data->state) {
  case ST_INIT:
    /* Mitjana de la potència (en escala lineal) de les primeres trames */
    vad_data->suma_pot_init += pow(10, f.p / 10);
    if (++vad_data->n_init >= N_INIT) {
      vad_data->k0 = 10 * log10(vad_data->suma_pot_init / vad_data->n_init);
      vad_data->k1 = vad_data->k0 + alfa1;
      vad_data->k2 = vad_data->k0 + ALFA2;
      vad_data->state = ST_SILENCE;
    }
    break;

  case ST_SILENCE:
    if (f.p > vad_data->k1) {
      vad_data->state = ST_MAYBE_VOICE;
      vad_data->n_maybe = 1;
    }
    break;

  case ST_MAYBE_VOICE:
    if (f.p < vad_data->k2)
      vad_data->state = ST_SILENCE;             /* era un soroll curt */
    else if (++vad_data->n_maybe >= MIN_VOICE)
      vad_data->state = ST_VOICE;               /* veu confirmada */
    break;

  case ST_VOICE:
    if (f.p < vad_data->k2) {
      vad_data->state = ST_MAYBE_SILENCE;
      vad_data->n_maybe = 1;
    }
    break;

  case ST_MAYBE_SILENCE:
    if (f.p > vad_data->k1)
      vad_data->state = ST_VOICE;               /* era una pausa curta */
    else if (++vad_data->n_maybe >= MIN_SILENCE)
      vad_data->state = ST_SILENCE;             /* silenci confirmat */
    break;

  case ST_UNDEF:
    break;
  }

  if (vad_data->state == ST_SILENCE || vad_data->state == ST_VOICE)
    return vad_data->state;
  else
    return ST_UNDEF;
}

void vad_show_state(const VAD_DATA *vad_data, FILE *out, float llindar) {
  fprintf(out, "%d\t%f\n", vad_data->state, vad_data->last_feature);
}
