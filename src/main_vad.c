#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <limits.h>
#include <math.h>
#include <sndfile.h>
#include <sys/stat.h>
#include "vad.h"
#include "vad_docopt.h"

// Llegeixo els valors de les proves i rebutjo nombres mal escrits.
static int read_frames(const char *text, int *value) {
    char *end;
    errno = 0;
    long number = strtol(text, &end, 10);
    if (end == text || *end != '\0' || errno || number < 1 || number > INT_MAX) return 0;
    *value = (int) number;
    return 1;
}

static int read_number(const char *text, float *value) {
    char *end;
    errno = 0;
    *value = strtof(text, &end);
    return end != text && *end == '\0' && !errno && isfinite(*value);
}

static int same_file(const char *a, const char *b) {
    struct stat x, y;
    return strcmp(a, b) == 0 ||
        (stat(a, &x) == 0 && stat(b, &y) == 0 && x.st_dev == y.st_dev && x.st_ino == y.st_ino);
}

// Escric només els segments que ja tenen una decisió definitiva.
static int write_segment(SNDFILE *input, SNDFILE *output, void *samples, int floating,
                         unsigned int size, sf_count_t start, sf_count_t end, VAD_STATE state) {
    if (output == NULL) return 0;
    if (state == ST_VOICE && sf_seek(input, start, SEEK_SET) != start) return 1;
    while (start < end) {
        sf_count_t count = end - start;
        if (count > size) count = size;
        if (floating) {
            double *values = samples;
            if (state == ST_VOICE) {
                if (sf_read_double(input, values, count) != count) return 1;
            } else {
                for (sf_count_t i = 0; i < count; i++) values[i] = 0.0;
            }
            if (sf_write_double(output, values, count) != count) return 1;
        } else {
            int *values = samples;
            if (state == ST_VOICE) {
                if (sf_read_int(input, values, count) != count) return 1;
            } else {
                for (sf_count_t i = 0; i < count; i++) values[i] = 0;
            }
            if (sf_write_int(output, values, count) != count) return 1;
        }
        start += count;
    }
    return 0;
}

int main(int argc, char *argv[]) {
    DocoptArgs args = docopt(argc, argv, 1, "2.0");
    char *number_end;
    errno = 0;
    float margin = strtof(args.llindar, &number_end);
    if (number_end == args.llindar || *number_end != '\0' || errno != 0 || !isfinite(margin) || margin <= 0) {
        fprintf(stderr, "El llindar ha de ser un marge positiu en dB.\n");
        return 1;
    }
    int init_frames, min_voice, min_silence;
    float alpha, gap;
    if (!read_frames(args.inici, &init_frames) || !read_frames(args.veu, &min_voice) ||
        !read_frames(args.silenci, &min_silence) || !read_number(args.alfa, &alpha) ||
        !read_number(args.histeresi, &gap) || alpha < 0 || alpha > 1 || gap < 0 || gap >= margin ||
        (args.treu_pic && init_frames < 2)) {
        fprintf(stderr, "Calen blocs positius, alfa entre 0 i 1 i una histèresi menor que el marge.\n");
        return 1;
    }
    float zcr_limit, discount, boost, update_margin;
    int max_wait;
    if (!read_number(args.zcr, &zcr_limit) || !read_number(args.rebaixa_zcr, &discount) ||
        !read_number(args.pujada, &boost) || !read_number(args.marge_soroll, &update_margin) ||
        !read_frames(args.espera, &max_wait) || zcr_limit <= 0 || discount < 0 || boost <= 0 ||
        update_margin < 0 || (!args.sense_zcr && discount >= margin) ||
        (!args.sense_confirmacio && max_wait < min_voice)) {
        fprintf(stderr, "Revisa ZCR, rebaixa, pujada, espera i marge de soroll.\n");
        return 1;
    }
    float down_factor, voice_range, frame_ms;
    if (!read_number(args.factor_baixada, &down_factor) || down_factor < 1 ||
        !read_number(args.rang_soroll, &voice_range) || voice_range <= 0 ||
        !read_number(args.frame_ms, &frame_ms) || frame_ms < 2 || frame_ms > 120) {
        fprintf(stderr, "Revisa el factor de baixada, el rang i la durada del bloc.\n");
        return 1;
    }
    if ((args.permet_baixada && args.sense_baixada) || (args.treu_dc && args.sense_dc) ||
        (args.rescat_zcr && args.sense_zcr) || (args.confirma_alt && args.sense_confirmacio) ||
        (args.soroll_asimetric && args.soroll_simetric) || (args.terra_soroll && args.sense_terra)) {
        fprintf(stderr, "No es pot activar i desactivar la mateixa opcio alhora.\n");
        return 1;
    }
    if (args.input_wav == NULL || args.output_vad == NULL) {
        fprintf(stderr, "%s\n", args.usage_pattern);
        return 1;
    }
    if (same_file(args.input_wav, args.output_vad) ||
        (args.output_wav && (same_file(args.input_wav, args.output_wav) || same_file(args.output_vad, args.output_wav)))) {
        fprintf(stderr, "L'entrada i la sortida han de tenir noms diferents.\n");
        return 1;
    }

    SF_INFO info = {0};
    SNDFILE *audio = sf_open(args.input_wav, SFM_READ, &info);
    if (audio == NULL) {
        fprintf(stderr, "No puc obrir l'àudio: %s\n", sf_strerror(NULL));
        return 1;
    }
    if (info.channels != 1 || info.frames == 0) {
        fprintf(stderr, "Cal un àudio mono que no sigui buit.\n");
        sf_close(audio);
        return 1;
    }

    VAD_DATA *data = vad_open(info.samplerate);
    if (data == NULL) {
        fprintf(stderr, "No puc inicialitzar el detector.\n");
        sf_close(audio);
        return 1;
    }
    data->frame_length = (unsigned int)(info.samplerate * frame_ms / 1000.0f);
    if (data->frame_length == 0) {
        vad_close(data);
        sf_close(audio);
        return 1;
    }
    data->asymmetric_noise = !args.soroll_simetric;
    data->floor_noise = !args.sense_terra;
    data->direct_voice = args.entrada_directa;
    data->down_factor = down_factor;
    data->voice_range = voice_range;
    data->voice_alpha = 1.0f - powf(0.9f, frame_ms / 10.0f);
    unsigned int frame_size = vad_frame_size(data);
    data->init_frames = init_frames;
    data->min_voice = min_voice;
    data->min_silence = min_silence;
    data->noise_alpha = alpha;
    data->silence_gap = gap;
    data->trim_initial = args.treu_pic;
    data->allow_dip = !args.sense_baixada;
    data->remove_dc = !args.sense_dc;
    data->backdate = !args.sense_retroces;
    data->rescue_zcr = !args.sense_zcr;
    data->confirm_high = !args.sense_confirmacio;
    data->guard_noise = args.limita_soroll;
    data->zcr_threshold = zcr_limit;
    data->zcr_discount = discount;
    data->confirm_boost = boost;
    data->max_wait = max_wait;
    data->noise_update_margin = update_margin;
    data->margin_db = margin;
    float *buffer = malloc(frame_size * sizeof(float));
    if (buffer == NULL) {
        fprintf(stderr, "No hi ha prou memòria.\n");
        vad_close(data);
        sf_close(audio);
        return 1;
    }
    FILE *labels = fopen(args.output_vad, "w");
    if (labels == NULL) {
        perror("No puc obrir el fitxer d'etiquetes");
        free(buffer);
        vad_close(data);
        sf_close(audio);
        return 1;
    }

    SNDFILE *copy = NULL, *clean = NULL;
    void *samples = NULL;
    int subtype = info.format & SF_FORMAT_SUBMASK;
    int floating = subtype == SF_FORMAT_FLOAT || subtype == SF_FORMAT_DOUBLE;
    if (args.output_wav) {
        SF_INFO copy_info = {0};
        SF_INFO output_info = info;
        output_info.format = SF_FORMAT_WAV | (info.format & SF_FORMAT_SUBMASK);
        output_info.frames = 0;
        if (!same_file(args.output_vad, args.output_wav) && sf_format_check(&output_info)) {
            copy = sf_open(args.input_wav, SFM_READ, &copy_info);
            samples = malloc(frame_size * sizeof(double));
            if (copy && samples) clean = sf_open(args.output_wav, SFM_WRITE, &output_info);
        }
        if (!copy || !samples || !clean) {
            fprintf(stderr, "No puc preparar el WAVE de sortida.\n");
            if (copy) sf_close(copy);
            if (clean) sf_close(clean);
            free(samples);
            fclose(labels);
            free(buffer);
            vad_close(data);
            sf_close(audio);
            return 1;
        }
    }

    int result = 0;
    double frame_time = (double) frame_size / info.samplerate;
    unsigned int t = 0, last_t = 0, pending = 0;
    VAD_STATE last_state = ST_UNDEF;
    sf_count_t n_read;

    while ((n_read = sf_read_float(audio, buffer, frame_size)) == frame_size) {
        VAD_STATE state = vad(data, buffer);
        if (args.verbose) {
            printf("%.5f\t", t * frame_time);
            vad_show_state(data, stdout);
        }
        // Guardo els blocs dubtosos fins que el detector es decideix.
        if (state == ST_UNDEF) {
            pending++;
        } else {
            unsigned int start = data->backdate ? t - pending : t;
            if (last_state == ST_UNDEF) {
                last_state = state;
            } else if (state != last_state) {
                if (start > last_t) {
                    if (write_segment(copy, clean, samples, floating, frame_size,
                                      (sf_count_t)last_t * frame_size, (sf_count_t)start * frame_size, last_state)) result = 1;
                    fprintf(labels, "%.6f\t%.6f\t%s\n", last_t * frame_time, start * frame_time, state2str(last_state));
                }
                last_t = start;
                last_state = state;
            }
            pending = 0;
        }
        t++;
    }

    if (sf_error(audio) != SF_ERR_NO_ERROR) result = 1;
    VAD_STATE final_state = vad_close(data);
    if (last_state == ST_UNDEF) last_state = final_state;
    // Incloc també les mostres que no omplen un bloc sencer.
    double end = ((double) t * frame_size + n_read) / info.samplerate;
    if (end > last_t * frame_time) {
        if (write_segment(copy, clean, samples, floating, frame_size, (sf_count_t)last_t * frame_size,
                          (sf_count_t)t * frame_size + n_read, last_state)) result = 1;
        fprintf(labels, "%.6f\t%.6f\t%s\n", last_t * frame_time, end, state2str(last_state));
    }
    if (ferror(labels)) result = 1;
    if (fclose(labels) != 0) result = 1;
    if (copy && sf_close(copy) != 0) result = 1;
    if (clean && sf_close(clean) != 0) result = 1;
    free(samples);
    free(buffer);
    sf_close(audio);
    if (result != 0) fprintf(stderr, "Error en llegir o escriure les dades.\n");
    return result;
}
