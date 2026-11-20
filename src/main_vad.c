#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <math.h>
#include <limits.h>
#include <sndfile.h>

#include "vad.h"
#include "vad_docopt.h"
#include "pav_analysis.h"

#define DEBUG_VAD 0x1
#define BINS_POTENCIA 131
#define PASO_HISTOGRAMA_DB 0.5F

static int convertir_real(const char *texto, float *valor) {
  char *fin;
  if (texto == NULL) return -1;
  errno = 0;
  float resultado = strtof(texto, &fin);
  if (texto == fin || *fin != 0 || errno == ERANGE || !isfinite(resultado))
    return -1;
  *valor = resultado;
  return 0;
}

static int convertir_entero(const char *texto, unsigned int *valor) {
  char *fin;
  unsigned long resultado;
  if (texto == NULL || texto[0] == 45) return -1;
  errno = 0;
  resultado = strtoul(texto, &fin, 10);
  if (texto == fin || *fin != 0 || errno == ERANGE || resultado > UINT_MAX)
    return -1;
  *valor = (unsigned int) resultado;
  return 0;
}

static unsigned int milisegundos_a_tramas(unsigned int milisegundos,
                                           float duracion_trama_ms) {
  unsigned int tramas = (unsigned int) ceilf(milisegundos / duracion_trama_ms);
  return tramas > 0 ? tramas : 1;
}

static int estimar_potencia_ruido(SNDFILE *archivo, float *buffer,
                                  int tam_trama, unsigned int percentil_ruido,
                                  float *potencia_ruido) {
  unsigned long long histograma[BINS_POTENCIA] = {0};
  unsigned long long total_tramas = 0;
  unsigned long long objetivo;
  unsigned long long acumulado = 0;
  sf_count_t n_leidos;
  int indice;

  if (sf_seek(archivo, 0, SEEK_SET) < 0) return -1;

  while ((n_leidos = sf_read_float(archivo, buffer, tam_trama)) > 0) {
    float potencia = compute_power(buffer, (unsigned int) n_leidos);
    if (!isfinite(potencia) || potencia < POTENCIA_RUIDO_MINIMA_DB)
      potencia = POTENCIA_RUIDO_MINIMA_DB;

    indice = (int) ((potencia - POTENCIA_RUIDO_MINIMA_DB) /
                    PASO_HISTOGRAMA_DB);
    if (indice < 0) indice = 0;
    if (indice >= BINS_POTENCIA) indice = BINS_POTENCIA - 1;
    histograma[indice]++;
    total_tramas++;

    if (n_leidos < tam_trama) break;
  }

  if (sf_seek(archivo, 0, SEEK_SET) < 0) return -1;
  if (total_tramas == 0) {
    *potencia_ruido = POTENCIA_RUIDO_MINIMA_DB;
    return 0;
  }

  objetivo = (total_tramas * percentil_ruido + 99) / 100;
  for (indice = 0; indice < BINS_POTENCIA; indice++) {
    acumulado += histograma[indice];
    if (acumulado >= objetivo) break;
  }

  *potencia_ruido = POTENCIA_RUIDO_MINIMA_DB +
                    ((float) indice + 0.5F) * PASO_HISTOGRAMA_DB;
  return 0;
}

int main(int argc, char *argv[]) {
  int verbose = 0;
  SNDFILE *sndfile_in = NULL, *sndfile_out = NULL;
  SF_INFO sf_info;
  FILE *vadfile = NULL;
  int n_read = 0, i;

  VAD_DATA *vad_data = NULL;
  VAD_STATE state, last_state;

  float *buffer = NULL, *buffer_zeros = NULL;
  int frame_size;         /* en muestras */
  float frame_duration;   /* en segundos */
  unsigned int t, last_t; /* en tramas */
  unsigned int trama_transicion;
  float potencia_ruido_inicial;
  float umbral, histeresis_db, margen_voz_clara_db, tasa_actualizacion_ruido;
  float duracion_trama_ms;
  unsigned int percentil_ruido;
  unsigned int confirmacion_clara_ms, confirmacion_dudosa_ms;
  unsigned int resguardo_silencio_ms;
  unsigned int tramas_confirmacion_clara, tramas_confirmacion_dudosa;
  unsigned int tramas_resguardo_silencio;

  char *input_wav, *output_vad, *output_wav;

  DocoptArgs args = docopt(argc, argv, /* help */ 1, /* version */ "2.0");

  verbose    = args.verbose ? DEBUG_VAD : 0;
  input_wav  = args.input_wav;
  output_vad = args.output_vad;
  output_wav = args.output_wav;

  if (convertir_real(args.umbral, &umbral) != 0 ||
      convertir_real(args.histeresis, &histeresis_db) != 0 ||
      convertir_real(args.margen_claro, &margen_voz_clara_db) != 0 ||
      convertir_real(args.adaptacion_ruido, &tasa_actualizacion_ruido) != 0 ||
      convertir_entero(args.percentil_ruido, &percentil_ruido) != 0 ||
      convertir_entero(args.confirmacion_clara_ms, &confirmacion_clara_ms) != 0 ||
      convertir_entero(args.confirmacion_dudosa_ms, &confirmacion_dudosa_ms) != 0 ||
      convertir_entero(args.resguardo_silencio_ms, &resguardo_silencio_ms) != 0 ||
      histeresis_db < 0.0F || margen_voz_clara_db < 0.0F ||
      tasa_actualizacion_ruido < 0.0F || tasa_actualizacion_ruido > 1.0F ||
      percentil_ruido >= 100 ||
      confirmacion_clara_ms == 0 || confirmacion_clara_ms > 60000 ||
      confirmacion_dudosa_ms == 0 || confirmacion_dudosa_ms > 60000 ||
      resguardo_silencio_ms == 0 || resguardo_silencio_ms > 60000) {
    fprintf(stderr, "Error: parámetros VAD fuera de rango. Consulta --help.\n");
    return -1;
  }

  if (input_wav == 0 || output_vad == 0) {
    fprintf(stderr, "%s\n", args.usage_pattern);
    return -1;
  }

  if ((sndfile_in = sf_open(input_wav, SFM_READ, &sf_info)) == 0) {
    fprintf(stderr, "Error opening input file %s (%s)\n", input_wav, strerror(errno));
    return -1;
  }

  if (sf_info.channels != 1) {
    fprintf(stderr, "Error: the input file has to be mono: %s\n", input_wav);
    sf_close(sndfile_in);
    return -2;
  }

  vad_data = vad_open(sf_info.samplerate);
  if (vad_data == NULL) {
    fprintf(stderr, "Error allocating VAD state\n");
    sf_close(sndfile_in);
    return -1;
  }

  frame_size = vad_frame_size(vad_data);
  frame_duration = (float) frame_size / (float) sf_info.samplerate;
  duracion_trama_ms = frame_duration * 1000.0F;
  tramas_confirmacion_clara =
      milisegundos_a_tramas(confirmacion_clara_ms, duracion_trama_ms);
  tramas_confirmacion_dudosa =
      milisegundos_a_tramas(confirmacion_dudosa_ms, duracion_trama_ms);
  tramas_resguardo_silencio =
      milisegundos_a_tramas(resguardo_silencio_ms, duracion_trama_ms);
  vad_configurar(vad_data, histeresis_db, margen_voz_clara_db,
                 tramas_confirmacion_clara, tramas_confirmacion_dudosa,
                 tramas_resguardo_silencio, tasa_actualizacion_ruido);
  buffer = (float *) malloc(frame_size * sizeof(float));
  buffer_zeros = (float *) malloc(frame_size * sizeof(float));
  if (buffer == NULL || buffer_zeros == NULL) {
    fprintf(stderr, "Error allocating audio buffers\n");
    free(buffer);
    free(buffer_zeros);
    vad_close(vad_data);
    sf_close(sndfile_in);
    return -1;
  }
  for (i = 0; i < frame_size; ++i) buffer_zeros[i] = 0.0F;

  if (percentil_ruido > 0) {
    if (estimar_potencia_ruido(sndfile_in, buffer, frame_size, percentil_ruido,
                               &potencia_ruido_inicial) != 0) {
      fprintf(stderr, "Error seeking input file %s\n", input_wav);
      free(buffer);
      free(buffer_zeros);
      vad_close(vad_data);
      sf_close(sndfile_in);
      return -1;
    }
    vad_establecer_ruido(vad_data, potencia_ruido_inicial);
  }

  if ((vadfile = fopen(output_vad, "wt")) == 0) {
    fprintf(stderr, "Error opening output vad file %s (%s)\n", output_vad, strerror(errno));
    free(buffer);
    free(buffer_zeros);
    vad_close(vad_data);
    sf_close(sndfile_in);
    return -1;
  }

  if (output_wav) {
    if ((sndfile_out = sf_open(output_wav, SFM_WRITE, &sf_info)) == 0) {
      fprintf(stderr, "Error opening output wav file %s (%s)\n", output_wav, strerror(errno));
      fclose(vadfile);
      free(buffer);
      free(buffer_zeros);
      vad_close(vad_data);
      sf_close(sndfile_in);
      return -1;
    }
  }

  last_state = ST_UNDEF;

  for (t = last_t = 0; ; t++) {
    if ((n_read = sf_read_float(sndfile_in, buffer, frame_size)) != frame_size) break;

    if (sndfile_out != NULL) {
      sf_write_float(sndfile_out, buffer, frame_size);
    }

    state = vad(vad_data, buffer, umbral);
    if (verbose & DEBUG_VAD) vad_show_state(vad_data, stdout);

    if (state != ST_UNDEF) {
      if (last_state == ST_UNDEF) {
        last_state = state;
      } else if (state != last_state) {
        trama_transicion = (t >= vad_data->retroceso_transicion)
                       ? t - vad_data->retroceso_transicion
                       : 0;
        if (trama_transicion < last_t) trama_transicion = last_t;
        if (trama_transicion > last_t)
          fprintf(vadfile, "%.5f\t%.5f\t%s\n", last_t * frame_duration, trama_transicion * frame_duration, state2str(last_state));
        if (sndfile_out != NULL && last_state == ST_SILENCE) {
          sf_seek(sndfile_out, last_t * frame_size, SEEK_SET);
          for (unsigned int k = last_t; k < trama_transicion; k++)
            sf_write_float(sndfile_out, buffer_zeros, frame_size);
          sf_seek(sndfile_out, 0, SEEK_END);
        }
        last_state = state;
        last_t = trama_transicion;
      }
    }
  }

  state = vad_close(vad_data);
  if (last_state == ST_UNDEF) last_state = state;

  if (t != last_t) {
    if (state != last_state) {
      fprintf(vadfile, "%.5f\t%.5f\t%s\n", last_t * frame_duration, t * frame_duration, state2str(last_state));
      last_t = t;
      last_state = state;
    }
    fprintf(vadfile, "%.5f\t%.5f\t%s\n", last_t * frame_duration, t * frame_duration + n_read / (float) sf_info.samplerate, state2str(last_state));
    if (sndfile_out != NULL && last_state == ST_SILENCE) {
      sf_seek(sndfile_out, last_t * frame_size, SEEK_SET);
      for (unsigned int k = last_t; k < t; k++)
        sf_write_float(sndfile_out, buffer_zeros, frame_size);
      if (n_read > 0)
        sf_write_float(sndfile_out, buffer_zeros, n_read);
    }
  }

  free(buffer);
  free(buffer_zeros);
  sf_close(sndfile_in);
  fclose(vadfile);
  if (sndfile_out) sf_close(sndfile_out);
  return 0;
}
