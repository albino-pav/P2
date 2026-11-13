#include <math.h>
#include "pav_analysis.h"

float compute_power(const float *x, unsigned int N) {
    if (N == 0) return 0.0f;
    
    double sum = 0.0;
    for (unsigned int i = 0; i < N; i++) {
        sum += x[i] * x[i];
    }
    double power = sum / N;
    

    if (power < 1e-10) {
        power = 1e-10;
    }
    
    return (float)(10.0 * log10(power));
}

float compute_am(const float *x, unsigned int N) {
    if (N == 0) return 0.0f;
    
    double sum = 0.0;
    for (unsigned int i = 0; i < N; i++) {
        sum += fabs(x[i]);
    }
    return (float)(sum / N);
}

float compute_zcr(const float *x, unsigned int N, float fm) {
    if (N <= 1) return 0.0f;
    
    unsigned int count = 0;
    for (unsigned int i = 1; i < N; i++) {
        if ((x[i] * x[i-1]) < 0.0f) {
            count++;
        }
    }

    float zcr = (count / (2.0f * N)) * fm;
    
    return zcr;
}