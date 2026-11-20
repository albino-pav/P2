#ifndef _VAD_H
#define _VAD_H
#include <stdio.h>

#define POTENCIA_RUIDO_MINIMA_DB (-65.0F)

typedef enum {
  ST_UNDEF = 0,
  ST_SILENCE,
  ST_VOICE,
  ST_INIT,
  ST_MAYBE_VOICE,
  ST_MAYBE_SILENCE
} VAD_STATE;

/* Return a string label associated to each state */
const char *state2str(VAD_STATE st);

typedef struct {
  VAD_STATE state;
  float sampling_rate;
  unsigned int frame_length;
  float last_feature; /* potencia de la trama para depuracion */
  float potencia_ruido;
  float ultima_zcr;
  float ultimo_ruido_estimado;
  float ultimo_umbral_voz;
  float ultimo_umbral_silencio;
  unsigned int init_frames;
  unsigned int voice_frames;
  unsigned int tramas_confirmacion_voz;
  unsigned int silence_frames;
  unsigned int contador_tramas;
  unsigned int indice_trama_actual;
  /* Tramas para retroceder el limite al confirmar un cambio de estado. */
  unsigned int retroceso_transicion;
  float histeresis_db;
  float margen_voz_clara_db;
  float tasa_actualizacion_ruido;
  unsigned int tramas_confirmacion_voz_clara;
  unsigned int tramas_confirmacion_voz_dudosa;
  unsigned int tramas_resguardo_silencio;
} VAD_DATA;

VAD_DATA *vad_open(float sampling_rate);
void vad_establecer_ruido(VAD_DATA *vad_data, float potencia_ruido);
void vad_configurar(VAD_DATA *vad_data, float histeresis_db,
                  float margen_voz_clara_db,
                  unsigned int tramas_confirmacion_voz_clara,
                  unsigned int tramas_confirmacion_voz_dudosa,
                  unsigned int tramas_resguardo_silencio,
                  float tasa_actualizacion_ruido);
unsigned int vad_frame_size(VAD_DATA *);
VAD_STATE vad(VAD_DATA *vad_data, float *x, float umbral);
VAD_STATE vad_close(VAD_DATA *vad_data);
void vad_show_state(const VAD_DATA *, FILE *);

#endif
