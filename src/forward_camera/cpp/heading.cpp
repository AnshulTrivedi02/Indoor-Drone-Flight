// C++ port of the FROZEN Phase 3 per-frame heading (src/forward_camera/fwd_measure.py: segments,
// vanishing_point, heading) and HeadingCore.measure/quality (heading_bridge_core.py).
// Same method, same frozen parameters (passed in), same OpenCV 4.6 LSD, and numpy's RNG and
// reductions reproduced (npy_random.hpp; numpy pairwise summation below). Build with
// -ffp-contract=off so no fused multiply-add changes the rounding against numpy.
// NOT used in any flight until the equivalence test passes and the user rules on switching
// (METHODOLOGY "C++ port of the heading node's per-frame computation").
#include "npy_random.hpp"
#include <opencv2/imgproc.hpp>
#include <opencv2/core.hpp>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <vector>

namespace {

constexpr double FX = 554.3827056884766, CX = 320.0, CY = 240.0;
constexpr double MIN_LEN_PX = 15.0, ANGLE_EXCL_DEG = 5.0;
constexpr int RANSAC_ITERS = 300;
constexpr double IMG_W = 640.0;
constexpr double HORIZON_BAND_DEG = 5.0;
constexpr double PI = 3.141592653589793;           // Py_MATH_PI / NPY_PI
constexpr double RAD2DEG = 180.0 / PI;             // numpy rad2deg and math.degrees constant
constexpr double DEG2RAD = PI / 180.0;             // math.radians constant
const double V_BAND = FX * std::tan(HORIZON_BAND_DEG * DEG2RAD);

// numpy DOUBLE_pairwise_sum, as used by ndarray.sum() (initial 0.0 + pairwise over all items)
double pairwise(const double *a, size_t n) {
    if (n < 8) {
        double r = 0.0;
        for (size_t i = 0; i < n; i++) r += a[i];
        return r;
    }
    if (n <= 128) {
        double r[8];
        for (int j = 0; j < 8; j++) r[j] = a[j];
        size_t i = 8, m = n - (n % 8);
        for (; i < m; i += 8)
            for (int j = 0; j < 8; j++) r[j] += a[i + j];
        double res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
        for (; i < n; i++) res += a[i];
        return res;
    }
    size_t n2 = n / 2; n2 -= n2 % 8;
    return pairwise(a, n2) + pairwise(a + n2, n - n2);
}
double npsum(const std::vector<double> &v) { return 0.0 + pairwise(v.data(), v.size()); }

struct Seg { double x1, y1, x2, y2; };

cv::Ptr<cv::LineSegmentDetector> &lsd() {
    static cv::Ptr<cv::LineSegmentDetector> d = cv::createLineSegmentDetector(cv::LSD_REFINE_STD);
    return d;
}

std::vector<Seg> segments(const cv::Mat &img) {
    std::vector<cv::Vec4f> lines;
    lsd()->detect(img, lines);
    std::vector<Seg> out;
    for (const auto &l : lines) {
        Seg s{double(l[0]), double(l[1]), double(l[2]), double(l[3])};
        double dx = s.x2 - s.x1, dy = s.y2 - s.y1;
        double length = std::hypot(dx, dy);
        double ang = std::atan2(std::fabs(dy), std::fabs(dx)) * RAD2DEG;
        if (length >= MIN_LEN_PX && ang > ANGLE_EXCL_DEG && ang < 90 - ANGLE_EXCL_DEG) out.push_back(s);
    }
    return out;
}

double residual_deg(const Seg &s, double px, double py) {
    double mx = 0.5 * (s.x1 + s.x2), my = 0.5 * (s.y1 + s.y2);   // 0.5 * (s[:, :2] + s[:, 2:])
    double dx = s.x2 - s.x1, dy = s.y2 - s.y1;
    double qx = px - mx, qy = py - my;
    double cross = std::fabs(dx * qy - dy * qx);
    double dot = std::fabs(dx * qx + dy * qy);
    return std::atan2(cross, dot) * RAD2DEG;
}

double balanced(const std::vector<Seg> &s, const std::vector<double> &L, const std::vector<char> &inl, double pu) {
    std::vector<double> l, r;
    for (size_t i = 0; i < s.size(); i++) {
        if (!inl[i]) continue;
        double mid_u = 0.5 * (s[i].x1 + s[i].x2);
        if (mid_u < pu) l.push_back(L[i]);
        if (mid_u > pu) r.push_back(L[i]);
    }
    return 2.0 * std::min(npsum(l), npsum(r));
}

}  // namespace

extern "C" {

// Per-frame heading. img: 8-bit mono, row stride in bytes. Outputs:
//   dout[0] psi_deg, [1] u, [2] v, [3] support, [4] len_inl, [5] processing seconds
//   iout[0] has_vp, [1] n_inl, [2] n_left, [3] n_right, [4] valid, [5] quality
// Returns 0.
int hc_heading(const uint8_t *img, int w, int h, int stride, uint64_t seed, double inlier_deg, double s_min,
               double *dout, int *iout) {
    auto t0 = std::chrono::steady_clock::now();
    cv::Mat m(h, w, CV_8UC1, const_cast<uint8_t *>(img), size_t(stride));
    std::vector<Seg> s = segments(m);
    for (int i = 0; i < 6; i++) dout[i] = 0.0;
    for (int i = 0; i < 6; i++) iout[i] = 0;
    iout[5] = -1;
    size_t n = s.size();
    bool have = false;
    double pu = 0, pv = 0;
    std::vector<double> L(n);
    std::vector<char> best;
    if (n >= 2) {
        for (size_t i = 0; i < n; i++) L[i] = std::hypot(s[i].x2 - s[i].x1, s[i].y2 - s[i].y1);
        double Ls = npsum(L);
        std::vector<double> pr(n);
        for (size_t i = 0; i < n; i++) pr[i] = L[i] / Ls;
        npyrand::PCG64 rng(seed);
        double best_score = 0.0;
        std::vector<char> inl(n);
        for (int it = 0; it < RANSAC_ITERS; it++) {
            int a, b;
            npyrand::choice2(rng, pr, a, b);
            // np.cross of homogeneous points -> lines, then the intersection
            double a0 = s[a].x1, a1 = s[a].y1, a2 = 1.0, b0 = s[a].x2, b1 = s[a].y2, b2 = 1.0;
            double la0 = a1 * b2 - a2 * b1, la1 = a2 * b0 - a0 * b2, la2 = a0 * b1 - a1 * b0;
            a0 = s[b].x1; a1 = s[b].y1; b0 = s[b].x2; b1 = s[b].y2;
            double lb0 = a1 * b2 - a2 * b1, lb1 = a2 * b0 - a0 * b2, lb2 = a0 * b1 - a1 * b0;
            double p0 = la1 * lb2 - la2 * lb1, p1 = la2 * lb0 - la0 * lb2, p2 = la0 * lb1 - la1 * lb0;
            if (std::fabs(p2) < 1e-9) continue;
            double qu = p0 / p2, qv = p1 / p2;
            if (!(std::isfinite(qu) && std::isfinite(qv)) || !(0 <= qu && qu < IMG_W && std::fabs(qv - CY) <= V_BAND)) continue;
            for (size_t i = 0; i < n; i++) inl[i] = residual_deg(s[i], qu, qv) <= inlier_deg;
            double sc = balanced(s, L, inl, qu);
            if (sc > best_score) { best = inl; best_score = sc; }
        }
        size_t nb = 0;
        for (char c : best) nb += c;
        if (!best.empty() && nb >= 2 && best_score > 0) {
            // least squares on the inlier lines in normal form, length-weighted
            cv::Mat A(int(nb), 2, CV_64F), bb(int(nb), 1, CV_64F);
            int r = 0;
            for (size_t i = 0; i < n; i++) {
                if (!best[i]) continue;
                double dx = s[i].x2 - s[i].x1, dy = s[i].y2 - s[i].y1, hn = std::hypot(dx, dy);
                double n0 = -dy / hn, n1 = dx / hn;
                double c = n0 * s[i].x1 + n1 * s[i].y1;
                double sw = std::pow(L[i], 0.5);
                A.at<double>(r, 0) = n0 * sw; A.at<double>(r, 1) = n1 * sw; bb.at<double>(r, 0) = c * sw;
                r++;
            }
            cv::Mat p;
            cv::solve(A, bb, p, cv::DECOMP_SVD);
            pu = p.at<double>(0); pv = p.at<double>(1);
            have = true;
        }
    }
    if (have) {
        std::vector<char> inl(n);
        std::vector<double> li;
        int nl = 0, nr = 0, ni = 0;
        for (size_t i = 0; i < n; i++) {
            inl[i] = residual_deg(s[i], pu, pv) <= inlier_deg;
            if (!inl[i]) continue;
            ni++; li.push_back(L[i]);
            double mid_u = 0.5 * (s[i].x1 + s[i].x2);
            nl += mid_u < pu; nr += mid_u > pu;
        }
        double sup = balanced(s, L, inl, pu);
        double psi = std::atan((pu - CX) / FX) * RAD2DEG;
        dout[0] = psi; dout[1] = pu; dout[2] = pv; dout[3] = sup; dout[4] = npsum(li);
        iout[0] = 1; iout[1] = ni; iout[2] = nl; iout[3] = nr;
        iout[4] = sup >= s_min;
        iout[5] = int(std::min(100.0, std::floor(50.0 * sup / s_min)));
    }
    dout[5] = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    return 0;
}

// RNG check: the first n Generator.random() values of default_rng(seed)
void hc_rng_randoms(uint64_t seed, int n, double *out) {
    npyrand::PCG64 r(seed);
    for (int i = 0; i < n; i++) out[i] = r.random();
}

// choice check: m successive choice(len(p), 2, replace=False, p=p) pairs from default_rng(seed)
void hc_rng_choice(uint64_t seed, const double *p, int np_, int m, int *out) {
    npyrand::PCG64 r(seed);
    std::vector<double> pv(p, p + np_);
    for (int i = 0; i < m; i++) npyrand::choice2(r, pv, out[2 * i], out[2 * i + 1]);
}

}  // extern "C"
