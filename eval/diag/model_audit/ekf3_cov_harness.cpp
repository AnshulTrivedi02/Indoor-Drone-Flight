// Model audit (2026-10-09), DIAGNOSTIC: EKF3's covariance prediction run standalone on recorded IMU deltas.
//
// The body of NavEKF3_core::CovariancePrediction's generated covariance code is NOT retyped: build.sh copies
// AP_NavEKF3_core.cpp lines 1196-1748 (pinned ArduPilot 7bac20cbcc; "// intermediate calculations" .. the end of
// `if (stateIndexLim > 9)`) verbatim into ekf3_gen.inc, which is #included below. Around it this file reproduces,
// from the same source:
//   - the noise set-up of CovariancePrediction (core.cpp:1036, 1045-1058, 1159-1163): daxVar = sq(dt*GYRO_P_NSE),
//     dvxVar = sq(dt*ACC_P_NSE), dAngBiasVar = sq(sq(dt)*GBIAS_P_NSE), dVelBiasVar = sq(sq(dt)*ABIAS_P_NSE);
//   - the bias process-noise addition and the symmetric copy (core.cpp:1750-1794);
//   - ConstrainVariances for states 0-15 with bias states active, badIMUdata false (core.cpp:1884-1984), switchable;
//   - the strapdown quaternion update (rotation by the bias-corrected delta angle), needed for q0..q3.
// Configuration: no mag, no wind -> stateIndexLim = 15 (updateStateIndexLim); dvelBiasAxisInhibit all false (in flight).
// No measurement is fused (free inertial). ftype = double (SITL builds EKF3 in double).
//
// Input (stdin): first line "q0 q1 q2 q3 constrain(0|1) dtEkfAvg"; second line 16 initial diagonal variances
// (EKF3 state units: quat, vel NED, pos NED, delta-angle bias rad, delta-velocity bias m/s); then one line per
// prediction step: "dt dax day daz dvx dvy dvz" (FRD body, accumulated delta angle / delta velocity).
// Output (stdout): per step "t q0 q1 q2 q3 P(0..15 x 0..15 upper triangle row-major)".
#include <cstdio>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <algorithm>

typedef double ftype;
static inline ftype sq(ftype x) { return x * x; }
static inline ftype constrain_ftype(ftype v, ftype lo, ftype hi) { return v < lo ? lo : (v > hi ? hi : v); }
static inline ftype fmaxF(ftype a, ftype b) { return a > b ? a : b; }

static ftype P[24][24], KHP[24][24];
static const uint8_t stateIndexLim = 15;
static const ftype GYRO_P_NSE = 1.5E-02, ACC_P_NSE = 3.5E-01, GBIAS_P_NSE = 1.0E-03, ABIAS_P_NSE = 2.0E-02;
static const ftype VEL_STATE_MIN_VARIANCE = 1E-4, POS_STATE_MIN_VARIANCE = 1E-4, ACCEL_BIAS_LIM_SCALER = 0.2f, ACC_BIAS_LIM = 1.0;
static ftype dtEkfAvg = 0.0125;
static int n_accbias_reset = 0, n_gbias_cap = 0;
static void calcTiltErrorVariance() {}

static void zeroRows(ftype M[24][24], uint8_t a, uint8_t b) { for (int r = a; r <= b; r++) for (int c = 0; c < 24; c++) M[r][c] = 0; }
static void zeroCols(ftype M[24][24], uint8_t a, uint8_t b) { for (int r = 0; r < 24; r++) for (int c = a; c <= b; c++) M[r][c] = 0; }

static void ConstrainVariances()   // core.cpp:1902-1984, states 0-15, bias states active, badIMUdata false
{
    for (uint8_t i = 0; i <= 3; i++) P[i][i] = constrain_ftype(P[i][i], 0.0, 1.0);
    for (uint8_t i = 4; i <= 5; i++) P[i][i] = constrain_ftype(P[i][i], VEL_STATE_MIN_VARIANCE, 1.0e3);
    if (P[6][6] < VEL_STATE_MIN_VARIANCE) P[6][6] = VEL_STATE_MIN_VARIANCE;   // clip-counter reset path not modelled (no fusion)
    for (uint8_t i = 7; i <= 9; i++) P[i][i] = constrain_ftype(P[i][i], POS_STATE_MIN_VARIANCE, 1.0e6);
    for (uint8_t i = 10; i <= 12; i++) { if (P[i][i] > sq(0.175 * dtEkfAvg)) n_gbias_cap++; P[i][i] = constrain_ftype(P[i][i], 0.0, sq(0.175 * dtEkfAvg)); }
    const ftype minSafeStateVar = 5E-9;
    ftype maxStateVar = 0.0; bool resetRequired = false;
    for (uint8_t s = 13; s <= 15; s++) {
        if (P[s][s] > maxStateVar) maxStateVar = P[s][s];
        else if (P[s][s] < minSafeStateVar) resetRequired = true;
    }
    const ftype minAllowedStateVar = fmaxF(0.01 * maxStateVar, minSafeStateVar);
    for (uint8_t s = 13; s <= 15; s++) P[s][s] = constrain_ftype(P[s][s], minAllowedStateVar, sq(10.0 * dtEkfAvg));
    if (resetRequired) {
        zeroCols(P, 13, 15); zeroRows(P, 13, 15);
        P[13][13] = sq(ACCEL_BIAS_LIM_SCALER * ACC_BIAS_LIM * dtEkfAvg); P[14][14] = P[13][13]; P[15][15] = P[13][13];
        n_accbias_reset++;
    }
}

// inputs of the generated block, at file scope so that the block's bare `return;` (quatCovResetOnly path, never
// taken here) is legal inside a void function
static ftype dt, dax, day, daz, dvx, dvy, dvz, q0, q1, q2, q3;
static ftype daxVar, dayVar, dazVar, dvxVar, dvyVar, dvzVar;
static const ftype dax_b = 0, day_b = 0, daz_b = 0, dvx_b = 0, dvy_b = 0, dvz_b = 0;   // bias states (zero, no fusion)
static const bool quatCovResetOnly = false;
static void generated_block()
{
    auto &nextP = KHP;
#include "ekf3_gen.inc"
}

int main()
{
    ftype dtavg; int constrain;
    if (scanf("%lf %lf %lf %lf %d %lf", &q0, &q1, &q2, &q3, &constrain, &dtavg) != 6) return 1;
    dtEkfAvg = dtavg;
    memset(P, 0, sizeof(P));
    for (int i = 0; i < 16; i++) if (scanf("%lf", &P[i][i]) != 1) return 1;
    ftype t = 0;
    while (scanf("%lf %lf %lf %lf %lf %lf %lf", &dt, &dax, &day, &daz, &dvx, &dvy, &dvz) == 7) {
        dt = constrain_ftype(dt, 0.5 * dtEkfAvg, 2.0 * dtEkfAvg);                    // core.cpp:1036
        // strapdown quaternion FIRST, as UpdateFilter (UpdateStrapdownEquationsNED then CovariancePrediction), bias 0
        const ftype a = sqrt(dax * dax + day * day + daz * daz);
        ftype r0 = 1, r1 = 0, r2 = 0, r3 = 0;
        if (a > 1e-12) { const ftype s = sin(0.5 * a) / a; r0 = cos(0.5 * a); r1 = dax * s; r2 = day * s; r3 = daz * s; }
        const ftype n0 = q0 * r0 - q1 * r1 - q2 * r2 - q3 * r3, n1 = q0 * r1 + q1 * r0 + q2 * r3 - q3 * r2;
        const ftype n2 = q0 * r2 - q1 * r3 + q2 * r0 + q3 * r1, n3 = q0 * r3 + q1 * r2 - q2 * r1 + q3 * r0;
        const ftype nn = sqrt(n0 * n0 + n1 * n1 + n2 * n2 + n3 * n3);
        q0 = n0 / nn; q1 = n1 / nn; q2 = n2 / nn; q3 = n3 / nn;
        ftype processNoiseVariance[14] = {};
        const ftype dAngBiasVar = sq(sq(dt) * constrain_ftype(GBIAS_P_NSE, 0.0, 1.0));
        for (int i = 0; i <= 2; i++) processNoiseVariance[i] = dAngBiasVar;
        const ftype dVelBiasVar = sq(sq(dt) * constrain_ftype(ABIAS_P_NSE, 0.0, 1.0));
        for (int i = 3; i <= 5; i++) processNoiseVariance[i] = dVelBiasVar;
        daxVar = sq(dt * GYRO_P_NSE); dayVar = daxVar; dazVar = daxVar;
        dvxVar = sq(dt * ACC_P_NSE); dvyVar = dvxVar; dvzVar = dvxVar;
        generated_block();
        auto &nextP = KHP;
        for (uint8_t i = 10; i <= stateIndexLim; i++) nextP[i][i] = nextP[i][i] + processNoiseVariance[i - 10];
        if ((P[7][7] + P[8][8]) > 1e4) {
            for (uint8_t i = 7; i <= 8; i++) for (uint8_t j = 0; j <= stateIndexLim; j++) { nextP[i][j] = P[i][j]; nextP[j][i] = P[j][i]; }
        }
        for (uint8_t row = 0; row <= stateIndexLim; row++) {
            P[row][row] = nextP[row][row];
            for (uint8_t column = 0; column < row; column++) P[row][column] = P[column][row] = nextP[column][row];
        }
        if (constrain) ConstrainVariances();
        t += dt;
        printf("%.6f %.15g %.15g %.15g %.15g", t, q0, q1, q2, q3);
        for (int i = 0; i < 16; i++) for (int j = i; j < 16; j++) printf(" %.9e", P[i][j]);
        printf("\n");
    }
    fprintf(stderr, "accel-bias resets %d, gyro-bias cap hits %d\n", n_accbias_reset, n_gbias_cap);
    return 0;
}
