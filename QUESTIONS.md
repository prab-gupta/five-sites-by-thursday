# Questions before building

Nobody is reachable before Thursday. These are the questions I would ask, each with the assumption I'm going ahead with. My view on Jonas's plan is at the end.

## For Jonas (data pull and his plan)

1. **What does "dataset average" mean here?** Is it the average across all 40 sites, across the sites in the same region, or across the same source? Each one gives a different number, and none of them describes the actual site.
   *Assumption:* Use the rubric weights exactly as agreed with the sponsor (30/15/20/10/15/10). No averaging anywhere. If I think a weight is wrong, I raise it with Maren afterwards instead of changing it myself.
2. **Why fill missing values with an average at all?** A site with no data would then score like a typical site. Shouldn't a missing value count against the site, or at least be marked as unverified, instead of being hidden?
   *Assumption:* A missing value scores 0 on that criterion and is marked "unknown", so a site that wasn't checked can never outrank one that was. The code never makes up a value.
3. **Where does the kill rule fit in your plan?** A weighted sum sorted descending never removes sites inside a protected nature area. Do we apply the kill rule before ranking?
   *Assumption:* Yes. Sites inside a protected nature area are excluded before ranking, whether the registry says so or a field note does. They're listed separately with the reason.
4. **Nordholm publishes headroom in kW, not MW.** Should the conversion happen in the daily extraction job, so the tracker always stores MW, or should I handle it in the scoring script for now?
   *Assumption:* I convert Nordholm kW to MW (÷ 1,000) in the scoring script and flag it for Jonas to fix in the extraction job.
5. **Is the vendor data reliable enough to use?** It comes from an unvalidated machine-learning model on a trial licence. Are we comfortable using it as a one-to-one fallback for gridmap, even when its stated uncertainty band is wide?
   *Assumption:* Vendor data is only used when gridmap has no figure, and even then I take the low end of its own uncertainty band: estimate × (1 − band_pct/100). The site is flagged "unverified headroom".

## For Maren

6. **Can I show how each site scored on each criterion, not just the total?** I understand the sponsor isn't technical. I'll keep the criteria in plain language, but a single number alone doesn't explain why a site made the list.
   *Assumption:* Yes. The page shows each site's score per criterion in plain language, next to the total.
7. **If the landowner hasn't been contacted yet, should the site be excluded?** Or can it stay on the shortlist with a lower score?
   *Assumption:* Not excluded. The rubric already scores "not contacted" low (1 out of 5), which is enough of a penalty.
8. **If a top-scoring site depends on the vendor's estimate because the official gridmap figure is missing, is that too risky to put in front of the sponsor?**
   *Assumption:* Too risky to present as confirmed. The low-band rule ranks these sites lower, and any that still make the list are labelled "headroom unverified, check first".

## For the business development team (MA, JK, RS, AV)

9. **Why is `owner_status` empty on notes about the council or municipality?** Was that deliberate, since those notes are about community sentiment and not the landowner? If so, should the tracker get a separate structured field for council and community sentiment?
   *Assumption:* These notes follow a pattern: they record what an authority (council, councillor, municipal officer) said, so they're about sentiment, not the landowner. Claude extracts owner status and community sentiment as separate signals, each with its exact quote, and the latest dated note wins.
10. **The land registry has no record for some parcels.** During your site visits, did you write down an estimated area or notice any flood risk that never made it into the tracker?
   *Assumption:* No hidden data. Missing registry fields score 0 and are marked "unknown", and the page lists them as things to check.

## What I think of Jonas's plan

**What's right:** one weighted sum using the rubric we agreed with the sponsor, one score per site, sorted. That's what Maren asked for, and it's simple enough to explain. Using all three sources is also right.

**What worries me:**
- **Averaging hides gaps.** A site with no data gets a typical score, so an unchecked site can outrank a checked one (Q1, Q2, Q10).
- **The vendor as a 1:1 fallback.** An unvalidated ML estimate gets treated the same as the official figure the sponsor trusts (Q5, Q8).
- **No kill rule.** A weighted sum never removes protected-area sites (Q3).
- **Units.** Nordholm's kW figures would read as huge MW values, so every Nordholm site would get the top grid score (Q4).
- **The notes are ignored.** Owner status and community sentiment only live in the field notes, so "load sites.json" alone can't score C3 or C4 (Q9).
