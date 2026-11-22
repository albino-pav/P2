#include <stdlib.h>
#include <stdio.h>

#include "vad.h"
#include "pav_analysis.h"

/*
 * const float FRAME_TIME = 120;  // in ms
 *
 * const float MARGE_P = 6.6;
 * const unsigned short N_FRAMES = 24;
*/

/* 
 * As the output state is only ST_VOICE, ST_SILENCE, or ST_UNDEF,
 * only this labels are needed. You need to add all labels, in case
 * you want to print the internal state in string format
 */

const char *state_str[] = {
  "UNDEF", "S", "V", "INIT"
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

Features compute_features(const float *x, int N) {
  /*
   * Input: x[i] : i=0 .... N-1 
   * Ouput: computed features
   */
  Features feat;
  //feat.zcr = compute_zcr(x, N, 1e3 / FRAME_TIME);
  feat.p = compute_power(x, N);
  //feat.am = compute_am(x, N);
  return feat;
}

/* 
 * Init the values of vad_data
 */

VAD_DATA * vad_open(float rate, float frame_time) {
  VAD_DATA *vad_data = malloc(sizeof(VAD_DATA));
  vad_data->state = ST_INIT;
  vad_data->sampling_rate = rate;
  vad_data->frame_length = rate * frame_time * 1e-3;
  return vad_data;
}

VAD_STATE vad_close(VAD_DATA *vad_data) {
  /* 
   * Decides what to do with the last undecided frames
   */
  VAD_STATE state = vad_data->state;

  free(vad_data);
  if (state != ST_SILENCE && state != ST_VOICE)
    return ST_SILENCE;
  return state;
}

unsigned int vad_frame_size(VAD_DATA *vad_data) {
  return vad_data->frame_length;
}

/* 
 * Implements the Voice Activity Detection
 * using a Finite State Automata
 */

VAD_STATE vad(VAD_DATA *vad_data, float *x, float llindar, float marge_p, unsigned short n_frames, unsigned short *count) {

  Features f = compute_features(x, vad_data->frame_length);
  vad_data->last_feature = f.p; /* save feature, in case you want to show */

  switch (vad_data->state) {
  case ST_INIT:
    vad_data->state = ST_SILENCE;
    vad_data->potencia_soroll = f.p;
    break;

  case ST_VOICE:
    if (f.p < vad_data->potencia_soroll + llindar) {
      vad_data->state = ST_SILENCE;
      *count = 0;
    }
    break;

  default:  // either ST_VOICE or ST_UNDEF
    if (f.p > vad_data->potencia_soroll + llindar + marge_p) {
      vad_data->state = ST_VOICE;
      *count = 0;
    } else if (f.p > vad_data->potencia_soroll + llindar) {
      if (*count == n_frames) {
        vad_data->state = ST_VOICE;
        *count = 0;
        break;
      }
      vad_data->state = ST_UNDEF;
      (*count)++;
    } else {
      vad_data->state = ST_SILENCE;
      *count = 0;
    }
    break;

  }

  if (vad_data->state == ST_SILENCE ||
      vad_data->state == ST_VOICE)
    return vad_data->state;
  else
    return ST_SILENCE;
}

void vad_show_state(const VAD_DATA *vad_data, FILE *out) {
  fprintf(out, "%d\t%f\n", vad_data->state, vad_data->last_feature);
}
