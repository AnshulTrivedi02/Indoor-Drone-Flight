// Test driver for libheading (real-flight plan, tooling item 2): reads frames from a binary file and prints every
// hc_heading output at full precision, so the x86 build and the ARM64 build (on a Pi, or under qemu-aarch64) can be
// compared output for output on identical inputs. File format (little-endian): int32 n, int32 w, int32 h, then n
// records of {uint64 seed; uint8 pixels[w*h]}. Args: FILE INLIER_DEG S_MIN.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
extern "C" int hc_heading(const uint8_t *img, int w, int h, int stride, uint64_t seed, double inlier_deg, double s_min,
                          double *dout, int *iout);
int main(int argc, char **argv) {
    if (argc < 4) { std::fprintf(stderr, "usage: %s FILE INLIER_DEG S_MIN\n", argv[0]); return 2; }
    FILE *f = std::fopen(argv[1], "rb");
    if (!f) { std::perror("open"); return 1; }
    int32_t hdr[3];
    if (std::fread(hdr, 4, 3, f) != 3) return 1;
    const int n = hdr[0], w = hdr[1], h = hdr[2];
    std::vector<uint8_t> img(size_t(w) * h);
    const double inl = std::atof(argv[2]), smin = std::atof(argv[3]);
    std::printf("seed,has_vp,psi_deg,u,v,support,len_inl,n_inl,n_left,n_right,valid,quality,proc_s\n");
    for (int i = 0; i < n; i++) {
        uint64_t seed;
        if (std::fread(&seed, 8, 1, f) != 1 || std::fread(img.data(), 1, img.size(), f) != img.size()) return 1;
        double d[6]; int k[6];
        hc_heading(img.data(), w, h, w, seed, inl, smin, d, k);
        std::printf("%llu,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%d,%d,%d,%d,%d,%.6f\n", (unsigned long long)seed, k[0], d[0], d[1], d[2],
                    d[3], d[4], k[1], k[2], k[3], k[4], k[5], d[5]);
    }
    return 0;
}
