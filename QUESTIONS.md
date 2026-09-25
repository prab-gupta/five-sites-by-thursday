# Questions before building

Nobody is reachable before Thursday. These are the questions I would ask. What I think of Jonas's plan, and the assumption I'm making for each question, are further down.

## For Jonas (data pull and his plan)

1. **What does "dataset average" mean here?** Is it the average across all 40 sites, across the sites in the same region, or across the same source? Each one gives a different number, and none of them describes the actual site.
2. **Why fill missing values with an average at all?** A site with no data would then score like a typical site. Shouldn't a missing value count against the site, or at least be marked as unverified, instead of being hidden?
3. **Where does the kill rule fit in your plan?** A weighted sum sorted descending never removes sites inside a protected nature area. Do we apply the kill rule before ranking?
4. **Nordholm publishes headroom in kW, not MW.** Should the conversion happen in the daily extraction job, so the tracker always stores MW, or should I handle it in the scoring script for now?
5. **Is the vendor data reliable enough to use?** It comes from an unvalidated machine-learning model on a trial licence. Are we comfortable using it as a one-to-one fallback for gridmap, even when its stated uncertainty band is wide?

## For Maren

6. **Can I show how each site scored on each criterion, not just the total?** I understand the sponsor isn't technical. I'll keep the criteria in plain language, but a single number alone doesn't explain why a site made the list.
7. **If the landowner hasn't been contacted yet, should the site be excluded?** Or can it stay on the shortlist with a lower score?
8. **If a top-scoring site depends on the vendor's estimate because the official gridmap figure is missing, is that too risky to put in front of the sponsor?**

## For the business development team (MA, JK, RS, AV)

9. **Why is `owner_status` empty on notes about the council or municipality?** Was that deliberate, since those notes are about community sentiment and not the landowner? If so, should the tracker get a separate structured field for council and community sentiment?
10. **The land registry has no record for some parcels.** During your site visits, did you write down an estimated area or notice any flood risk that never made it into the tracker?
