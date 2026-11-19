#include <math.h>
#include <stddef.h>
#include "pav_analysis.h"

/* Potencia mitjana de la senyal en dB:
    PdB = 10 * log10( (1/N) * sum(x[n]^2) )
*/
float compute_power(const float *x, unsigned int N) {    
    float suma = 0;
    for (unsigned int n = 0; n < N; n++) {
        suma += x[n] * x[n];
    }
    
    return 10.0f * log10f((suma / (float)N) + 1e-12f);
}

/* Amplitud mitjana: valor mitg del valor absolut de la senyal.
    A = 1/N * sum |x[n]|
*/
float compute_am(const float *x, unsigned int N) {   
    if (x == NULL || N == 0) return 0.0f;

    float suma = 0.0f;
    for (unsigned int n = 0; n < N; n++) {
        suma += fabsf(x[n]);
    }    
    return suma / (float)N;
}

/* XCR: Definin el signe com: positiu si x[n] >= 0, negatiu si x[n] < 0.
 *  per evitar cas "zero"
 */
float compute_zcr(const float *x, unsigned int N, float fm) {
    if (x == NULL || N <= 1) return 0.0f;
   
    unsigned int cont = 0;
    for (unsigned int n = 1; n < N; n++) {
        // Un canvi de signe es produeix si una mostra és positiva/zero i l'altra és negativa
        if ((x[n] >= 0.0f && x[n - 1] < 0.0f) || (x[n] < 0.0f && x[n - 1] >= 0.0f)) {
            cont++;
        }
    }    
    return (fm /2.0f) * ((float)cont / (float)(N - 1));
}


