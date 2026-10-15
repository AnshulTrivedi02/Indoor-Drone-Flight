#!/usr/bin/env python3
"""READER-FACING THESIS FIGURE SET (2026-10-15). Plotting only: no number is recomputed, re-run or changed.

Plots the FROZEN results that eval/figs_final_pack.py already reads (eval/results/** and, for the flight paths, heading
error and the O time series, the recorded dataflash/bag/TUM files under ~/thesis_data/trials). The loaders below are
COPIED from eval/figs_final_pack.py (that script runs everything at module level, so importing it would regenerate the
frozen pack; it is left untouched, as is docs/thesis/final_results_pack.pdf).

Every figure keeps the numbers.md CROSS-CHECK of figs_final_pack.py: each plotted key value is computed here from the
result file and compared with the value typed from docs/thesis/numbers.md (or METHODOLOGY where numbers.md has no row).
A failed check marks the figure FLAGGED in the index.

Rules (task brief 2026-10-15): one-line takeaway titles; captions in the combined PDF and the index only; NO log axes;
a fixed Okabe-Ito colour per estimator; filled/solid = live, open/dashed = hindsight; no panels with differing y-scales;
thin marks; units on every axis; a legend wherever >= 2 series; no dual axes.

Outputs: docs/thesis/figures_thesis/<id>_*.pdf/.png, thesis_figures_combined.pdf, index.md.
Usage: /home/makerspace/venv-evo/bin/python eval/figs_thesis.py   (pymavlink via ~/.cache/thesis_pyshim, inserted below)"""
import json, math, os, re, subprocess, sys, textwrap
sys.path.insert(0, os.path.expanduser("~/.cache/thesis_pyshim"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Patch
from matplotlib.backends.backend_pdf import PdfPages
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from cruise_window import cruise_bounds
RES = os.path.join(ROOT, "eval", "results"); TD = os.path.expanduser("~/thesis_data/trials")
OUT = os.path.join(ROOT, "docs", "thesis", "figures_thesis"); os.makedirs(OUT, exist_ok=True)
PDF = os.path.join(OUT, "thesis_figures_combined.pdf"); INDEX = os.path.join(OUT, "index.md")
SCRIPT = "eval/figs_thesis.py"
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

# ---------------------------------------------------------------------------------------------------------- style
# Okabe-Ito (colour-blind safe). One fixed colour and one marker shape per estimator, in every figure.
C = {"EKF3": "#0072B2", "UKF": "#009E73", "FGO": "#D55E00"}
MK = {"EKF3": "o", "UKF": "^", "FGO": "s"}
TRUTH = "#999999"                      # reserved for truth / references (never an estimator)
INK, INK2, GRID, SURF, WALL = "#111111", "#4d4d4d", "#e4e4e4", "#ffffff", "#5e5e5e"
EST = ("EKF3", "UKF", "FGO")
plt.rcParams.update({"font.size": 10.5, "axes.titlesize": 11, "axes.labelsize": 10.5, "xtick.labelsize": 9.5,
                     "ytick.labelsize": 9.5, "legend.fontsize": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "axes.axisbelow": True, "figure.facecolor": SURF, "axes.facecolor": SURF,
                     "savefig.facecolor": SURF, "lines.linewidth": 1.2, "lines.markersize": 5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.8, "pdf.fonttype": 42})
L = lambda f: json.load(open(os.path.join(RES, f)))
ITEMS = []; CHK = []; ROUNDING = []


def f2(v, n=2):
    return f"{v:.{n}f}"


def rng(vals, n=2, unit=""):
    return f"{min(vals):.{n}f}–{max(vals):.{n}f}{unit}"


NUM = re.compile(r"[-+−]?\d+(?:\.\d+)?(?:e[-+]?\d+)?")


def check(label, computed, expected, src, exact=False):
    """Copied from figs_final_pack.py: exact string match, or a numeric match within one unit of the expected value's
    last printed digit (recorded as a rounding-boundary note, not a mismatch)."""
    c, e = str(computed), str(expected)
    ok = c == e
    if not ok and not exact:
        a = NUM.findall(c.replace("−", "-")); b = NUM.findall(e.replace("−", "-"))
        if a and len(a) == len(b) and NUM.sub("#", c.replace("−", "-")) == NUM.sub("#", e.replace("−", "-")):
            unit = lambda s: 10 ** -len(s.split(".")[1]) if "." in s and "e" not in s else 1
            if all(abs(float(x) - float(y)) <= unit(y) * 1.0001 for x, y in zip(a, b)):
                ok = True; ROUNDING.append((label, c, e, src))
    CHK.append((label, c, e, src, ok))


def save(fig, fid, name, title, caption, inputs, rows, logscale="none needed", uncheck=""):
    """Writes <name>.pdf and <name>.png; records caption, sources and checks for the combined PDF and the index."""
    global CHK
    fig.suptitle(title, x=0.01, ha="left", fontsize=12.5, weight="bold")
    base = os.path.join(OUT, name)
    fig.savefig(base + ".png", dpi=170, bbox_inches="tight"); fig.savefig(base + ".pdf", bbox_inches="tight"); plt.close(fig)
    ok = all(c[4] for c in CHK)
    ITEMS.append(dict(id=fid, png=base + ".png", pdf=base + ".pdf", title=title, caption=caption, inputs=inputs, rows=rows,
                      checks=CHK, status="CURRENT" if ok else "FLAGGED (check mismatch)", logscale=logscale, uncheck=uncheck))
    print(f"wrote {base}.png/.pdf  checks {sum(c[4] for c in CHK)}/{len(CHK)}")
    for c in CHK:
        if not c[4]:
            print("   CHECK FAIL:", c)
    CHK = []


def legend_est(ax, ests=EST, extra=(), **kw):
    h = [Line2D([], [], ls="-", marker=MK[e], color=C[e], ms=6, label=e) for e in ests] + list(extra)
    return ax.legend(handles=h, frameon=False, **kw)


# ------------------------------------------------------------------ flight-data helpers (COPIED from figs_final_pack.py)
_sim = {}
def sim_path(tr):
    """Simulator-truth path from dataflash SIM: (t s, x East m, y North m, yaw deg), origin at the first sample (spawn)."""
    if tr in _sim:
        return _sim[tr]
    m = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); S = []
    while True:
        r = m.recv_match(type=["SIM"])
        if r is None:
            break
        S.append((r.TimeUS / 1e6, r.Lat, r.Lng, r.Yaw))
    S = np.array(S); lat, lng = S[:, 1], S[:, 2]
    if abs(lat).max() > 1000:
        lat, lng = lat / 1e7, lng / 1e7
    N = np.radians(lat - lat[0]) * 6378137; E = np.radians(lng - lng[0]) * 6378137 * math.cos(math.radians(lat.mean()))
    _sim[tr] = np.column_stack([S[:, 0], E, N, S[:, 3]]); return _sim[tr]


def log_yaw(tr, est):
    """Heading error of the flying estimator against SIM yaw from cruise start (copied; FGO branch added: XFGO.Yaw, the
    source closed_loop_score.py uses for --est fgo)."""
    m = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); E, S = [], []
    while True:
        r = m.recv_match(type=["SIM", "XKF1", "XUKO", "XFGO"])
        if r is None:
            break
        t = r.get_type()
        if t == "SIM": S.append((r.TimeUS / 1e6, r.Lat, r.Lng, r.Yaw))
        elif t == "XKF1" and est == "EKF3" and r.C == 0: E.append((r.TimeUS / 1e6, r.Yaw))
        elif t == "XUKO" and est == "UKF": E.append((r.TimeUS / 1e6, r.Yaw))
        elif t == "XFGO" and est == "FGO": E.append((r.TimeUS / 1e6, r.Yaw))
    S, E = np.array(S), np.array(E); lat, lng = S[:, 1], S[:, 2]
    if abs(lat).max() > 1000:
        lat, lng = lat / 1e7, lng / 1e7
    N = np.radians(lat - lat[0]) * 6378137; Ee = np.radians(lng - lng[0]) * 6378137 * math.cos(math.radians(lat.mean()))
    c0, _ = cruise_bounds(S[:, 0], Ee, N)
    un = lambda d: np.degrees(np.unwrap(np.radians(d)))
    w = E[:, 0] >= c0
    e = (un(E[w, 1]) - np.interp(E[w, 0], S[:, 0], un(S[:, 3])) + 180) % 360 - 180
    return E[w, 0] - c0, e


def cl_meta(tr):
    js = L(f"closed_loop_{tr}.json")
    c0 = js["cruise_s"][0] if "cruise_s" in js else js["cruise_start_s"]
    ct = js.get("contact")
    if ct and "t_rel_cruise_s" not in ct:
        ct = {"x": ct["E_m"], "y": ct["N_m"], "t_rel_cruise_s": ct["cruise_plus_s"]}
    return c0, ct


def draw_corridor(ax):
    for yw in (10, -10):
        ax.axhspan(yw - 0.1, yw + 0.1, color=WALL, lw=0)
    ax.axhline(9.58, color=WALL, lw=0.6, ls=":"); ax.axhline(-9.58, color=WALL, lw=0.6, ls=":")
    ax.set_ylim(-10.6, 10.6); ax.set_xlim(0, 160); ax.set_yticks([-10, -5, 0, 5, 10])


WIN = {"EKF3": (155, 215), "UKF": (146, 218), "FGO": (145, 196)}
# ============================================================================================ data used by several figures
ev = {**L("rerun_dsn_evo.json")["trials"], **L("dsn_extra_evo.json")["trials"]}
pt = L("dsn_paired_test.json")
DSN = {}
for est in EST:
    DSN[est] = [(i, ev[f"dsn_tex_r{i}"]["est"][est]["ate_a_cruise"]["+0.00"]) for i in range(1, 10)
                if est in ev[f"dsn_tex_r{i}"]["est"] and ev[f"dsn_tex_r{i}"]["est"][est]["ate_a_cruise"].get("+0.00") is not None]
CAMB = [(ds, r) for ds in ("fwdc", "fwdplainc") for r in (1, 2, 3)]
P4 = {}
for ds, r in CAMB:
    e = L(f"phase4_{ds}_evo.json")["trials"][f"{ds}_tex_r{r}"]["est"]
    P4[(ds, r)] = {k: e[k]["ate_a_cruise"]["+0.00"] for k in ("EKF3", "UKF_baseline", "FGO_baseline", "UKF_heading", "FGO_heading")}
bb = L("blank_behaviour.json")
BLANK = {}
for est, keys in (("UKF", ("ukf", "ukf_baseline")), ("FGO", ("fgo", "fgo_baseline"))):
    rows = []
    for trn, v in bb.items():
        if "blank" not in trn or trn.startswith("ds_"):
            continue
        a = next((v[k] for k in keys if k in v), None)
        if a is None:
            continue
        rows.append([math.hypot(a[t]["along_m"], a[t]["cross_m"]) for t in ("+10s", "+30s", "+60s", "end")])
    BLANK[est] = np.array(rows)
EK_INV = [v["EKF3_invalid_period"]["duration_in_cruise_s"] for k, v in bb.items() if "blank" in k and "EKF3_invalid_period" in v]
agg = L("expT/t_aggregate.json")
TCOND = "ABCD"; TLAB = {"A": "8 tags", "B": "4 tags", "C": "2 tags", "D": "1 tag"}
TRK = ("EKF3 live", "UKF live", "FGO live", "RTS-UKF (hindsight)", "FGO hindsight (whole-flight batch)")
TSTY = {"EKF3 live": ("EKF3", "live"), "UKF live": ("UKF", "live"), "FGO live": ("FGO", "live"),
        "RTS-UKF (hindsight)": ("UKF", "hind"), "FGO hindsight (whole-flight batch)": ("FGO", "hind")}
TSHORT = {"EKF3 live": "EKF3 live", "UKF live": "UKF live", "FGO live": "FGO live", "RTS-UKF (hindsight)": "RTS-UKF (hindsight)",
          "FGO hindsight (whole-flight batch)": "FGO batch (hindsight)"}
OFL = ("O_r1", "O_r2", "O_r3b")
OI = {n: [L(f"expO/{t}.json")["tracks"][n]["indoor_rmse_m"] for t in OFL] for n in TRK}
HJ = lambda t: L(f"expH/{t}.json")
S1 = ["s1_r1", "s1_r2", "s1_r3"]; S1F = ["s1far_r1", "s1far_r2", "s1far_r3b"]
S2V = ["s2v2_r1", "s2v2_r2", "s2v2_r3"]; S2O = ["s2_r1", "s2_r2", "s2_r3"]
S3V = ["s3v2_r1", "s3v2_r2", "s3v2_r3"]; S3O = ["s3_r1", "s3_r2", "s3_r3"]
HALF = {"EKF3": ("cl_a_tex_half", [f"cl_bcpp_tex_r{i}_half" for i in (1, 2, 3)]),
        "UKF": ("cl_ukf_a_tex_half_v2", [f"cl_ukf_b_tex_r{i}_half_v2" for i in (1, 2, 3)]),
        "FGO": ("cl_fgo_a_tex_half_v3", [f"cl_fgo_b_tex_r{i}_half_v3" for i in (1, 2, 3)])}
HBUILD = {"EKF3": "EKF3", "UKF": "UKF v2", "FGO": "FGO v3 (OLD priors)"}
LL = {}
for mode in ("lc", "nolc"):
    for kind in ("live", "hindsight"):
        LL[(mode, kind)] = [L(f"expL/T_A_r{r}_t245.json")["tracks"][f"{mode} {kind}"] for r in (1, 2, 3)]


def drifts(trs, key, metric="eff"):
    out = [[], [], [], []]
    for t in trs:
        for i, lo in enumerate(HJ(t)["losses"]):
            v = lo[key]
            out[i].append(1e3 * (v["effective"]["drift_m"] if metric == "eff" else v["drift_end_m"]))
    return out


# =============================================================================================== FIG 1 scorecard
CAT = {"BEST": ("#cfcfcf", "best"), "TIED": ("#f0f0f0", "tied"), "BEHIND": ("#ffffff", "behind"),
       "FAILED": ("#ffffff", "failed"), "PASSED": ("#f0f0f0", "passed"), "N/A": ("#ffffff", "n/a")}
med = {e: float(np.median([v for _, v in DSN[e]])) for e in EST}
check("dsn_tex median r1–r9 EKF3 / UKF / FGO (m)", " / ".join(f2(med[e]) for e in EST), "4.10 / 5.13 / 4.46", "numbers.md §6.1 standing row")
check("confirmatory EKF3 − FGO verdict", pt["verdict"], "no ordering claimed", "numbers.md §6.1 confirmatory row; claim 2")
u6 = [P4[b]["UKF_heading"] for b in CAMB]; g6 = [P4[b]["FGO_heading"] for b in CAMB]
check("C0 with heading UKF / FGO range, 6 textured bags (m)", f"{rng(u6)} / {rng(g6)}", "0.13–0.25 / 0.06–0.22", "numbers.md §6.6 heading-arm rows")
check("C0 FGO lower than UKF", f"{sum(a < b for a, b in zip(g6, u6))}/6", "6/6", "numbers.md §6.6 C0 row; claim 7")
check("blank end-of-cruise UKF / FGO (km) †", f"{rng(BLANK['UKF'][:, 3] / 1e3, 0)} / {rng(BLANK['FGO'][:, 3] / 1e3, 0)}", "29–40 / 22–41", "numbers.md §6.2")
check("EKF3 blank invalid for (s of cruise), all 14", rng(EK_INV, 0) + f" (n {len(EK_INV)})", "301–310 (n 14)", "numbers.md §6.2 ('blank from take-off (all 14), for 301–310 s')")
mrD = agg["conditions"]["D"]["mean_rmse_m"]
check("T condition D live EKF3 / UKF / FGO (m)", " / ".join(f"{mrD[k]:.3f}" for k in ("EKF3 live", "UKF live", "FGO live")), "0.096 / 0.131 / 0.083", "numbers.md §16.1 table")
check("T FGO batch A–D (m)", rng([agg["conditions"][c]["mean_rmse_m"]["FGO hindsight (whole-flight batch)"] for c in TCOND], 3), "0.011–0.028", "numbers.md §16.1 table")
check("O indoor live RMSE EKF3 / UKF / FGO (m)", " / ".join(rng(OI[f"{e} live"]) for e in EST), "1.42–1.43 / 0.77–0.84 / 0.83–0.89", "numbers.md §16.2 table")
ho2 = [max(OI[f"{e} live"][i] for e in EST) / min(OI[f"{e} live"][i] for e in EST) for i in range(3)]
ho2_max_is_ekf3 = all(max(EST, key=lambda e: OI[f"{e} live"][i]) == "EKF3" for i in range(3))
check("O H-O2 live max/min ratio; largest = EKF3 in every flight", f"{rng(ho2)}; {ho2_max_is_ekf3}", "1.72–1.84; True", "numbers.md §16.2 H-O2 bullet")
check("O FGO batch / RTS-UKF indoor (m)", f"{rng(OI['FGO hindsight (whole-flight batch)'])} / {rng(OI['RTS-UKF (hindsight)'])}", "0.59–0.59 / 0.58–0.60", "numbers.md §16.2 table")
check("L live with / without loop closure (m)", f"{rng([t['rmse_m'] for t in LL[('lc', 'live')]], 3)} / {rng([t['rmse_m'] for t in LL[('nolc', 'live')]], 3)}",
      "0.049–0.076 / 0.262–0.361", "numbers.md §16.3")
_hc = [v for k, v in L("expH/h_comparative_2026-10-11.json")["sets"].items() if k.startswith("re-flown")][0]
hE = [np.mean([w["mean_m"] * 1e3 for w in HJ(t)["hold_windows_vehicle"]]) for t in S1F]
hU = [r["hold_mean_mm"] for r in _hc["UKF"]]; hF = [r["hold_mean_mm"] for r in _hc["FGO"]]
check("H run-mean hold error EKF3 (S1 far) / UKF (S2v2) / FGO (S3v2) (mm)", f"{rng(hE, 1)} / {rng(hU, 1)} / {rng(hF, 1)}", "7.8–7.9 / 6.4–7.1 / 8.3–8.6", "numbers.md §17.2 table")
check("H comparative H-H2; P-H3; H-H4 15 s; H-H4 5 s (re-flown)", "; ".join(_hc["criteria"][k].split()[0] for k in ("H-H2", "P-H3", "H-H4 (15 s)", "H-H4 (5 s)")),
      "FAIL; FAIL; FAIL; FAIL", "numbers.md §17.2 (PENDING ruling)")
B2h = {e: [L(f"closed_loop_{t}.json")["B"]["B2"]["max_abs_x_cruise_m"] for t in HALF[e][1]] for e in EST}
passh = {e: sum(L(f"closed_loop_{t}.json")["B"]["pass"] and L(f"closed_loop_{t}.json").get("S2", {}).get("pass", True) for t in HALF[e][1]) for e in EST}
check("closed loop half, with heading: B2 range EKF3 / UKF v2 / FGO v3 (m)", " / ".join(rng(B2h[e]) for e in EST), "0.24–0.33 / 0.22–0.25 / 0.03–0.39",
      "numbers.md §15 B2 row (EKF3 half) and re-flown rows (UKF v2 0.231/0.253/0.219; FGO v3 0.118/0.033/0.392)")
check("closed loop half, with heading: flights passing B1–B5 (+S2)", " / ".join(f"{passh[e]}/3" for e in EST), "3/3 / 3/3 / 3/3", "numbers.md §15")

COLS = ["Standard sensors\n(textured, no heading)", "With camera\nheading (offline)", "Blank floor\n(no flow)", "T: tags at\nknown positions",
        "O: GNSS outside,\nindoors without", "L: tags at\nunknown positions", "H: hold on\na wall tag", "Closed loop\n(estimator flies)"]
CELLS = {
    "EKF3": [("TIED", f"median {med['EKF3']:.2f} m", "claim 2: no ordering"),
             ("N/A", "no offline\nheading arm", "EKF3 ruling 09-29"),
             ("FAILED", "position invalid\nfrom take-off", "origin output, unscored"),
             ("TIED", f"1 tag: {mrD['EKF3 live'] * 100:.1f} cm live", "ruling 7: no live order"),
             ("BEHIND", f"indoor {rng(OI['EKF3 live'])} m", "H-O2 FAIL; 4.10 m jump"),
             ("N/A", "FGO capability\nonly", "claim 23"),
             ("TIED", f"hold {rng(hE, 1)} mm", "bands PASS"),
             ("TIED", f"{passh['EKF3']}/3 pass; B2 ≤ {max(B2h['EKF3']):.2f} m", "no ordering claimed")],
    "UKF": [("TIED", f"median {med['UKF']:.2f} m", "claim 1b: descriptive"),
            ("BEHIND", f"{rng(u6)} m", "claim 7 (C0)"),
            ("FAILED", f"{rng(BLANK['UKF'][:, 3] / 1e3, 0)} km at end †", "claim 10"),
            ("TIED", f"1 tag: {mrD['UKF live'] * 100:.1f} cm live", "ruling 7: no live order"),
            ("TIED", f"indoor {rng(OI['UKF live'])} m", "UKF ≈ FGO live"),
            ("N/A", "no loop-closure\nequivalent", "claim 23"),
            ("TIED", f"hold {rng(hU, 1)} mm", "bands PASS"),
            ("TIED", f"{passh['UKF']}/3 pass; B2 ≤ {max(B2h['UKF']):.2f} m", "UKF v2")],
    "FGO": [("TIED", f"median {med['FGO']:.2f} m", "claim 2: no ordering"),
            ("BEST", f"{rng(g6)} m", "lower on 6/6 (claim 7)"),
            ("FAILED", f"{rng(BLANK['FGO'][:, 3] / 1e3, 0)} km at end †", "claim 10"),
            ("TIED", f"1 tag: {mrD['FGO live'] * 100:.1f} cm live", "batch 1.1–2.8 cm, H-T1 PASS"),
            ("TIED", f"indoor {rng(OI['FGO live'])} m", "batch 0.59 = RTS-UKF"),
            ("PASSED", f"live {rng([t['rmse_m'] * 100 for t in LL[('lc', 'live')]], 1)} cm", "H-L1–P-L4 PASS 3/3"),
            ("TIED", f"hold {rng(hF, 1)} mm", "bands PASS"),
            ("TIED", f"{passh['FGO']}/3 pass; B2 ≤ {max(B2h['FGO']):.2f} m", "FGO v3, OLD priors")]}
fig = plt.figure(figsize=(15.5, 5.6)); ax = fig.add_axes([0.075, 0.13, 0.92, 0.70]); ax.axis("off")
ax.set_xlim(0, 8); ax.set_ylim(0, 3)
for j, cl in enumerate(COLS):
    ax.text(j + 0.5, 3.06, cl, ha="center", va="bottom", fontsize=10, weight="bold")
for i, est in enumerate(EST):
    y0 = 2 - i
    ax.text(-0.20, y0 + 0.5, est, ha="right", va="center", fontsize=13, weight="bold", color=C[est])
    ax.plot([-0.10], [y0 + 0.5], marker=MK[est], color=C[est], ms=9, clip_on=False, transform=ax.transData)
    for j, (cat, key, note) in enumerate(CELLS[est]):
        fc, word = CAT[cat]
        ax.add_patch(Rectangle((j + 0.03, y0 + 0.04), 0.94, 0.92, facecolor=fc, edgecolor=INK2 if cat == "BEST" else GRID,
                               lw=1.6 if cat == "BEST" else 0.8, hatch="////" if cat == "FAILED" else None))
        if cat == "FAILED":
            ax.add_patch(Rectangle((j + 0.10, y0 + 0.62), 0.80, 0.27, facecolor=SURF, edgecolor="none"))
            ax.add_patch(Rectangle((j + 0.10, y0 + 0.10), 0.80, 0.46, facecolor=SURF, edgecolor="none"))
        ax.text(j + 0.5, y0 + 0.76, word.upper(), ha="center", va="center", fontsize=11, weight="bold",
                color=INK if cat != "N/A" else INK2)
        ax.text(j + 0.5, y0 + 0.43, key, ha="center", va="center", fontsize=9.2, color=INK, linespacing=1.1)
        ax.text(j + 0.5, y0 + 0.17, note, ha="center", va="center", fontsize=7.8, color=INK2)
fig.text(0.075, 0.075, "BEST = a stated ordering puts it first · TIED = no ordering is claimed (or all pass the same criteria) · BEHIND = a stated "
         "ordering or verdict puts it below · FAILED = does not bound position · PASSED = met its pre-registered criteria, no comparison · "
         "N/A = not run.", fontsize=8.6, color=INK2)
fig.text(0.075, 0.035, "Key numbers: standard sensors = evo -a (cruise), median of dsn_tex r1–r9; heading = C0 bags; T = horizontal RMSE, 1 tag; "
         "O = indoor RMSE; L = with loop closure; H = mean hold error; closed loop = half speed. † runaway magnitude (order only).",
         fontsize=8.6, color=INK2)
save(fig, "F1", "F1_scorecard", "Which estimator wins where: mostly ties; the FGO wins only with the camera heading; none survives a blank floor",
     "Scorecard of the restated verdicts (numbers.md; headline_claims_before_after.md), one row per estimator and one column per "
     "experiment, each cell with its key number. The categories come ONLY from the restated verdicts: no ordering is claimed between the "
     "three estimators on standard sensors (claim 2, confirmatory test 'no ordering claimed'; the UKF medians are descriptive, claim 1b), in "
     "T (ruling 7), in H (all drift bands PASS; the comparative criteria H-H2/P-H3/H-H4 FAIL as adjudicated, the same on the re-flown sets, "
     "PENDING a ruling) or in the closed loop (every set passes); the FGO is lower than the UKF with the camera heading on all 6 textured "
     "bags (C0, claim 7); in O the live errors are not similar (H-O2 FAIL), EKF3 being the largest in every flight, while the FGO batch equals "
     "the RTS-UKF (P-O3 PASS); L is an FGO-only capability; on the blank floor no estimator bounds position (claim 10).",
     "eval/results/rerun_dsn_evo.json, dsn_extra_evo.json, dsn_paired_test.json, phase4_{fwdc,fwdplainc}_evo.json, blank_behaviour.json, "
     "expT/t_aggregate.json, expO/O_*.json, expL/T_A_r*_t245.json, expH/s1far_r*.json, expH/h_comparative_2026-10-11.json, "
     "closed_loop_cl_*_half(_v2/_v3).json",
     "§6.1, §6.2, §6.6, §15, §16.1–§16.3, §17.2; claims 1a, 1b, 2, 7, 10, 14, 17–19, 23, 25")

# =============================================================================================== FIG 2 heading stops drift
fig = plt.figure(figsize=(15.5, 8.6))
gs = fig.add_gridspec(3, 3, width_ratios=[1.25, 1.25, 1.0], hspace=0.42, wspace=0.18)
CT2 = {}; B3c = {}; YMAX = []
axe0 = None
for i, est in enumerate(EST):
    off, ons = HALF[est]
    ax0 = fig.add_subplot(gs[i, 0]); ax1 = fig.add_subplot(gs[i, 1], sharex=ax0, sharey=ax0)
    draw_corridor(ax0); draw_corridor(ax1)
    g = sim_path(off); c0, ct = cl_meta(off); w = g[:, 0] >= 20
    ax0.plot(g[w, 2], g[w, 1], color=C[est], lw=1.3)
    ax0.plot(ct["y"], ct["x"], marker="X", ms=8, color=INK, mec=SURF, mew=1, zorder=5)
    t = ct["t_rel_cruise_s"]; a, b = WIN[est]; CT2[est] = t
    ax0.annotate(f"wall contact, cruise +{t:.1f} s\n(window +{a}…+{b} s: {'inside' if a <= t <= b else 'after it'})",
                 (ct["y"], ct["x"]), xytext=(ct["y"] + 6 if ct["y"] < 100 else ct["y"] - 62, 3.5), fontsize=8.5,
                 arrowprops=dict(arrowstyle="-", color=INK2, lw=0.7))
    for k, tr in enumerate(ons):
        gg = sim_path(tr); ww = gg[:, 0] >= 20
        ax1.plot(gg[ww, 2], gg[ww, 1], color=C[est], lw=1.0, alpha=1 if k == 0 else 0.75)
    ax1.text(80, 5.3, f"3 flights; max |cross-track| in cruise {max(B2h[est]):.2f} m", ha="center", fontsize=8.5)
    ax0.set_title(f"{est} flying: no camera heading (1 flight)", loc="left", fontsize=10)
    ax1.set_title(f"{est} flying: with camera heading (3 flights)", loc="left", fontsize=10)
    ax0.set_ylabel("true East x (m)"); plt.setp(ax1.get_yticklabels(), visible=False)
    if i == 2:
        ax0.set_xlabel("distance along the corridor, true North y (m)"); ax1.set_xlabel("distance along the corridor, true North y (m)")
    # heading error, ONE shared y-scale over all three estimators
    ax2 = fig.add_subplot(gs[i, 2], sharey=axe0) if axe0 is not None else fig.add_subplot(gs[i, 2])
    axe0 = axe0 or ax2
    te, ee = log_yaw(off, est); keep = te <= t - 3.0
    ax2.plot(te[keep], ee[keep], color=C[est], lw=1.3, label="no heading (until contact)")
    YMAX.append(np.abs(ee[keep]).max())
    for k, tr in enumerate(ons):
        tt, e2 = log_yaw(tr, est)
        js = L(f"closed_loop_{tr}.json"); c0b, c1b = js["cruise_s"]; wk = tt <= (c1b - c0b)
        ax2.plot(tt[wk], e2[wk], color=C[est], lw=0.8, ls="-", alpha=0.55, label="with heading (3 flights)" if k == 0 else None)
        B3c.setdefault(est, []).append((js["B"]["B3"], float(np.abs(e2[wk]).max())))
    for yb in (2, -2):
        ax2.axhline(yb, color=TRUTH, lw=0.7, ls=":")
    ax2.set_title(f"{HBUILD[est]}: heading error, estimate − truth", loc="left", fontsize=10)
    ax2.set_ylabel("heading error (°)"); ax2.set_xlim(0, 310)
    if i == 2: ax2.set_xlabel("time since cruise start (s)")
    ax2.legend(loc="lower left", frameon=False, fontsize=8)
lim = math.ceil(max(YMAX) + 1)
axe0.set_ylim(-lim, lim); axe0.set_xlim(0, 310)
axe0.text(305, 2.3, "±2° (B3 max band)", ha="right", fontsize=7.5, color=INK2)
check("no-heading wall contact EKF3 / UKF v2 / FGO v3 (s)", " / ".join(f"+{CT2[e]:.1f}" for e in EST), "+242.1 / +165.9 / +169.9", "numbers.md §15 contact rows")
check("UKF v2 B2 r1/r2/r3 (m)", " / ".join(f"{x:.3f}" for x in B2h["UKF"]), "0.231 / 0.253 / 0.219", "numbers.md §15 re-flown row")
check("FGO v3 B2 r1/r2/r3 (m)", " / ".join(f"{x:.3f}" for x in B2h["FGO"]), "0.118 / 0.033 / 0.392", "numbers.md §15 re-flown row")
check("EKF3 half B2 range (m)", rng(B2h["EKF3"]), "0.24–0.33", "numbers.md §15 B2 row")
fmtb3 = lambda e: "; ".join(f"{b['p95_deg']:.3f} / {b['max_deg']:.3f} / {b['mean_deg']:.3f}" for b, _ in B3c[e])
check("UKF v2 B3 p95/max/mean per flight (deg)", fmtb3("UKF"), "0.382 / 0.512 / 0.242; 0.361 / 0.407 / 0.253; 0.344 / 0.406 / 0.250", "numbers.md §15 re-flown B3 row")
check("FGO v3 B3 p95/max/mean per flight (deg)", fmtb3("FGO"), "0.293 / 0.340 / 0.212; 0.336 / 0.427 / 0.220; 0.361 / 0.682 / 0.187", "numbers.md §15 re-flown B3 row")
check("EKF3 half B3 p95 / max range (deg)", f"{rng([b['p95_deg'] for b, _ in B3c['EKF3']])}/{rng([b['max_deg'] for b, _ in B3c['EKF3']])}", "0.28–0.32/0.33–0.39", "numbers.md §15 B3 row")
dB3 = max(abs(b["max_deg"] - m) for e in EST for b, m in B3c[e])
check("plotted heading-error curve max vs scored B3 max, all 9 flights, |Δ| <= 0.10°", "ok" if dB3 <= 0.10 else f"{dB3:.3f}", "ok", "curve source vs scorer")
save(fig, "F2", "F2_heading_stops_sideways_drift",
     "The camera heading stops the sideways drift: without it every estimator flies into the wall",
     "Half-speed textured corridor (corridor_textured_half_fwdc), each estimator flying the vehicle (closed loop); true paths from the "
     "simulator (dataflash SIM), top-down; walls at x = ±10 m, dotted = the 9.58 m contact threshold. Left: without a heading source the "
     "flying estimator's yaw drifts and every vehicle reaches the west wall (X; EKF3 +242.1 s, after its pre-registered window, D21; UKF v2 "
     "+165.9 s; FGO v3 +169.9 s). Middle: with the camera heading all 9 flights stay within 0.39 m of the centreline and pass B1–B5. Right: "
     "the flying estimator's heading error on ONE shared scale; with the heading it stays inside ±0.7° (B3 p95 ≤ 0.38°). Builds: the "
     "jitter-corrected UKF port (v2) and the final FGO (v3), which flew the OLD FGO priors (initial yaw σ 1e-3 rad); earlier builds are in "
     "the appendix table. n = 1 per no-heading flight; closed-loop run-to-run variability is unmeasured; no cross-speed comparison.",
     "paths: dataflash SIM of cl_a_tex_half, cl_bcpp_tex_r1–r3_half, cl_ukf_a_tex_half_v2, cl_ukf_b_tex_r1–r3_half_v2, cl_fgo_a_tex_half_v3, "
     "cl_fgo_b_tex_r1–r3_half_v3; heading error: dataflash XKF1 / XUKO / XFGO against SIM; contact, B2, B3: eval/results/closed_loop_<trial>.json",
     "§15 (contact rows, B2 row, re-flown B1/B2/B4 and B3 rows); claim 14")

# =============================================================================================== FIG 3 accuracy without / with heading
fig, (ax, bx) = plt.subplots(1, 2, figsize=(15.5, 6.0), gridspec_kw={"width_ratios": [1.15, 1]})
xs = {e: i for i, e in enumerate(EST)}; jit = np.array([-0.06, 0, 0.06])
for e in EST:
    x0 = xs[e] - 0.18; v = [p[1] for p in DSN[e]]
    ax.scatter(x0 + np.linspace(-0.08, 0.08, len(v)), v, s=26, marker=MK[e], color=C[e], edgecolor=SURF, lw=0.5, zorder=3)
    ax.plot([x0 - 0.12, x0 + 0.12], [med[e]] * 2, color=INK, lw=1.4, zorder=4)
    x1 = xs[e] + 0.18; key = {"EKF3": "EKF3", "UKF": "UKF_baseline", "FGO": "FGO_baseline"}[e]
    vc = [P4[b][key] for b in CAMB]
    ax.scatter(x1 + np.linspace(-0.09, 0.09, 6), vc, s=26, marker=MK[e], color=C[e], edgecolor=SURF, lw=0.5, zorder=3)
    ax.text(x0 + 0.13, med[e], f"{med[e]:.2f}", va="center", fontsize=8.5)
ax.set_xticks([x + d for x in range(3) for d in (-0.18, 0.18)]); ax.set_xticklabels(["dsn_tex\nr1–r9", "camera\nbags"] * 3, fontsize=8)
for e in EST: ax.text(xs[e], -0.12, e, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=11, weight="bold", color=C[e])
ax.set_xlim(-0.55, 2.55); ax.set_ylim(0, 14); ax.set_ylabel("position error, evo -a (cruise) (m)")
ax.set_title("No heading (standard sensors): no ordering claimed", loc="left", fontsize=10.5)
ax.text(-0.5, 13.8, f"Confirmatory EKF3 − FGO test (r4–r10): {pt['verdict']}\nmean d {pt['mean_d_m']:+.3f} m, 95% CI "
        f"[{pt['t95_ci_m'][0]:+.3f}, {pt['t95_ci_m'][1]:+.3f}] m", fontsize=8.8, va="top")
ax.legend(handles=[Line2D([], [], color=INK, lw=1.4, label="median, dsn_tex r1–r9")] +
          [Line2D([], [], ls="", marker=MK[e], color=C[e], label=e) for e in EST], loc="upper right", frameon=False, fontsize=8.5)
for e in EST:
    if e == "EKF3":
        bx.text(xs[e], 12, "EKF3 has no\noffline heading arm\n(it flies with one: F2)", ha="center", va="center", fontsize=9, color=INK2)
        continue
    key = f"{e}_heading"
    for k, ds in enumerate(("fwdc", "fwdplainc")):
        xk = xs[e] + (-0.18 if ds == "fwdc" else 0.18)
        vals = [P4[(ds, r)][key] * 100 for r in (1, 2, 3)]
        bx.scatter(xk + jit, vals, s=30, marker=MK[e], color=C[e], edgecolor=SURF, lw=0.5, zorder=3)
        for xv, yv in zip(xk + jit, vals):
            pass
        bx.text(xk + 0.11, max(vals), f"{min(vals):.0f}–{max(vals):.0f}" if f"{min(vals):.0f}" != f"{max(vals):.0f}" else f"{min(vals):.0f}",
                fontsize=8.5, va="center")
    bx.axvspan(xs[e] + 0.02, xs[e] + 0.36, color="#f2f2f2", zorder=0)
bx.set_xticks([x + d for x in (1, 2) for d in (-0.18, 0.18)]); bx.set_xticklabels(["line\nwalls", "plain\nwalls*"] * 2, fontsize=8)
for e in EST: bx.text(xs[e], -0.12, e, transform=bx.get_xaxis_transform(), ha="center", va="top", fontsize=11, weight="bold", color=C[e])
bx.set_xlim(-0.55, 2.55); bx.set_ylim(0, 30); bx.set_ylabel("position error, evo -a (cruise) (cm)")
bx.set_title("With the camera heading (same 6 textured bags): FGO lower on 6/6", loc="left", fontsize=10.5)
bx.text(2.52, 28.8, "* shaded: plain walls over the checkerboard floor, where the heading\n  FAILED Phase 3 validation: no heading benefit is claimed there",
        ha="right", va="top", fontsize=8, color=INK2)
legend_est(bx, ("UKF", "FGO"), loc="upper left", fontsize=8.5)
dec = L("phase5_analysis.json")["decomposition"]
hd = {a: [abs(dec[f"fwdc_tex_r{r}"][a]["xtrack_head_m"]) for r in (1, 2, 3)] for a in ("EKF3", "UKF_baseline", "FGO_baseline", "UKF_heading", "FGO_heading")}
nh = [x for a in ("EKF3", "UKF_baseline", "FGO_baseline") for x in hd[a]]
check("dsn_tex mean r1–r3 EKF3 / UKF / FGO (m)", " / ".join(f2(np.mean([v for i, v in DSN[e] if i <= 3])) for e in EST), "4.00 / 3.59 / 3.44", "numbers.md §6.1; claim 1a")
check("dsn_tex UKF r1–r9 range (m)", rng([v for _, v in DSN["UKF"]]), "1.17–5.85", "numbers.md §6.1 D15 wording row")
check("confirmatory mean d, CI (m)", f"{pt['mean_d_m']:.3f} [{pt['t95_ci_m'][0]:.3f}, {pt['t95_ci_m'][1]:.3f}]", "-0.021 [-0.989, 0.947]", "numbers.md §6.1")
check("no heading EKF3 fwdc / fwdplainc r1–r3 (m)", " / ".join(f2(P4[b]["EKF3"]) for b in CAMB), "4.09 / 3.60 / 4.08 / 4.08 / 4.06 / 4.08", "numbers.md §6.4")
check("no heading FGO fwdc / fwdplainc r1–r3 (m)", " / ".join(f2(P4[b]["FGO_baseline"]) for b in CAMB), "4.47 / 2.26 / 4.54 / 4.54 / 4.52 / 4.74", "numbers.md §6.4")
check("no heading UKF fwdc / fwdplainc r1–r3 (m)", " / ".join(f2(P4[b]["UKF_baseline"]) for b in CAMB), "4.96 / 1.78 / 4.96 / 5.02 / 11.19 / 10.82", "numbers.md §6.4")
check("with heading UKF fwdc / fwdplainc r1–r3 (m)", " / ".join(f2(P4[b]["UKF_heading"]) for b in CAMB), "0.13 / 0.13 / 0.14 / 0.19 / 0.15 / 0.25", "numbers.md §6.6")
check("with heading FGO fwdc / fwdplainc r1–r3 (m)", " / ".join(f2(P4[b]["FGO_heading"]) for b in CAMB), "0.06 / 0.06 / 0.06 / 0.15 / 0.09 / 0.22", "numbers.md §6.6")
mism = 0
for ds, r in CAMB:
    a = L(f"phase4_{ds}_arms.json")[f"{ds}_tex_r{r}"]
    for arm in ("UKF_heading", "FGO_heading"):
        try:
            mism += abs(a[arm]["evo"]["ate_a_cruise"]["+0.00"] - P4[(ds, r)][arm]) > 1e-6
        except (KeyError, TypeError):
            pass
check("phase4 evo vs arms json agreement (mismatches)", mism, 0, "phase4_*_evo.json vs phase4_*_arms.json")
save(fig, "F3", "F3_accuracy_without_and_with_heading",
     "Without a heading source all three drift by metres; with the camera heading the UKF and FGO stay within 25 cm",
     "Left (m): position error, evo -a (cruise), without any heading source: the standard-sensor flights dsn_tex r1–r9 (bar = median) and the "
     "6 forward-camera textured bags (fwdc / fwdplainc r1–r3) with their heading unused. No ordering is claimed: the pre-registered "
     "EKF3 − FGO test on r4–r10 gives 'no ordering claimed' (the former 'EKF3 beats the FGO' is WITHDRAWN); the UKF medians are descriptive "
     "(n = 9). Right (cm): the UKF and FGO with the camera heading on the same 6 bags: line-textured walls UKF 13–14, FGO 6 cm; plain walls "
     "UKF 15–25, FGO 9–22 cm (C0: FGO lower on 6/6, margin 3–6 cm on plain walls). On the plain-wall bags (checkerboard floor) the heading "
     f"failed Phase 3 validation, so no heading benefit is claimed there (conditional on the initial yaw σ). Phase 5 decomposition (fwdc_tex): "
     f"without heading the estimator's own heading error drives {min(nh):.0f}–{max(nh):.0f} m of end-of-cruise cross-track; with the "
     f"heading ≤ {max(hd['UKF_heading'] + hd['FGO_heading']) * 100:.0f} cm (checked against its JSON only; numbers.md has no row). evo -a "
     "aligns away a constant yaw offset, so it is metres, not tens of metres.",
     "eval/results/rerun_dsn_evo.json, dsn_extra_evo.json (ate_a_cruise '+0.00'); dsn_paired_test.json; phase4_{fwdc,fwdplainc}_evo.json, "
     "cross-checked against phase4_*_arms.json; phase5_analysis.json (decomposition)",
     "§6.1, §6.4, §6.6; claims 1a, 1b, 2, 5, 7", uncheck="Phase 5 decomposition magnitudes (caption only): JSON only, no numbers.md row (§6.3 'NOT RESTATED')")

# =============================================================================================== FIG 4 blank floor
fig, ax = plt.subplots(figsize=(12.5, 5.8)); tx = [10, 30, 60]
for est in ("UKF", "FGO"):
    cu = BLANK[est][:, :3]
    for row in cu:
        ax.plot(tx, row, color=C[est], lw=0.7, alpha=0.45)
    mdn = np.median(cu, axis=0)
    ax.plot(tx, mdn, color=C[est], lw=2.0, marker=MK[est], ms=6, label=f"{est} (thin: each of {len(cu)} flights; thick: median)")
    ax.annotate(f"{est} at +60 s: {rng(cu[:, 2], 0)} m\n→ end of cruise {rng(BLANK[est][:, 3] / 1e3, 0)} km (†, far off this axis)",
                (60, mdn[2]), xytext=(63, mdn[2] + (8 if est == "FGO" else -22)), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=C[est], lw=0.9))
ax.set_xlim(0, 90); ax.set_ylim(0, 220); ax.set_xticks([0, 10, 30, 60])
ax.set_xlabel("time since flow loss (s); cut at +60 s"); ax.set_ylabel("position error magnitude (m)")
ax.text(2, 165, "EKF3: no curve. Its position is flagged INVALID from take-off on every blank flight (0 valid airborne\n"
        "flow frames in cruise, so flow aiding never starts); it outputs the origin, which is not scored.",
        fontsize=9.2, va="top", bbox=dict(boxstyle="round,pad=0.4", fc=SURF, ec=C["EKF3"], lw=1.0))
ax.legend(loc="center left", bbox_to_anchor=(0.0, 0.50), frameon=False)
check("UKF +10/+30/+60 s ranges (m)", f"{rng(BLANK['UKF'][:, 0], 1)} / {rng(BLANK['UKF'][:, 1], 1)} / {rng(BLANK['UKF'][:, 2], 0)}", "6.4–8.2 / 27.3–36.5 / 60–108", "numbers.md §6.2")
check("FGO +10/+30/+60 s ranges (m)", f"{rng(BLANK['FGO'][:, 0], 1)} / {rng(BLANK['FGO'][:, 1], 1)} / {rng(BLANK['FGO'][:, 2], 0)}", "6.4–8.2 / 28.0–37.0 / 154–204", "numbers.md §6.2")
check("n flights UKF / FGO", f"{len(BLANK['UKF'])}/{len(BLANK['FGO'])}", "11/11", "numbers.md §6.2")
check("end of cruise UKF / FGO (km) †", f"{rng(BLANK['UKF'][:, 3] / 1e3, 0)} / {rng(BLANK['FGO'][:, 3] / 1e3, 0)}", "29–40 / 22–41", "numbers.md §6.2")
check("EKF3 invalid, s of cruise, all 14 blank", rng(EK_INV, 0), "301–310", "numbers.md §6.2")
nvalid = [v["valid_frames_in_cruise"] for k, v in bb.items() if "blank" in k]
check("valid airborne flow frames in cruise, all blank bags", f"max {max(nvalid)} over {len(nvalid)}", "max 0 over 14", "numbers.md §6.2 ('0', all 14 blank bags)")
save(fig, "F4", "F4_blank_floor_flow_loss",
     "On a blank floor nothing bounds position: the UKF and FGO dead-reckon away; EKF3 declares itself invalid",
     "Position error after the loss of flow aiding on the blank floor (UKF and FGO baselines; 11 flights: dsn, p1c, fwdc and fwdplainc blank), "
     "linear axis cut at +60 s: UKF 6.4–8.2 / 27.3–36.5 / 60–108 m and FGO 6.4–8.2 / 28.0–37.0 / 154–204 m at +10 / +30 / +60 s. Beyond +60 s "
     "both run away to km scale (end of cruise UKF 29–40 km, FGO 22–41 km, †: evidence of divergence with its order of magnitude, not "
     "bit-reproducible values), shown by the arrows rather than a log axis. EKF3 has no curve because its position is flagged invalid for "
     "the whole cruise (301–310 s) on every blank flight and its held-origin output is not scored (evaluation rule). Behaviour under total "
     "loss, not accuracy. With the camera heading the yaw is held but position still is not (+60 s UKF 40–89, FGO 135–190 m †; claim 10).",
     "eval/results/blank_behaviour.json (along_m, cross_m at +10/+30/+60 s and end; EKF3_invalid_period; valid_frames_in_cruise)",
     "§6.2; claim 10", logscale="km-scale end-of-cruise runaway next to tens of metres: axis CUT at +60 s, the end values given as annotated arrows (†)")

# =============================================================================================== FIG 5 T
fig, ax = plt.subplots(figsize=(12.5, 6.0)); xc = np.arange(4); offs = dict(zip(TRK, np.linspace(-0.16, 0.16, 5)))
TT = {}
for n in TRK:
    est, kind = TSTY[n]
    per = np.array([[1e2 * L(f"expT/T_{c}_r{r}.json")["tracks"][n]["horiz_err_m"]["rmse"] for r in (1, 2, 3)] for c in TCOND])
    mn = np.array([1e2 * agg["conditions"][c]["mean_rmse_m"][n] for c in TCOND]); TT[n] = mn
    x = xc + offs[n]
    ax.plot(x, mn, color=C[est], ls="-" if kind == "live" else "--", lw=1.4, marker=MK[est], ms=6,
            mfc=C[est] if kind == "live" else SURF, mec=C[est], mew=1.2, label=TSHORT[n] + " (mean of 3)", zorder=3)
    for j in range(4):
        ax.scatter([x[j]] * 3, per[j], s=10, marker=MK[est], color=C[est] if kind == "live" else SURF, edgecolor=C[est], lw=0.6, zorder=2, alpha=0.8)
gm = [agg["conditions"][c]["gap_length_median_s"] for c in TCOND]
ax.set_xticks(xc); ax.set_xticklabels([f"{TLAB[c]}\n(median gap {g:.1f} s)" for c, g in zip(TCOND, gm)])
ax.set_xlabel("tags available (condition A → D)"); ax.set_ylabel("horizontal RMSE over the 5 laps (cm)")
ax.set_ylim(0, 15.5); ax.set_xlim(-0.45, 3.45)
ax.legend(loc="upper left", frameon=False, ncol=2)
h1 = agg["H-T1 (FGO live -> whole-flight batch)"]; p2 = agg["P-T2 (UKF live -> RTS)"]
fig.text(0.98, -0.03, f"hindsight gain (median per gap): FGO batch vs FGO live {', '.join(f'{100 * h1['median_gain_m'][c]:.1f}' for c in TCOND)} cm "
        f"(H-T1 {'PASS' if h1['PASS'] else 'FAIL'}, grows with the gap)\nRTS-UKF vs UKF live {', '.join(f'{100 * p2['median_gain_m'][c]:+.1f}' for c in TCOND)} cm "
        f"(P-T2 {'PASS' if p2['PASS'] else 'FAIL'}, not increasing)", ha="right", va="top", fontsize=9, color=INK2)
exp10 = {"A": "0.039 0.037 0.020 0.014 0.011", "B": "0.055 0.061 0.026 0.031 0.015", "C": "0.074 0.076 0.053 0.039 0.019", "D": "0.096 0.131 0.083 0.109 0.028"}
for c in TCOND:
    mr = agg["conditions"][c]["mean_rmse_m"]
    check(f"T {TLAB[c]}: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m)", " ".join(f"{mr[k]:.3f}" for k in TRK), exp10[c], "numbers.md §16.1 table")
check("T median gaps A–D (s)", " / ".join(f"{g:.1f}" for g in gm), "4.3 / 10.1 / 22.0 / 46.3", "numbers.md §16.1 table header")
check("tags per lap in B", str(L("expT/T_B_r1.json")["gates"]["laps_ids"][0]), "[0, 1, 2, 3]", "T_B_r1.json gates (4 corner tags)", exact=True)
check("H-T1 median gain A–D (m), rho, PASS", " / ".join(f"{h1['median_gain_m'][c]:.3f}" for c in TCOND) + f" {h1['spearman_rho']:+.2f} {h1['PASS']}",
      "0.010 / 0.011 / 0.023 / 0.052 +0.30 True", "numbers.md §16.1")
check("P-T2 gain A–D (m), PASS", " / ".join(f"{p2['median_gain_m'][c]:+.3f}" for c in TCOND) + f" {p2['PASS']}", "+0.020 / +0.032 / +0.037 / +0.029 False", "numbers.md §16.1")
save(fig, "F5", "F5_T_tags_known_positions",
     "Fewer tags, larger live errors (no live ordering claimed); the FGO's hindsight batch stays at 1–3 cm",
     "Experiment T (room_tags, 5 laps of a 6 m square, open loop on simulator truth): horizontal RMSE in the world frame, no alignment, "
     "against the tags sent (A all 8, B the 4 corners, C 2 diagonal, D 1 tag; median gap between fixes 4.3 / 10.1 / 22.0 / 46.3 s). Solid, "
     "filled = live; dashed, open = hindsight (the FGO whole-flight batch and the RTS-smoothed UKF); small marks = each of 3 flights, line = "
     "their mean. Live errors grow from 2–4 cm to 8–13 cm as tags thin out; no live ordering is claimed (in D the FGO live 8.3 cm against "
     "EKF3 9.6 cm is descriptive, n = 3; ruling 7). P-T3 FAILS (live max/min 1.97 / 2.36 / 1.42 / 1.58). The FGO batch stays at 1.1–2.8 cm; "
     "its hindsight gain grows with the gap (H-T1 PASS), the RTS-UKF's does not (P-T2 FAIL), and the batch-to-RTS ratio is 1.31–3.89 (P-T4 "
     "FAIL). Same tag fixes for every estimator.",
     "eval/results/expT/T_{A,B,C,D}_r{1,2,3}.json (tracks.*.horiz_err_m.rmse), expT/t_aggregate.json",
     "§16.1 table and bullets (H-T1, P-T2, P-T3, P-T4, condition D); claims 17, 18")

# =============================================================================================== FIG 6 O
ts = get_typestore(Stores.ROS2_JAZZY)
tr = "O_r1"; D = f"{TD}/{tr}"
o = L(f"expO/{tr}.json"); mk = o["markers_bag_s"]; toff, ton = mk["GNSS OFF"], mk["GNSS ON"]
G = np.loadtxt(f"{D}/room_ukf/ground_truth.tum")
TR = []
with Reader(f"{D}/bag") as rd:
    cs = [c for c in rd.connections if c.topic == "/imu/time_ref"]
    for con, _, raw in rd.messages(connections=cs):
        m = ts.deserialize_cdr(raw, con.msgtype)
        TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9))
    tag_topics = [c.topic for c in rd.connections if "tag" in c.topic]
TR = np.array(TR); sitl, dd = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(dd[w]); env.append((sitl[w][i], dd[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
oE, oN = np.load(f"{D}/gnss.npz")["ekf3_origin_EN"]
mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); k1 = []
while True:
    r = mv.recv_match(type=["XKF1"])
    if r is None: break
    if r.C == 0:
        t = r.TimeUS / 1e6; k1.append((t + kk * t + c0, r.PE + oE, r.PN + oN))
tracks = {"EKF3 live": np.array(k1)}
for n, p in (("UKF live", "room_ukf/ukf_live.tum"), ("RTS-UKF (hindsight)", "room_ukf/ukf_rts.tum"), ("FGO live", "room_fgo/fgo_live.tum"),
             ("FGO hindsight (whole-flight batch)", "room_fgo/fgo_batch.tum")):
    tracks[n] = np.loadtxt(f"{D}/{p}")[:, :3]
fig, axs = plt.subplots(1, 2, figsize=(15.5, 6.0), sharey=True, gridspec_kw={"width_ratios": [2.3, 1]})
ax = axs[0]; ax.axvspan(0, ton - toff, color="#f2f2f2", zorder=0)
t_far = mk["OUTBACK BACK START"] - 3.0 - toff; t_back = mk["OUTBACK BACK START"] - toff
ax.axvline(t_far, color=TRUTH, lw=0.8, ls=":"); ax.axvline(t_back, color=TRUTH, lw=0.8, ls=":")
ax.text((t_far + t_back) / 2, 4.55, f"far end (y = 50 m, 30 m inside): stop {t_far:.0f} s,\n3 s hold, then reverse (no yaw turn) at {t_back:.0f} s",
        ha="center", va="top", fontsize=8.3, color=INK2)
ax.text(110, 4.55, f"indoors, GNSS off\n({ton - toff:.0f} s)", ha="center", va="top", fontsize=8.5, color=INK2)
rm_ind = {}
for n, Tk in tracks.items():
    est, kind = TSTY[n]; w = (Tk[:, 0] > toff - 40) & (Tk[:, 0] < ton + 30)
    e = np.hypot(Tk[w, 1] - np.interp(Tk[w, 0], G[:, 0], G[:, 1]), Tk[w, 2] - np.interp(Tk[w, 0], G[:, 0], G[:, 2]))
    ax.plot(Tk[w, 0] - toff, e, color=C[est], ls="-" if kind == "live" else "--", lw=1.1, label=TSHORT[n])
    wi = (Tk[:, 0] >= toff) & (Tk[:, 0] <= ton)
    ei = np.hypot(Tk[wi, 1] - np.interp(Tk[wi, 0], G[:, 0], G[:, 1]), Tk[wi, 2] - np.interp(Tk[wi, 0], G[:, 0], G[:, 2]))
    rm_ind[n] = float(np.sqrt(np.mean(ei ** 2)))
ax.set_xlabel("time from GNSS OFF at the entrance (s)"); ax.set_ylabel("horizontal error (m)"); ax.set_xlim(-40, ton - toff + 30); ax.set_ylim(0, 4.7)
ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.86), fontsize=8.5, frameon=False)
jump = o["tracks"]["EKF3 live"]["max_step_after_return_m"]
ax.annotate(f"EKF3 reset jump at\nGNSS return: {jump:.2f} m", (ton - toff + 1, 3.4), xytext=(ton - toff + 6, 2.3), fontsize=8.5,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.7))
ax.set_title("O_r1: error against time (world frame, no alignment)", loc="left", fontsize=10)
bx = axs[1]
for i, n in enumerate(TRK):
    est, kind = TSTY[n]
    bx.scatter([i] * 3, OI[n], s=32, marker=MK[est], color=C[est] if kind == "live" else SURF, edgecolor=C[est], lw=1.2, zorder=3)
    bx.text(i, max(OI[n]) + 0.12, rng(OI[n]), fontsize=7.8, ha="center")
bx.set_xticks(range(5)); bx.set_xticklabels([TSHORT[n].replace(" (", "\n(") for n in TRK], fontsize=8)
bx.set_xlim(-0.5, 4.9); bx.set_title("indoor RMSE, 3 flights (filled live, open hindsight)", loc="left", fontsize=10)
exO = {"EKF3 live": "1.42–1.43", "UKF live": "0.77–0.84", "FGO live": "0.83–0.89", "RTS-UKF (hindsight)": "0.58–0.60", "FGO hindsight (whole-flight batch)": "0.59–0.59"}
for n in TRK:
    check(f"O indoor RMSE {TSHORT[n]} (m)", rng(OI[n]), exO[n], "numbers.md §16.2 table")
jumps = [L(f"expO/{t}.json")["tracks"]["EKF3 live"]["max_step_after_return_m"] for t in OFL]
check("O EKF3 reset jump (m)", rng(jumps), "4.10–4.10", "numbers.md §16.2 ('4.10 m, every flight')")
check("O indoor duration (s)", f"{ton - toff:.0f}", "123", "numbers.md §16.2 heading ('123 s, GNSS off')")
dO = max(abs(rm_ind[n] - o["tracks"][n]["indoor_rmse_m"]) for n in TRK)
check("O_r1 curve indoor RMSE recomputed vs json, max |Δ| <= 0.05 m", "ok" if dO <= 0.05 else f"{dO:.3f}", "ok", "curve source vs scorer")
check("O_r1 bag has no tag topics", len(tag_topics), 0, "O design: no tags in outdoor_indoor.sdf")
save(fig, "F6", "F6_O_outdoor_indoor",
     "Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return; hindsight cuts the error to 0.6 m",
     "Experiment O (outdoor → indoor → outdoor, open loop on simulator truth). Indoor sensor set, the same for all three estimators: IMU "
     "(accelerometer and gyro), downward optical flow and the downward LiDAR rangefinder only; no GNSS (switched off at the entrance), no "
     "compass, no forward-camera heading (descoped) and no tags (none in the world). Route: 15 m GNSS yaw-alignment run outdoors, then 0.5 m/s "
     "north through the entrance (GNSS OFF) to the far end 30 m inside (reached ~60 s after OFF), a 3 s hold, and back in reverse at the same "
     "heading (no yaw turn), re-crossing the entrance at GNSS ON (123 s indoors). Left: O_r1 horizontal error, world frame; EKF3 resets to "
     "GNSS on return with a 4.10 m jump (every flight). Right: indoor RMSE, 3 flights. H-O1 PASS 3/3 (FGO batch below both filters' live "
     "tracks); H-O2 FAIL (live max/min 1.72–1.84, EKF3 largest); P-O3 PASS (FGO batch 0.59 m = RTS-UKF 0.58–0.60 m within 1–5%). The former "
     "'FGO batch ~2× better than the RTS-UKF' is WITHDRAWN (a noise-model artefact). Same GNSS samples for every estimator.",
     "eval/results/expO/O_*.json; curves: O_r1 room_ukf/, room_fgo/ TUMs, dataflash XKF1 about EKF3's origin (gnss.npz), bag /imu/time_ref "
     "(clock map); route from markers_bag_s; design: METHODOLOGY 'Experiment O: pre-registration', sim/worlds/outdoor_indoor.sdf, "
     "fly_trial.py outback(), o_gnss.parm", "§16.2 table and bullets; claims 19–22")

# =============================================================================================== FIG 7 L
fig, axs = plt.subplots(1, 2, figsize=(14.5, 5.6), sharey=True)
for ax, mode, lab in ((axs[0], "lc", "with loop closure (tags re-identified)"), (axs[1], "nolc", "without loop closure")):
    for kind in ("live", "hindsight"):
        for r, tk in enumerate(LL[(mode, kind)]):
            v = np.array(tk["per_lap_rmse_m"]) * 100
            ax.plot(range(1, 6), v, color=C["FGO"], ls="-" if kind == "live" else "--", marker=MK["FGO"], ms=5,
                    mfc=C["FGO"] if kind == "live" else SURF, mec=C["FGO"], lw=1.1,
                    label=f"{'live (fixed-lag)' if kind == 'live' else 'hindsight (full iSAM2 estimate)'}" if r == 0 else None)
    ax.set_title(f"keyframe FGO, {lab}: T_A_r1–r3", loc="left", fontsize=10)
    ax.set_xticks(range(1, 6)); ax.set_xlabel("lap of the 6 m square")
    ax.legend(loc="upper left", frameon=False)
axs[0].set_ylabel("horizontal RMSE per lap (cm)"); axs[0].set_ylim(0, None)
lc5 = [t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL[("lc", "live")]]
nl5 = [t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL[("nolc", "live")]]
axs[0].text(5, axs[0].get_ylim()[1] * 0.55, f"live lap 5 ÷ lap 1: {rng(lc5)}\n(error falls after lap 1)", ha="right", fontsize=9)
axs[1].text(5, axs[0].get_ylim()[1] * 0.08, f"live lap 5 ÷ lap 1: {rng(nl5, 1)}\n(error grows over the laps)", ha="right", fontsize=9)
check("L lc live overall (m)", rng([t["rmse_m"] for t in LL[("lc", "live")]], 3), "0.049–0.076", "numbers.md §16.3")
check("L lc hindsight overall (m)", rng([t["rmse_m"] for t in LL[("lc", "hindsight")]], 3), "0.017–0.027", "numbers.md §16.3")
check("L nolc live overall (m)", rng([t["rmse_m"] for t in LL[("nolc", "live")]], 3), "0.262–0.361", "numbers.md §16.3")
check("L nolc hindsight overall (m)", rng([t["rmse_m"] for t in LL[("nolc", "hindsight")]], 3), "0.221–0.266", "numbers.md §16.3")
check("L lap5/lap1 lc live; nolc live", rng(lc5) + "; " + rng(nl5, 1), "0.16–0.43; 2.9–4.5", "numbers.md §16.3")
save(fig, "F7", "F7_L_loop_closure",
     "Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 3–4× over five laps",
     "Experiment L: the keyframe FGO with AprilTags at UNKNOWN positions (each tag a landmark), T_A_r1–r3, horizontal RMSE per 6 m lap in "
     "the first tag's frame, one shared linear axis. Left: with loop closure the live error falls after lap 1 (lap 5 ÷ lap 1 0.16–0.43; "
     "overall 4.9–7.6 cm live, 1.7–2.7 cm hindsight). Right: without re-identification it grows 2.9–4.5× over five laps (overall 26.2–36.1 cm "
     "live). H-L1, H-L2, H-L3 and P-L4 PASS 3/3. This is an FGO capability, not an FGO-against-filter result (the filters have no "
     "loop-closure equivalent); one estimator, so one colour, with live solid/filled and hindsight dashed/open. V-L is not re-scorable on the "
     "corrected FGO (ruling 6).",
     "eval/results/expL/T_A_r*_t245.json (per_lap_rmse_m, rmse_m)", "§16.3 table and bullets; claims 23, 24")

# =============================================================================================== FIG 8 H
LOSS = ["5 s hover", "15 s hover", "30 s hover", "~7 s during a move"]
FLY = {"EKF3": (S1 + S1F, "EKF3", "EKF3 (S1 + S1 far, 6 flights)"), "UKF": (S2V, "UKF_port", "UKF v2 port (S2v2, 3 flights)"),
       "FGO": (S3V, "FGO_flying", "FGO v3 node (S3v2, 3 flights; OLD priors)")}
BAND = {"EKF3": [50, 100, 200, 150], "FGO": [50, 100, 200, 150], "UKF": [100, 200, 400, 300]}
YL = 60
fig, ax = plt.subplots(figsize=(13.5, 6.0)); DR = {}
for li in range(4):
    for k, est in enumerate(EST):
        trs, key, lab = FLY[est]; d = drifts(trs, key)[li]; DR[(est, li)] = d
        x = li + (k - 1) * 0.24
        ax.scatter(x + np.linspace(-0.05, 0.05, len(d)), d, s=26, marker=MK[est], color=C[est], edgecolor=SURF, lw=0.5, zorder=3,
                   label=lab if li == 0 else None)
        bnd = BAND[est][li]
        if bnd <= YL:
            ax.plot([x - 0.1, x + 0.1], [bnd, bnd], color=C[est], lw=1.6, zorder=2)
            ax.text(x, bnd + 1, f"band {bnd}", ha="center", fontsize=7.5, color=C[est])
        else:
            ax.annotate(f"band\n{bnd} mm", (x, YL - 0.5), xytext=(x, YL - 7.5), ha="center", fontsize=7.5, color=C[est],
                        arrowprops=dict(arrowstyle="->", color=C[est], lw=0.9))
ax.set_xticks(range(4)); ax.set_xticklabels([f"tag lost:\n{s}" for s in LOSS]); ax.set_xlim(-0.5, 3.5); ax.set_ylim(0, YL)
ax.set_ylabel("drift at re-acquisition, effective (mm)")
ax.legend(loc="center", frameon=False, bbox_to_anchor=(0.5, 0.62), ncol=3)
for est, key, exp in (("EKF3", "EKF3", ["13–27", "6–25", "3–11", "7–31"]),):
    dd_ = drifts(S1, key); check("S1 EKF3 flying drift 5/15/30/move (mm, effective)", " | ".join(rng(x, 0) for x in dd_), " | ".join(exp), "numbers.md §17 table")
for nm, trs, key, exp in (("S2v2 UKF", S2V, "UKF_port", "5/7/8 | 19/7/26 | 6/10/10 | 26/4/5"), ("S3v2 FGO", S3V, "FGO_flying", "13/20/17 | 7/25/27 | 22/15/9 | 17/11/18")):
    de = drifts(trs, key, "end")
    check(f"{nm} flying end-of-loss drift r1/r2/r3 (mm)", " | ".join("/".join(f"{x:.0f}" for x in row) for row in de), exp, "numbers.md §17.1 table")
dmax = max(abs(a - b) for trs, key in ((S1 + S1F, "EKF3"), (S2V, "UKF_port"), (S3V, "FGO_flying"))
           for ra, rb in zip(drifts(trs, key), drifts(trs, key, "end")) for a, b in zip(ra, rb))
check("effective vs end-of-loss drift, max |Δ| at printed (mm) precision", f"≤ {dmax:.0f} mm", "≤ 5 mm",
      f"numbers.md §17.1 ('differ by ≤ 5 mm'); unrounded {dmax:.1f} mm (S2v2 r1, move loss)")
inband = all(v <= BAND[e][li] for (e, li), d in DR.items() for v in d)
check("every plotted drift inside its pre-registered band (P-H5)", inband, True, "numbers.md §17, §17.1 (every band PASSES)")
lock = [lo[k]["lockout"] for t in S1 + S1F + S2V + S3V for lo in HJ(t)["losses"] for k in lo if isinstance(lo[k], dict) and "lockout" in lo[k]]
check("lockouts in any loss", sum(bool(x) for x in lock), 0, "numbers.md §17 (P-H7 PASS)")
save(fig, "F8", "F8_H_tag_loss_drift",
     "Holding on a wall tag, every flying estimator drifts at most ~3 cm while the tag is hidden, inside every band",
     "Experiment H (marker-relative hold on a wall tag, forward camera), FLYING estimators only: the drift at re-acquisition after each "
     "tag loss (5, 15, 30 s in the hover; ~7 s during a move), each mark one loss in one flight, EFFECTIVE metric (last fix → first returning "
     "fix; the end-of-loss metric of numbers.md §17.1 differs by ≤ 5 mm). EKF3 = S1 near-spawn (r1–r3) and S1 far-spawn (r1, r2, r3b; "
     "METHODOLOGY only, no numbers.md row); UKF = the jitter-corrected port (S2v2); FGO = the final C++ node (S3v2, flown with the OLD FGO "
     "priors). Pre-registered bands (P-H5): EKF3 and FGO ≤ 50 / 100 / 200 / 150 mm, UKF ≤ 100 / 200 / 400 / 300 mm; bands above the 60 mm axis "
     "are shown as arrows with their value. Every loss is inside its band and no estimator locked out (P-H5, P-H7 PASS). The comparative "
     "criteria (H-H2, P-H3, H-H4) FAIL as adjudicated, with the same verdicts on these re-flown sets (PENDING a ruling). Each estimator flew "
     "its own flights: pairing by run index, not trajectory.",
     "eval/results/expH/s1_r{1,2,3}.json, s1far_r{1,2,3b}.json, s2v2_r*.json, s3v2_r*.json (losses[*].<est>.effective.drift_m, drift_end_m, lockout)",
     "§17 (S1 table, P-H5, P-H7), §17.1 (S2v2, S3v2), §17.2; claims 25, 26",
     logscale="bands up to 400 mm next to drifts ≤ 31 mm: linear axis clipped at 60 mm; off-scale bands drawn as arrows with their value",
     uncheck="S1-far EKF3 drifts (3 of the 6 EKF3 flights): METHODOLOGY only, no numbers.md row")

# =============================================================================================== APPENDIX tables
def setb(trs):
    B = [L(f"closed_loop_{t}.json")["B"] for t in trs]
    r_ = lambda f: f"{min(f(b) for b in B):.2f}–{max(f(b) for b in B):.2f}"
    js = [L(f"closed_loop_{t}.json") for t in trs]
    fails = [f"r{i + 1} {k}" for i, b in enumerate(B) for k in ("B1", "B2", "B3", "B4", "B5") if not b[k]["pass"]]
    n = sum(b["pass"] and j.get("S2", {}).get("pass", True) for b, j in zip(B, js))
    return (f"{n}/3 " + ("PASS" if n == 3 else "FAIL") + (f" ({', '.join(fails)})" if fails else ""),
            r_(lambda b: b["B2"]["max_abs_x_cruise_m"]) + " m", r_(lambda b: b["B3"]["p95_deg"]) + "° / " + r_(lambda b: b["B3"]["max_deg"]) + "°",
            r_(lambda b: b["B4"]["max_abs_lat_speed_mps"]) + " m/s")


def seta(tr, win):
    if tr is None:
        return "not flown"
    c0, ct = cl_meta(tr); t_ = ct["t_rel_cruise_s"]
    return f"+{t_:.1f} s, {'PASS' if win[0] <= t_ <= win[1] else 'MISS'} [+{win[0]}, +{win[1]}]"


rowsA = [
    ("EKF3, full speed", "unmodified; Python bridge", "—", *setb([f"cl_b_tex_r{i}" for i in (1, 2, 3)])),
    ("EKF3, full speed", "unmodified; C++ bridge", seta("cl_a_tex", WIN["EKF3"]), *setb([f"cl_bcpp_tex_r{i}" for i in (1, 2, 3)])),
    ("EKF3, half speed", "unmodified; C++ bridge", seta("cl_a_tex_half", WIN["EKF3"]) + " (D21)", *setb([f"cl_bcpp_tex_r{i}_half" for i in (1, 2, 3)])),
    ("UKF, full speed", "v1 port (pre-jitter fix)", seta("cl_ukf_a_tex", WIN["UKF"]), *setb([f"cl_ukf_b_tex_r{i}" for i in (1, 2, 3)])),
    ("UKF, half speed", "v1 port (pre-jitter fix)", seta("cl_ukf_a_tex_half", WIN["UKF"]), *setb([f"cl_ukf_b_tex_r{i}_half" for i in (1, 2, 3)])),
    ("UKF, half speed", "v2 port (jitter-corrected) FINAL", seta("cl_ukf_a_tex_half_v2", WIN["UKF"]), *setb([f"cl_ukf_b_tex_r{i}_half_v2" for i in (1, 2, 3)])),
    ("FGO, half speed", "original (old noise model), hard gate", seta("cl_fgo_a_tex_half", WIN["FGO"]), *setb([f"cl_fgo_b_tex_r{i}_half" for i in (1, 2, 3)])),
    ("FGO, half speed", "original, robust heading weight", "not flown", *setb([f"cl_fgo_b_robust_tex_r{i}_half" for i in (1, 2, 3)])),
    ("FGO, half speed", "v2: noise fix only (ABLATION)", seta("cl_fgo_a_tex_half_v2", WIN["FGO"]), *setb([f"cl_fgo_b_tex_r{i}_half_v2" for i in (1, 2, 3)])),
    ("FGO, half speed", "v3: noise fix + gated yaw cap FINAL", seta("cl_fgo_a_tex_half_v3", WIN["FGO"]), *setb([f"cl_fgo_b_tex_r{i}_half_v3" for i in (1, 2, 3)])),
]
check("EKF3 half contact MISS", rowsA[2][2].split(",")[1].strip().split()[0], "MISS", "numbers.md §15 (D21)")
check("UKF v1 half heading set", rowsA[4][3].split()[0], "2/3", "numbers.md §15 (r3 B4 0.296 m/s)")
check("UKF v2 / FGO v3 heading sets", f"{rowsA[5][3]} / {rowsA[9][3]}", "3/3 PASS / 3/3 PASS", "numbers.md §15 (re-flown sets)")
check("FGO v2 ablation heading set", rowsA[8][3], "3/3 PASS", "numbers.md §15")
check("FGO original hard / robust heading sets (D28)", f"{rowsA[6][3]} / {rowsA[7][3]}", "3/3 PASS / 3/3 PASS", "numbers.md §15 (D28)")
check("contacts UKF v1 half / UKF v2 / FGO orig / FGO v2 / FGO v3 (s)",
      " / ".join(r[2].split(",")[0].replace(" s", "") for r in (rowsA[4], rowsA[5], rowsA[6], rowsA[8], rowsA[9])), "+198.0 / +165.9 / +165.8 / +169.6 / +169.9", "numbers.md §15 contact rows")
check("EKF3 full no-heading contact; UKF v1 full contact", f"{rowsA[1][2].split(',')[0].replace(' s', '')}; {rowsA[3][2].split(',')[0].replace(' s', '')}", "+186.2; +163.0", "numbers.md §15 rows 1–2")
check("UKF v1 half / FGO original B3 p95/max ranges", f"{rowsA[4][5]}; {rowsA[6][5]}", "0.18–0.21° / 0.28–1.32°; 0.26–0.38° / 1.28–1.88°", "numbers.md §15 B3 row (original builds)")
APP_A = ITEMS_A = None
CHK_A = CHK; CHK = []


def hsum(trs, key):
    hm = [1e3 * w["mean_m"] for t in trs for w in HJ(t)["hold_windows_vehicle"]]
    dr = [1e3 * lo[key]["effective"]["drift_m"] for t in trs for lo in HJ(t)["losses"]]
    lk = sum(lo[key]["lockout"] for t in trs for lo in HJ(t)["losses"])
    return f"{min(hm):.1f}–{max(hm):.1f} mm", f"{min(dr):.0f}–{max(dr):.0f} mm", f"{lk}", "every band PASS" if all(
        1e3 * lo[key]["effective"]["drift_m"] <= BAND[{"EKF3": "EKF3", "UKF_port": "UKF", "FGO_flying": "FGO"}[key]][i]
        for t in trs for i, lo in enumerate(HJ(t)["losses"])) else "band FAIL"


rowsH = [("S1, EKF3 flying (near spawn)", "unmodified EKF3", *hsum(S1, "EKF3")),
         ("S1 far re-fly, EKF3 flying", "unmodified EKF3", *hsum(S1F, "EKF3")),
         ("S2, UKF flying", "v1 port (pre-jitter fix)", *hsum(S2O, "UKF_port")),
         ("S2v2, UKF flying", "v2 port (jitter-corrected) FINAL", *hsum(S2V, "UKF_port")),
         ("S3, FGO flying", "noise fix only (ABLATION); OLD priors", *hsum(S3O, "FGO_flying")),
         ("S3v2, FGO flying", "v3 final node f642cd37; OLD priors", *hsum(S3V, "FGO_flying"))]
check("S2 / S2v2 / S3 / S3v2 hold window means (mm)", " ; ".join(r[2].replace(" mm", "") for r in rowsH[2:]), "4.9–6.3 ; 6.1–7.4 ; 7.6–8.2 ; 8.1–9.0", "numbers.md §17.1 table")
check("lockouts S1 / S1far / S2v2 / S3v2", " / ".join(rowsH[i][4] for i in (0, 1, 3, 5)), "0 / 0 / 0 / 0", "numbers.md §17, §17.1")

SAFE = [  # (test, file, build, notes)
    ("UKF (a) PARAM", "safety_ukf_a", "v1 port; first run", "first run"),
    ("UKF (a) PARAM", "safety_ukf_a_rerun", "v1 port; re-run", ""),
    ("UKF (a) PARAM", "safety_ukf_a_v2", "v2 port (jitter-corrected)", ""),
    ("UKF (a) PARAM", "safety_ukf_a_v3", "v2 port abb0357d (re-test)", "ruled PASS 2026-10-11"),
    ("UKF (b) KILL", "safety_ukf_b", "v1 port", ""),
    ("UKF (b) KILL", "safety_ukf_b_v2", "v2 port (jitter-corrected)", "S-A2 relay drain; stays FAILED AS WORDED"),
    ("UKF (b) KILL", "safety_ukf_b_v3", "v2 port abb0357d (re-test)", "S-A2 relay drain; stays FAILED AS WORDED"),
    ("FGO (a) KILL", "safety_fgo_a", "original FGO; old hold", ""),
    ("FGO (a) KILL", "safety_fgo_a_v2", "noise fix only (ABLATION); OLD priors", ""),
    ("FGO (a) KILL", "safety_fgo_a_v3", "v3 node f642cd37; OLD priors", ""),
    ("FGO (a) KILL", "safety_fgo_a_v4", "corrected node 4c07374b; NEW priors", "S-A3 1.45 m near its 1.5 m bound"),
    ("FGO (b) KILL", "safety_fgo_b", "original FGO; old hold", "room-box breach in the landing"),
    ("FGO (b) KILL", "safety_fgo_b2", "original FGO; 2 m-clearance hold", ""),
    ("FGO (b) KILL", "safety_fgo_b_v2", "noise fix only (ABLATION); OLD priors", ""),
    ("FGO (b) KILL", "safety_fgo_b_v3", "v3 node f642cd37; OLD priors", ""),
    ("FGO (b) KILL", "safety_fgo_b_v4", "corrected node 4c07374b; NEW priors", ""),
    ("EKF3 reference KILL", "safety_ekf3_ref", "unmodified EKF3", "drift 1.40 m against a ≤ 0.5 m prediction (wrong); no breach"),
]


def srow(test, f, build, note):
    j = HJ(f); fl = []
    for k, nm in (("S-A1", "A1"), ("S-A2", "A2"), ("S-A3", "A3"), ("S-A4_single_landing", "A4")):
        if f == "safety_ekf3_ref" and k == "S-A2":
            fl.append("A2 n/a"); continue
        fl.append(f"{nm} {'PASS' if j[k]['PASS'] else 'FAIL'}")
    s2 = j["S-A2"]; s3 = j["S-A3"]
    t2 = f"{s2['text_delay_s']:.2f} s (bound {s2['bound_s']:.2f})" if s2.get("text_delay_s") is not None else "—"
    d3 = f"{s3['horiz_disp_m']:.2f} m" if s3.get("horiz_disp_m") is not None else ("breach" if s3.get("breach") else "—")
    allp = all(j[k]["PASS"] for k in ("S-A1", "S-A2", "S-A3", "S-A4_single_landing")) if f != "safety_ekf3_ref" else None
    verdict = "reference (no criteria)" if allp is None else ("ALL PASS" if allp else "FAILED AS WORDED")
    return (test, j["trial"], build, ", ".join(fl), t2, d3, verdict, note)


rowsS = [srow(*s) for s in SAFE]
SV = {r[1]: r for r in rowsS}
check("UKF (b) v2 / v3 S-A2 delay (s), verdict", f"{HJ('safety_ukf_b_v2')['S-A2']['text_delay_s']:.2f} / {HJ('safety_ukf_b_v3')['S-A2']['text_delay_s']:.2f}, "
      f"{SV['H_safety_ukf_b_v2'][6]} / {SV['H_safety_ukf_b_v3'][6]}", "5.75 / 5.69, FAILED AS WORDED / FAILED AS WORDED", "numbers.md §15 safety row (v2); METHODOLOGY 2d (v3)")
check("UKF (a) v2 / v3 verdict", f"{SV['H_safety_ukf_a_v2'][6]} / {SV['H_safety_ukf_a_v3'][6]}", "ALL PASS / ALL PASS", "numbers.md §15 (v2); METHODOLOGY rulings 2026-10-11 item 3 (v3)")
check("FGO (a) v3 S-A2 / disp; (b) v3", f"{HJ('safety_fgo_a_v3')['S-A2']['text_delay_s']:.2f} s / {HJ('safety_fgo_a_v3')['S-A3']['horiz_disp_m']:.2f} m; "
      f"{HJ('safety_fgo_b_v3')['S-A2']['text_delay_s']:.2f} s / {HJ('safety_fgo_b_v3')['S-A3']['horiz_disp_m']:.2f} m", "0.54 s / 0.83 m; 0.25 s / 1.19 m", "numbers.md §15 safety row")
check("FGO (a) v4 S-A2 / disp; (b) v4", f"{HJ('safety_fgo_a_v4')['S-A2']['text_delay_s']:.2f} s / {HJ('safety_fgo_a_v4')['S-A3']['horiz_disp_m']:.2f} m; "
      f"{HJ('safety_fgo_b_v4')['S-A2']['text_delay_s']:.2f} s / {HJ('safety_fgo_b_v4')['S-A3']['horiz_disp_m']:.2f} m", "0.60 s / 1.45 m; 0.62 s / 0.21 m",
      "METHODOLOGY 'Band C with forced gate decisions … FGO safety re-tests PASS'")
check("FGO v4 a / b verdict", f"{SV['H_safety_fgo_a_v4'][6]} / {SV['H_safety_fgo_b_v4'][6]}", "ALL PASS / ALL PASS", "METHODOLOGY (v4: S-A1–S-A4 PASS as worded)")
check("FGO v2 ablation a / b: S-A2 s, disp m", f"{HJ('safety_fgo_a_v2')['S-A2']['text_delay_s']:.2f} s, {HJ('safety_fgo_a_v2')['S-A3']['horiz_disp_m']:.2f} m; "
      f"{HJ('safety_fgo_b_v2')['S-A2']['text_delay_s']:.2f} s, {HJ('safety_fgo_b_v2')['S-A3']['horiz_disp_m']:.2f} m", "0.29 s, 0.78 m; 0.43 s, 1.27 m", "numbers.md §15 history row")
check("history: UKF a rerun / UKF b / FGO a / FGO b2 disp (m); UKF b S-A2 (s)",
      f"{HJ('safety_ukf_a_rerun')['S-A3']['horiz_disp_m']:.2f} / {HJ('safety_ukf_b')['S-A3']['horiz_disp_m']:.2f} / {HJ('safety_fgo_a')['S-A3']['horiz_disp_m']:.2f} / "
      f"{HJ('safety_fgo_b2')['S-A3']['horiz_disp_m']:.2f}; {HJ('safety_ukf_b')['S-A2']['text_delay_s']:.2f}", "0.42 / 0.28 / 0.37 / 1.25; 4.81", "numbers.md §15 history row")
check("FGO (b) first run S-A3; UKF (a) first run S-A2 / S-A3", f"{HJ('safety_fgo_b')['S-A3']['PASS']}; {HJ('safety_ukf_a')['S-A2']['PASS']} / {HJ('safety_ukf_a')['S-A3']['PASS']}",
      "False; False / False", "numbers.md §15 history row (S-A3 FAIL; S-A2 FAIL as worded, S-A3 FAIL)")
check("EKF3 reference drift (m)", f"{HJ('safety_ekf3_ref')['S-A3']['horiz_disp_m']:.2f}", "1.40", "numbers.md §15 history row")
CHK_HS = CHK; CHK = []

f1 = L("f1_test.json"); dec1 = f1["decision"]
bagsF = ["fwdplainc_tex_r1", "fwdplainc_tex_r2", "fwdplainc_tex_r3"]
check("F1 robust lower yaw max on", f"{dec1['robust_lower_yaw_max_on']}/6", "6/6", "numbers.md §15.2 F1 row")
check("F1 lockouts FGO_robust = UKF_hard", json.dumps(dec1["lockout_total"], sort_keys=True), json.dumps({"FGO_robust": 3, "UKF_hard": 3}, sort_keys=True), "numbers.md §15.2")
check("F1 verdict robust_FGO_better", dec1["robust_FGO_better"], False, "numbers.md §15.2 (NOT met, lockout tie)")
check("FGO_hard plain-wall yaw max (deg)", rng([f1[b]["FGO_hard"]["yaw_max_deg"] for b in bagsF]), "4.59–5.03", "numbers.md §15.2 F1 row")
ST = {}
for mode in ("lc", "nolc"):
    for key in ("step_median_ms", "step_p99_ms", "wall_s"):
        ST[(mode, key)] = [json.load(open(f"{TD}/T_A_r{r}/lc_fgo_{mode}_t245/stats.json"))[key] for r in (1, 2, 3)]
check("L LC median (ms)", rng(ST[("lc", "step_median_ms")], 0), "35–41", "numbers.md §16.3 (restated 2026-10-11)", exact=True)
check("L no-LC median (ms)", rng(ST[("nolc", "step_median_ms")], 0), "50–61", "numbers.md §16.3", exact=True)
check("L LC p99 (ms)", rng(ST[("lc", "step_p99_ms")], 0), "80–94", "numbers.md §16.3", exact=True)
check("L no-LC wall (s)", rng(ST[("nolc", "wall_s")], 0), "7276–9583", "numbers.md §16.3", exact=True)
CHK_F = CHK; CHK = []

ABL = [  # build ablations: (ablation, measure, earlier build, final build, verdict)
    ("UKF v1 → v2 (jitter correction)", "closed loop, no heading: wall contact", rowsA[4][2].split(",")[0] + " (PASS)", rowsA[5][2].split(",")[0] + " (PASS)", "both inside the window"),
    ("UKF v1 → v2", "closed loop, with heading: B1–B5", rowsA[4][3], rowsA[5][3], "v1 r3 failed B4 (D22 flow validity)"),
    ("UKF v1 → v2", "H hold, window means / drift", f"{rowsH[2][2]} / {rowsH[2][3]}", f"{rowsH[3][2]} / {rowsH[3][3]}", "every band PASS in both"),
    ("FGO v2 (noise fix only) → v3 (+ gated yaw cap)", "closed loop, no heading: wall contact", rowsA[8][2].split(",")[0] + " (PASS)", rowsA[9][2].split(",")[0] + " (PASS)", "gating alone: +0.3 s"),
    ("FGO v2 → v3", "closed loop, with heading: B1–B5; B3 max", f"{rowsA[8][3]}; {rowsA[8][5].split('/ ')[1]}", f"{rowsA[9][3]}; {rowsA[9][5].split('/ ')[1]}", "v3 r3 B4 0.246 m/s (band 0.25)"),
    ("FGO v2 → v3", "H hold, window means / drift", f"{rowsH[4][2]} / {rowsH[4][3]}", f"{rowsH[5][2]} / {rowsH[5][3]}", "few-mm level only"),
    ("FGO v2 → v3 → v4 node", "safety (a) / (b)", f"{SV['H_safety_fgo_a_v2'][6]} / {SV['H_safety_fgo_b_v2'][6]}",
     f"v3 {SV['H_safety_fgo_a_v3'][6]} / {SV['H_safety_fgo_b_v3'][6]}; v4 {SV['H_safety_fgo_a_v4'][6]} / {SV['H_safety_fgo_b_v4'][6]}", "v4 = NEW priors"),
    ("Flown FGO priors", "closed loop, H S3/S3v2, safety v2/v3", "OLD priors: initial yaw σ 1e-3 rad, roll/pitch 2°", "offline FGO: 1°, 5° (= UKF)",
     "no re-fly before the freeze; only safety v4 used the NEW priors"),
]


def table_page(title, header, rows, widths, notes=(), fs=8.0):
    """One A4-landscape page (or more) of a wrapped text table; returns the list of figures."""
    figs = []; lh = fs * 1.34 / 72 / 8.27

    def newpage(k):
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.text(0.03, 0.965, title + (f" (continued, {k})" if k > 1 else ""), fontsize=12, weight="bold", va="top")
        x = 0.03; y = 0.925
        for h, w in zip(header, widths):
            fig.text(x, y, "\n".join(textwrap.wrap(h, max(6, int(w * 0.95)))), fontsize=fs + 0.3, weight="bold", va="top"); x += w / sum(widths) * 0.94
        return fig, y - 3.6 * lh
    k = 1; fig, y = newpage(k)
    for row in rows:
        cells = [textwrap.wrap(str(c), max(6, int(w * 0.95))) or [""] for c, w in zip(row, widths)]
        n = max(len(c) for c in cells)
        if y - n * lh < 0.05:
            figs.append(fig); k += 1; fig, y = newpage(k)
        fig.add_artist(Line2D([0.03, 0.97], [y + 0.45 * lh, y + 0.45 * lh], color=GRID, lw=0.6, transform=fig.transFigure))
        x = 0.03
        for c, w in zip(cells, widths):
            bold = any(s in " ".join(c) for s in ("FAILED", "FAIL (", "MISS", "NOT met", "FAIL r"))
            fig.text(x, y, "\n".join(c), fontsize=fs, va="top", linespacing=1.22, weight="bold" if bold else "normal"); x += w / sum(widths) * 0.94
        y -= (n + 0.65) * lh
    for nt in notes:
        lines = textwrap.wrap(nt, 190)
        if y - len(lines) * lh < 0.05:
            figs.append(fig); k += 1; fig, y = newpage(k)
        fig.text(0.03, y, "\n".join(lines), fontsize=fs - 0.3, va="top", color=INK2); y -= (len(lines) + 0.6) * lh
    figs.append(fig)
    return figs


def save_table(figs, fid, name, title, caption, inputs, rows_, checks):
    global CHK
    pngs = []
    for k, f in enumerate(figs):
        base = os.path.join(OUT, name + (f"_p{k + 1}" if len(figs) > 1 else ""))
        f.savefig(base + ".png", dpi=150); f.savefig(base + ".pdf"); plt.close(f); pngs.append(base + ".png")
    ok = all(c[4] for c in checks)
    ITEMS.append(dict(id=fid, png=pngs, pdf=None, title=title, caption=caption, inputs=inputs, rows=rows_, checks=checks,
                      status="CURRENT" if ok else "FLAGGED (check mismatch)", logscale="none needed (table)", uncheck=""))
    print(f"wrote {name} ({len(pngs)} page(s))  checks {sum(c[4] for c in checks)}/{len(checks)}")
    for c in checks:
        if not c[4]:
            print("   CHECK FAIL:", c)


figs = table_page("Appendix A1. Closed loop in the textured corridor: every flown build, pass/fail against the pre-registered criteria",
                  ["flying estimator", "build", "no heading: wall contact (window)", "with heading: B1–B5 (+S2)", "B2 max cross-track",
                   "B3 yaw error p95 / max", "B4 max lateral speed"], rowsA, [16, 30, 30, 22, 13, 22, 14],
                  notes=["Contact windows are pre-registered per estimator (EKF3 [+155, +215] s, UKF [+146, +218] s, FGO [+145, +196] s). n = 1 per "
                         "no-heading flight; closed-loop run-to-run variability is unmeasured; no cross-speed comparison (D21). FINAL builds are the "
                         "UKF v2 port and the FGO v3 node; the rest are recorded earlier builds and the FGO v2 ablation. ALL flown FGO flights used the "
                         "OLD FGO priors (initial yaw σ 1e-3 rad, roll/pitch 2°). The UKF v1 half r3 B4 failure (0.296 m/s) and the FGO v3 r3 near-miss "
                         "(0.246 m/s against 0.25) are D22, a shared flow-validity limitation. Robust heading weighting (FGO): F1 'NOT met (lockout tie)', "
                         "see A3."])
save_table(figs, "A1", "A1_closed_loop_builds", "Closed loop: every flown build against B1–B5 and the contact window",
           "Pass/fail of every closed-loop corridor set (replaces pack F15a), computed from the closed-loop score files, with the build ablations "
           "labelled: UKF v1 (pre-jitter fix) against v2 (final); FGO original, robust, v2 (noise fix only, ABLATION) and v3 (final, OLD priors).",
           "eval/results/closed_loop_<trial>.json", "§15 (contacts, B1–B5 counts, B2, B3, re-flown sets); claim 14", CHK_A)
figs = table_page("Appendix A2. Experiment H hold sets and the safety tests (all runs, as-worded verdicts)",
                  ["H flight set", "build", "hold error (window means)", "tag-loss drift (effective, all losses)", "lockouts", "P-H5 drift bands"],
                  rowsH, [26, 34, 20, 26, 10, 18], fs=8.0) + \
       table_page("Appendix A2 (cont.). Safety tests: failure injected in the hold; the FC must declare position lost",
                  ["test", "trial", "build", "criteria as worded", "S-A2 'position lost' delay", "S-A3 drift to touchdown", "verdict", "note"],
                  rowsS, [13, 21, 25, 30, 18, 12, 15, 26], fs=7.0,
                  notes=["UKF (b) S-A2 FAILS AS WORDED in both v2 (5.75 s) and v3 (5.69 s) against 5.5 s: MAVProxy relay drain after the SIGKILL, the trigger "
                         "fired 5.0 s after the last flow received; both stay recorded as FAILED (ruling 2026-10-11 item 2; the supplementary S-A2b is for "
                         "FUTURE tests only). FGO v4 flew the corrected node 4c07374b (initial yaw 1°, roll/pitch 5°, the NEW priors); every earlier FGO "
                         "safety run flew the OLD priors. The first UKF (a) and FGO (b) runs also show S-A4 FAIL in their score files (numbers.md cites only "
                         "S-A2/S-A3 for them). The EKF3 reference has no thesis-nav text (S-A2 not applicable). numbers.md §15 lists v2/v3 as the final runs; "
                         "the v3 (UKF) and v4 (FGO) re-tests are recorded in METHODOLOGY only."])
save_table(figs, "A2", "A2_H_and_safety", "H hold sets and the safety tests (all runs)",
           "Experiment H sets (S1, S1 far, S2/S2v2, S3/S3v2) with hold error, drift, lockouts and the P-H5 bands, and every safety-test run with its "
           "as-worded verdict, including the v3 (UKF) and v4 (FGO, NEW priors) re-tests (replaces pack F15b).",
           "eval/results/expH/s1*_r*.json, s2*_r*.json, s3*_r*.json, safety_*.json", "§15 safety rows, §17, §17.1; METHODOLOGY 2d and 'Band C … FGO safety re-tests'", CHK_HS)
rowsF = [("F1 (k = 2.385)", "robust FGO better than the hard-gated UKF on the heading", "NOT met (lockout tie)",
          f"robust FGO lower worst-case yaw on {dec1['robust_lower_yaw_max_on']}/6 bags, but lockouts FGO_robust {dec1['lockout_total']['FGO_robust']} = UKF_hard "
          f"{dec1['lockout_total']['UKF_hard']}; FGO_hard plain-wall yaw max {rng([f1[b]['FGO_hard']['yaw_max_deg'] for b in bagsF])}° (= UKF_hard to 0.01°)"),
         ("L compute cost (DIAGNOSTIC)", "per-update solve time and wall time, keyframe FGO, workstation Python, 6 parallel jobs", "no criterion",
          f"median LC {rng(ST[('lc', 'step_median_ms')], 1)} ms, no-LC {rng(ST[('nolc', 'step_median_ms')], 1)} ms; p99 LC {rng(ST[('lc', 'step_p99_ms')], 0)} ms, "
          f"no-LC {rng(ST[('nolc', 'step_p99_ms')], 0)} ms; no-LC wall {rng(ST[('nolc', 'wall_s')], 0)} s. Says nothing about onboard feasibility")]
figs = table_page("Appendix A3. The F1 robust-weighting test, the L compute cost, and the build ablations",
                  ["item", "what is tested", "verdict", "key numbers"], rowsF, [24, 46, 24, 96])
figs2 = table_page("Appendix A3 (cont.). Build ablations: earlier build against the final build, same experiment",
                   ["ablation", "measure", "earlier build", "final build", "note"], ABL, [36, 34, 38, 42, 40],
                   notes=["Earlier builds are kept as recorded and labelled; the thesis cites the final builds. Attribution: the corrections were applied "
                          "jointly and are not attributed individually (numbers.md §18), apart from the traced plain-wall case and the O partial attribution."])
save_table(figs + figs2, "A3", "A3_F1_cost_ablations", "F1, the L compute cost and the build ablations",
           "Pass/fail table for the F1 robust-weighting test (replaces pack F07), the L compute cost (diagnostic, replaces F13; linear values, no "
           "plot) and the build ablations: UKF v1 against v2; FGO v2 (noise fix only) against v3 (final) and the v4 node; the flown-FGO OLD-priors note.",
           "eval/results/f1_test.json; ~/thesis_data/trials/T_A_r{1,2,3}/lc_fgo_{lc,nolc}_t245/stats.json; closed_loop_*, expH/*",
           "§15.2 F1 row; §16.3 cost bullets; §15, §17.1", CHK_F)

# =============================================================================================== combined PDF + index
PAL = "EKF3 #0072B2 (blue, circle) · UKF #009E73 (bluish green, triangle) · FGO #D55E00 (vermilion, square) · truth / references #999999 (grey)"


def caption_page(P, it):
    pngs = it["png"] if isinstance(it["png"], list) else [it["png"]]
    for pi, png in enumerate(pngs):
        img = plt.imread(png); h, w = img.shape[:2]
        fig = plt.figure(figsize=(11.69, 8.27))
        top = 0.965; avail = 0.70 if not isinstance(it["png"], list) else 0.80; aw = 0.95; ah = aw * (h / w) * 11.69 / 8.27
        if ah > avail: aw *= avail / ah; ah = avail
        ax = fig.add_axes([0.5 - aw / 2, top - ah, aw, ah]); ax.imshow(img); ax.axis("off")
        y = top - ah - 0.02
        if pi == len(pngs) - 1:
            cap = "\n".join(textwrap.wrap(f"Figure {it['id']}. {it['caption']}", 175))
            fig.text(0.03, y, cap, fontsize=8.6, va="top"); y -= 0.0185 * (cap.count("\n") + 1) + 0.01
            okc = sum(c[4] for c in it["checks"])
            src = "\n".join(textwrap.wrap(f"Cross-check against numbers.md / METHODOLOGY: {okc}/{len(it['checks'])} match. Source: {SCRIPT} "
                                          f"(commit {COMMIT}); inputs: {it['inputs']}. numbers.md rows: {it['rows']}.", 200))
            fig.text(0.03, max(y, 0.02 + 0.0165 * (src.count("\n") + 1)), src, fontsize=7.2, va="top", color=INK2)
        P.savefig(fig); plt.close(fig)


with PdfPages(PDF) as P:
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.text(0.06, 0.86, "Thesis figures", fontsize=24, weight="bold")
    fig.text(0.06, 0.81, "EKF3, UKF and FGO for indoor UAV state estimation under degraded sensing (simulation; results FROZEN 2026-10-11)", fontsize=12)
    intro = ("Reader-facing figure set, plotted from the frozen result files (no number recomputed). Each title is the takeaway; each caption "
             "states what is plotted and the verdict it supports. Every plotted key value is cross-checked against docs/thesis/numbers.md (or "
             "METHODOLOGY where numbers.md has no row); the match count is under each caption. Conventions: one fixed colour and marker per "
             "estimator; solid lines and filled marks = live, dashed lines and open marks = hindsight; linear axes only (no log axes); evo = "
             "evo -a (cruise). † = a runaway magnitude from a diverging estimate (order of magnitude only). Flown FGO results used the OLD FGO "
             f"priors (initial yaw σ 1e-3 rad) except the v4 safety re-tests. Built by {SCRIPT} at commit {COMMIT}.")
    fig.text(0.06, 0.75, "\n".join(textwrap.wrap(intro, 140)), fontsize=10, va="top")
    fig.text(0.06, 0.57, "Colours", fontsize=12, weight="bold")
    for k, e in enumerate(EST):
        fig.add_artist(Line2D([0.07, 0.10], [0.535 - 0.03 * k] * 2, color=C[e], lw=2, marker=MK[e], ms=7, transform=fig.transFigure))
        fig.text(0.11, 0.535 - 0.03 * k, f"{e}  {C[e]}", fontsize=10, va="center")
    fig.add_artist(Line2D([0.07, 0.10], [0.445] * 2, color=TRUTH, lw=2, transform=fig.transFigure)); fig.text(0.11, 0.445, f"truth / reference  {TRUTH}", fontsize=10, va="center")
    y = 0.39; fig.text(0.06, y, "Contents", fontsize=12, weight="bold"); y -= 0.028
    for it in ITEMS:
        okc = sum(c[4] for c in it["checks"])
        fig.text(0.07, y, f"{it['id']}  {it['title']}   [checks {okc}/{len(it['checks'])}]", fontsize=9); y -= 0.025
    P.savefig(fig); plt.close(fig)
    for it in ITEMS:
        caption_page(P, it)
print("wrote", PDF)

with open(INDEX, "w") as f:
    f.write("# Thesis figures: index (2026-10-15)\n\n")
    f.write(f"Built by `{SCRIPT}` at commit `{COMMIT}` (run with `/home/makerspace/venv-evo/bin/python`; plotting only, no number recomputed). "
            "Combined PDF for the supervisor: `docs/thesis/figures_thesis/thesis_figures_combined.pdf`. Each figure is here as `.pdf` and `.png`. "
            "The frozen pack (`docs/thesis/final_results_pack.pdf`, `eval/figs_final_pack.py`) is untouched.\n\n")
    f.write(f"**Colour mapping (Okabe–Ito, colour-blind safe; fixed across every figure):** {PAL}. Solid lines / filled marks = live; dashed lines / "
            "open marks = hindsight. No log axes anywhere.\n\n")
    f.write("**Scorecard categories (F1):** BEST = a stated ordering puts it first; TIED = no ordering is claimed (or all pass the same criteria); "
            "BEHIND = a stated ordering or failed similarity verdict puts it below; FAILED = does not bound position; PASSED = met its pre-registered "
            "criteria with no comparison (L, FGO only); N/A = not run. BEHIND, PASSED and N/A are additions to the brief's best/tied/failed, used "
            "where those three do not fit (listed in the handover).\n\n")
    f.write("| id | files | takeaway title | status | checks | log-scale handling |\n|---|---|---|---|---|---|\n")
    for it in ITEMS:
        okc = sum(c[4] for c in it["checks"])
        files = ", ".join(f"`{os.path.basename(p)}`" for p in (it["png"] if isinstance(it["png"], list) else [it["png"]]))
        f.write(f"| {it['id']} | {files} (+ .pdf) | {it['title']} | {it['status']} | {okc}/{len(it['checks'])} | {it['logscale']} |\n")
    if ROUNDING:
        f.write("\n**Last-digit rounding matches (accepted, as in the pack):** " + "; ".join(f"{r[0]}: file `{r[1]}`, numbers.md `{r[2]}`" for r in ROUNDING) + ".\n")
    f.write("\n## Captions, sources and checks\n\n")
    for it in ITEMS:
        f.write(f"### {it['id']}: {it['title']}\n\n- **Caption:** {it['caption']}\n- **Inputs:** {it['inputs']}\n- **numbers.md rows:** {it['rows']}\n")
        if it["uncheck"]:
            f.write(f"- **Not cross-checkable:** {it['uncheck']}\n")
        f.write("\n| check | computed | expected | source | match |\n|---|---|---|---|---|\n")
        for c in it["checks"]:
            rnd = any(r[0] == c[0] and r[1] == c[1] for r in ROUNDING)
            f.write(f"| {c[0]} | `{c[1]}` | `{c[2]}` | {c[3]} | {('yes (last-digit rounding)' if rnd else 'yes') if c[4] else '**NO**'} |\n")
        f.write("\n")
print("wrote", INDEX)
