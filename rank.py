"""Score and rank the candidate battery sites.

Claude reads the field notes (see prompts/); this file decides every score.
Run: python rank.py            ranked table
     python rank.py S-013      why one site scored what it did
     python rank.py --check    extraction vs hand labels
"""
import argparse
import csv
import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).parent
OUT = ROOT / "out"

# --- Sponsor rubric: the only place the numbers live -------------------------
BEST_CASE = "Assumes missing criteria receive maximum points. Existing values and estimates stay unchanged."
WEIGHTS = {"C1": 30, "C2": 15, "C3": 20, "C4": 10, "C5": 15, "C6": 10}
LABELS = {"C1": "Grid headroom", "C2": "Distance to substation", "C3": "Landowner",
          "C4": "Council / community", "C5": "Flood zone", "C6": "Usable area"}
OWNER = {"loi_signed": 5, "in_talks": 3, "not_contacted": 1, "refused": 0}
SENTIMENT = {"supportive": 5, "neutral": 3, "opposed": 0}
FLOOD = {"none": 5, "low": 4, "medium": 2, "high": 0}


def tier_headroom(mw):  # exactly 2.0 counts as "2-4", like ">= 4" does
    return 5 if mw >= 4 else 3 if mw >= 2 else 1 if mw >= 1 else 0


def tier_distance(km):
    return 5 if km <= 1 else 3 if km <= 3 else 1 if km <= 6 else 0


def tier_area(m2):
    return 5 if m2 >= 1200 else 2 if m2 >= 800 else 0


def crit(value, tier, source, quote=None, note=None):
    """One criterion's evidence. tier None = unknown (scores 0, best case 5)."""
    return {"value": value, "tier": tier, "source": source, "quote": quote, "note": note}


# --- Load + data fixes -------------------------------------------------------
def load():
    sites = json.loads((ROOT / "data/sites.json").read_text())["sites"]
    with open(ROOT / "data/fetch_log.csv") as f:
        log = {(r["site_id"], r["source"]): r for r in csv.DictReader(f)}
    return merge_duplicates(sites), log


def merge_duplicates(sites):
    """Same land parcel logged twice (S-017 / S-031): one site, all notes kept."""
    by_parcel = {}
    for s in sites:
        s["ids"] = [s["site_id"]]
        first = by_parcel.setdefault(s["parcel_id"], s)
        if first is not s:
            first["ids"].append(s["site_id"])
            first["site_id"] += "/" + s["site_id"]
            first["field_notes"] += s["field_notes"]
    return list(by_parcel.values())


def grid_criteria(s, log):
    g = s["sources"]["gridmap"] or {}
    msg = log[(s["ids"][0], "gridmap")]["message"]
    if g.get("headroom") is not None:
        # Nordholm publishes kW and the feed doesn't convert. Delete once it does.
        mw = g["headroom"] / 1000 if s["region"] == "Nordholm" else g["headroom"]
        km = g["substation_distance_km"]
        asof = f"as of {g['data_as_of']}"
        return crit(mw, tier_headroom(mw), "gridmap", note=asof), crit(km, tier_distance(km), "gridmap", note=asof)
    if "no substation" in msg:  # a real answer, not missing data
        return crit(None, 0, "gridmap", note=msg), crit(None, 0, "gridmap", note=msg)
    # Fetch failed (503): official figure unknown. Vendor estimate, low end of its band.
    v = s["sources"]["vendor_estimate"]
    far = crit(None, None, "unknown", note=f"gridmap fetch failed: {msg}")
    if not v:
        return dict(far), far
    mw = round(v["headroom_mw_est"] * (1 - v["band_pct"] / 100), 2)
    note = f"unverified: vendor estimate {v['headroom_mw_est']} MW ±{v['band_pct']}%, scored at low end"
    return crit(mw, tier_headroom(mw), "vendor-lowband", note=note), far


# --- Claude reads the notes --------------------------------------------------
MODEL = os.environ.get("MODEL", "claude-opus-5")
PROMPT = (ROOT / "prompts/extract_notes.md").read_text()


def signal(values, value_type="string"):
    value = {"type": value_type, "enum": values} if values else {"type": value_type}
    return {"type": "object", "additionalProperties": False, "required": ["value", "quote"],
            "properties": {"value": value, "quote": {"type": "string"}}}


SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["owner_status", "sentiment", "area_m2", "protected_area", "caveats"],
    "properties": {
        "owner_status": signal(["loi_signed", "in_talks", "not_contacted", "refused", "unknown"]),
        "sentiment": signal(["supportive", "neutral", "opposed", "unknown"]),
        "area_m2": signal(None, ["integer", "null"]),
        "protected_area": signal(["protected", "unknown"]),
        "caveats": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["detail", "quote"],
            "properties": {"detail": {"type": "string"}, "quote": {"type": "string"}}}},
    },
}


def extract(client, site):
    """One call per site. Returns Claude's raw JSON; nothing is trusted until verify()."""
    notes = sorted(site["field_notes"], key=lambda n: n["date"])
    lines = [f"[{n['date']}] (owner_status: {n.get('owner_status') or 'none'}) {n['text']}" for n in notes]
    resp = client.messages.create(
        model=MODEL, max_tokens=16000, system=PROMPT,
        messages=[{"role": "user", "content": "\n".join(lines)}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
    )
    if resp.stop_reason != "end_turn":
        raise RuntimeError(f"{site['site_id']}: stop_reason {resp.stop_reason}")
    return json.loads(next(b.text for b in resp.content if b.type == "text"))


def extractions(sites, refresh):
    """Cached per site in out/extractions.json; only missing sites hit the API.
    refresh: None = use cache, [] = re-read every site, ["S-013", ...] = re-read those."""
    path = OUT / "extractions.json"
    cache = json.loads(path.read_text()) if path.exists() and refresh != [] else {}
    for sid in list(cache):
        if refresh and set(sid.split("/")) & set(refresh):
            del cache[sid]
    client, calls = None, 0
    for s in sites:
        if s["site_id"] in cache or not s["field_notes"]:
            continue
        client = client or anthropic.Anthropic()
        print(f"reading notes: {s['site_id']}")
        cache[s["site_id"]] = extract(client, s)
        calls += 1
        OUT.mkdir(exist_ok=True)
        path.write_text(json.dumps(cache, indent=2, sort_keys=True))  # after each site
    return cache, calls


def norm(text):
    return " ".join(text.split())


def verify(raw, notes):
    """Keep a signal only if its quote is verbatim in a note. Date comes from that note."""
    def source(quote):
        return next((n for n in notes if quote and norm(quote) in norm(n["text"])), None)

    out, rejected = {}, []
    for key in ("owner_status", "sentiment", "area_m2", "protected_area"):
        sig = raw.get(key) or {}
        if sig.get("value") in ("unknown", None):
            continue
        n = source(sig["quote"])
        if not n:
            rejected.append({"field": key, **sig})
            continue
        out[key] = {"value": sig["value"], "quote": sig["quote"], "date": n["date"],
                    "check": key == "sentiment" and bool(n.get("owner_status"))}
    out["caveats"] = [c for c in raw.get("caveats", []) if source(c["quote"])]
    rejected += [{"field": "caveat", **c} for c in raw.get("caveats", []) if not source(c["quote"])]
    out["rejected"] = rejected
    return out


FIELDS = ("owner_status", "sentiment", "area_m2", "protected_area")


def check(sites, raw):
    """Compare Claude's verified signals with hand labels (eval/gold_notes.json, one per distinct note)."""
    gold = json.loads((ROOT / "eval/gold_notes.json").read_text())
    agree = {f: 0 for f in FIELDS}
    mismatches, rejected, compared = [], [], 0
    for s in sites:
        if not s["field_notes"]:
            continue
        compared += 1
        got = verify(raw.get(s["site_id"], {}), s["field_notes"])
        rejected += [(s["site_id"], r) for r in got["rejected"]]
        for f in FIELDS:
            labelled = [(n["date"], gold[n["text"]][f]) for n in s["field_notes"]
                        if gold[n["text"]][f] not in ("unknown", None)]
            want = max(labelled)[1] if labelled else "unknown"
            have = got.get(f, {}).get("value", "unknown")
            if want == have:
                agree[f] += 1
            else:
                mismatches.append((s["site_id"], f, want, have, got.get(f, {}).get("quote")))
    print(f"Sites compared: {compared} (S-024 has no notes)\n")
    print("| Signal | Agree |\n|---|---|")
    for f in FIELDS:
        print(f"| {f} | {agree[f]}/{compared} |")
    print(f"\nMismatches: {len(mismatches) or 'none'}")
    for m in mismatches:
        print(f"- {m[0]} {m[1]}: hand label `{m[2]}`, Claude `{m[3]}`" + (f' — "{m[4]}"' if m[4] else ""))
    print(f"\nQuotes rejected (not verbatim in the notes): {len(rejected) or 'none'}")
    for sid, r in rejected:
        print(f"- {sid} {r['field']}: \"{r['quote']}\"")


def headroom_conflict(s, c1):
    """Official figure scores; warn when the vendor's central estimate lands in a different tier."""
    v = s["sources"]["vendor_estimate"]
    if c1["source"] != "gridmap" or c1["value"] is None or not v:
        return None
    if tier_headroom(v["headroom_mw_est"]) == c1["tier"]:
        return None
    return (f"headroom sources disagree: official {c1['value']} MW (grid operator, "
            f"{c1['note']}) vs vendor estimate {v['headroom_mw_est']} MW (estimated {v['estimated_at']}). "
            "Vendor model is unvalidated; check with the grid operator. Score uses the official figure.")


def latest_owner_status(notes):
    typed = [n for n in notes if n.get("owner_status")]
    return max(typed, key=lambda n: n["date"]) if typed else None


# --- Scoring -----------------------------------------------------------------
def evaluate(s, log, ex):
    """ex = verified Claude signals for this site ({} if not extracted yet)."""
    c = {}
    c["C1"], c["C2"] = grid_criteria(s, log)

    n = latest_owner_status(s["field_notes"])
    claude_owner = ex.get("owner_status", {}).get("value")
    c["C3"] = (crit(n["owner_status"], OWNER[n["owner_status"]], "typed-field",
                    quote=n["text"], note=n["date"]) if n else
               crit(None, None, "unknown", note="no owner status in notes"))
    c["C3"]["claude"] = claude_owner

    sent = ex.get("sentiment", {})
    c["C4"] = (crit(sent["value"], SENTIMENT[sent["value"]], "note", quote=sent["quote"], note=sent.get("date"))
               if sent.get("value") in SENTIMENT else crit(None, None, "unknown", note="no council/community note"))

    lr = s["sources"]["landreg"]
    if lr is None:
        c["C5"] = crit(None, None, "unknown", note="parcel not in land registry")
        c["C6"] = crit(None, None, "unknown", note="parcel not in land registry")
    else:
        c["C5"] = crit(lr["flood_zone"], FLOOD[lr["flood_zone"]], "landreg", note=lr["record_date"])
        area = ex.get("area_m2", {})
        if area and area["date"] > lr["record_date"]:
            c["C6"] = crit(area["value"], tier_area(area["value"]), "note", quote=area["quote"],
                           note=f"note {area['date']} overrides registry {lr['area_m2']} m² ({lr['record_date']})")
        else:
            c["C6"] = crit(lr["area_m2"], tier_area(lr["area_m2"]), "landreg", note=lr["record_date"])

    kill = None
    if lr and lr["protected_area"]:
        kill = {"source": "registry", "quote": None, "note": "land registry: protected nature area"}
    elif ex.get("protected_area", {}).get("value") == "protected":
        p = ex["protected_area"]
        kill = {"source": "note", "quote": p["quote"], "note": "field note says protected area; needs checking"}

    flags = []
    if c["C1"]["source"] == "vendor-lowband":
        flags.append("headroom unverified (vendor estimate)")
    if conflict := headroom_conflict(s, c["C1"]):
        flags.append(conflict)
    if claude_owner and n and claude_owner != n["owner_status"]:
        flags.append(f"check owner: typed '{n['owner_status']}', notes read as '{claude_owner}'")
    if sent.get("check"):
        flags.append("check sentiment: quote came from an owner note")
    if c["C6"]["source"] == "note":
        flags.append("area from a field note, approximate: confirm size")
    if len(s["ids"]) > 1:
        flags.append("logged twice (" + ", ".join(s["ids"]) + "), merged")

    for k, v in c.items():  # page.py reads these; the rubric lives only here
        v["weight"], v["points"] = WEIGHTS[k], WEIGHTS[k] * (v["tier"] or 0) / 5
    known = sum(v["tier"] is not None for v in c.values())
    return {
        "site_id": s["site_id"], "name": s["name"], "region": s["region"],
        "score": points(c), "best_case": points(c, best=True), "known": known,
        "criteria": c, "kill": kill, "flags": flags, "caveats": ex.get("caveats", []),
        "rejected_quotes": ex.get("rejected", []),
    }


def points(c, best=False):
    return round(sum(WEIGHTS[k] * (v["tier"] if v["tier"] is not None else 5 * best) / 5
                     for k, v in c.items()), 1)


# --- Output ------------------------------------------------------------------
def print_table(ranked, excluded):
    print(f"{'#':>2}  {'site':<12}{'name':<26}{'score':>6}{'best*':>6}  known  flags")
    for i, r in enumerate(ranked, 1):
        print(f"{i:>2}  {r['site_id']:<12}{r['name'][:25]:<26}{r['score']:>6}{r['best_case']:>6}  "
              f"{r['known']}/6    {'; '.join(r['flags'])}")
        if i == 5:
            print("    " + "-" * 60 + " shortlist above")
    print(f"\n* best case: {BEST_CASE}")
    print("\nExcluded (protected nature area):")
    for r in excluded:
        print(f"    {r['site_id']:<12}{r['name']:<26}{r['kill']['note']}"
              + (f' — "{r["kill"]["quote"]}"' if r["kill"]["quote"] else ""))


def print_site(r):
    print(f"{r['site_id']} {r['name']} ({r['region']})  score {r['score']}  best case {r['best_case']}")
    print(f"  (best case: {BEST_CASE})")
    if r["kill"]:
        print(f"  EXCLUDED: {r['kill']['note']} [{r['kill']['source']}]"
              + (f' "{r["kill"]["quote"]}"' if r["kill"]["quote"] else ""))
    for k, v in r["criteria"].items():
        tier = "unknown" if v["tier"] is None else f"tier {v['tier']}"
        print(f"  {k} {LABELS[k]:<24}{str(v['value']):<14}{tier:<9}{v["points"]:>5.1f}/{v["weight"]}  [{v['source']}]"
              + (f"  {v['note']}" if v["note"] else ""))
        if v["quote"]:
            print(f'       "{v["quote"]}"')
    for f in r["flags"]:
        print(f"  ! {f}")
    for cav in r["caveats"]:
        print(f'  caveat: {cav["detail"]} — "{cav["quote"]}"')


def main():
    load_dotenv(ROOT / ".env", override=True)  # repo key wins over any shell key
    ap = argparse.ArgumentParser()
    ap.add_argument("site", nargs="?", help="show why one site scored what it did, e.g. S-013")
    ap.add_argument("--check", action="store_true", help="compare Claude's extraction with hand labels")
    ap.add_argument("--refresh", nargs="*", metavar="SITE",
                    help="re-read notes with Claude: all sites, or only the ones named")
    args = ap.parse_args()

    sites, log = load()
    raw, calls = extractions(sites, args.refresh)
    footer = f"\nClaude calls this run: {calls} ({len(raw) - calls} from cache out/extractions.json)"
    if args.check:
        check(sites, raw)
        return print(footer)
    results = [evaluate(s, log, verify(raw.get(s["site_id"], {}), s["field_notes"])) for s in sites]

    by_id = {r["site_id"]: r for r in results}
    assert len(results) == 39, len(results)
    assert by_id["S-020"]["criteria"]["C3"]["value"] == "refused"
    assert by_id["S-033"]["kill"]["source"] == "registry"
    assert by_id["S-003"]["score"] == 97, by_id["S-003"]["score"]  # formula check
    assert by_id["S-013"]["criteria"]["C6"]["value"] == 700
    assert by_id["S-009"]["kill"]["source"] == "note"

    ranked = sorted((r for r in results if not r["kill"]), key=lambda r: (-r["score"], -r["known"]))
    excluded = [r for r in results if r["kill"]]
    OUT.mkdir(exist_ok=True)
    (OUT / "results.json").write_text(json.dumps({"best_case_means": BEST_CASE, "ranked": ranked, "excluded": excluded}, indent=2))

    if args.site:
        match = [r for r in results if args.site in r["site_id"].split("/")]
        print_site(match[0]) if match else print(f"no site {args.site}")
    else:
        print_table(ranked, excluded)
    print(footer)


if __name__ == "__main__":
    main()
