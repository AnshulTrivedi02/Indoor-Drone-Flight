# Methodology chapter: conventions for reporting results — DRAFT FOR THE USER

*DRAFT, 2026-10-16. Branch `fwd-camera` at `6a0fa0f`. A new file; nothing else was edited. Each definition below is built
from how the project's own rulings and records used the term. **It is not an external or textbook definition.** "M" means
`METHODOLOGY.md`, followed by its line number.*

The repository uses these terms many times without ever defining them. Counts in `METHODOLOGY.md` (case-insensitive):

| term | count |
|---|---|
| "as worded" | 118 |
| "descriptive" | 30 |
| "confirmatory" | 25 |
| "withdrawn" / "withdraw" | 19 |
| "post hoc" / "post-hoc" | 18 |
| "exploratory" | 18 |

`glossary_flags.md:116` and `:168` list "as worded" and "post hoc" as UNDEFINED, and `glossary_flags.md:1170` asks for them
to be defined once in the methodology chapter. The paragraphs below are drafted for that purpose.

---

## As worded

**Draft definition.** A criterion is scored *as worded* when it is applied exactly as it was written before the data were
seen. This holds even when, after scoring, the wording turns out to be faulty, ambiguous or to measure something other
than what was intended. The literal verdict is recorded and never re-scored. Any explanation of a fault is stated beside
the verdict, not in place of it.

**How the rulings used it:**
- Applied to a primary band: `fwdc_tex_r2` was "recorded as a PRIMARY MISS as worded, not re-scored", though it missed by
  0.01 m in the better direction (M:5332-5336).
- Applied to blank-floor P4 misses, where the band measured runaway size and not sensing (M:5338-5345).
- Applied to the re-lock criterion P-H6 after a measurement-definition fault was found (M:10798, M:10836).
- Applied to the safety criterion S-A2 of UKF (b), whose bound assumed that flow stops at the kill: "BOTH runs … stay
  recorded as FAILED AS WORDED" (M:13667).

**Usage varied in four ways:**
1. **Failed as worded despite a known fault in the wording.** The main use (above; also M:3447, M:3461, M:8432, M:8439).
2. **Accepted as worded by a later ruling.** A verdict that flipped in a re-run is accepted in its literal form: "F3c (b):
   TRUE accepted as worded, flagged FRAGILE" (M:13362); "F2 (NOT met → MET) and F3c (b) (TRUE → FALSE) are accepted as
   worded" (M:12799).
3. **Committed in advance to be recorded "as worded, whatever it shows".** Used before a run (M:11100, M:11420).
4. **Passed as worded.** Used for passes, to show that no re-reading was needed (M:5754, M:13690, M:14155).

In every use the verdict is the literal one. The phrase never marks a re-scored verdict.

---

## Post hoc

**Draft definition.** An analysis, check or acceptance form is *post hoc* when it was chosen after the relevant results
had been seen.
- Such an analysis is always labelled "POST HOC" where it is reported.
- It is never presented as a pre-registered pass.
- It can explain or bound a pre-registered verdict, but it does not replace it.

**How the rulings used it:**
- A post-hoc condition check showing zero valid flow frames on every blank flight, "clearly labelled POST HOC", sits beside
  the as-worded P4 misses it explains (M:5343).
- A diagnostic build option added after the results "is a post-hoc diagnosis, not a pre-registered pass" (M:10756).
- The H "effective" drift and re-lock metrics are "POST HOC, labelled; both kept" (M:10849).
- The corrected-FGO contact-prediction replay is "a post-hoc consistency check: the flight has already flown, so it is not
  a prediction" (M:12696). It is reported as DESCRIPTIVE (post hoc) in `numbers.md:467`.
- An outlier "is not removed post hoc" (M:6354).

**Usage varied in two ways:**
- **A post-hoc form can be accepted by ruling.** "E5: failed as worded; accepted post hoc on increments (ruled)" (M:13800;
  also M:13496).
- **The label stays on the result, but the result counts.** "B6b's repeat pass stays recorded as POST HOC" (M:13907).
- **The term also describes a risk.** The U10 band "must be PRE-REGISTERED before rung-1 day 3, or the gate becomes post
  hoc" (M:13743).

The thesis should say which applies each time: "post hoc, not a result", or "post hoc, accepted by ruling".

---

## Descriptive

**Draft definition.** A result is *descriptive* when it reports what was observed but makes no claim that would need a
test or a pre-registered decision rule. Typical cases are an ordering of means, a per-flight count, or a comparison of
separate flights. A descriptive result is stated with its sample size. It is never worded as an ordering ("X is better"),
and it is shown beside the confirmatory result where one exists.

**How the rulings used it:**
- "The main textured corridor means (FGO 3.44, UKF 3.59, EKF3 4.00 m) are DESCRIPTIVE ONLY, alongside the confirmatory 'no
  ordering claimed'" (M:13371).
- "T, condition D: the ordering … is descriptive only (n = 3)" (M:12803).
- The UKF's textured median is "descriptive; no pre-registered UKF ordering test" (M:7187).
- Closed-loop sets flown on different flights are compared "DESCRIPTIVE only (n = 1 per estimator; different flights, so no
  ordering claim)" (M:9332; also M:9355).

**Usage varied in two ways:**
1. **Paired with "exploratory".** The label marks an unregistered mechanism study: "EXPLORATORY, descriptive" (M:9401);
   "supported, descriptively" (M:9453).
2. **Applied to the non-decision parts of a pre-registered test.** "Descriptive comparison … (pre-registered; n = 3 each,
   different flights, no decision)" (M:9915), and the outcomes of F1 other than its decision rule (M:8433). Here the
   comparison was registered, but as reported with no decision.

`numbers.md` uses "DESCRIPTIVE" as a status column value (`numbers.md:236, 468, 492`), in both senses.

---

## Confirmatory

**Draft definition.** A test is *confirmatory* when it meets three conditions:
1. Its hypothesis, its data set and its decision rule were all fixed before the data were collected.
2. The data set is separate from the data on which the hypothesis was formed.
3. Only the verdict that the rule produces may be claimed. That verdict is either the claim, the mirror claim, or "no
   ordering claimed".

**How the rulings used it.** The project has exactly one test labelled confirmatory: the EKF3-vs-FGO ordering on the
textured floor (H1.1).
- It was registered on seven new flights, r4–r10, because "testing it on the same three flights would be circular"
  (M:5644-5646).
- Its rule requires both a sign count and a 95% interval (M:5649-5656). The pre-registered alternative is "no ordering is
  claimed" (M:5654).
- When it was re-run with the corrected FGO under the original rule, the new verdict "REPLACES the old one" (M:12794).
  "EKF3 beats the FGO on standard sensors" was withdrawn (M:12796).

**Usage varied in two ways:**
1. **"Confirmation" for a primary rule's pass.** Elsewhere the word is used for a pre-registered primary rule in general:
   "A P1 miss is a failure of the confirmation as worded" (M:9742, plan step 2(a)).
2. **As the contrast to exploratory work.** "It is EXPLORATORY and carries no confirmatory weight" (M:8934; also M:9464).

The thesis could reserve "confirmatory" for H1.1 and call every other registered rule "pre-registered". Alternatively it
could adopt the broader use. **This is a choice for the user.**

---

## Exploratory

**Draft definition.** An analysis is *exploratory* when it was not pre-registered. It is undertaken to look for a pattern
or mechanism. It is labelled EXPLORATORY where it is reported, carries no confirmatory weight, and may motivate a later
pre-registered test but cannot be one.

**How the rulings used it:**
- "F1 EXPLORATORY (not pre-registered): robust FGO against the hard-gated FGO, same bags" (M:8460; announced at M:8436).
- "EXPLORATORY (bounded 1 h; not pre-registered)" for the C0/F2 pattern (M:8731). It was ruled "recorded as reported … It is
  EXPLORATORY and carries no confirmatory weight" (M:8927-8934).
- The D26 diagnosis: "EXPLORATORY; no confirmatory weight" (M:9464).
- An exploratory result was then tested: "the exploratory F1 benefit of robust weighting largely did not replicate on fresh
  flights" (M:9967), the replication being plan step 2(a) (M:9729).

**Usage varied in two ways:**
- **Before any amendment.** In the real-flight timing work, "EXPLORATORY" marks a same-bag replay "labelled as seen before
  any amendment" (M:11102, M:11422). There it records *when* the analysis was seen, not only that it was unregistered.
- **As a status value.** `numbers.md` uses "DESCRIPTIVE (EXPLORATORY)" as a status value (`numbers.md:480-481`).

---

## Withdrawn

**Draft definition.** A claim is *withdrawn* when a later ruling finds it no longer supported, usually because the
analysis behind it is shown to be invalid.
- The claim is no longer made anywhere in the thesis.
- It is not deleted from the record. Earlier entries stay as written and are read as superseded.
- Where it was a verdict, the replacing verdict is stated.

**How the rulings used it:**
- "'EKF3 beats the FGO on standard sensors' is WITHDRAWN everywhere" (M:12796). The correction note names where it appears
  and leaves those entries unedited (M:12820-12827).
- "'FGO batch ~2× better than RTS-UKF' is WITHDRAWN" (M:12800), and "It stays withdrawn" (M:13298).
- The claims table uses WITHDRAWN as one of its three statuses (`headline_claims_before_after.md:9`): 3 rows withdrawn.
- `numbers.md` keeps withdrawn rows in place, marked (`numbers.md:33, 226, 228`).

**Usage varied in four ways:**
1. **For a claim** (above).
2. **For the project's own reading or diagnosis.** "That retraction is itself withdrawn" (M:4024); "D3 is withdrawn" (M:6325);
   a timing statement "WITHDRAWN as overstated" (M:6739); "0.935 is withdrawn" (M:4916).
3. **For a planned fallback.** "The UKF_horizon fallback is WITHDRAWN (not needed)" (M:14022), and a queued job (M:12405).
4. **An unrelated sense, NOT the methodological term.** The safety watcher "withdraws the confirmation", "withdraws" and
   "withdrawn +0.64 s" (M:10943, M:13940, M:13948, M:14116). This means the watcher dropping its permission to fly. The
   thesis should use a different word there, such as "revokes", or define it separately.

---

## PENDING (added for completeness; see `docs/thesis/pending_items.md`)

**Draft definition.** A result or setting is *PENDING* when it has been computed or proposed but is awaiting a user or
supervisor ruling.
- It is not adopted.
- The previously adjudicated verdict stands until the ruling (the former `numbers.md` §17.2 wording, kept verbatim in its
  block "Superseded by the rulings of 2026-10-16").
- PENDING is never a verdict. The thesis must not go to submission with a PENDING item, and each needs a ruling.
- **Status after the rulings of 2026-10-16:** no thesis-facing item is PENDING. The one remaining PENDING item, the
  rung-1 first-leg length, belongs to the real-flight plan and its flight cards, not to the thesis results.

---

## Rounding of displayed values (ADOPTED for thesis tables, ruling 2026-10-16, item 3)

**Rule.** Every number displayed in a thesis table is the full-precision value in its result file, rounded **once**, to
the printed precision, **half away from zero**. The rule is applied when the tables are generated (`eval/figs_thesis.py`,
function `rd()`), not by editing any record.
- `numbers.md` shows the same single rounding (ruling 2026-10-16, option (a)): its double-rounded displays were corrected
  in place, with the old rows kept verbatim in its Superseded section (numbers.md flag 8).
- The value is read through its shortest decimal form, so a value stored at 4 dp (for example the confirmatory r5
  difference, −0.4885) rounds as written (−0.489), not as its binary neighbour.
- The thesis cross-check is EXACT: each generated display must equal its `numbers.md` cell character for character (no
  tolerance, no last-digit acceptance); no verdict, range or ordering changed (numbers.md flag 8).
- Source: M:14184-14185 (RULINGS 2026-10-16, item 3) and RULING 2026-10-16 "numbers.md rounding, option (a)"; `numbers.md` flag 8.

---

## Half real-time (RTF 0.5)

**Definition.** The closed-loop corridor flights ran in a copy of the textured corridor world whose real-time factor is
0.5. **The simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s.**
- The thesis writes "half real-time (RTF 0.5)", never "half speed", which reads as half the velocity.
- The other closed-loop world runs at the default real-time factor (1.0); no comparison across the two is claimed.
- Source: M:14193-14195 (RULINGS 2026-10-16, captions); glossary.md:134 ("half SIM speed, not half velocity");
  `sim/worlds/corridor_textured_half_fwdc.sdf:44`.

---

## Measured before corrections; not recomputed (ruling 2026-10-16, open items, 9)

**Definition.** A value that the corrections (the roll gains, the flow sign and the time sync) may have changed, and that was
not recomputed on the re-flown bags. These are the `numbers.md` rows listed under "Rows elsewhere in this file affected by
the corrections but NOT recomputed": §1 cruise roll / pitch and the camera-dataset RTF; §2 P2 latencies; §11 the ceiling
effect size (+0.43 px/s); §14 timing.
- Cite one only where the text needs it, labelled exactly "measured before corrections; not recomputed".
- **Never describe one as unaffected.** The corrections changed flow, attitude and latency; the reasoning that the flow
  measurements do not depend on the estimator corrections is WITHDRAWN.
- The ceiling effect size keeps its standing rule: any ceiling-vs-`dsn` comparison on the transition world states it, with
  this label. At 2026-10-16 no thesis-facing material makes such a comparison or cites any of these rows.
- Source: METHODOLOGY "RULINGS (user, 2026-10-16): the open pending items", item 9; `numbers.md` §9 (the not-recomputed
  list).

---

### Open choices for the user

1. **Confirmatory:** reserve the word for H1.1 only, or use it for every pre-registered primary rule?
2. **Withdrawn:** replace the watcher sense ("withdraws the confirmation") in the thesis with "revokes"?
3. **Post hoc:** require each use to state which applies, "post hoc, not a result" or "post hoc, accepted by ruling"?
4. **Pre-registered** (16 uses in the thesis-facing captions) and **CLOSED** are not drafted here. `glossary_flags.md:1170`
   asks for both.
