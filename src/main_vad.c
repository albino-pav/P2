#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>  // Comprovo els errors de conversió del marge.
#include <limits.h>
#include <math.h>  // Comprovo que el marge sigui un nombre finit.
#include <sndfile.h>  // Llegeixo les mostres amb libsndfile.
#include "vad.h"
#include "vad_docopt.h"  // Aprofito el lector d'arguments que ja venia amb la pràctica.

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

int main(int argc, char *argv[]) {
    DocoptArgs args = docopt(argc, argv, 1, "2.0");  // Llegeixo els noms dels fitxers i l'opció verbose.
    char *number_end;  // Localitzo el final del nombre escrit per l'usuari.
    errno = 0;  // Reinicio l'error abans de convertir el text.
    float margin = strtof(args.llindar, &number_end);  // Converteixo el marge de text a float.
    if (number_end == args.llindar || *number_end != '\0' || errno != 0 || !isfinite(margin) || margin <= 0) {  // Rebutjo valors invàlids.
        fprintf(stderr, "El llindar ha de ser un marge positiu en dB.\n");  // Explico el valor que necessito.
        return 1;  // Aturo el programa abans de tocar els fitxers.
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
        update_margin < 0 || (args.rescat_zcr && discount >= margin) ||
        (args.confirma_alt && max_wait < min_voice)) {
        fprintf(stderr, "Revisa ZCR, rebaixa, pujada, espera i marge de soroll.\n");
        return 1;
    }
    if (args.input_wav == NULL || args.output_vad == NULL) {  // Comprovo els dos arguments obligatoris.
        fprintf(stderr, "%s\n", args.usage_pattern);  // Mostro la forma d'executar el programa.
        return 1;  // Indico que falten arguments.
    }
    if (strcmp(args.input_wav, args.output_vad) == 0) {  // Evito escriure sobre l'entrada amb el mateix nom.
        fprintf(stderr, "L'entrada i la sortida han de tenir noms diferents.\n");  // Explico l'error.
        return 1;  // Aturo el programa abans d'obrir la sortida.
    }

    SF_INFO info = {0};  // Inicialitzo les dades que omplirà libsndfile.
    SNDFILE *audio = sf_open(args.input_wav, SFM_READ, &info);  // Obro l'àudio per llegir-lo.
    if (audio == NULL) {  // Comprovo que el fitxer es pugui llegir.
        fprintf(stderr, "No puc obrir l'àudio: %s\n", sf_strerror(NULL));  // Mostro el motiu de l'error.
        return 1;  // Indico que l'entrada no és vàlida.
    }
    if (info.channels != 1 || info.frames == 0) {  // Necessito àudio mono amb alguna mostra.
        fprintf(stderr, "Cal un àudio mono que no sigui buit.\n");  // Indico el format necessari.
        sf_close(audio);  // Tanco l'entrada abans de sortir.
        return 1;  // Retorno un error.
    }

    VAD_DATA *data = vad_open(info.samplerate);  // Preparo el detector amb la freqüència real.
    if (data == NULL) {  // Comprovo que he pogut inicialitzar-lo.
        fprintf(stderr, "No puc inicialitzar el detector.\n");  // Mostro l'error.
        sf_close(audio);  // Tanco l'entrada.
        return 1;  // Aturo l'execució.
    }
    unsigned int frame_size = vad_frame_size(data);  // Consulto quantes mostres necessita cada bloc.
    data->init_frames = init_frames;
    data->min_voice = min_voice;
    data->min_silence = min_silence;
    data->noise_alpha = alpha;
    data->silence_gap = gap;
    data->trim_initial = args.treu_pic;
    data->allow_dip = args.permet_baixada;
    data->remove_dc = args.treu_dc;
    data->backdate = !args.sense_retroces;
    data->rescue_zcr = args.rescat_zcr;
    data->confirm_high = args.confirma_alt;
    data->guard_noise = args.limita_soroll;
    data->zcr_threshold = zcr_limit;
    data->zcr_discount = discount;
    data->confirm_boost = boost;
    data->max_wait = max_wait;
    data->noise_update_margin = update_margin;
    data->margin_db = margin;  // Aplico el marge rebut per argument.
    float *buffer = malloc(frame_size * sizeof(float));  // Reservo només la memòria d'un bloc.
    if (buffer == NULL) {  // Comprovo la reserva.
        fprintf(stderr, "No hi ha prou memòria.\n");  // Mostro l'error.
        vad_close(data);  // Allibero el detector.
        sf_close(audio);  // Tanco l'entrada.
        return 1;  // Retorno un error.
    }
    FILE *labels = fopen(args.output_vad, "w");  // Obro el fitxer d'etiquetes.
    if (labels == NULL) {  // Comprovo que pugui escriure la sortida.
        perror("No puc obrir el fitxer d'etiquetes");  // Mostro el motiu de l'error.
        free(buffer);  // Allibero el bloc de mostres.
        vad_close(data);  // Allibero el detector.
        sf_close(audio);  // Tanco l'entrada.
        return 1;  // Retorno un error.
    }

    double frame_time = (double) frame_size / info.samplerate;  // Calculo la durada exacta d'un bloc.
    unsigned int t = 0, last_t = 0, pending = 0;  // Compto blocs, inici del segment i blocs pendents.
    VAD_STATE last_state = ST_UNDEF;  // Encara no tinc cap segment confirmat.
    sf_count_t n_read;  // Guardo les mostres que llegeixo a cada pas.

    while ((n_read = sf_read_float(audio, buffer, frame_size)) == frame_size) {  // Llegeixo un bloc cada vegada.
        VAD_STATE state = vad(data, buffer);  // Demano una decisió al detector.
        if (args.verbose) {  // Mostro el seguiment només si l'he demanat.
            printf("%.5f\t", t * frame_time);  // Escric el temps del bloc.
            vad_show_state(data, stdout);  // Escric estat, potència i llindar.
        }
        if (state == ST_UNDEF) {  // Espero una decisió quan l'estat és provisional.
            pending++;  // Recordo quants blocs hauré d'assignar després.
        } else {
            unsigned int start = data->backdate ? t - pending : t;  // Retrocedeixo fins al primer bloc pendent.
            if (last_state == ST_UNDEF) {  // Resolc el primer segment del fitxer.
                last_state = state;  // Guardo la primera etiqueta S o V.
            } else if (state != last_state) {  // Tanco el segment quan es confirma un canvi.
                if (start > last_t) {  // Evito escriure segments de durada zero.
                    fprintf(labels, "%.6f\t%.6f\t%s\n", last_t * frame_time, start * frame_time, state2str(last_state));  // Escric el segment anterior.
                }
                last_t = start;  // Guardo l'inici real del segment nou.
                last_state = state;  // Guardo la nova etiqueta confirmada.
            }
            pending = 0;  // Ja he resolt els blocs que tenia pendents.
        }
        t++;  // Avanço al bloc següent.
    }

    int result = 0;  // Començo suposant que la lectura ha acabat correctament.
    if (sf_error(audio) != SF_ERR_NO_ERROR) result = 1;  // Comprovo si la lectura ha fallat.
    VAD_STATE final_state = vad_close(data);  // Resolc els possibles blocs pendents al final.
    if (last_state == ST_UNDEF) last_state = final_state;  // Etiqueto també els àudios més curts que la inicialització.
    double end = ((double) t * frame_size + n_read) / info.samplerate;  // Incloc les mostres del darrer bloc incomplet.
    if (end > last_t * frame_time) {  // Escric l'últim segment fins al final real de l'àudio.
        fprintf(labels, "%.6f\t%.6f\t%s\n", last_t * frame_time, end, state2str(last_state));  // Mantinc l'última decisió confirmada.
    }
    if (ferror(labels)) result = 1;  // Comprovo els errors d'escriptura.
    if (fclose(labels) != 0) result = 1;  // Detecto també els errors en tancar la sortida.
    free(buffer);  // Allibero la memòria del bloc.
    sf_close(audio);  // Tanco l'entrada.
    if (result != 0) fprintf(stderr, "Error en llegir o escriure les dades.\n");  // Aviso si alguna operació ha fallat.
    return result;  // Retorno l'estat de l'execució.
}
