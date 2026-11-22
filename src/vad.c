#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include "pav_analysis.h"
#include "vad.h"

const float FRAME_TIME = 10.0F; /* in ms. */

#define HANGOVER_FRAMES 11
#define ZCR_THRESHOLD 3500.0f
#define MARGEN_ZCR 7.0f
#define DEFAULT_ALPHA 11.2f

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

Features compute_features(const float *x, int N, float rate) {
  Features feat;
  feat.p = compute_power(x, N);
  feat.zcr = compute_zcr(x, N, rate);
  feat.am = compute_am(x, N);
  return feat;
}

VAD_DATA * vad_open(float rate) {
  VAD_DATA *vad_data = malloc(sizeof(VAD_DATA));
  vad_data->state = ST_INIT;
  vad_data->sampling_rate = rate;
  vad_data->frame_length = rate * FRAME_TIME * 1e-3;
  vad_data->counter = 0;
  vad_data->init_frames = 0;
  vad_data->potencia_soroll = 0.0f;
  vad_data->last_feature = 0.0f;
  return vad_data;
}

VAD_STATE vad_close(VAD_DATA *vad_data) {
  VAD_STATE state = vad_data->state;
  free(vad_data);
  return state;
}

unsigned int vad_frame_size(VAD_DATA *vad_data) {
  return vad_data->frame_length;
}

VAD_STATE vad(VAD_DATA *vad_data, float *x, float llindar) {
  Features f = compute_features(x, vad_data->frame_length, vad_data->sampling_rate);
  vad_data->last_feature = f.p;

  /* If threshold passed is negative or <= 0 (e.g. default -40 from unconfigured docopt), use calibrated default */
  float alpha = (llindar > 0.0f) ? llindar : DEFAULT_ALPHA;

  if (vad_data->state == ST_INIT) {
    if (vad_data->init_frames == 0) {
      vad_data->potencia_soroll = f.p;
    } else {
      vad_data->potencia_soroll = 0.8f * vad_data->potencia_soroll + 0.2f * f.p;
    }
    vad_data->init_frames++;
    if (vad_data->init_frames >= 5) {
      vad_data->state = ST_SILENCE;
    }
    return ST_SILENCE;
  }

  /* Check voice condition: energy above noise floor, or moderate energy with high ZCR (unvoiced fricatives) */
  int is_voice = 0;
  if (f.p > vad_data->potencia_soroll + alpha) {
    is_voice = 1;
  } else if (f.p > vad_data->potencia_soroll + (alpha - 4.0f) && f.zcr > 2800.0f) {
    is_voice = 1;
  }

  switch (vad_data->state) {
  case ST_SILENCE:
    if (is_voice) {
      vad_data->state = ST_VOICE;
      vad_data->counter = 0;
    } else {
      /* Slowly adapt noise floor during silence if power is close to estimated noise */
      if (f.p < vad_data->potencia_soroll + 3.0f) {
        vad_data->potencia_soroll = 0.995f * vad_data->potencia_soroll + 0.005f * f.p;
      }
    }
    break;

  case ST_VOICE:
    if (is_voice) {
      vad_data->counter = 0;
    } else {
      vad_data->counter++;
      if (vad_data->counter >= HANGOVER_FRAMES) {
        vad_data->state = ST_SILENCE;
        vad_data->counter = 0;
      }
    }
    break;

  case ST_INIT:
  case ST_UNDEF:
    break;
  }

  return vad_data->state;
}

void vad_show_state(const VAD_DATA *vad_data, FILE *out) {
  fprintf(out, "%d\t%f\n", vad_data->state, vad_data->last_feature);
}
