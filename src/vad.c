#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include "pav_analysis.h"
#include "vad.h"

const float FRAME_TIME = 10.0F; /* en ms. */

#define NUM_TRAMAS_INICIALES     10     /* 100 ms iniciales para la calibracion de respaldo */
#define CONFIRMACION_VOZ_CLARA   3      /* 30 ms si la potencia supera claramente el umbral */
#define CONFIRMACION_VOZ_DUDOSA  3      /* 30 ms con la configuración fija */
#define MARGEN_VOZ_CLARA_DB      3.0F   /* margen para considerar clara la deteccion */
#define TRAMAS_RESGUARDO_SILENCIO    10     /* 100 ms de resguardo para oclusivas */
#define HISTERESIS_DB       2.0F   /* diferencia entre umbrales de entrada y salida */

const char *state_str[] = {
  "UNDEF", "S", "V", "INIT", "MAYBE_V", "MAYBE_S"
};

const char *state2str(VAD_STATE st) {
  return state_str[st];
}

typedef struct {
  float zcr;
  float p;
  float am;
} Features;

Features compute_features(const float *x, int N, float rate) {
  Features feat;
  feat.p   = compute_power(x, N);
  feat.am  = compute_am(x, N);
  feat.zcr = compute_zcr(x, N, rate);
  return feat;
}

VAD_DATA *vad_open(float rate) {
  VAD_DATA *vad_data = malloc(sizeof(VAD_DATA));
  if (vad_data == NULL) return NULL;

  vad_data->state = ST_INIT;
  vad_data->sampling_rate = rate;
  vad_data->frame_length = rate * FRAME_TIME * 1e-3;
  vad_data->potencia_ruido = 0.0F;
  vad_data->ultima_zcr = 0.0F;
  vad_data->ultimo_ruido_estimado = POTENCIA_RUIDO_MINIMA_DB;
  vad_data->ultimo_umbral_voz = 0.0F;
  vad_data->ultimo_umbral_silencio = 0.0F;
  vad_data->init_frames = 0;
  vad_data->voice_frames = 0;
  vad_data->tramas_confirmacion_voz = 0;
  vad_data->silence_frames = 0;
  vad_data->contador_tramas = 0;
  vad_data->indice_trama_actual = 0;
  vad_data->retroceso_transicion = 0;
  vad_data->histeresis_db = HISTERESIS_DB;
  vad_data->margen_voz_clara_db = MARGEN_VOZ_CLARA_DB;
  vad_data->tasa_actualizacion_ruido = 0.0F;
  vad_data->tramas_confirmacion_voz_clara = CONFIRMACION_VOZ_CLARA;
  vad_data->tramas_confirmacion_voz_dudosa = CONFIRMACION_VOZ_DUDOSA;
  vad_data->tramas_resguardo_silencio = TRAMAS_RESGUARDO_SILENCIO;
  return vad_data;
}

void vad_establecer_ruido(VAD_DATA *vad_data, float potencia_ruido) {
  if (vad_data == NULL) return;
  if (!isfinite(potencia_ruido) || potencia_ruido < POTENCIA_RUIDO_MINIMA_DB)
    potencia_ruido = POTENCIA_RUIDO_MINIMA_DB;

  vad_data->potencia_ruido = potencia_ruido;
  vad_data->state = ST_SILENCE;
  vad_data->init_frames = NUM_TRAMAS_INICIALES;
  vad_data->voice_frames = 0;
  vad_data->tramas_confirmacion_voz = 0;
  vad_data->silence_frames = 0;
  vad_data->retroceso_transicion = 0;
}

void vad_configurar(VAD_DATA *vad_data, float histeresis_db,
                  float margen_voz_clara_db,
                  unsigned int tramas_confirmacion_voz_clara,
                  unsigned int tramas_confirmacion_voz_dudosa,
                  unsigned int tramas_resguardo_silencio,
                  float tasa_actualizacion_ruido) {
  if (vad_data == NULL) return;
  if (isfinite(histeresis_db) && histeresis_db >= 0.0F)
    vad_data->histeresis_db = histeresis_db;
  if (isfinite(margen_voz_clara_db) && margen_voz_clara_db >= 0.0F)
    vad_data->margen_voz_clara_db = margen_voz_clara_db;
  if (tramas_confirmacion_voz_clara > 0)
    vad_data->tramas_confirmacion_voz_clara = tramas_confirmacion_voz_clara;
  if (tramas_confirmacion_voz_dudosa > 0)
    vad_data->tramas_confirmacion_voz_dudosa = tramas_confirmacion_voz_dudosa;
  if (tramas_resguardo_silencio > 0)
    vad_data->tramas_resguardo_silencio = tramas_resguardo_silencio;
  if (isfinite(tasa_actualizacion_ruido) &&
      tasa_actualizacion_ruido >= 0.0F && tasa_actualizacion_ruido <= 1.0F)
    vad_data->tasa_actualizacion_ruido = tasa_actualizacion_ruido;
}

VAD_STATE vad_close(VAD_DATA *vad_data) {
  if (vad_data == NULL) return ST_SILENCE;
  VAD_STATE state = vad_data->state;
  free(vad_data);

  if (state == ST_VOICE || state == ST_MAYBE_SILENCE)
    return ST_VOICE;
  else
    return ST_SILENCE;
}

unsigned int vad_frame_size(VAD_DATA *vad_data) {
  return vad_data->frame_length;
}

VAD_STATE vad(VAD_DATA *vad_data, float *x, float umbral) {
  Features f = compute_features(x, vad_data->frame_length, vad_data->sampling_rate);
  vad_data->indice_trama_actual = vad_data->contador_tramas++;
  vad_data->ultima_zcr = f.zcr;
  vad_data->last_feature = f.p;
  vad_data->retroceso_transicion = 0;

  float ruido_efectivo = vad_data->potencia_ruido;
  if (!isfinite(ruido_efectivo) || ruido_efectivo < POTENCIA_RUIDO_MINIMA_DB)
    ruido_efectivo = POTENCIA_RUIDO_MINIMA_DB;

  float umbral_voz = ruido_efectivo + umbral;
  float umbral_silencio = umbral_voz - vad_data->histeresis_db;
  float potencia_observada = f.p;
  if (!isfinite(potencia_observada) ||
      potencia_observada < POTENCIA_RUIDO_MINIMA_DB)
    potencia_observada = POTENCIA_RUIDO_MINIMA_DB;

  vad_data->ultimo_ruido_estimado = ruido_efectivo;
  vad_data->ultimo_umbral_voz = umbral_voz;
  vad_data->ultimo_umbral_silencio = umbral_silencio;

  switch (vad_data->state) {
  case ST_INIT:
    /* Respaldo para usos que no proporcionen una estimacion previa. */
    vad_data->potencia_ruido += potencia_observada;
    vad_data->init_frames++;
    if (vad_data->init_frames >= NUM_TRAMAS_INICIALES) {
      vad_data->potencia_ruido /= (float) NUM_TRAMAS_INICIALES;
      if (!isfinite(vad_data->potencia_ruido) ||
          vad_data->potencia_ruido < POTENCIA_RUIDO_MINIMA_DB)
        vad_data->potencia_ruido = POTENCIA_RUIDO_MINIMA_DB;
      vad_data->state = ST_SILENCE;
    }
    break;

  case ST_SILENCE:
    if (f.p > umbral_voz) {
      vad_data->state = ST_MAYBE_VOICE;
      vad_data->voice_frames = 1;
      vad_data->tramas_confirmacion_voz =
          (f.p - umbral_voz >= vad_data->margen_voz_clara_db)
          ? vad_data->tramas_confirmacion_voz_clara
          : vad_data->tramas_confirmacion_voz_dudosa;
    } else if (potencia_observada < umbral_silencio) {
      /* Actualizacion lenta del ruido solo durante silencio firme. */
      vad_data->potencia_ruido =
          (1.0F - vad_data->tasa_actualizacion_ruido) * ruido_efectivo +
          vad_data->tasa_actualizacion_ruido * potencia_observada;
      if (!isfinite(vad_data->potencia_ruido) ||
          vad_data->potencia_ruido < POTENCIA_RUIDO_MINIMA_DB)
        vad_data->potencia_ruido = POTENCIA_RUIDO_MINIMA_DB;
    }
    break;

  case ST_MAYBE_VOICE:
    if (f.p > umbral_voz) {
      vad_data->voice_frames++;
      if (vad_data->voice_frames >= vad_data->tramas_confirmacion_voz) {
        vad_data->state = ST_VOICE;
        vad_data->retroceso_transicion = vad_data->voice_frames - 1;
      }
    } else {
      vad_data->state = ST_SILENCE;
      vad_data->voice_frames = 0;
      vad_data->tramas_confirmacion_voz = 0;
    }
    break;

  case ST_VOICE:
    if (f.p < umbral_silencio) {
      vad_data->state = ST_MAYBE_SILENCE;
      vad_data->silence_frames = 1;
    }
    break;

  case ST_MAYBE_SILENCE:
    if (f.p < umbral_silencio) {
      vad_data->silence_frames++;
      if (vad_data->silence_frames >= vad_data->tramas_resguardo_silencio) {
        vad_data->state = ST_SILENCE;
        vad_data->retroceso_transicion = vad_data->silence_frames - 1;
      }
    } else {
      vad_data->state = ST_VOICE;
    }
    break;

  case ST_UNDEF:
    break;
  }

  if (vad_data->state == ST_SILENCE || vad_data->state == ST_VOICE)
    return vad_data->state;
  else
    return ST_UNDEF;
}

void vad_show_state(const VAD_DATA *vad_data, FILE *out) {
  float tiempo = (float) vad_data->indice_trama_actual *
                 (float) vad_data->frame_length / vad_data->sampling_rate;
  fprintf(out, "%.5f\t%s\t%f\t%f\t%f\t%f\t%f\n", tiempo,
          state2str(vad_data->state), vad_data->last_feature,
          vad_data->ultima_zcr, vad_data->ultimo_ruido_estimado,
          vad_data->ultimo_umbral_voz, vad_data->ultimo_umbral_silencio);
}
