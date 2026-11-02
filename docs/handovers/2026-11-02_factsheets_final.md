# Handover, 2026-11-02: methodology fact sheets, final state (sheet 3.9 + updates)

**Branch:** `factsheets-final`, reset from `fwd-camera` at `4861f3d` (the E6 merge). Commit: `96c5d63`.

## What was done

- **New sheet** `docs/thesis/methodology_factsheets/3.9_extension_experiments.md`, "3.9 Extension experiments E2–E6
  and the attribution ablation". One `### ` subsection each for E2, E3, E4, E5, E6 and the attribution ablation
  (EXPLORATORY), each with: purpose (one line), recordings (which bags, n, new flights vs replays), arms, metrics,
  pre-registration (file:line and date, every amendment/clarification dated and cited at its own line), gates (and
  how each came out), and labels (verdicts exactly as worded, with counts, cited to the results file and
  `numbers_tier1.md`). Plus Appendix candidates, Flags (a) and Flags (b) sections.
- **Updated existing sheets** for facts the extensions changed or added (no existing bullet deleted):
  - `3.3_estimators.md`: three new facts (E3's robust tag-factor FGO variant, E5's landmark UKF design, E6's
    `--tag-map` flag), plus citation fixes (below).
  - `3.4_run_modes.md`: three new facts (offline replay as the E2–E6/ablation mode; E6's map-supplied replay
    sub-mode; the one-job-at-a-time `heavy.py` discipline).
  - `3.6_metrics_statistics.md`: six new facts (the tier-1 verdict vocabulary; map error; gap retention R; effective
    mislabel rate; E6's two-sided range-band method; a pointer to 3.9).
  - `3.7_verification.md`: five new facts (the tier-1 checksum guard; supplementary code snapshots for E5/E6;
    reproduction gates G0-L/G0-UKF/G-E4/G-E4′; the per-experiment exact cross-check scripts; the ablation's own
    identity gate).
  - `3.1`, `3.2`, `3.5`, `3.8` checked for extension-related facts: 3.5's loop-closure claim scope (C1–C3) was
    already applied at `4c783b5` and only needed its citations fixed (see below); 3.1/3.2/3.8 had nothing the
    extensions changed, so no new bullet was added to them.
- **New checker** `docs/thesis/methodology_factsheets/check_factsheets.py` (stdlib only, read-only). For every
  `3.*.md` sheet it: (a) resolves every `file:line`/`file:a-b` citation against this worktree; (b) for every bullet
  carrying a `numbers.md`/`numbers_tier1.md` citation or a `[NOT IN …]` tag, checks every "claimed" numeric token
  (decimals, k/n counts, thousands-grouped integers, bare `%`/`°`/`×` integers) against the text of every citation's
  line in that bullet (any resolved citation, not only the numbers-file one — a token sourced only from a direct
  `M:`/code citation in the same bullet is not re-demanded of the numbers file); (c) prints per-sheet and TOTAL
  counts. Run: **TOTAL bullets=584 citations=1590 (0 failed) tokens=667 (0 failed), PASS**.
- **README.md** rewritten: base commit `4861f3d`, 3.9 added to the index, recomputed counts table (347 facts / 99
  appendix / 83 (a) / 55 (b) = 584 total, up from 502), the NOT-IN tags list rebuilt from the current sheets (58
  tags), and the most-important-flags list extended.

## Checker totals (final, after every fix)

```
TOTAL bullets=584 citations=1590 citation_failures=0 tokens=667 token_failures=0
TOTAL RESULT: PASS
```

Per-sheet bullet counts (Facts/Appendix/Flags-a/Flags-b), before (at `337c931`/`4c783b5`) → after:
- 3.1: 34/10/8/3 → unchanged (not touched)
- 3.2: 40/13/8/9 → unchanged (citation fix only, no bullet count change)
- 3.3: 49/17/16/10 → 52/17/16/10 (+3 facts)
- 3.4: 23/8/6/4 → 26/8/6/4 (+3 facts)
- 3.5: 40/14/18/8 → unchanged (citation fixes only)
- 3.6: 30/11/9/8 → 36/11/9/8 (+6 facts)
- 3.7: 34/10/6/5 → 39/10/6/5 (+5 facts)
- 3.8: 32/8/7/4 → unchanged (not touched)
- 3.9: new → 48/8/5/4
- **Total: 282/91/78/51 (502) → 347/99/83/55 (584)**

## Other checks run (not touched by this pass; still pass)

- `python3 tools/check_numbers_frozen.py` → PASS.
- `python3 docs/thesis/tier1/check_claims_applied.py` → **58/58** (confirmed unbroken; one edit to 3.3's E4 bullet
  initially broke the literal substring `(P-E4.2 PASS)` the checker asserts — fixed by moving the added citation
  outside that exact parenthetical; re-ran to 58/58 afterwards. This is the one genuine regression risk this task
  carried, and it's now closed.)
- `python3 docs/thesis/ablation/check_discussion.py` → 18/18.
- `python3 docs/thesis/tier1/e6/check_e6_prose.py` → 68 checks, 100 pairs, 0 mismatches.

## Line-drift fixes (pre-existing, found by the checker, not introduced by this pass)

1. `eval/cruise_window.py:10-37` → `:10-33` (3.6; file is now 33 lines).
2. `M:4569-4575` → `M:4569-4576` (3.2; the roll-gain `_D` old/new values sit one line further down).
3. `ukf_core.py:313-314` → `:314-315` (3.3; UKF initial bias σ).
4. `fgo_core.py:38-39` → `:39-40` (3.3; FGO initial bias σ, same cause).
5. `thesis_vocabulary.md:145` → `:150` (3.5; H1.3 wording moved; `:145` is now blank at this commit).
6. `M:1711-1716, M:1857-1862` (3.5; P4 FGO dejittered-baseline band) — the actual "0.40 m floor" sentence is at
   `M:1869`, outside both cited ranges; added rather than replaced, since the original ranges still cover other
   parts of the same bullet correctly.
7. `thesis_values_provenance.md` "row 20" (3.5, S-A2 bound) had no line number at all; added `:78`.

All seven are stale citations that predate this task (most from the `337c931` creation pass or the `4c783b5` claims
pass); none is a new error introduced here. Fixing them required re-reading the actual source line, not just
shifting by a guessed offset — my first attempt at the B1–B5 bullet in 3.6 (`M:4953`/`:4958`/`:4966`) assumed a
drift that turned out not to exist; I reverted that one after checking with `awk 'NR==…'` directly.

## FS decisions (coordinator assigns D-numbers at merge)

- **FS-1.** Sheet 3.9 structure: one `### ` subsection per experiment under a single `## Facts` section (not six
  separate `##` sections), so the existing bullet-counting convention (which keys on the four `##` section names)
  continues to work unchanged, as the advisor suggested before writing.
- **FS-2.** Where a claim-pass NOT-IN tag's underlying number turned out to already be in `numbers_tier1.md`
  (because that file didn't exist when the tag was written), I replaced the tag with a direct citation rather than
  keeping it as "NOT IN" — e.g. the E2/E3/E5 bullets in 3.5, and the H1.3 bullet. Kept as NOT-IN only where the
  exact value genuinely isn't in `numbers.md`/`numbers_tier1.md` even now (e.g. the ablation's own verdicts, which
  live only in `ablation_numbers.md`, and criterion bounds that live only in a pre-registration file or
  METHODOLOGY).
- **FS-3.** `3.4`'s and `3.6`'s stray trailing `</content>`/`</invoke>` lines (a tool-output leak baked into the
  committed file since the original 2026-10-17 pass) were removed, since I was already editing both files and
  leaving a non-content artefact in a "FINAL-STATE facts only" sheet seemed worse than a one-line cleanup. No bullet
  content was lost — the last real bullet in each file was already a complete sentence.
- **FS-4.** The two "27–28 ms" / cap-10-convergence bullets in `3.3` (E4) keep their rounded wording verbatim
  (`check_claims_applied.py` asserts the exact substrings), with a direct `numbers_tier1.md` citation added
  alongside the pre-existing `tier1/e4_results.md` section reference, rather than rewording to an exact-match figure
  that would break the claims-applied check.
- **FS-5.** I did not attempt to reproduce the original "49 tags" NOT-IN count as a single historical number in the
  README; that count predates the `4c783b5` claims pass (which added NOT-IN tags of its own without updating the
  README) and was already stale before this task started. I instead listed the current, complete set (58 tags,
  grep-counted and individually resolved by the checker) and called out what changed in this pass as its own
  group, rather than reconciling an un-reconstructable historical total.

## Conflicts for the coordinator to rule on (Flags (b), newly identified in this pass)

1. **"NOT MET" has two different, colliding meanings.** The main-experiment thesis vocabulary (`thesis_vocabulary.md:530`)
   defines "NOT MET" as a pre-registered rule that was applied and gave a "no ordering" outcome — a normal, expected
   result category. The tier-1 extensions' `preregistration.md` §0.5 (`tier1/preregistration.md:168-180`) defines it
   narrowly as "insufficient data" (a crashed run or failed gate only); a criterion whose stated count wasn't reached
   is **FAIL**, not NOT MET, under that scheme. E3's own 2026-10-22 ruling used the main-experiment sense for a
   genuinely diverged run and was clarified the same day, in writing, to the tier-1 FAIL sense
   (`tier1/preregistration.md:409-424`). Both wordings are on the record in `preregistration.md` itself (the
   original text is kept, marked superseded). I recorded this in 3.6 and 3.9's own Flags (b); it should probably be
   resolved once, centrally, by the coordinator (e.g. in the vocabulary or `methodology_definitions_draft.md`),
   since it will recur anywhere a reader compares a main-experiment NOT MET with a tier-1 one.
2. **E6's P2 bands conflate a computed number with a judgement method.** The band edges themselves
   ([0.016691, 0.023695] m FGO; [0.033011, 0.040785] m UKF) are exact, computed from the stored repeat spread. The
   *method* that produced them — one range-width added on each side — is itself pre-registered as "judgement, not
   derived from data" (D87). Recorded as a Flags (b) item in 3.9; not something this pass could or should resolve,
   since it's a property of the pre-registration itself, not a documentation error.
3. **No new conflict was found between the extension experiments and the main thesis's existing claims** beyond
   what `4c783b5`/`claims_applied.md` already resolved (C1–C5). E6's map-reuse question is scoped to condition A
   with correct tag IDs only, so it doesn't reopen E2's or E3's scoping.

## Citations I could not fully verify

- None outstanding. Every citation added or edited in this pass was checked against the actual file content at
  `4861f3d` (not assumed from memory or from the earlier `337c931` line numbers), and every bullet with a
  numbers-file source now has its numeric tokens matched by `check_factsheets.py`.
- One soft caveat: the checker's token-matching is pragmatic by design (decimals, k/n counts, thousands-grouped and
  bare `%`/`°`/`×` integers only — bare small integers like tag counts or seed numbers are not checked, per the
  brief's own "pragmatic" instruction). A handful of bullets state small integer facts (e.g. "8 tags", "3 circuits")
  that are not independently re-verified against a numbers file by the script; I read these directly from the
  tier-1 source files while drafting 3.9 and believe them accurate, but they are not mechanically checked the way
  the decimal/ratio/count figures are.

## Files changed

- `docs/thesis/methodology_factsheets/3.2_simulation.md` (1-line citation fix)
- `docs/thesis/methodology_factsheets/3.3_estimators.md` (+3 facts, several citation fixes)
- `docs/thesis/methodology_factsheets/3.4_run_modes.md` (+3 facts, stray-tag cleanup)
- `docs/thesis/methodology_factsheets/3.5_experiments.md` (citation fixes only, no new facts)
- `docs/thesis/methodology_factsheets/3.6_metrics_statistics.md` (+6 facts, 1 citation fix, stray-tag cleanup)
- `docs/thesis/methodology_factsheets/3.7_verification.md` (+5 facts)
- `docs/thesis/methodology_factsheets/3.9_extension_experiments.md` (new)
- `docs/thesis/methodology_factsheets/check_factsheets.py` (new)
- `docs/thesis/methodology_factsheets/README.md` (rewritten: base commit, index, counts, NOT-IN list, flags)
- `docs/handovers/2026-11-02_factsheets_final.md` (this file)

Not touched: `numbers.md`, `numbers_tier1.md`, `decisions_log.md`, `limitations.md`, `METHODOLOGY.md`, the
vocabulary/definitions files, any results file, PDF, generator or the frozen pack.
