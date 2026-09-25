---
title: "feat: Claude field-notes extraction for site scoring"
date: 2026-09-25
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
depth: standard
---

# feat: Claude field-notes extraction for site scoring

## Product Contract

### Summary

Use Claude to read each site's field notes and return structured signals: owner status, community sentiment, area override, protected-area flag and caveats. Every signal carries the exact quote it came from, or `unknown`. Code verifies the quotes, picks the latest note per signal and maps signals to rubric tiers. Claude never sees the rubric or scores anything.

### Problem Frame

The rubric needs C3 (landowner), C4 (council/community sentiment) and C6 (area), plus the protected-area kill rule. C4 exists **only** in free text. Some facts that override the official sources also live only in the notes: S-009 is protected, S-013 has shrunk to 700 m². Notes are out of date order at 11 sites, so "take the first note" gives wrong answers (S-020's latest status is `refused`).

### What the data actually looks like (from reading all 70 notes)

- 40 sites, 70 notes, but only **18 distinct note texts**. The team reused stock phrases. S-024 has no notes at all.
- **`owner_status` is already structured on every owner note.** Only S-024 (no notes) and S-036 ("No idea who owns it") have no owner status. So for C3, Claude is a cross-check, not the source.
- **Sentiment is free text only.** 7 phrasings map cleanly:
  - supportive: co-op wrote to council backing it; committee minutes record support; ward councillor openly in favour
  - neutral: neighbours indifferent; council has no formal position
  - opposed: residents' petition (S-030); councillor fire-safety objections (S-040)
  - no sentiment note (so unknown): S-005, 012, 019, 022, 023, 024, 031, 032, 033, 036, 038, 039
- **Text-only facts that must change the score or the kill decision:**

  | Site | Quote | Effect |
  |---|---|---|
  | S-009 | "northern third of the plot falls inside the Esker Meadows reserve" | kill rule (registry record from 2018 says not protected) |
  | S-013 | "roughly 700 m² remains" | C6 area override (registry from 2017 says 2,400 m²) |
  | S-020 | "Owner declined to lease. Board voted against." (latest, 09-05) | C3 = refused |
- **Caveats to show, no score change:** S-003 "Wants 12% revenue share"; S-020 "Revisit in 2027"; S-031 "(Brekke depot, finally.)" (duplicate hint, since the data layer already merges S-017 and S-031 by parcel); S-036 "Yard looks disused and big".

### Requirements

- R1. One Claude call per site. Input: all of that site's notes with date, author and structured status. Output: JSON matching a fixed schema.
- R2. Every signal is `{value, quote}`. If the notes are silent, it's `value: "unknown"` with `quote: null`. Never guessed.
- R3. Code rejects any signal whose quote is not a verbatim substring of one of that site's notes. The signal becomes `unknown` and the rejection is logged.
- R4. Code, not the model, picks the latest-dated note per signal and maps values to tiers.
- R5. Extraction is checked against hand labels, and the result is reported in `EVAL.md`.
- R6. The prompt lives in the repo. The API key comes from `.env`, overriding the shell's own key. Results are cached so reruns and the page build don't call the API.

### Scope Boundaries

- No agent framework, no multi-step chains, no database.
- Claude does not score, weight or rank anything, and doesn't see the rubric.
- Signals from sources other than notes (gridmap, landreg, vendor) stay in the data layer.

---

## Planning Contract

### Key Technical Decisions

- **KTD1. Rubric weights and tiers are exactly as agreed with the sponsor.** (session-settled: user-directed, chosen over re-weighting by own research: the sponsor agreed these.)
- **KTD2. Missing = 0, marked "unknown".** (session-settled: user-directed, chosen over dataset averaging.) So S-024 gets C3 = 0 and C4 = 0, and the 12 sites with no sentiment note get C4 = 0.
- **KTD3. Kill rule if the registry *or* a note says protected.** (session-settled: user-directed, chosen over registry only.) S-009 is excluded, shown with its quote and labelled "needs checking". Code sets `source: note` for a kill that comes from a note and `source: registry` for one from landreg, so the page can tell a confirmed kill from a hedged one.
- **KTD4. The structured `owner_status` is authoritative for C3; Claude's owner value is a cross-check.** The field is typed by the team at the moment of the event, while text needs interpretation. Code stores both values side by side: `owner_status_field` (from the typed field, used for C3) and `owner_status_claude` (from the text), each one of the 5 statuses. When they differ, the page shows "check" with both values visible. This keeps C3 deterministic and turns the model into a verifier for it.
- **KTD5. One call per site, not per note.** It matches the brief ("per site or per batch") and gives the model the context of neighbouring notes (the S-013 note carries both an owner status and an area fact). The cost is trivial (39 calls).
- **KTD6. The model returns only value + quote. Code finds the note that contains the quote and takes the date from that note.** The model never handles dates, so a date mistake can't flip S-020.
- **KTD7. Area override applies only when the note is newer than the landreg `record_date`.** Then the note wins for C6. S-013: note 2026-08-28 vs record 2017, so area = 700 m² and C6 = 0.
- **KTD8. Structured output via a forced tool call with a JSON schema.** Enums include `unknown`. `claude-opus-5` by default, with a `MODEL` env override.
- **KTD9. The check uses gold labels per distinct note text, expanded to every site.** There are only 18 distinct texts, so labelling those by hand gives a gold answer for **all 39 sites with notes**. That's a full check, not a sample, for about 15 minutes of labelling.

### Signal schema (directional)

```
owner_status:      loi_signed | in_talks | not_contacted | refused | unknown   + quote
sentiment:         supportive | neutral | opposed | unknown                      + quote
area_override_m2:  number | unknown                                               + quote
protected_area:    true | unknown                                                 + quote   (code adds source: registry | note)
caveats[]:         {detail, quote}
```

### Signal-to-rubric mapping (in code)

| Signal | Rubric use |
|---|---|
| owner_status_field (typed; `owner_status_claude` shown next to it) | C3: loi 5 · talks 3 · not contacted 1 · refused 0 · unknown 0 |
| sentiment | C4: supportive 5 · neutral 3 · opposed 0 · unknown 0 |
| area_override_m2 (if newer than landreg) | C6 tier from the overridden area |
| protected_area = true | kill, listed as excluded with the quote |
| caveats | shown on the page, no score change |

### Open Questions

- **S-036 "No idea who owns it":** owner unknown (C3 = 0) or not contacted (C3 = 1)? Default: **unknown = 0**, following the brief's "if the notes don't say, unknown". Flagged on the page.

---

## Implementation Units

### U1. Prompt + extraction call + cache

**Goal:** Turn one site's notes into validated signals.
**Requirements:** R1, R2, R6. KTD5, KTD6, KTD8.
**Files:** `prompts/extract_notes.md`, `rank.py` (extraction function), `out/extractions.json` (committed cache).
**Approach:** The prompt defines each category in plain words (what counts as supportive, neutral, opposed). It says "quote verbatim, one continuous span", "unknown if not stated" and "do not infer from tone". It gives no rubric numbers. The site's notes go in date-sorted, each tagged with date. The cache is keyed by site_id; `--refresh` re-calls the API (use it after editing the prompt). The cache is written after each site, so if a call fails the run stops, and rerunning only calls the API for sites missing from the cache. `.env` is read by hand (no python-dotenv), overriding the shell's `ANTHROPIC_API_KEY`.
**Test scenarios:**
- S-024 (no notes) returns every signal `unknown`, without calling the API.
- S-030 returns sentiment opposed, with the petition quote.
- A second run makes zero API calls (served from the cache).
**Verification:** The cache holds 39 entries that match the schema.

### U2. Quote verification + latest-note resolution

**Goal:** Code-side guardrails.
**Requirements:** R3, R4. KTD4, KTD6, KTD7.
**Dependencies:** U1.
**Files:** `rank.py`.
**Approach:** For each signal, check that the quote is a substring of one of the site's note texts (after whitespace normalisation). If not, the signal becomes unknown and the rejected quote is recorded in that site's entry in `out/extractions.json`. Owner status comes from the latest-dated note that has a structured `owner_status`. Claude's value is stored as `owner_status_claude` next to `owner_status_field`. C3 is scored from the field, and the page shows "check" whenever the two differ. The area override is applied only if the note date is later than the landreg `record_date`.
**Test scenarios:**
- A fabricated quote is rejected and the signal becomes unknown.
- S-020 resolves to refused, even though the notes are stored out of order.
- A site where Claude's owner value differs from the typed field keeps the field's value for C3, and both values appear in the output.
- S-013 area resolves to 700, so C6 = 0.
- S-009 resolves to protected with `source: note`, so the site goes to the excluded list with its quote and a "needs checking" label. S-033 resolves with `source: registry`.
**Verification:** Asserts in `rank.py` for S-020, S-013 and S-009 pass on every run.

### U3. Extraction check

**Goal:** Prove the extraction is right.
**Requirements:** R5. KTD9.
**Dependencies:** U1, U2.
**Files:** `eval/gold_notes.json` (18 distinct texts, hand-labelled), `rank.py` (`--check` flag), `EVAL.md`.
**Approach:** Hand-label each distinct note text once (owner, sentiment, area, protected). Expand the labels to every site by text match. Resolve per site with the same latest-note logic as U2, then compare against Claude's resolved signals. Report agreement per signal, every mismatch with its quote, and the count of rejected quotes.
**Test scenarios:**
- A deliberately wrong gold label shows up as a mismatch line (proves the check isn't vacuous).
- All 39 sites with notes are compared, and S-024 is reported as "no notes".
**Verification:** `EVAL.md` shows agreement per signal and explains every mismatch.

---

## Verification Contract

- `python3 rank.py` works from a clean clone with the key set, and a second run makes zero API calls.
- The asserts pass: S-020 refused, S-013 700 m², S-009 excluded with `source: note`, no rejected quotes (or each one explained in `EVAL.md`).
- `python3 rank.py --check` prints per-signal agreement across 39 sites.
- `grep -r sk-ant` finds nothing in the repo or git history.

## Definition of Done

U1–U3 are committed. `EVAL.md` reports the full check. The prompt is in `prompts/`. The cache is committed so graders can reproduce the results without a key.
