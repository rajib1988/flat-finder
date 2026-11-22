"""Polite, cached, resumable Magicbricks crawler.

usage: python mb_crawl.py list <city>      # all list pages -> out/<city>/mb_index.json
       python mb_crawl.py projects <city>  # every project page -> out/<city>/mb_projects.json
<city> is a key in data/cities.json (default gurgaon).
"""
import gzip
import hashlib
import json
import re
import pathlib
import sys
import time
import urllib.request

import mb_parse

ROOT = pathlib.Path(__file__).parent
CACHE = ROOT / "cache" / "mb"
OUT = ROOT / "out"
CITIES = json.loads((ROOT.parent / "data" / "cities.json").read_text())
CITY = next((a for a in sys.argv[1:] if a in CITIES), "gurgaon")
CFG = CITIES[CITY]
SLUGS = [CFG["magicbricks"]] + CFG.get("magicbricks_alt", [])
LIST_URL = "https://www.magicbricks.com/residential-projects-in-" + SLUGS[0] + "-nprid/page-{}"
OUT = OUT / CITY
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
DELAY = 1.0


def fetch(url):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".html.gz")
    if f.exists() and f.stat().st_size > 2000:
        return gzip.decompress(f.read_bytes()).decode("utf-8", "ignore")
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            html = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "ignore")
            f.write_bytes(gzip.compress(html.encode("utf-8"), 9))
            time.sleep(DELAY)
            return html
        except Exception as e:  # network hiccup: back off and retry
            print("  retry", attempt + 1, url, e, flush=True)
            time.sleep(5 * (attempt + 1))
    return None


def crawl_list():
    global LIST_URL
    total = None
    for slug in SLUGS:  # the portal's city slug is not always the city name (Delhi: new-delhi or delhi)
        LIST_URL = "https://www.magicbricks.com/residential-projects-in-" + slug + "-nprid/page-{}"
        first = fetch(LIST_URL.format(1))
        total = mb_parse.parse_total(first) if first else None
        print("slug", slug, "->", total, "projects" if total else ("no project count on page: " + (first or "no response")[:200].replace("\n", " ")), flush=True)
        if total:
            break
    if not total:
        # discover the slug from links on a city page that is known to work
        word = CFG["name"].lower().split()[-1]
        found = set()
        for probe in ("https://www.magicbricks.com/residential-projects-in-kolkata-nprid/page-1", "https://www.magicbricks.com/"):
            html = fetch(probe) or ""
            found |= set(re.findall(r"residential-projects-in-([A-Za-z0-9-]+)-nprid", html))
            found |= {m for m in re.findall(r"new-projects-([A-Za-z0-9-]+)", html)}
        cands = sorted(c for c in found if word in c.lower() and c not in SLUGS)
        print("slugs seen on other pages:", sorted(found)[:80], flush=True)
        for probe in ("https://www.magicbricks.com/residential-projects-in-kolkata-nprid/page-1", "https://www.magicbricks.com/",
                      "https://www.magicbricks.com/new-projects-New-Delhi", "https://www.magicbricks.com/new-projects-Delhi"):
            html = fetch(probe) or ""
            links = sorted(set(re.findall(r'(?:href=|"url":|")["\']?((?:https://www\.magicbricks\.com)?/[^"\'\s<>]*(?:nprid|projects?-|Delhi|delhi)[^"\'\s<>]*)', html)))
            print("PROBE", probe, "len", len(html), "links:", links[:120], flush=True)
            if len(html) < 20000:
                print("BODY", probe, html[:4200].replace("\n", " "), flush=True)
        for slug in cands:
            LIST_URL = "https://www.magicbricks.com/residential-projects-in-" + slug + "-nprid/page-{}"
            first = fetch(LIST_URL.format(1))
            total = mb_parse.parse_total(first) if first else None
            print("discovered slug", slug, "->", total, flush=True)
            if total:
                break
    if not total and CFG.get("magicbricks_localities"):
        return crawl_localities()
    if not total:
        raise SystemExit("Could not read the project list for " + CITY + " (tried " + ", ".join(SLUGS) + ")")
    pages = -(-total // 20)
    projects = {}
    for n in range(1, pages + 1):
        html = fetch(LIST_URL.format(n))
        if not html:
            continue
        for c in mb_parse.parse_list_page(html):
            projects[c["psmid"]] = mb_parse.card_to_project(c)
        print(f"list {n}/{pages}: {len(projects)} projects", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "mb_index.json").write_text(json.dumps(list(projects.values()), indent=0))
    print("total reported", total, "collected", len(projects))


def crawl_localities():
    """No city-wide list (Delhi): union the per-locality project lists, e.g. residential-projects-dwarka-in-new-delhi-nprid."""
    projects = {}
    for loc in CFG["magicbricks_localities"][: int(__import__("os").environ.get("MB_LOC_LIMIT", "999"))]:
        for slug in SLUGS[:2]:
            base = f"https://www.magicbricks.com/residential-projects-{loc}-in-{slug}-nprid"
            first = fetch(base)
            total = mb_parse.parse_total(first) if first else None
            if not total:
                continue
            pages = -(-total // 20)
            for n in range(1, pages + 1):
                html = first if n == 1 else fetch(f"{base}/page-{n}")
                for c in mb_parse.parse_list_page(html or ""):
                    projects[c["psmid"]] = mb_parse.card_to_project(c)
            print(f"locality {loc} ({slug}): {total} listed, {len(projects)} projects so far", flush=True)
            break
        else:
            print(f"locality {loc}: no list page", flush=True)
    if not projects:
        for probe in ("https://www.magicbricks.com/flats-in-new-delhi-for-sale-pppfs", "https://www.magicbricks.com/property-for-sale-in-new-delhi-pppfs",
                      "https://www.magicbricks.com/flats-in-dwarka-new-delhi-for-sale-pppfs"):
            html = fetch(probe) or ""
            keys = {k: html.count(k) for k in ('"psmName"', '"psmid"', '"prjname"', '"projectName"', '"projectId"', '"pdpUrl"', 'pdpid', '"societyName"', '"lmtDName"', '"prjId"', 'totalCount', '"latitude"', '"pmtLat"')}
            print("LISTING", probe, "len", len(html), keys, flush=True)
            i = html.find('"projectName"') if '"projectName"' in html else html.find("pdpid")
            print("SNIP", html[max(0, i - 600):i + 900].replace("\n", " "), flush=True)
        raise SystemExit("No locality project lists found for " + CITY)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "mb_index.json").write_text(json.dumps(list(projects.values()), indent=0))
    print("collected", len(projects), "projects from locality lists")


def crawl_projects():
    index = json.loads((OUT / "mb_index.json").read_text())
    from concurrent.futures import ThreadPoolExecutor

    def one(p):
        html = fetch(p["url"])
        try:
            detail = mb_parse.parse_project_page(html) if html else {}
        except Exception as e:
            print("  parse failed", p["url"], e, flush=True)
            detail = {}
        return {**p, **{k: v for k, v in detail.items() if v not in (None, [], "")}}

    out = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        for i, merged in enumerate(ex.map(one, index), 1):
            out.append(merged)
            if i % 100 == 0 or i == len(index):
                print(f"project {i}/{len(index)}", flush=True)
                (OUT / "mb_projects.json").write_text(json.dumps(out, indent=0))


if __name__ == "__main__":
    {"list": crawl_list, "projects": crawl_projects}[sys.argv[1]]()
