# Five sites by Thursday

Scores and ranks 40 candidate community-battery sites against the sponsor's rubric. Claude reads the field notes and returns quoted signals; the code decides every score.

- **Page for Maren:** https://five-sites-by-thursday.vercel.app
- **Written recommendation:** [NOTE.md](NOTE.md)
- **Questions and assumptions (written before any code):** [QUESTIONS.md](QUESTIONS.md)
- **Extraction check:** [EVAL.md](EVAL.md)

## Run it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python rank.py                     # ranked table, shortlist, excluded sites
.venv/bin/python rank.py S-013               # why one site scored what it did
.venv/bin/python rank.py --check             # Claude's extraction vs hand labels
python3 page.py                              # builds site/index.html (Maren's page) from out/results.json
```

Every run ends with a line like `Claude calls this run: 0 (38 from cache out/extractions.json)`, so you can see whether the AI actually ran.

**No API key is needed for the commands above.** Claude's answers are saved in `out/extractions.json` (committed), so every run reuses them. `page.py` never calls Claude: it only reads `out/results.json` and writes a static page with no scripts and no key.

## Calling Claude for real

Put the key in `.env` as `ANTHROPIC_API_KEY=...` (it overrides any key already in your shell). The model defaults to `claude-opus-5`; set `MODEL` to change it.

```bash
.venv/bin/python rank.py --refresh S-013             # re-read one site (1 call)
.venv/bin/python rank.py --refresh S-010 S-027       # re-read several
.venv/bin/python rank.py --refresh                   # re-read all 38 sites with notes (38 calls)
.venv/bin/python rank.py --check                     # then confirm the new answers still match the hand labels
```

A call happens only for a site that is named in `--refresh`, or missing from the cache. The cache is written after each site, so if a call fails, re-running only calls the sites still missing. S-024 has no notes and is never sent.

Every run also checks a few known facts with `assert` and stops if one breaks: S-003 scores 97 (formula check), S-020 is refused, S-013 has 700 m², S-009 and S-033 are excluded.

## How it works

One file, [rank.py](rank.py), in this order:

1. **Load and fix the data** (see decisions below).
2. **Claude reads each site's notes.** One call per site, prompt in [prompts/extract_notes.md](prompts/extract_notes.md), JSON-schema output: owner status, community sentiment, area, protected area, caveats. Each is `{value, quote}` or `unknown`. Claude never sees the rubric.
3. **Code checks every quote** is word for word in one of that site's notes. A quote that isn't is thrown out and the signal becomes `unknown`. The note that contains the quote gives the date.
4. **Score in code.** Weights and tiers sit at the top of `rank.py`, the only place the numbers live. Score = Σ weight × tier ÷ 5.
5. **Output.** For each criterion a site keeps its value, tier, points, source (`gridmap`, `landreg`, `note`, `typed-field`, `vendor-lowband`, `unknown`) and quote. That record is the "why".

## Decisions

Reasoning for each is in [QUESTIONS.md](QUESTIONS.md).

| Issue in the data | What the code does |
|---|---|
| Nordholm publishes headroom in kW (2,200 = 2.2 MW) | Divides Nordholm by 1,000. Delete that line once the feed converts, or it will divide twice. |
| Gridmap is empty for two different reasons | `fetch_log.csv` tells them apart. 8 sites timed out (503): headroom and distance unknown. 2 sites have "no substation within 10 km": scored 0 as a real answer, not a gap. |
| Vendor estimate is unvalidated | Scores only for the 8 timeout sites, at the low end of its own band (estimate × 0.6), flagged "unverified". Where official data exists it never scores; if it lands in a different tier the site gets a warning with both figures and dates (S-007, S-021, S-032 and three others). |
| Missing values | Score 0 and are marked `unknown`. No averaging. Each site also shows a best case: *assumes missing criteria receive maximum points; existing values and estimates stay unchanged.* |
| Same parcel logged twice (S-017, S-031) | Merged into one site with all notes kept. |
| Notes are out of date order (S-020's latest status is "refused") | Latest dated note wins. |
| Owner status | Taken from the typed `owner_status` field on the latest note. Claude's reading is stored next to it and the site is flagged if they differ (none do). |
| Community sentiment exists only in free text | From Claude, with its quote. Notes with no `owner_status` are the ones that record council and community reactions; the prompt says so, and a sentiment quote from an owner note is flagged. |
| Registry area is old (S-013: 2,400 m² in 2017, note says 700 m² remains) | A note newer than the registry record overrides the area, flagged "approximate: confirm size". |
| Protected area | Excluded if the registry says so (S-033) or a note does (S-009, labelled "needs checking"). |
| Parcel missing from the registry (S-024, S-036) | Area, flood zone and protected status unknown. Not excluded. |
| Tier boundary at exactly 2 MW | Counts as "2–4 MW", the same way "≥ 4" includes 4. |
| Claude caveats that claimed more than the notes say | Four caveats said a noise report was "pending" or "not delivered"; the notes don't say that. Fixed at the source: the prompt now forbids inferring missing facts, and those four sites were re-read. |

## Checking the extraction

The 70 notes use only 18 distinct sentences. I labelled each one by hand ([eval/gold_notes.json](eval/gold_notes.json)) and expanded the labels to every site, so `--check` compares all 38 sites with notes, not a sample. Claude agrees on 38/38 for all four signals and no quote was rejected. Details and limits in [EVAL.md](EVAL.md). `--check` covers the four structured signals, not the wording of free-text caveats; those were reviewed by hand.

## Result

| # | Site | Score |
|---|---|---|
| 1 | S-003 Kessby Old Quarry Yard | 97 |
| 2 | S-018 Grelle Harbour Plot | 97 |
| 3 | S-017/S-031 Brekke Depot | 96 |
| 4 | S-027 Varne Farm Edge | 93 |
| 5 | S-014 Orlund Depot Yard | 86 |

Jonas's plan (vendor fallback, dataset averages, no kW fix, no kill rule) would have put S-006 and S-009 in the top five: S-006 has 1.7 MW, not 1,700; S-009 is partly inside a nature reserve according to the notes.

## What I'd do next

1. Re-fetch gridmap for the 8 sites that timed out.
2. Look up S-024 and S-036 in the land registry and find their owners (both have strong grid numbers and nothing else checked).
3. Confirm the reserve boundary at S-009 with the municipal ecologist. If it's outside, it's the top site.
4. Ask the Nordholm operator to confirm its figures are kW.
5. Compare the vendor estimate with gridmap across all sites before relying on it anywhere.

## AI use

Built with Claude Code and a Gemini chat. Conversations are in [ai-transcripts/](ai-transcripts/); moments I disagreed with or corrected the AI are in [AI_LOG.md](AI_LOG.md).

## Time spent

About 4.5 hours in total.
