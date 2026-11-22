#include <math.h>
#include "pav_analysis.h"

float compute_power(const float *x, unsigned int N) {
    float power = 0.0;

    for (unsigned int n = 0; n < N; n++) {
        power += x[n] * x[n];
    }

    power = power / N;

    return 10 * log10(power);
}

float compute_am(const float *x, unsigned int N) {
    float am = 0.0;

    for (unsigned int n = 0; n < N; n++) {
        am += fabs(x[n]);
    }

    return am / N;
}

float compute_zcr(const float *x, unsigned int N, float fm) {
    unsigned int cruces = 0;

    for (unsigned int n = 1; n < N; n++) {
        if ((x[n] >= 0 && x[n-1] < 0) ||
            (x[n] < 0 && x[n-1] >= 0)) {
            cruces++;
        }
    }

    return (fm / 2.0) * ((float)cruces / (N - 1));
}
