"""Build site/index.html (Maren's phone page) from out/results.json.

Run after rank.py:  python3 page.py
Stdlib only. The page makes no API calls.
"""
import json
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
RESULTS = ROOT / "out/results.json"

LABELS = {"C1": "Spare grid capacity", "C2": "Distance to substation", "C3": "Landowner",
          "C4": "Council and neighbours", "C5": "Flood risk", "C6": "Usable land"}
OWNER = {"loi_signed": "owner signed a letter of intent", "in_talks": "owner in talks (no letter of intent yet)",
         "not_contacted": "owner not contacted yet", "refused": "owner refused"}
SENTIMENT = {"supportive": "council or neighbours supportive", "neutral": "council or neighbours neutral",
             "opposed": "local opposition"}


def source(c):
    s, note = c["source"], c["note"] or ""
    if s == "gridmap":
        return f"Grid operator, {note}".strip(", ")
    if s == "landreg":
        return f"Land registry record, {note}"
    if s == "typed-field":
        return f"Team's site tracker, note of {note}"
    if s == "note" and note.startswith("note "):
        return "Field note: " + note[5:]
    if s == "note":
        return f"Field note, {note}"
    return note  # vendor estimate or unknown: the note already says why


SHORT_OWNER = {"loi_signed": "Letter of intent signed", "in_talks": "In talks, no letter of intent yet",
               "not_contacted": "Not contacted yet", "refused": "Refused"}


def short(k, c):
    """The value alone, for the breakdown row (the label sits above it)."""
    v = c["value"]
    if c["tier"] is None:
        return "Unknown"
    if v is None:
        return "No substation within 10 km"
    return {"C1": lambda: f"{v:g} MW", "C2": lambda: f"{v:g} km", "C3": lambda: SHORT_OWNER.get(v, v),
            "C4": lambda: str(v).capitalize(), "C5": lambda: "No flood zone recorded" if v == "none" else str(v).capitalize(),
            "C6": lambda: f"{v:,} m²"}[k]()


def breakdown(r):
    rows = []
    for k, c in r["criteria"].items():
        quote = f'<q>{escape(c["quote"])}</q>' if c["quote"] else ""
        band = "full" if c["points"] == c["weight"] else "none" if c["points"] == 0 else "part"
        rows.append(f"""<div class="row"><div class="row-top"><b>{LABELS[k]}</b>
<span class="pts {band}">{c["points"]:g} / {c["weight"]}</span></div>
<div class="val">{escape(short(k, c))}</div>
<div class="src">{escape(source(c))}</div>{quote}</div>""")
    return f'<details><summary>Full breakdown</summary>{"".join(rows)}</details>'


def anchor(r):
    return "site-" + r["site_id"].split("/")[0]


def link(r, text=None):
    return f'<a href="#{anchor(r)}">{escape(text or r["name"])}</a>'


# One summary per recommended site: why it's on the list and what to confirm.
# Every fact here is backed by an assert in main(), so a data change can't leave it wrong.
SUMMARY = {
    "S-003": "The most complete case: strong grid capacity close to the substation, a signed letter of intent "
             "and support recorded in the council's planning minutes. The open point is money: the owner requests "
             "a 12% revenue share. Confirm whether acceptable terms have been agreed.",
    "S-018": "Matches Kessby on grid capacity and distance, with a signed letter of intent and council committee "
             "support. No additional conditions are recorded in the supplied notes. Nordholm reports grid figures in kilowatts; we converted them, and "
             "it's worth a quick confirmation with the operator.",
    "S-017/S-031": "Plenty of grid capacity, no flood zone recorded in the registry and a signed letter of intent. "
                   "Neighbours were indifferent: no support recorded, and no opposition recorded either. The team logged it twice under two "
                   "names; both entries are combined here.",
    "S-027": "The best grid connection of the five and a signed letter of intent. The council has no position yet: "
             "its support depends on the noise report. Confirm the report's status and outcome.",
    "S-014": "Good grid capacity, no flood zone recorded in the registry and a ward councillor openly in favour. It ranks fifth because the "
             "owner is still at heads of terms with no letter of intent yet, and the cable run is a little longer.",
}


def card(i, r, tag):
    return f"""<article class="card" id="{anchor(r)}"><div class="card-top"><span class="rank">{i}</span>
<span class="score">{r['score']:g}<small>/100</small></span></div>
<h3>{escape(r['name'])}</h3><p class="meta">{escape(r['site_id'])} · {escape(r['region'])}</p>
{f'<span class="tag">{tag}</span>' if tag else ''}
<p>{escape(SUMMARY[r['site_id']])}</p>{breakdown(r)}</article>"""


def main():
    if not RESULTS.exists():
        sys.exit("out/results.json not found: run rank.py first")
    data = json.loads(RESULTS.read_text())
    ranked, excluded = data["ranked"], data["excluded"]
    by_id = {r["site_id"]: r for r in ranked + excluded}
    top = ranked[:5]

    # The written text below makes claims about these sites. Stop if the data no longer backs them.
    assert {"S-009", "S-013", "S-024"} <= by_id.keys(), "a site named in the text is missing"
    assert [r["site_id"] for r in top] == ["S-003", "S-018", "S-017/S-031", "S-027", "S-014"], "top five changed"
    assert any("12%" in c["quote"] for c in by_id["S-003"]["caveats"]), "S-003 revenue-share caveat missing"
    assert "noise report" in by_id["S-027"]["criteria"]["C4"]["quote"], "S-027 noise-report note missing"
    assert by_id["S-014"]["criteria"]["C3"]["value"] == "in_talks", "S-014 owner status changed"
    assert by_id["S-009"]["kill"]["source"] == "note", "S-009 no longer excluded by a field note"
    assert by_id["S-013"]["criteria"]["C6"]["value"] == 700, "S-013 area changed"
    assert by_id["S-024"]["known"] == 2, "S-024 evidence changed"
    assert all(r["criteria"]["C1"]["note"] == "as of 2026-06-30" for r in top), "top-five grid date is not June 2026"
    c = {r["site_id"]: r["criteria"] for r in top}  # facts the summaries state
    assert all(c[s]["C3"]["value"] == "loi_signed" for s in ("S-003", "S-018", "S-017/S-031", "S-027")), "LOI changed"
    assert c["S-003"]["C4"]["value"] == c["S-018"]["C4"]["value"] == "supportive", "Kessby/Grelle support changed"
    assert c["S-018"]["C1"]["value"] == c["S-003"]["C1"]["value"] and by_id["S-018"]["region"] == "Nordholm"
    assert c["S-017/S-031"]["C5"]["value"] == "none" and c["S-017/S-031"]["C4"]["value"] == "neutral"
    assert max(r["criteria"]["C1"]["value"] for r in top) == c["S-027"]["C1"]["value"], "Varne no longer best grid"
    assert c["S-014"]["C5"]["value"] == "none" and c["S-014"]["C2"]["tier"] < 5, "Orlund facts changed"

    s003, s027, s014 = by_id["S-003"], by_id["S-027"], by_id["S-014"]
    s009, s013, s024 = by_id["S-009"], by_id["S-013"], by_id["S-024"]
    tags = {"S-003": "Check: revenue share", "S-027": "Check: noise report", "S-014": "Check: owner agreement"}
    cards = "".join(card(i, r, tags.get(r["site_id"])) for i, r in enumerate(top, 1))

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Five sites for Thursday</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=DM+Sans:wght@500&display=swap" rel="stylesheet">
<style>
:root{{--patina:#1faa6b;--lava:#e5484d;--ember:#fc5000;--violet:#524ae9;--sulfur:#f5f28e;--limestone:#f7f6f2;--pumice:#e2e2df;--obsidian:#070607;--chalk:#fff}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
.card{{scroll-margin-top:16px}}
a{{color:inherit;text-decoration-thickness:1.5px;text-underline-offset:3px}}
body{{margin:0;background:var(--pumice);color:var(--obsidian);font:500 16px/1.55 "DM Sans",system-ui,sans-serif}}
main{{max-width:40rem;margin:0 auto;padding:16px}}
h1,h2,h3,.rank,.score{{font-family:Anton,"Bebas Neue",Impact,sans-serif;font-weight:400;letter-spacing:.02em;margin:0}}
h1{{font-size:clamp(48px,14vw,96px);line-height:.95}}
h2{{font-size:clamp(32px,9vw,48px);line-height:1;margin:48px 0 16px}}
h3{{font-size:28px;line-height:1.1;margin-top:8px}}
.hero{{position:relative;overflow:hidden;border-radius:40px;padding:32px 24px;color:var(--chalk);
background:linear-gradient(135deg,var(--violet) 50%,var(--ember))}}
.hero::after{{content:"";position:absolute;inset:0;pointer-events:none;
background:radial-gradient(circle,var(--ember) 1.8px,transparent 2.2px) 0 0/10px 10px;
-webkit-mask-image:linear-gradient(135deg,transparent 60%,#000 90%);mask-image:linear-gradient(135deg,transparent 60%,#000 90%)}}
.hero>*{{position:relative;z-index:1}}
.hero p{{font-size:18px;margin:16px 0 0}}
.jump{{display:inline-flex;align-items:center;min-height:44px;margin-top:16px;padding:0 20px;border:1.5px solid var(--chalk);border-radius:800px;text-decoration:none}}
h2{{scroll-margin-top:16px}}
.hero .asof{{font-size:14px;opacity:.9}}
.card{{background:var(--limestone);border-radius:40px;padding:24px;margin:16px 0}}
.card-top{{display:flex;justify-content:space-between;align-items:center}}
.rank{{font-size:48px;line-height:1}}
.score{{background:var(--patina);color:var(--obsidian);border-radius:800px;padding:6px 18px;font-size:28px}}
.score.out{{background:var(--lava)}}
.score small{{font-family:"DM Sans",sans-serif;font-size:14px}}
.meta{{margin:0;font-size:14px}}
.tag{{display:inline-block;background:var(--sulfur);border-radius:800px;padding:4px 12px;font-size:14px;margin:8px 0 0}}
details{{margin-top:16px}}
summary{{display:flex;align-items:center;min-height:44px;padding:0 20px;border:1.5px solid var(--obsidian);border-radius:800px;cursor:pointer;list-style:none;width:max-content}}
summary::-webkit-details-marker{{display:none}}
summary::after{{content:"+";margin-left:12px;font-size:20px}}
details[open] summary::after{{content:"−"}}
.row{{border-bottom:1.5px dotted var(--obsidian);padding:12px 0}}
.row:last-child{{border-bottom:0}}
.row-top{{display:flex;justify-content:space-between;align-items:center;gap:12px}}
.row-top b{{font-weight:700}}
.pts{{border:2px solid;border-radius:800px;padding:1px 12px;font-size:14px;white-space:nowrap}}
.pts.full{{border-color:#138a55}}.pts.part{{border-color:#a88700}}.pts.none{{border-color:var(--lava)}}
.val{{display:inline-block;background:var(--pumice);border-radius:800px;padding:2px 12px;margin:6px 0 4px}}
.src{{font-size:14px;opacity:.75}}
q{{display:block;font-style:italic;margin-top:4px}}
.box{{background:var(--limestone);border-radius:40px;padding:24px;margin:16px 0}}
.box h3{{font-size:24px}}
ol,ul{{padding-left:22px}}
li{{margin:6px 0}}
footer{{font-size:14px;margin:48px 0 24px;opacity:.8}}
</style></head><body><main>

<section class="hero">
<h1>Bring these five sites on Thursday</h1>
<p>Picked from 40 candidates using the rubric agreed with the sponsor. <b>Three come with a condition to check first.</b></p>
<a class="jump" href="#takeaways">Click here for summary</a>
<p class="asof">Based on the site tracker export of 21 Sep 2026.</p>
</section>

<h2>The five</h2>
{cards}

<h2>Why not these</h2>
<article class="card" id="{anchor(s009)}"><div class="card-top"><h3>{escape(s009['name'])}</h3><span class="score out">{s009['score']:g}<small>/100</small></span></div><p class="meta">{escape(s009['site_id'])} · would score this if it weren't excluded</p>
<span class="tag">Left out: possible nature reserve</span>
<p>On paper it's the best site. But a field note says part of the plot is inside a protected nature reserve. The reserve boundary needs verification before the site can be reconsidered. We can't build in a reserve, so it stays excluded until then.</p>
<q>{escape(s009['kill']['quote'])}</q>{breakdown(s009)}</article>
<article class="card" id="{anchor(s013)}"><div class="card-top"><h3>{escape(s013['name'])}</h3><span class="score out">{s013['score']:g}<small>/100</small></span></div><p class="meta">{escape(s013['site_id'])}</p>
<span class="tag">Left out: plot too small</span>
<p>The land registry says 2,400 m², but that record is from 2017. A recent field note says half was sold and only about 700 m² remains. A 2 MW battery needs about 1,200 m².</p>
<q>{escape(s013['criteria']['C6']['quote'])}</q>{breakdown(s013)}</article>
<article class="card" id="{anchor(s024)}"><div class="card-top"><h3>{escape(s024['name'])}</h3><span class="score out">{s024['score']:g}<small>/100</small></span></div><p class="meta">{escape(s024['site_id'])} · {s024['best_case']:g} if everything checks out</p>
<span class="tag">Left out: not enough evidence</span>
<p>It has one of the strongest grid figures ({s024['criteria']['C1']['value']:g} MW, {s024['criteria']['C2']['value']:g} km away). But there is no land registry record and no field note, so we don't know the owner, the plot size, the flood risk or local opinion. Worth a visit, not a pitch.</p>{breakdown(s024)}</article>

<h2>How sure we are</h2>
<div class="box">
<p><b>"6/6 known" means every part of the rubric has a value from a source.</b> It does not mean the site is confirmed feasible. None of these sites has had a feasibility study; that is exactly what the sponsor would pay for.</p>
<ul>
<li>Grid figures are the official ones, published quarterly (these are from June 2026).</li>
<li>Letters of intent are non-binding.</li>
<li>The notes on council and neighbours are the team's own reports.</li>
<li>Where a figure was missing we scored it zero, not an average. "If everything checks out" assumes missing parts get full marks; known values stay as they are.</li>
</ul></div>

<h2 id="takeaways">Takeaways</h2>
<div class="box"><ol>
<li>Bring these five: {", ".join(link(r) for r in top)}. These are recommendations for feasibility studies, not confirmed buildable sites.</li>
<li>Confirm {link(s003, "Kessby")}'s revenue-share terms and the status of {link(s027, "Varne")}'s noise report.</li>
<li>Confirm the next step toward a signed owner agreement at {link(s014, "Orlund")}.</li>
<li>Confirm the reserve boundary at {link(s009, "Esk Mill")} (S-009). If it's outside, it's the strongest site.</li>
<li>Look up {link(s024, "Pellick Lane")} (S-024) and Gorse Hill (S-036) in the land registry and find their owners.</li>
</ol></div>

<footer>Wishing you all the best for the meeting. I remain available for any further information.</footer>
</main></body></html>
"""
    out = ROOT / "site/index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html)
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
