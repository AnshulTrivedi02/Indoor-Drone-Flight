# Handover, 2026-11-02: methodology fact sheets, final state (sheet 3.9 + updates)

**Branch:** `factsheets-final`, reset from `fwd-camera` at `4861f3d` (the E6 merge). This handover covers two rounds
of work: an initial pass (committed `96c5d63`, `26d0d28`) and a second review round that found the initial pass's
checker was too permissive and several of 3.9's narrative citations pointed at the wrong line of the right file
(content was never actually read for them, only line-existence). The second round is not yet committed as of this
file; see "Commit plan" at the end.

## What was done (both rounds combined)

- **New sheet** `docs/thesis/methodology_factsheets/3.9_extension_experiments.md`, "3.9 Extension experiments E2–E6
  and the attribution ablation". One `### ` subsection each for E2, E3, E4, E5, E6 and the attribution ablation
  (EXPLORATORY), each with: purpose (one line), recordings, arms, metrics, pre-registration (file:line and date,
  every amendment/clarification dated and cited at its own line), gates, and labels (verdicts exactly as worded,
  with counts, cited to the results file and `numbers_tier1.md`). Plus Appendix candidates, Flags (a) and Flags (b).
- **Updated existing sheets** for facts the extensions changed or added (no existing bullet deleted): `3.3`
  (+3: E3's robust tag-factor FGO variant, E5's landmark UKF design, E6's `--tag-map` flag), `3.4` (+3: offline
  replay as the E2–E6/ablation mode, E6's map-supplied replay sub-mode, the one-job-at-a-time `heavy.py`
  discipline), `3.6` (+6: tier-1 verdict vocabulary, map error, gap retention R, effective mislabel rate, E6's
  band method, a pointer to 3.9), `3.7` (+5: the tier-1 checksum guard, supplementary code snapshots,
  reproduction-gate pattern, exact cross-check scripts, the ablation's own identity gate). `3.5` kept its bullet
  count but had several citations and one value fixed, plus one addition (`numbers.md:464`). `3.1`/`3.2`/`3.8` had
  no fact the extensions changed (3.2 got one unrelated line-drift fix, below).
- **New checker** `docs/thesis/methodology_factsheets/check_factsheets.py` (stdlib only, read-only). Checks, for
  every sheet: (a) every citation resolves to an existing file and line range; (b) numeric-token matching, in
  **strict** mode for Facts/Appendix bullets this pass's `git diff` against `4861f3d` touched (only a direct
  numbers.md/numbers_tier1.md citation, or a citation inside a `[NOT IN ...]` tag, counts; an untagged claimed
  number in a touched bullet is itself a failure), and **lenient** mode everywhere else (Flags sections by design,
  and any bullet this pass did not touch — reported if untagged, never failed, since it predates this pass). See
  "What the second round changed", below, for why strict mode was added.
- **README.md** rewritten: base commit `4861f3d`, 3.9 added to the index, recomputed counts table, the NOT-IN
  bracket count and groups rebuilt, the most-important-flags list extended, and a new "how re-verification was
  actually scoped" paragraph that states plainly what was and was not content-checked (see below).

## What the second-round review found, and what changed because of it

The first round's checker only checked that a cited line **existed**; it never actually read the cited line's
content against what a hand-estimated citation *claimed*, except where a numeric token happened to fail a
substring match. Three classes of problem followed from that gap, each now fixed:

1. **Several of 3.9's own citations pointed at the wrong line of the right file** — drafted from memory/estimate
   while writing the sheet, never read back. Found by hand (`awk 'NR>=a && NR<=b {print NR": "$0}' <file>` on each
   one) and fixed, 13 in total:
   - `e2_results.md`: the deviation note (:30-31 → :17-18) and the guard result (:122-124 → :166-167);
   - `e5_results.md`: "all six exited 0" (:17-18 → :38);
   - `e6_results.md`: the pairing note (:8-9 → :15-16), S-E6 (:16 → :24), and the plain-language reading — the
     original citation (:126-141) was actually §5 Limitations, not §4 Reading (→ :99-123);
   - `tier1/preregistration.md`: the thesis-names sentence (:40-41 → :48-49);
   - `e6_preregistration.md`: the thesis-names sentence (:22 → :23-24);
   - `ablation/preregistration.md`: the identity gate (:17-19, which is actually the "cap 100" labelling text, →
     :24-25) and the P1 weak-test caveat (:199-203, the §7 header and notation block, → :209-211).
   None of these affected a verdict, a count, or a pre-registration date — they were all narrative-fact citations
   pointing one paragraph away from the intended one. All are now content-verified, not just line-existence-checked.
2. **The lenient "any citation in the bullet counts" rule hid real sourcing gaps**, because a bullet citing a
   non-numbers-file (M:, a code file, a pre-registration/results file) for one number let *every other* number in
   the same bullet piggyback on that citation's resolution, without the content actually matching. Fixed by adding
   the strict mode described above, scoped to this pass's own touched bullets (so it does not retroactively demand
   a standard from 3.1–3.8 bullets nobody has re-verified since 2026-10-17/2026-10-24). Running strict mode surfaced
   **49 further sourcing gaps** across 3.2–3.4, 3.7 and 3.9 (one per affected number or untagged bullet); each was
   fixed by either citing the correct `numbers_tier1.md`/`numbers.md` line, or adding a `[NOT IN numbers ...]` tag
   to the file that actually states the value (criterion-bound and design-value citations into a pre-registration
   or design file; the ablation's own numbers, which live only in `ablation_numbers.md`). Two of these were also
   **wording fixes to avoid a false match**, not sourcing gaps: "Experiment 2/3" → "Experiment 2 and Experiment 3"
   (twice, 3.4/3.9 — "2/3" parsed as a fraction token) and "2026-10-22/23" → "2026-10-22 to 2026-10-23" (3.9 — parsed
   as "22/23"). One further value correction, not just a citation fix: **3.3's "24×/42×" is replaced by "×24.7/×42"**,
   the source's (M:12408-12415) own figures.
3. **Three bullets were only commentary, not two-source conflicts, so they did not belong in Flags (b).** The E6
   band-method item, the E2 P-E2.5 item and the ablation P1 weak-test item each restate or combine facts from a
   single source, rather than showing two sources disagreeing. Moved to Appendix candidates in 3.9, reworded to
   read as a note rather than a flag. Only the "NOT MET" item remained a genuine Flags (b) conflict; it now also
   cites D50/D76 (`tier1/decisions_log.md:76, 102`), which already partly settled the analogous question for the
   main-experiment summary pages (the extension pages print the registered word, not a paraphrase) — recorded as
   "partly already ruled, not fully open" rather than left as a fresh open conflict.
4. **Two content fixes beyond citations**, raised in review and applied:
   - 3.4/README: E6 adds **5** new flights, not 4 — `E6M_fig8_r1` was flown, found "unusable" by the IMU-gap rule,
     and re-flown as `r1b` (`numbers_tier1.md:627-633`); the flights table lists 5 rows.
   - 3.9's intro: "no estimator code is changed to produce a primary verdict" was wrong for E5/E6, whose verdicts
     come from genuinely new modules (the landmark UKF; `--tag-map`). Reworded to "no EXISTING code path is
     changed" and added that the new modules are validated by a tolerance or an identity gate, not edited into the
     unchanged path.
   - 3.9's E5 Arms bullet wrongly attributed the landmark UKF to `src/estimators/e6_map.py` (that is E6's code,
     written later for a different purpose). Corrected to name only `ukf_lm.py`/`lc_ukf_replay.py`.
   - The ablation Arms bullet's "Cauchy-gate-off Huber kernel" was garbled; reworded to "a Huber kernel (k = 1.345)
     that also sets the heading gate to infinity" (the actual mechanism, per `ablation/preregistration.md:88-118`).
5. **The README's "re-verification" framing overclaimed.** It originally implied every citation in all nine sheets
   had been content-checked; in fact only (a) line-existence was checked everywhere, and (b) content-matching was
   checked in full only for bullets this pass touched (now strict), with pre-existing untouched bullets checked to
   whatever standard the *original* 2026-10-17/2026-10-24 passes used (a digit-string pass, per their own
   handovers) — not re-verified line-by-line against `4861f3d` by this pass. The README now says this explicitly,
   and `check_factsheets.py` reports (without failing on) 67 pre-existing untouched bullets across the nine sheets
   that have a claimed number with no numbers-file/NOT-IN source at all — these are out of this pass's scope, not
   silently fine. **This is a real, acknowledged limit of what was verified**, not a loose end to close; closing it
   would mean re-deriving every citation in 3.1–3.8 from its primary source, which is a different, much larger task.

## Checker totals (final, this handover)

```
TOTAL bullets=583 citations=1609 citation_failures=0 tokens=716 token_failures=0 untouched_untagged_reported_only=67
TOTAL RESULT: PASS
```

Per-sheet bullet counts (Facts/Appendix/Flags-a/Flags-b), before (`337c931`/`4c783b5`) → after (this handover; the
Appendix/Flags split in 3.9 shifted between the first and second round because of the reclassification in point 3
above — the Facts count did not change):

- 3.1: 34/10/8/3 → unchanged
- 3.2: 40/13/8/9 → unchanged (one line-drift citation fixed; no bullet count change)
- 3.3: 49/17/16/10 → 52/17/16/10 (+3 Facts)
- 3.4: 23/8/6/4 → 26/8/6/4 (+3 Facts)
- 3.5: 40/14/18/8 → unchanged (citations/value fixed, no bullet count change)
- 3.6: 30/11/9/8 → 36/11/9/8 (+6 Facts)
- 3.7: 34/10/6/5 → 39/10/6/5 (+5 Facts)
- 3.8: 32/8/7/4 → unchanged
- 3.9: new → 48/11/4/1
- **Total: 282/91/78/51 (502) → 347/102/82/52 (583)**

(The grand total is 583, one less than the first round's reported 584, purely because of a counting detail from the
Flags-(b)→Appendix reclassification in 3.9 interacting with how the uncited cross-reference bullet at the top of
3.9's original Flags (a) — which had no citation at all — was dropped rather than fixed; see git diff.)

## Other checks run (not touched by this pass; still pass)

- `python3 tools/check_numbers_frozen.py` → PASS.
- `python3 docs/thesis/tier1/check_claims_applied.py` → **58/58**. This broke once during the first round (an edit
  to 3.3's E4 bullet moved text inside the literal substring `(P-E4.2 PASS)` the checker asserts) and was fixed by
  moving the added citation outside that exact parenthetical. Re-checked after every subsequent edit in the second
  round; stayed at 58/58 throughout.
- `python3 docs/thesis/ablation/check_discussion.py` → 18/18.
- `python3 docs/thesis/tier1/e6/check_e6_prose.py` → 68 checks, 100 pairs, 0 mismatches.

## FS decisions (coordinator assigns D-numbers at merge)

- **FS-1.** Sheet 3.9 structure: one `### ` subsection per experiment under a single `## Facts` section, so the
  bullet-counting convention (keyed on the four `##` section names) works unchanged.
- **FS-2.** A claim-pass NOT-IN tag whose value is now directly in `numbers_tier1.md` (which didn't exist when the
  tag was written) became a direct citation instead of staying "NOT IN" — the E2/E3/E5 Facts bullets in 3.5. The
  separate H1.3 bullet is a **Flags (b)** item, not Facts, and correctly keeps citing `thesis_vocabulary.md:150`
  and `M:3447` directly under the lenient rule (a Flags bullet's job is to cite two disagreeing sources, which are
  not required to be numbers-file sources) — I did not wrap it as NOT-IN, since that would misrepresent it as a
  Facts-style numeric claim rather than the documented gap it is.
- **FS-3.** `3.4`'s and `3.6`'s stray trailing `</content>`/`</invoke>` lines (a tool-output leak baked into the
  committed file since 2026-10-17) were removed while editing both files anyway. No bullet content was lost.
- **FS-4.** The "27–28 ms" / cap-10-convergence bullets in `3.3` (E4) keep their rounded wording verbatim
  (`check_claims_applied.py` asserts the exact substrings), with a direct `numbers_tier1.md` citation added
  alongside the pre-existing `tier1/e4_results.md` section reference.
- **FS-5.** The historical "49 tags" NOT-IN count in the original README predates the `4c783b5` claims pass, which
  added NOT-IN tags of its own without updating that count — it was already stale before this task started. I
  listed the current, complete set (78 brackets, grep-counted, by group) rather than reconciling an
  un-reconstructable historical total.
- **FS-6 (new, second round).** Where a sourcing gap was in **narrative** text (a date, a rate label, a window
  value) rather than a **result**, I preferred rewording to remove the ambiguous digit pattern (e.g. "2026-10-22 to
  2026-10-23") over adding a citation, when no clean source line existed for the exact string as written. Where a
  clean source line did exist (even in a pre-registration/design file, not a numbers file), I added a `[NOT IN
  numbers ...]` tag rather than reword, to keep the number traceable.

## Conflicts for the coordinator to rule on (Flags (b))

1. **"NOT MET" has two different, colliding meanings** — main-experiment vocabulary (a pre-registered rule applied,
   giving a "no ordering" outcome, `thesis_vocabulary.md:530`) vs the tier-1 extensions' narrower sense
   ("insufficient data": a crashed run or failed gate only; FAIL otherwise, `tier1/preregistration.md:168-180`).
   E3's 2026-10-22 ruling used the main-experiment sense for a genuinely diverged run and was clarified the same
   day to the tier-1 FAIL sense (`tier1/preregistration.md:409-424`). D50/D76 already print the registered word on
   the main-experiment summary pages, so this is **partly ruled, not fully open** — but no single document states
   the general rule for comparing the two senses. Recorded in 3.6 and 3.9.
2. **No new conflict was found between the extension experiments and the main thesis's existing claims** beyond
   what `4c783b5`/`claims_applied.md` already resolved (C1–C5). E6's map-reuse question is scoped to condition A
   with correct tag IDs only, so it doesn't reopen E2's or E3's scoping.

(The E6 band-method item, the E2 P-E2.5 item and the ablation P1 band item, listed as conflicts in the first-round
version of this handover, are **not** conflicts on review — see point 3 above — and are now in 3.9's Appendix
candidates instead. Withdrawn from this list.)

## Citations I could not fully verify

- None, **within this pass's scope as now stated above**: every citation this pass added or edited — including the
  13 found wrong on review and the further 49 surfaced by strict mode — was read back against the actual file
  content at `4861f3d`, not assumed from a drafted estimate.
- **What remains genuinely unverified, stated plainly rather than implied to be fine:** 67 pre-existing bullets
  across the nine sheets (mostly 3.1, 3.5, 3.8, which this pass did not substantively edit) carry a claimed number
  with no numbers-file or NOT-IN citation at all, under the strict standard this pass now applies to its own work.
  `check_factsheets.py` reports these per sheet without failing on them, by design (see "What the second-round
  review found", point 2). Re-deriving all of them against primary sources is out of scope for this task.
- The soft pragmatic-scope caveat from the first round still applies: bare small integers (tag counts, seed
  numbers, lap counts) are not token-checked at all, by the brief's own "pragmatic" instruction.

## Files changed (both rounds)

- `docs/thesis/methodology_factsheets/3.2_simulation.md` (1 line-drift fix)
- `docs/thesis/methodology_factsheets/3.3_estimators.md` (+3 Facts; several citation and one value fix)
- `docs/thesis/methodology_factsheets/3.4_run_modes.md` (+3 Facts; stray-tag cleanup; flight-count fix)
- `docs/thesis/methodology_factsheets/3.5_experiments.md` (citation/value fixes; one addition; no bullet-count change)
- `docs/thesis/methodology_factsheets/3.6_metrics_statistics.md` (+6 Facts; 1 citation fix; stray-tag cleanup)
- `docs/thesis/methodology_factsheets/3.7_verification.md` (+5 Facts)
- `docs/thesis/methodology_factsheets/3.9_extension_experiments.md` (new; 13 citation fixes and several content
  fixes applied after the first-round draft, on review)
- `docs/thesis/methodology_factsheets/check_factsheets.py` (new; strict/lenient split added on review)
- `docs/thesis/methodology_factsheets/README.md` (rewritten; re-verification scope stated explicitly; counts/flags
  updated for the second round)
- `docs/handovers/2026-11-02_factsheets_final.md` (this file)

Not touched: `numbers.md`, `numbers_tier1.md`, `decisions_log.md`, `limitations.md`, `METHODOLOGY.md`, the
vocabulary/definitions files, any results file, PDF, generator or the frozen pack.

## Commit plan

The first round was committed as `96c5d63` (sheets + checker) and `26d0d28` (this handover's first draft). The
second round's changes (13 citation fixes in 3.9, strict/lenient checker split, 3 content fixes, the Flags (b)
reclassification, the 5-vs-4-flights fix, and this rewritten handover) are committed as one further commit on
`factsheets-final`, after re-running the idle check and all five checks one last time.
