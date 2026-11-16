#ifndef VAD_H
#define VAD_H
#include <stdio.h>

// Distingeixo els estats confirmats dels dos estats provisionals.
typedef enum {ST_UNDEF, ST_SILENCE, ST_VOICE, ST_INIT, ST_MAYBE_VOICE, ST_MAYBE_SILENCE} VAD_STATE;

typedef struct {
    VAD_STATE state;  // Guardo l'estat actual de l'autòmat.
    float sampling_rate;  // Guardo la freqüència de mostreig.
    unsigned int frame_length;  // Guardo les mostres de cada bloc de 10 ms.
    int initial_frames;  // Compto els blocs que uso per estimar el soroll inicial.
    float initial_max;  // Guardo el màxim inicial si vull deixar-lo fora.
    float initial_sum;  // Acumulo la potència lineal dels blocs inicials.
    float noise;  // Guardo la potència estimada del soroll en dB.
    float margin_db;  // Guardo el marge que he rebut per argument.
    int init_frames;  // Nombre de blocs per calcular el soroll inicial.
    int min_voice;  // Blocs alts que demano per confirmar veu.
    int min_silence;  // Blocs baixos que demano per confirmar silenci.
    float noise_alpha;  // Quant canvia el soroll a cada bloc de silenci.
    float silence_gap;  // Diferència entre el llindar d’entrada i el de sortida.
    int trim_initial;  // Deixo fora el bloc inicial més fort.
    int allow_dip;  // Permeto una baixada mentre confirmo veu.
    int remove_dc;  // Resto la mitjana abans de calcular la potència.
    int backdate;  // Torno al primer bloc pendent quan confirmo un canvi.
    int voice_dips;  // Baixades que ja he permès en aquest intent.
    int count;  // Compto els blocs consecutius d'un estat provisional.
    float last_feature;  // Guardo la potència actual per a --verbose.
} VAD_DATA;

const char *state2str(VAD_STATE state);  // Converteixo els estats a text.
VAD_DATA *vad_open(float sampling_rate);  // Reservo i inicialitzo el detector.
unsigned int vad_frame_size(VAD_DATA *data);  // Consulto la mida d'un bloc.
VAD_STATE vad(VAD_DATA *data, float *x);  // Analitzo un bloc nou.
VAD_STATE vad_close(VAD_DATA *data);  // Resolc els blocs pendents i allibero la memòria.
void vad_show_state(const VAD_DATA *data, FILE *out);  // Mostro dades de comprovació.
#endif
