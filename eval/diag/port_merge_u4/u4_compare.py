"""U4 positive test (2026-10-12): the u4-gndclr Replay with UKF_TEST_RNG_LOW=0.15 ('low') against its default run
('reg', = the installed Replay), on the same log. Pairs ukf_shadow.csv rows by TimeUS."""
import csv, json, math, sys
S = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/s12/u4"


def load(p):
    with open(p) as f:
        return {int(r["TimeUS"]): r for r in csv.DictReader(f)}


out = {}
for L in sys.argv[1:]:
    reg, low = load(f"{S}/{L}/reg/ukf_shadow.csv"), load(f"{S}/{L}/low/ukf_shadow.csv")
    ts = sorted(set(reg) & set(low))
    t_air = next(t for t in ts if -float(reg[t]["PD"]) > 0.5)          # first time the default UKF is above 0.5 m
    pre = [t for t in ts if t < t_air - 2_000_000]                        # on the ground (2 s before lift-off)
    d = lambda t, k: float(low[t][k]) - float(reg[t][k])
    hor = lambda t: math.hypot(d(t, "PN"), d(t, "PE"))
    post = [t for t in ts if t >= t_air + 30_000_000]
    first_eq = next((t for t in ts if t > t_air and all(low[t][k] == reg[t][k] for k in ("PN", "PE", "PD", "Yaw"))), None)
    out[L] = {
        "rows_paired": len(ts), "rows_reg": len(reg), "rows_low": len(low),
        "first_row_us": [min(reg), min(low)],
        "t_airborne_us": t_air,
        "ground_h_reg_m": [round(-float(reg[t]["PD"]), 4) for t in (pre[0], pre[-1])],
        "ground_h_low_m": [round(-float(low[t]["PD"]), 4) for t in (pre[0], pre[-1])],
        "ground_SS_low_equal_reg": all(low[t]["SS"] == reg[t]["SS"] for t in pre),
        "ground_healthy_low": sorted({low[t]["Healthy"] for t in pre}),
        "Ra_at_airborne_reg_low": [reg[t_air]["Ra"], low[t_air]["Ra"]],
        "max_dPD_m_whole": round(max(abs(d(t, "PD")) for t in ts), 4),
        "max_dH_m_whole": round(max(hor(t) for t in ts), 4),
        "max_dYaw_deg_whole_wrapped": round(max(abs((d(t, "Yaw") + 180) % 360 - 180) for t in ts), 4),
        "max_dPD_m_from_air+30s": round(max(abs(d(t, "PD")) for t in post), 4),
        "max_dH_m_from_air+30s": round(max(hor(t) for t in post), 4),
        "first_identical_row_after_airborne_us": first_eq,
    }
print(json.dumps(out, indent=1))
json.dump(out, open(f"{S}/u4_compare.json", "w"), indent=1)
