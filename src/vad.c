#include <math.h>
#include <stdlib.h>
#include <stdio.h>

#include "vad.h"
#include "pav_analysis.h"

const float FRAME_TIME = 10.0F; /* in ms. */

/* 
 * As the output state is only ST_VOICE, ST_SILENCE, or ST_UNDEF,
 * only this labels are needed. You need to add all labels, in case
 * you want to print the internal state in string format
 */

const char *state_str[] = {
  "UNDEF", "S", "V", "INIT", "MAYBE_V", "MAYBE_S"
};

const char *state2str(VAD_STATE st) {
  return state_str[st];
}

/* Define a datatype with interesting features */
typedef struct {
  float zcr;
  float p;
  float am;
} Features;

/* 
 * DONE: Delete and use your own features!
 */

Features compute_features(const float *x, int N, float fm) {
  /*
   * Input: x[i] : i=0 .... N-1 
   * Ouput: computed features
   */
  /* 
   * DELETE and include a call to your own functions
   *
   * For the moment, compute random value between 0 and 1 
   */
  /*DONE*/
  Features feat;
  feat.p   = compute_power(x, N);
  feat.am  = compute_am(x, N);
  feat.zcr = compute_zcr(x, N, fm);
  return feat;
}

/* 
 * DONE: Init the values of vad_data
 */

VAD_DATA *vad_open(float rate, float alpha1, float alpha2, unsigned int min_voice, unsigned int min_silence, unsigned int n_init) {
  VAD_DATA *vad_data = malloc(sizeof(VAD_DATA));
  vad_data->state          = ST_INIT;
  vad_data->sampling_rate  = rate;
  vad_data->frame_length   = rate * FRAME_TIME * 1e-3;
  vad_data->last_feature   = 0.0f;
  vad_data->last_zcr       = 0.0f;

  vad_data->alpha1         = alpha1;
  vad_data->alpha2         = alpha2;
  vad_data->k0             = -100.0f;
  vad_data->k1             = -100.0f;
  vad_data->k2             = -100.0f;

  vad_data->n_init         = (n_init > 0) ? n_init : 1;
  vad_data->min_voice      = min_voice;
  vad_data->min_silence    = min_silence;
  vad_data->max_maybe_v    = 25; /* máx 250 ms para fonemas débiles iniciales */

  vad_data->count_init     = 0;
  vad_data->count_state    = 0;
  vad_data->high_power_seen = 0;
  vad_data->sum_power_lin  = 0.0;

  return vad_data;
}

VAD_STATE vad_close(VAD_DATA *vad_data) {
  /* 
   * DONE: decide what to do with the last undecided frames
   */
  /* Si quedan tramas pendientes (UNDEF), resolvemos al estado confirmado previo */
  VAD_STATE state = ST_SILENCE;
  if (vad_data->state == ST_VOICE || vad_data->state == ST_MAYBE_VOICE) {
    /* Si terminó en MAYBE_SILENCE, las últimas tramas eran silencio real al final del fichero */
    state = (vad_data->state == ST_VOICE) ? ST_VOICE : ST_SILENCE;
  } else {
    state = ST_SILENCE;
  }

  free(vad_data);
  return state;
}

unsigned int vad_frame_size(VAD_DATA *vad_data) {
  return vad_data->frame_length;
}

/* 
 * DONE: Implement the Voice Activity Detection 
 * using a Finite State Automata
 */

VAD_STATE vad(VAD_DATA *vad_data, float *x) {

  /* 
   * DONE: You can change this, using your own features,
   * program finite state automaton, define conditions, etc.
   */

  Features f = compute_features(x, vad_data->frame_length, vad_data->sampling_rate);
  vad_data->last_feature = f.p;
  vad_data->last_zcr     = f.zcr;

  switch (vad_data->state) {
  case ST_INIT:
    vad_data->count_init++;
    vad_data->sum_power_lin += pow(10.0, f.p / 10.0);

    if (vad_data->count_init >= vad_data->n_init) {
      vad_data->k0 = 10.0f * log10f((float)(vad_data->sum_power_lin / vad_data->count_init));
      vad_data->k1 = vad_data->k0 + vad_data->alpha1;
      vad_data->k2 = vad_data->k1 + vad_data->alpha2;
      vad_data->state = ST_SILENCE;
    }
    break;

  case ST_SILENCE:
    if (f.p > vad_data->k1) {
      vad_data->state = ST_MAYBE_VOICE;
      vad_data->count_state = 1;
      vad_data->high_power_seen = (f.p > vad_data->k2) ? 1 : 0;
    }
    break;

  case ST_MAYBE_VOICE:
    if (f.p > vad_data->k1) {
      vad_data->count_state++;
      if (f.p > vad_data->k2) {
        vad_data->high_power_seen = 1;
      }
      if (vad_data->count_state >= vad_data->min_voice && vad_data->high_power_seen) {
        vad_data->state = ST_VOICE;
      } else if (vad_data->count_state > vad_data->max_maybe_v && !vad_data->high_power_seen) {
        /* Demasiado tiempo sin superar k2: era ruido de fondo ligeramente superior a k1 */
        vad_data->state = ST_SILENCE;
      }
    } else {
      vad_data->state = ST_SILENCE;
      vad_data->count_state = 0;
    }
    break;

  case ST_VOICE:
    if (f.p <= vad_data->k1) {
      vad_data->state = ST_MAYBE_SILENCE;
      vad_data->count_state = 1;
    }
    break;

  case ST_MAYBE_SILENCE:
    if (f.p <= vad_data->k1) {
      vad_data->count_state++;
      if (vad_data->count_state >= vad_data->min_silence) {
        vad_data->state = ST_SILENCE;
      }
    } else {
      /* Vuelve a subir la potencia antes de cumplir el tiempo mínimo de silencio */
      vad_data->state = ST_VOICE;
      vad_data->count_state = 0;
    }
    break;

  case ST_UNDEF:
    break;
  }

  if (vad_data->state == ST_SILENCE ||
      vad_data->state == ST_VOICE)
    return vad_data->state;
  else
    return ST_UNDEF;
}

void vad_show_state(const VAD_DATA *vad_data, FILE *out) {
  fprintf(out, "%f\t%f\n", vad_data->last_feature, vad_data->last_zcr);
}
