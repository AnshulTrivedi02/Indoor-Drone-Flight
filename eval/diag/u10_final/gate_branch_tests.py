#!/usr/bin/env python3
"""U10 gate tool, every pass/fail branch executed once (2026-10-12). PLUMBING on SITL Replay outputs of the installed
Replay 3c3b62bb (scratchpad u10f/rep_inst) and their SIM-truth scores; edited COPIES of the CSVs in a scratch Replay
directory (the .BIN is symlinked inside the scratchpad). Writes eval/results/u10_final/gate_branch_tests.json."""
import copy, json, os, shutil, sys, tempfile

W = "/home/makerspace/thesis_ws/.claude/worktrees/agent-a5e6fd9bcc14a040c"
S = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/u10f"
sys.path.insert(0, W + "/eval")
import u10_gate as G  # noqa: E402

R = W + "/eval/results/u10_final"
BASE, BASE_SCORE = S + "/rep_inst/cl_ukf_b_tex_r1_half_v2", R + "/score_cl_ukf_b_tex_r1_half_v2_sim_truth_inst.json"
CLA_SCORE = R + "/score_cl_a_tex_half_sim_truth_inst.json"
res = {}


def scratch(tag, edit=None):
    d = os.path.join(S, "branch", tag)
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d + "/logs")
    for f in ("ukf_shadow.csv", "ukf_geometry.csv", "ukf_stats.csv", "replay.log", "binary.md5"):
        shutil.copy(os.path.join(BASE, f), d)
    os.symlink(os.path.join(BASE, "logs", "00000001.BIN"), d + "/logs/00000001.BIN")
    if edit:
        edit(d)
    return d


def run(tag, d, score=BASE_SCORE, extra=()):
    out = G.main(["flight", "--replay-dir", d, "--score", score, "--d-max", "1.0", "--name", tag,
                  "--json", f"{S}/branch/{tag}.json", *extra]) if score else \
        G.main(["flight", "--replay-dir", d, "--d-max", "1.0", "--name", tag, "--json", f"{S}/branch/{tag}.json"])
    return out


def rec(name, out, expect):
    got = out["verdict"]
    res[name] = {"verdict": got, "expected": expect, "ok": got.startswith(expect) if expect != "PASS" else got == "PASS",
                 "why": {g: out[g].get("why") for g in ("preconditions", "G1", "G2", "G3", "G4", "G5", "G6") if g in out
                         and not out[g]["pass"]}}


def sub(path, old, new, count=1):
    t = open(path).read(); assert t.count(old) >= 1, old; open(path, "w").write(t.replace(old, new, count))


old_main = G.main
def quiet(argv):                                     # G.main prints the JSON; keep the test output short
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):
        return old_main(argv)
G.main = quiet

os.makedirs(S + "/branch", exist_ok=True)
base = run("base", scratch("base")); rec("base flight (fork-flown, G6 applies)", base, "PASS")
# G1
rec("G1 source not log_parm", run("g1src", scratch("g1src", lambda d: sub(d + "/ukf_geometry.csv", "flow_delay_ms,10,log_parm",
                                                                           "flow_delay_ms,10,replay_registered_default"))), "FAIL: G1")
rec("G1 late PARM changing a used value", run("g1late", scratch("g1late", lambda d: open(d + "/ukf_geometry.csv", "a").write(
    "warning_late_parm,30000,EK3_FLOW_DELAY,25\n"))), "FAIL: G1")
rec("G1 late PARM equal to the used value", run("g1same", scratch("g1same", lambda d: open(d + "/ukf_geometry.csv", "a").write(
    "warning_late_parm,30000,EK3_FLOW_DELAY,10\n"))), "PASS")
rec("G1 late PARM lever arm", run("g1lever", scratch("g1lever", lambda d: open(d + "/ukf_geometry.csv", "a").write(
    "warning_late_parm,30000,FLOW_POS_X,0.01\n"))), "PASS")
rec("G1 late PARM other (RNGFND2_MIN)", run("g1other", scratch("g1other", lambda d: open(d + "/ukf_geometry.csv", "a").write(
    "warning_late_parm,30000,RNGFND2_MIN,0.2\n"))), "FAIL: G1")
sh = G.read_shadow(BASE + "/ukf_shadow.csv")
g1_noarm = G.g1(BASE + "/ukf_geometry.csv", sh, None, need_arm=True)
res["G1 gated flight with no ARM record (function level)"] = {"pass": g1_noarm["pass"], "why": g1_noarm["why"],
                                                              "ok": g1_noarm["pass"] is False}
g1_h = G.g1(BASE + "/ukf_geometry.csv", sh, None, need_arm=False)
res["G1 H log with no ARM record (function level)"] = {"pass": g1_h["pass"], "ok": g1_h["pass"] is True,
                                                       "init_before_arming": g1_h["init_before_arming"]}
# G2
W0, W1 = json.load(open(BASE_SCORE))["window_s"]
def edit_rows(pred, fn):
    def e(d):
        lines = open(d + "/ukf_shadow.csv").read().splitlines(); hdr = lines[0].split(","); out = [lines[0]]
        for l in lines[1:]:
            v = l.split(","); t = int(v[0]) / 1e6
            if pred(t):
                v = fn(hdr, v)
                if v is None:
                    continue
            out.append(",".join(v))
        open(d + "/ukf_shadow.csv", "w").write("\n".join(out) + "\n")
    return e
mid = 0.5 * (W0 + W1)
rec("G2 coverage gap of 2 s inside W", run("g2gap", scratch("g2gap", edit_rows(lambda t: mid < t < mid + 2.0, lambda h, v: None))), "FAIL: G2")
def setcol(col, val):
    def f(h, v):
        v = list(v); v[h.index(col)] = val; return v
    return f
rec("G2 one row Healthy = 0", run("g2h", scratch("g2h", edit_rows(lambda t: abs(t - mid) < 0.02, setcol("Healthy", "0")))), "FAIL: G2")
rec("G2 one row FlowAgeMs = 5000", run("g2age", scratch("g2age", edit_rows(lambda t: abs(t - mid) < 0.02, setcol("FlowAgeMs", "5000")))), "FAIL: G2")
rec("G2 one row SS bit 3 clear", run("g2ss", scratch("g2ss", edit_rows(lambda t: abs(t - mid) < 0.02,
    lambda h, v: setcol("SS", str(int(v[h.index("SS")]) & ~8))(h, v)))), "FAIL: G2")
# G3
rec("G3 n_chol_fail = 1", run("g3fail", scratch("g3fail", lambda d: sub(d + "/ukf_stats.csv", "n_chol_fail,0", "n_chol_fail,1"))), "FAIL: G3")
rec("G3 ukf_stats.csv missing (rule 1)", run("g3miss", scratch("g3miss", lambda d: os.remove(d + "/ukf_stats.csv"))), "FAIL: G3")
# G4 (a score copy with the UKF error raised above the band)
s4 = json.load(open(BASE_SCORE)); k = s4["estimators"]["EKF3"]["evo_ape_a_se3"]["rmse_m"]
s4["estimators"]["UKF"]["evo_ape_a_se3"]["rmse_m"] = max(2 * k, k + 0.1) + 0.001
json.dump(s4, open(S + "/branch/score_g4.json", "w"))
rec("G4 UKF just above the band (edited score copy)", run("g4", scratch("g4"), score=S + "/branch/score_g4.json"), "FAIL: G4")
# G6
rec("G6 bands set below the observed differences", run("g6", scratch("g6"), extra=("--g6-bands", "1e-9", "1e-9", "1e-9", "1e-9")), "FAIL: G6")
# preconditions
rec("precondition: score of a different log", run("presha", scratch("presha"), score=CLA_SCORE), "FAIL: preconditions")
s5 = copy.deepcopy(json.load(open(BASE_SCORE))); s5["estimators"]["UKF"]["physical_record"] = "XUKO"
json.dump(s5, open(S + "/branch/score_phys.json", "w"))
rec("precondition: UKF row read from the onboard XUKO", run("prephys", scratch("prephys"), score=S + "/branch/score_phys.json"), "FAIL: preconditions")
# the set
fl = []
for i in range(4):
    run(f"F{i + 1}", scratch(f"F{i + 1}")); fl.append(f"{S}/branch/F{i + 1}.json")
st = G.gate_set(fl); res["set: 4 passing flights"] = {"verdict": st["verdict"], "ok": st["verdict"] == "PASS"}
st = G.gate_set(fl[:3] + [f"{S}/branch/g2gap.json"]); res["set: 3 passing + 1 failing"] = {"verdict": st["verdict"], "ok": st["verdict"] == "FAIL"}
st = G.gate_set(fl[:3]); res["set: 3 flights"] = {"verdict": st["verdict"], "ok": st["verdict"].startswith("NOT EVALUABLE")}
j = json.load(open(fl[3])); j["replay_binary_md5"] = "0" * 32; j["flight"] = "F4x"; json.dump(j, open(S + "/branch/F4x.json", "w"))
st = G.gate_set(fl[:3] + [S + "/branch/F4x.json"]); res["set: mixed binaries"] = {"verdict": st["verdict"], "ok": st["verdict"].startswith("INVALID")}
j["replay_binary_md5"] = None; json.dump(j, open(S + "/branch/F4n.json", "w"))
try:
    G.gate_set(fl[:3] + [S + "/branch/F4n.json"]); res["set: missing md5"] = {"ok": False}
except SystemExit as e:
    res["set: missing md5"] = {"refused": str(e), "ok": True}
try:
    G.gate_set(fl[:3] + [f"{S}/branch/F1.json"]); res["set: duplicate flight"] = {"ok": False}
except SystemExit as e:
    res["set: duplicate flight"] = {"refused": str(e), "ok": True}
try:
    run("hplumb", scratch("hplumb"), score=None); G.gate_set(fl[:3] + [f"{S}/branch/hplumb.json"]); res["set: H record refused"] = {"ok": False}
except SystemExit as e:
    res["set: H record refused"] = {"refused": str(e), "ok": True}
res["ALL_OK"] = all(v["ok"] for v in res.values())
json.dump(res, open(R + "/gate_branch_tests.json", "w"), indent=1)
for k, v in res.items():
    print(("OK  " if (v is True or (isinstance(v, dict) and v.get("ok"))) else "BAD ") + k, "" if isinstance(v, bool) else v.get("verdict", ""))
shutil.rmtree(S + "/branch")
