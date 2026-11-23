#include <math.h>
#include <stdlib.h>
#include "vad.h"
#include "pav_analysis.h"

// Per defecte treballo amb blocs de 20 ms. Els marges són en dB.
const int INIT_FRAMES = 1;
const int MIN_VOICE = 5;
const int MIN_SILENCE = 8;
const float MARGIN_DB = 7.0f;
const float NOISE_ALPHA = 0.0023082305f;

const char *state2str(VAD_STATE state) {
    const char *names[] = {"UNDEF", "S", "V", "INIT", "MAYBE_V", "MAYBE_S"};
    return names[state];
}

VAD_DATA *vad_open(float rate) {
    if (rate < 100) return NULL;
    VAD_DATA *data = malloc(sizeof(VAD_DATA));
    if (data == NULL) return NULL;
    data->state = ST_INIT;
    data->sampling_rate = rate;
    data->frame_length = (unsigned int) (rate * 0.020);
    data->initial_frames = 0;
    data->initial_max = 0.0f;
    data->initial_sum = 0.0f;
    data->noise = -100.0f;
    data->margin_db = MARGIN_DB;
    data->init_frames = INIT_FRAMES;
    data->min_voice = MIN_VOICE;
    data->min_silence = MIN_SILENCE;
    data->noise_alpha = NOISE_ALPHA;
    data->silence_gap = 0.0f;
    data->trim_initial = 0;
    data->allow_dip = 1;
    data->remove_dc = 1;
    data->backdate = 1;
    data->rescue_zcr = data->confirm_high = 1;
    data->guard_noise = 0;
    data->zcr_threshold = 1750.0f;
    data->zcr_discount = 3.625f;
    data->confirm_boost = 6.0f;
    data->noise_update_margin = 2.0f;
    data->max_wait = 15;
    data->elapsed = data->high_seen = 0;
    data->asymmetric_noise = data->floor_noise = 1;
    data->direct_voice = 0;
    data->down_factor = 9.25f;
    data->voice_range = 41.25f;
    data->voice_level = -80.0f;
    data->voice_alpha = 1.0f - powf(0.9f, 2.0f);
    data->voice_dips = 0;
    data->count = 0;
    data->last_feature = -100.0f;
    return data;
}

unsigned int vad_frame_size(VAD_DATA *data) {
    return data->frame_length;
}

VAD_STATE vad(VAD_DATA *data, float *x) {
    float power = data->remove_dc ? compute_power_centered(x, data->frame_length) : compute_power(x, data->frame_length);
    if (power < -100.0f) power = -100.0f;
    data->last_feature = power;

    // Faig la mitjana en potència lineal i després passo a dB.
    if (data->state == ST_INIT) {
        float linear_power = powf(10.0f, power / 10.0f);
        if (data->trim_initial && linear_power > data->initial_max) {
            data->initial_sum += data->initial_max;
            data->initial_max = linear_power;
        } else {
            data->initial_sum += linear_power;
        }
        data->initial_frames++;
        if (data->initial_frames < data->init_frames) return ST_UNDEF;
        data->noise = 10.0f * log10f(data->initial_sum / (data->initial_frames - data->trim_initial));
        data->voice_level = data->noise + 20.0f;
        data->state = ST_SILENCE;
        return ST_SILENCE;
    }

    if (data->floor_noise) {
        if (data->state == ST_VOICE || data->state == ST_MAYBE_SILENCE)
            data->voice_level += data->voice_alpha * (power - data->voice_level);
        if (data->noise < data->voice_level - data->voice_range)
            data->noise = data->voice_level - data->voice_range;
    }
    float zcr = data->rescue_zcr ? compute_zcr(x, data->frame_length, data->sampling_rate) : 0.0f;
    float threshold = data->noise + data->margin_db;
    int candidate = power > threshold || (data->rescue_zcr && zcr > data->zcr_threshold && power > threshold - data->zcr_discount);
    float exit_threshold = threshold - data->silence_gap;
    int continuing = power > exit_threshold || (data->rescue_zcr && zcr > data->zcr_threshold && power > exit_threshold - data->zcr_discount);
    switch (data->state) {
    case ST_SILENCE:
        if (candidate) {
            data->state = ST_MAYBE_VOICE;
            data->count = 1;
            data->voice_dips = 0;
            data->elapsed = 1;
            data->high_seen = power > threshold + data->confirm_boost;
            if ((data->direct_voice && data->high_seen) || (data->min_voice == 1 && (!data->confirm_high || data->high_seen))) data->state = ST_VOICE;
        } else if (!data->guard_noise || power < data->noise + data->noise_update_margin) {
            float alpha = data->noise_alpha;
            if (data->asymmetric_noise && power < data->noise) {
                alpha *= data->down_factor;
                if (alpha > 1.0f) alpha = 1.0f;
            }
            data->noise += alpha * (power - data->noise);
        }
        break;
    // Els estats MAYBE esperen abans de confirmar el canvi.
    case ST_MAYBE_VOICE:
        data->elapsed++;
        if (power > threshold + data->confirm_boost) data->high_seen = 1;
        if (candidate) {
            data->count++;
            if ((data->direct_voice && power > threshold + data->confirm_boost) || (data->count >= data->min_voice && (!data->confirm_high || data->high_seen))) data->state = ST_VOICE;
        } else if (data->allow_dip && data->voice_dips == 0) {
            data->voice_dips = 1;
        } else {
            data->state = ST_SILENCE;
            data->count = 0;
        }
        if (data->confirm_high && data->state == ST_MAYBE_VOICE && data->elapsed >= data->max_wait) {
            data->state = ST_SILENCE;
            data->count = 0;
        }
        break;
    case ST_VOICE:
        if (!continuing) {
            data->state = ST_MAYBE_SILENCE;
            data->count = 1;
            if (data->min_silence == 1) data->state = ST_SILENCE;
        }
        break;
    case ST_MAYBE_SILENCE:
        if (!continuing) {
            data->count++;
            if (data->count >= data->min_silence) data->state = ST_SILENCE;
        } else {
            data->state = ST_VOICE;
            data->count = 0;
        }
        break;
    default:
        break;
    }

    if (data->state == ST_SILENCE || data->state == ST_VOICE) return data->state;
    return ST_UNDEF;
}

VAD_STATE vad_close(VAD_DATA *data) {
    VAD_STATE state = ST_SILENCE;
    if (data->state == ST_VOICE || data->state == ST_MAYBE_SILENCE) state = ST_VOICE;
    free(data);
    return state;
}

void vad_show_state(const VAD_DATA *data, FILE *out) {
    fprintf(out, "%s\t%.3f\t%.3f\n", state2str(data->state), data->last_feature, data->noise + data->margin_db);
}
