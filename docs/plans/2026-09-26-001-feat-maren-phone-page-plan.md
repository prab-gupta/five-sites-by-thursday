---
title: "feat: Static phone page for Maren from out/results.json"
date: 2026-09-26
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
depth: lightweight
---

# feat: Static phone page for Maren from out/results.json

## Product Contract

### Summary

One static HTML page, generated from `out/results.json`, that Maren reads on her phone before the sponsor meeting: the five recommended sites with a plain-language reason each, the conditions to check, why the tempting alternatives were left out, an honest note on confidence, and expandable per-criterion evidence with quotes.

### Requirements

- R1. The recommended five in rank order, each with score out of 100 and a plain-language reason.
- R2. Conditions and next checks: Kessby's 12% revenue-share request, Varne's noise-report dependency, Orlund's unfinished owner agreement.
- R3. Why tempting alternatives weren't selected: S-009 (protected, per a field note), S-013 (only about 700 m² left), S-024 (key evidence missing).
- R4. Confidence explained honestly: "6/6 fields available" means every rubric field has a value, not that the site is confirmed feasible.
- R5. Expandable criterion details and supporting quotes for every site shown.
- R6. Works on a phone; no login, no backend, no API call from the page.

### Scope Boundaries

- No JavaScript, no framework, no new dependency.
- `rank.py`, the rubric and the ranking are not touched.
- Deploying is a separate step after local testing.

---

## Planning Contract

### Key Technical Decisions

- **KTD1. Separate `page.py`, stdlib only, reads `out/results.json`.** The request says "from out/results.json", and keeping it out of `rank.py` leaves the scorer untouched. Runs with plain `python3` (no venv needed).
- **KTD2. One self-contained `site/index.html`:** inline CSS, native `<details>` for expandables. No JS means nothing to break on a phone.
- **KTD3. Reasons are generated from the data; judgment text is written once.** Each card's reason is built from its criteria ("4.6 MW spare grid capacity · 0.8 km to substation · letter of intent signed · council supportive · low flood risk · 2,100 m²"), so it can't disagree with the scores. The conditions, why-not and confidence paragraphs are hand-written in `page.py`.
- **KTD4. The hand-written text is guarded by asserts.** `page.py` stops with an error if the data no longer matches what the text claims: the top-five IDs, S-003's revenue-share caveat, S-027's noise-report caveat, S-014 in talks, S-009 excluded with source `note`, S-013 area 700, S-024 with only 2 of 6 fields known, and the top five's grid figures all dated 2026-06-30 (the confidence paragraph says "June 2026"). If `out/results.json` is missing, it stops with "run rank.py first". Without this, a data change could leave the page saying something false.
- **KTD5. All data text is HTML-escaped** (`html.escape`), since quotes come from free-text notes.
- **KTD7. Visual style: the user-supplied "Caldera" reference, adapted to a phone.**
  - Colours: Pumice `#e2e2df` canvas, Limestone `#f7f6f2` cards, Obsidian `#070607` text, Ember `#fc5000` for the score badges, Sulfur `#f5f28e` pill tags for conditions ("Check: revenue share"), Plasma Violet `#524ae9` only for the headline block (violet-to-ember gradient with a CSS radial-gradient halftone dot overlay).
  - Type: Anton (the guide's named substitute for PP Neue Corp Compact) for headings with +0.02em tracking, DM Sans 500 for body, both from Google Fonts with system fallbacks. Body 16px minimum.
  - Shapes: flat, no shadows; 40px card radius (padding 24px on phone widths instead of 40px), 800px pills for tags and `<summary>` controls, 1.5px dotted Obsidian dividers between criterion rows.
  - Phone adaptation: display type capped with `clamp()` (about 56px on a phone, up to 96px on desktop) instead of the guide's 189px; each `<summary>` at least 44px tall.
  - Contrast: Obsidian text on Ember (as the guide's primary button does), never white on Ember, so small text stays readable.
- **KTD6. Plain-language labels only.** No C1–C6 codes or internal source names on the page: "Spare grid capacity", "Distance to substation", "Landowner", "Council and neighbours", "Flood risk", "Usable land". Sources shown as "grid operator, as of 2026-06-30", "land registry, 2025-11-03", "field note, 2026-08-28".

### Page structure (top to bottom)

1. **Headline:** "Bring these five sites on Thursday", one sentence on how they were picked, data date (tracker export 2026-09-21).
2. **The five:** one card each: rank, name, region, score/100, reason line, the site's condition (if any), `<details>` "Why this score" with a row per criterion (label, value, points out of weight, source + date, quote if any).
3. **Check before or during the meeting:** Kessby 12% revenue share (LOI signed, share not agreed); Varne council support depends on the noise report (confirm status and outcome); Orlund owner still at heads of terms, no letter of intent.
4. **Why not these:** S-009 would score 100 but a field note says part of the plot is in a nature reserve (quote, "needs checking"); S-013 registry says 2,400 m² (2017) but a note says about 700 m² remains, below the 1,200 m² a 2 MW battery needs; S-024 has the strongest grid figure (5 MW, 0.6 km) but no land-registry record and no notes, so 45 now and 100 only if everything checks out. Each with the same `<details>` breakdown.
5. **How sure we are:** 6/6 means every rubric field has a value from a source, not that the site is feasible. Grid figures are quarterly (June 2026); letters of intent are non-binding; no site has had a feasibility study, which is what the sponsor would fund. Best case explained in one line.
6. **Footer:** method in one line (field notes read by Claude with exact quotes; scores computed by code from the agreed rubric), generation date.

---

## Implementation Units

### U1. page.py generates site/index.html

**Goal:** Produce the page from `out/results.json`.
**Requirements:** R1–R6. KTD1–KTD7.
**Files:** `page.py` (new), `site/index.html` (generated).
**Approach:** Load results; pick `ranked[:5]`, the three why-not sites by ID from `ranked`/`excluded`; build HTML with f-strings and one small render helper per card and per criterion row; write the file. Asserts from KTD4 run before writing.
**Test scenarios:**
- Happy path: page contains all five top IDs in order with scores 97, 97, 96, 93, 86.
- Missing input: with `out/results.json` absent, `page.py` exits with "run rank.py first" and writes nothing.
- R2: page mentions "12%", "noise report", and Orlund's heads of terms.
- R3: S-009, S-013 and S-024 each appear with their reason and a breakdown.
- Guard: breaking each KTD4 fact in turn in a copy of results.json (e.g. S-013's area, S-003's caveat, a top-five grid date) makes `page.py` fail with a clear assert naming that fact, not write a wrong page.
- Escaping: a quote containing `'` or `&` renders as text, not markup.
**Verification:** `python3 page.py` writes `site/index.html` and exits 0; the checks above pass by grepping the output.

### U2. Phone check + README

**Goal:** Confirm the page reads well at phone width and document the command.
**Requirements:** R6.
**Dependencies:** U1.
**Files:** `README.md` (one line under "Run it", page link placeholder stays until deploy).
**Approach:** Headless Chrome screenshot at 390×844 of the full page, plus one with a `<details>` open; check no horizontal scroll, readable text, and that the Caldera colours, pills and 40px cards render.
**Test expectation:** visual check only; no unit test for layout.
**Verification:** screenshots show the headline and first card above the fold, no sideways scrolling, expandables work.

---

## Verification Contract

- `python3 page.py` exits 0 and writes `site/index.html`.
- The page contains everything in R1–R5; the guard assert fires on contradicted data.
- Phone-width screenshot reads cleanly.
- `grep -i "sk-ant\|api" site/index.html` finds no key and no API call.

## Definition of Done

U1 and U2 done, tested locally, not committed until the user says so.
