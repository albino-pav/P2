#include <math.h>
#include <stddef.h>
#include "pav_analysis.h"

float compute_power(const float *x, unsigned int N) {
    if (x == NULL || N == 0) return -100.0f;
    
    float sum_sq = 0.0f; 
    for (unsigned int n = 0; n<N; n++) {
        sum_sq += x[n] * x[n];
    }

    float power = sum_sq / (float)N;
    if (power <= 0.0f) {
        return -100.0f;
    } 
    
    return 10.0f * log10f(power);
}

float compute_am(const float *x, unsigned int N) {
    if (x == NULL || N == 0) return 0.0f;
    
    float sum_abs = 0.0f;
    for (unsigned int n = 0; n < N; n++) {
        sum_abs += fabsf(x[n]); 
    }
    
    return sum_abs / (float)N;
}

float compute_zcr(const float *x, unsigned int N, float fm) {
    if (x == NULL || N <= 1) return 0.0f;
    
    unsigned int crossings = 0;
    for (unsigned int n = 1; n < N; n++) {  
        if ((x[n] >= 0.0f && x[n - 1] < 0.0f) || (x[n] < 0.0f && x[n - 1] >= 0.0f)) { 
            crossings++; 
        } 
    } 
    
    return (fm / 2.0f) * ((float)crossings / (float)(N - 1));
}

