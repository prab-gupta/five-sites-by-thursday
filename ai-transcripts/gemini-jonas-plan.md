Cracking the Take-Home Test Trap
https://gemini.google.com/app/f7306bfca3c0199c

User prompt: Easy one. Load sites.json. For each criterion take whatever value the sources have (use the vendor estimate if gridmap is empty). Fill any remaining gaps with the dataset average so every site gets a score. Weighted sum, sort descending i dont get this what value are we taking?
Response: You are quoting Jonas's message from the "Five sites by Thursday" prompt. This is a classic trap in a forward-deployed engineering take-home test.
By "value," Jonas means the raw data numbers from the sites.json file that correspond to the six scoring criteria (C1–C6) in the rubric.
Here is exactly what his quick-and-dirty plan is suggesting you do:
The Primary Source: Grab the official number from the JSON. For example, for Criterion 1 (Grid headroom), take the headroom value under the gridmap source.
The Fallback: If the official gridmap data is null or empty, take the headroom_mw_est value from the vendor_estimate source instead.
The Averages: If a site is completely missing data for a criterion (e.g., no distance recorded anywhere), he wants you to calculate the mean average of that metric across the other 39 sites and plug it in. This forces every site to have a number so his weighted sum formula doesn't break.
However, Part 1 of your task explicitly asks what worries you about Jonas's plan. You are not actually supposed to follow his instructions blindly, because his logic is fundamentally flawed:
Raw values aren't scores: You cannot just drop raw values (like m2 or km) into a weighted sum. The rubric strictly requires converting those raw values into standardized tiers (0–5) first.
You can't average text: Criteria like "Landowner status" and "Community sentiment" do not have numerical values. They exist only as unstructured text within the field_notes and must be extracted using Claude.
Averaging physical reality is dangerous: If a plot is missing headroom data, assigning it the dataset average might trick the sponsor into funding a feasibility study for a site that actually has zero capacity.
The unit trap: The data dictionary explicitly states that the Nordholm region reports headroom in kW, while the others use MW. Taking "whatever value" without normalizing the units will completely skew the math.
The Kill Rule: Jonas's formula just calculates a sum and sorts descending. It completely ignores the rule that any site inside a designated nature area must be instantly disqualified, regardless of its score.

User prompt: Averaging physical reality is dangerous: If a plot is missing headroom data, assigning it the dataset average might trick the sponsor into funding a feasibility study for a site that actually has zero capacity explain
Response: Grid headroom is a strict physical constraint, not a statistical variable. It measures the actual available capacity at a specific local substation.
If you do not have the headroom data for a specific site and you plug in the dataset average (e.g., assuming 3 MW because other sites have that much), you are essentially inventing physical electrical capacity out of thin air. The power grid does not care about mathematical averages; a specific local substation either has the physical wiring and transformer capacity to connect a battery, or it does not.
Here is why applying an average to a physical missing value is dangerous in this scenario:
Financial Waste: The sponsor is using your top-five list to pay for real-world feasibility studies. If they fund a study for a site because your "average" gave it a high score, but the actual local substation has 0 MW of spare capacity, the project is dead on arrival. The sponsor has just wasted their money on a site that can never be built.
Loss of Credibility: Your venture's core goal is to prove to this sponsor that your data-driven approach is reliable and fast. Passing off a statistical guess as a physical fact will destroy your team's credibility the moment the sponsor's engineers check the actual grid data.
Masking Critical Risk: In engineering, an unknown value must be treated as an unknown. Averaging silently converts a massive blind spot into a safe-looking, passing score.
If a site is missing its most critical physical metric, the correct approach is to either drop it from the shortlist, give it a baseline score of zero for that category to reflect the extreme risk, or explicitly flag it to the venture lead as a gamble that requires manual investigation.

User prompt: so sites with which null value should be ranked lower?
Response: In a risk-averse engineering context, any missing physical data or constraint should result in a score of zero for that specific criterion. By scoring null values as the lowest possible tier, the sites naturally sink to the bottom of the ranking without needing manual disqualification.
Based on the rubric and the data dictionary, sites with null values in the following fields should be ranked lower:
headroom (Gridmap) & headroom_mw_est (Vendor Estimate): This is the single most important criterion, weighted at 30 points. If the official gridmap headroom is null, and the unvalidated vendor estimate is also null, the site should score 0 for C1. Without this value, you cannot guarantee the battery can connect to the grid.
substation_distance_km (Gridmap): Weighted at 15 points. A missing distance means you cannot estimate the cost or feasibility of running the connecting cable to the grid. It should score 0 for C2.
flood_zone (Land Registry): Weighted at 15 points. Batteries and floods do not mix. An unknown flood risk must be treated as a high-risk unknown, scoring 0 for C5.
area_m2 (Land Registry): Weighted at 10 points. A standard 2 MW battery requires approximately 1,200 m² of space. If the usable area is null, you cannot prove the physical footprint exists, resulting in a score of 0 for C6.
protected_area (Land Registry): The rubric includes a strict "kill rule": any site inside a designated nature area is immediately excluded, regardless of its score. If this value is null, the site carries a catastrophic hidden risk and should either be heavily penalized or flagged immediately to the venture lead.
By assigning zeros to these null values instead of averages, you protect the sponsor from funding feasibility studies on unviable land, which is exactly the analytical judgement the venture lead is looking for.

User prompt: 22 entries dont have headroom mw east makes sense to exclude them?
Response: It would be a mistake to exclude all 22 of those sites, because you are looking at the fallback metric rather than the primary one.
The vendor estimate (ve_headroom_mw_est) is an unvalidated, third-party machine-learning model. You should only look at this column if the official grid operator data is missing. The primary source for capacity is the gridmap feed (gm_headroom), because it is the official figure that the sponsor will trust.
If you look at both columns together across the 40 sites, here is the actual data overlap:
22 sites are missing the vendor estimate.
10 sites are missing the official gridmap headroom.
Only 2 sites are missing both values.
Instead of dropping 22 sites, you should apply a fallback logic:
Primary Check: Always use the official gm_headroom first. (Note: Keep in mind that Nordholm's gridmap figures are published in kW, not MW, and must be divided by 1,000 before scoring).
Fallback Check: If gm_headroom is empty, use ve_headroom_mw_est in its place.
The True Zeros: If a site is missing both values (which only applies to 2 sites), then it has no known physical capacity. Those 2 specific sites should receive a score of 0 for Criterion 1.

User prompt: what should be criterias
Response: The criteria and their specific scoring tiers are explicitly defined in the project rubric agreed upon with the sponsor. You must evaluate each site against these six criteria, converting the raw data into a tier score (0 to 5) before applying the weighted sum.

#
Criterion
Weight
Tiers (Score 0–5)
C1
Grid headroom at nearest substation
30
≥ 4 MW → 5

2–4 MW → 3

1–2 MW → 1

< 1 MW → 0
C2
Distance to that substation
15
≤ 1 km → 5

≤ 3 km → 3

≤ 6 km → 1

> 6 km → 0
C3
Landowner status
20
LOI signed → 5

in talks → 3

not contacted → 1

refused → 0
C4
Local council / community sentiment
10
supportive → 5

neutral → 3

opposed → 0
C5
Flood zone
15
none → 5

low → 4

medium → 2

high → 0
C6
Usable area (~1,200 m² needed for 2 MW)
10
≥ 1,200 m² → 5

800–1,200 m² → 2

< 800 m² → 0

To calculate the final score (which runs from 0 to 100), use the exact formula provided: Site score = Σ (weight × tier ÷ 5).
You must also apply the strict Kill Rule: any site inside a protected nature area must be completely excluded, regardless of how high its score is.

User prompt: use the names of the columns too
Response:
#
Criterion
Data Source / Column Names
Tiers (Score 0–5)
Weight
C1
Grid headroom
Primary: gm_headroom (DB) / headroom (JSON)

Fallback: ve_headroom_mw_est (DB) / headroom_mw_est (JSON)

Note: Check the region column; if Nordholm, divide the gm_headroom value by 1,000 to convert kW to MW.
≥ 4 MW → 5

2–4 MW → 3

1–2 MW → 1

< 1 MW → 0
30
C2
Substation distance
gm_distance_km (DB) / substation_distance_km (JSON)
≤ 1 km → 5

≤ 3 km → 3

≤ 6 km → 1

> 6 km → 0
15
C3
Landowner status
owner_status located inside the notes table (DB) or field_notes array (JSON)
LOI signed → 5

in talks → 3

not contacted → 1

refused → 0
20
C4
Community sentiment
text located inside the notes table (DB) or field_notes array (JSON)

Note: This requires Claude to read the unstructured text and extract the sentiment.
supportive → 5

neutral → 3

opposed → 0
10
C5
Flood zone
lr_flood_zone (DB) / flood_zone (JSON)
none → 5

low → 4

medium → 2

high → 0
15
C6
Usable area
lr_area_m2 (DB) / area_m2 (JSON)
≥ 1,200 m² → 5

800–1,200 m² → 2

< 800 m² → 0
10

Kill Rule: Check lr_protected (DB) or protected_area (JSON). If this value is 1 or true, the site is inside a designated nature area and must be excluded entirely regardless of its score.
