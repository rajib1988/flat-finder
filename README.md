# Flat Finder · Kolkata & Delhi

Every housing society in Kolkata and Delhi on one night map, built on [kairothq/flat-finder](https://github.com/kairothq/flat-finder) (the Gurugram original at flat-finder.pages.dev). Gurugram's data is kept as a third city.

**Site:** https://rajib1988.github.io/flat-finder/

## What's on the map

- **Every society from Magicbricks**, drawn with its real OpenStreetMap buildings where they're mapped (otherwise towers drawn from the listed tower count, marked "approximate shape").
- **Building type:** *Complex / gated society* (2+ towers, 60+ units, 1.5+ acres, or clubhouse/pool/gym listed) or *Standalone building*. Villas and plots are shown separately. Each card says what the call was based on.
- **Age of construction:** years since the possession year, or "under construction".
- **Approval:**
  - *RERA registered*: the RERA number as listed, with a link to check it on WBRERA, Delhi RERA or HRERA.
  - *Before RERA*: completed before 2017, so no registration is expected.
  - *No RERA number listed*: check before paying anything.
  - *Govt / cooperative*: built by DDA, HIDCO, NKDA, a Housing Board or NBCC, or a CGHS cooperative society, going by the developer name.
- **Nearby places on the map:** metro and rail stations, schools, hospitals, parks, malls and markets from OpenStreetMap, switchable from "Show on map". Each card lists the nearest of each with the distance.
- **Prices:** buy and rent medians of live Magicbricks listings for each BHK, estimates marked "~", and an **area guide** from rent reports (`data/localities.json`) for the nearest locality.
- Filters for BHK, budget, size, smallest bedroom, amenities, distance to a park, metro or school, and ready to move. Plus My list, CSV downloads, and street, dark and day maps.
- **Update data** (top bar) opens the companion page. There you can paste Facebook, X and Instagram posts for Claude to read, edit locality numbers, and add localities.

## How the data stays fresh

| What | How often | How |
|---|---|---|
| Societies, prices, listings, buildings, nearby places | Monthly, 2nd at 02:00 IST | GitHub Action `.github/workflows/update-data.yml` crawls Magicbricks and OpenStreetMap, rebuilds, commits, redeploys |
| Locality rent ranges (`data/localities.json`) | Monthly, 3rd | A Claude scheduled task reads the latest rent reports and commits the new ranges |
| Your own posts and edits | Whenever you add them | The Update data page |

To refresh now: **Actions → Monthly data refresh → Run workflow**. The crawl takes 1–3 hours per city.

## One-time setup

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
2. **Actions → Monthly data refresh → Run workflow** builds Kolkata and Delhi for the first time. Until it finishes, the site shows Gurugram.

If Magicbricks blocks GitHub's servers (the crawl step fails with errors in the log), run the pipeline on your own computer and push the result:

```bash
cd pipeline
python3 mb_crawl.py list kolkata && python3 mb_crawl.py projects kolkata
python3 osm_fetch.py kolkata && python3 build_city.py kolkata
# same for delhi, then:
python3 write_cities.py && git add ../web/public/data && git commit -m "Data refresh" && git push
```

## Run the site locally

```bash
cd web && npm install && npm run dev     # http://localhost:5173/?city=kolkata
```

Useful links: `?city=kolkata`, `?city=delhi`, `?map=light`, `?open=<society id>`, `?nointro`.

## Caveats

- "Complex" vs "standalone", age and RERA come from what the portal lists. A missing RERA number on the portal doesn't prove the project is unregistered, so check the state RERA site. Building-plan sanction (KMC, MCD, DDA) isn't published in any open dataset, so it isn't shown.
- Rent ranges in the area guide are indicative asking prices from public reports, not quotes.

## Sources

Magicbricks project pages (listing facts, live listings, ratings, reviews), OpenStreetMap contributors (buildings, areas, nearby places; ODbL), Esri World Imagery and OpenFreeMap (base maps), WBRERA, Delhi RERA and HRERA (for checking registrations), and public rent reports for the area guide (listed in `data/localities.json`). Original code and Gurugram research by [kairothq/flat-finder](https://github.com/kairothq/flat-finder).
