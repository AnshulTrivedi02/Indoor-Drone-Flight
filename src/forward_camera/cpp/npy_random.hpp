// Bit-exact C++ reproduction of the numpy 1.26.4 random stack used by the frozen Phase 3
// heading RANSAC: np.random.default_rng(seed) (SeedSequence -> PCG64), Generator.random(), and
// Generator.choice(n, 2, replace=False, p=...). Verified against numpy by
// eval/heading_cpp_equivalence.py (RNG check first). METHODOLOGY "C++ port of the heading node".
#pragma once
#include <cstdint>
#include <vector>
#include <algorithm>

namespace npyrand {

// ---- SeedSequence (numpy/random/bit_generator.pyx) ----
constexpr uint32_t INIT_A = 0x43b0d7e5u, MULT_A = 0x931e8875u, INIT_B = 0x8b51f9ddu, MULT_B = 0x58f38dedu;
constexpr uint32_t MIX_MULT_L = 0xca01f9ddu, MIX_MULT_R = 0x4973f715u;
constexpr int XSHIFT = 16, POOL_SIZE = 4;

inline uint32_t hashmix(uint32_t value, uint32_t &hash_const) {
    value ^= hash_const;
    hash_const *= MULT_A;
    value *= hash_const;
    value ^= value >> XSHIFT;
    return value;
}

inline uint32_t mix(uint32_t x, uint32_t y) {
    uint32_t r = MIX_MULT_L * x - MIX_MULT_R * y;
    r ^= r >> XSHIFT;
    return r;
}

// generate_state(4, np.uint64) for a non-negative integer seed (no spawn key)
inline void seed_state_u64x4(uint64_t seed, uint64_t out[4]) {
    std::vector<uint32_t> ent;
    if (seed == 0) {
        ent.push_back(0);
    } else {
        while (seed) { ent.push_back(uint32_t(seed & 0xffffffffu)); seed >>= 32; }
    }
    uint32_t pool[POOL_SIZE];
    uint32_t hc = INIT_A;
    for (int i = 0; i < POOL_SIZE; i++) {
        pool[i] = hashmix(i < int(ent.size()) ? ent[i] : 0u, hc);
    }
    for (int s = 0; s < POOL_SIZE; s++)
        for (int d = 0; d < POOL_SIZE; d++)
            if (s != d) pool[d] = mix(pool[d], hashmix(pool[s], hc));
    for (size_t s = POOL_SIZE; s < ent.size(); s++)
        for (int d = 0; d < POOL_SIZE; d++)
            pool[d] = mix(pool[d], hashmix(ent[s], hc));
    uint32_t st[8];
    uint32_t hb = INIT_B;
    for (int i = 0; i < 8; i++) {
        uint32_t v = pool[i % POOL_SIZE];
        v ^= hb;
        hb *= MULT_B;
        v *= hb;
        v ^= v >> XSHIFT;
        st[i] = v;
    }
    for (int i = 0; i < 4; i++) out[i] = uint64_t(st[2 * i]) | (uint64_t(st[2 * i + 1]) << 32);   // little-endian view
}

// ---- PCG64 (XSL-RR 128/64), numpy/random/src/pcg64 ----
using u128 = unsigned __int128;
struct PCG64 {
    u128 state, inc;
    static constexpr u128 MULT = (u128(2549297995355413924ULL) << 64) + 4865540595714422341ULL;
    explicit PCG64(uint64_t seed) {
        uint64_t v[4];
        seed_state_u64x4(seed, v);
        u128 s = (u128(v[0]) << 64) + v[1];     // PCG_128BIT_CONSTANT(high = seed[0], low = seed[1])
        u128 i = (u128(v[2]) << 64) + v[3];
        state = 0; inc = (i << 1) | 1u;
        step(); state += s; step();
    }
    void step() { state = state * MULT + inc; }
    uint64_t next64() {
        step();
        uint64_t x = uint64_t(state >> 64) ^ uint64_t(state);
        unsigned rot = unsigned(state >> 122);
        return (x >> rot) | (x << ((64 - rot) & 63));
    }
    double random() { return double(next64() >> 11) * (1.0 / 9007199254740992.0); }
};

// Generator.choice(n, 2, replace=False, p=p): numpy's weighted no-replacement algorithm
// (cumsum, normalise by the last element, searchsorted side='right', keep first occurrences,
// zero the found entries and redraw the remainder).
inline void choice2(PCG64 &rng, const std::vector<double> &p_in, int &i0, int &i1) {
    std::vector<double> p(p_in), cdf(p_in.size());
    int found[2]; int nf = 0;
    while (nf < 2) {
        int need = 2 - nf;
        double x[2];
        for (int j = 0; j < need; j++) x[j] = rng.random();
        for (int j = 0; j < nf; j++) p[found[j]] = 0.0;
        double acc = 0.0;
        for (size_t j = 0; j < p.size(); j++) { acc += p[j]; cdf[j] = acc; }
        double last = cdf.back();
        for (auto &c : cdf) c /= last;
        int nw[2];
        for (int j = 0; j < need; j++) nw[j] = int(std::upper_bound(cdf.begin(), cdf.end(), x[j]) - cdf.begin());
        // unique with first-occurrence order
        for (int j = 0; j < need; j++) {
            bool dup = false;
            for (int q = 0; q < j; q++) if (nw[q] == nw[j]) dup = true;
            if (!dup) found[nf++] = nw[j];
        }
    }
    i0 = found[0]; i1 = found[1];
}

}  // namespace npyrand
