# Checking Claude's extraction

**Result: Claude matched the hand labels on all 38 sites with notes, for all four signals. Every quote it returned is word for word in the notes. The free-text caveats had one real problem, now fixed at the prompt, and three smaller overreaches that don't affect any score.**

Re-run it: `.venv/bin/python rank.py --check` (no API key needed; it uses the saved answers in `out/extractions.json`).

## What Claude extracts, and what the code does with it

For each site Claude returns four signals, each with the exact quote it came from or `unknown`:

| Signal | Used for |
|---|---|
| Owner status | Cross-check only. C3 is scored from the team's typed `owner_status` field; the site is flagged if Claude reads the notes differently. |
| Community sentiment | C4 (council and neighbours). Only exists in free text. |
| Area | C6, when a note is newer than the land-registry record. |
| Protected area | The kill rule, when a note (not the registry) says the plot is in a reserve. |

Plus free-text **caveats**: anything else worth knowing. These never change a score.

Two automatic checks run on every extraction:

1. **Quote check.** A signal is kept only if its quote appears word for word in one of that site's notes; otherwise it becomes `unknown`. Result: **0 quotes rejected** out of 38 sites.
2. **Owner cross-check.** Claude's owner status vs the typed field on the latest note. Result: **0 disagreements**.

## The hand check

The 70 notes use only 18 distinct sentences; the team reused stock phrases. So instead of sampling sites, I labelled each of the 18 sentences by hand ([eval/gold_notes.json](eval/gold_notes.json)): what it says about the owner, sentiment, area and protected area, or `unknown`. `--check` copies those labels to every site that uses the sentence, takes the latest-dated note per signal (the same rule the scorer uses), and compares with Claude. That covers all 38 sites with notes, not a sample.

The labels were first drafted with Claude Code, then I went through all 18 and confirmed or corrected each one. The judgment calls:

| Note | My label | Why |
|---|---|---|
| "Council has no formal position yet; officer said 'depends on the noise report'." | neutral | Undecided. The rubric has only supportive / neutral / opposed, and "no position yet" is neutral. |
| "Owner signed the letter of intent. Owner very keen." | owner: LOI signed; sentiment: unknown | Keenness is the landowner's, not the council's or neighbours'. |
| "Owner signed the letter of intent. Wants 12% revenue share." | owner: LOI signed | The 12% request is a condition to confirm, not a change of owner status. Whether terms were agreed is unknown. |
| "Municipal ecologist says the northern third of the plot falls inside the Esker Meadows reserve… Needs checking…" | protected | Unconfirmed, but the site stays excluded and is labelled "needs checking". |
| "Southern half was sold for housing last year; roughly 700 m² remains…" | area: 700 | Approximate; the site is flagged "confirm size". |
| "Drove past. Yard looks disused and big. No idea who owns it." | owner: unknown | Nothing says anyone was contacted or not. |

## Result

```
Sites compared: 38 (S-024 has no notes)

| Signal         | Agree |
|----------------|-------|
| owner_status   | 38/38 |
| sentiment      | 38/38 |
| area_m2        | 38/38 |
| protected_area | 38/38 |

Mismatches: none
Quotes rejected (not verbatim in the notes): none
```

## What `--check` does not cover: the caveats

`--check` tests the four structured signals, not whether a free-text caveat says only what the note says. I read all 12 caveats by hand.

- **Found and fixed.** Four caveats (S-010, S-016, S-021, S-027) said the noise report was "pending" or "not yet delivered". The notes only say support "depends on the noise report". I added a rule to the prompt (caveats must not infer missing facts, such as whether a report exists or has been delivered) and re-read those four sites. None repeats the claim, and all their signals stayed the same.
- **Minor overreaches, left as they are.** None changes a score, and each keeps its exact quote next to it:
  - S-017/S-031: "Heads of terms **were sent**…". The note says "sending heads of terms".
  - S-030: "commercial terms **not yet agreed**". A reasonable reading of "in talks", but not stated.
  - S-030: the school "**is driving** local objection". The petition does mention the school, but the causal claim is Claude's.

## Limits of this check

- **The data is easy.** 18 stock sentences are much easier than real field notes. A perfect score here does not mean messy real notes would score perfectly. With real notes I would label a random sample of sites, not sentences, and track disagreements over time.
- **One labeller.** The labels are my reading. A second person labelling the six judgment calls above would show how much people disagree.
- **Run-to-run wording.** Caveat wording changes between runs. The signals didn't change across the four sites re-read, but I haven't measured stability across a full re-run.

## Model and runs

- Model: `claude-opus-5`, one call per site, JSON-schema output. Prompt in [prompts/extract_notes.md](prompts/extract_notes.md).
- All 38 sites read on 2026-09-25. S-010, S-016, S-021 and S-027 re-read on 2026-09-26 after the prompt fix.
