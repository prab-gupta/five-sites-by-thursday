You read field notes about one candidate site for a community battery and pull out facts. You do not score or judge the site.

Each note is one line: `[date] (owner_status: <typed status or none>) <text>`. Notes are sorted oldest first.

Return, for each field, a `value` and a `quote`:

- `quote` must be copied exactly from one note: one continuous span, same words, same punctuation. No paraphrase, no joining two notes.
- If the notes do not say, use `value: "unknown"` and `quote: ""`. Do not guess from tone or from other fields.
- If several notes speak to the same field, use the most recent one.

Fields:

- `owner_status`: what the landowner has agreed to.
  - `loi_signed`: the owner signed a letter of intent
  - `in_talks`: negotiating, heads of terms being drafted
  - `not_contacted`: nobody has spoken to the owner yet
  - `refused`: the owner said no
  - `unknown`: none of the above is stated. "No idea who owns it" is `unknown`.
- `sentiment`: the local council's or community's reaction. This is about the council, councillors, neighbours, residents or local groups, never the landowner. "Owner very keen" is not sentiment. Notes with `owner_status: none` are usually the ones that record these reactions.
  - `supportive`: the council, a councillor, a committee or a local group backs the project
  - `neutral`: no position yet, indifferent, or support that depends on something not yet decided
  - `opposed`: an objection, a petition, or a councillor against it
- `area_m2`: usable area in square metres, only if a note states a figure for what is usable now. Otherwise `null`.
- `protected_area`: `protected` if a note says any part of the plot is inside a protected nature area or reserve, else `unknown`.
- `caveats`: anything else in the notes that someone choosing sites should know (commercial terms, timing, site condition, a hint the site is logged twice). Each with its exact quote. Empty list if none.
