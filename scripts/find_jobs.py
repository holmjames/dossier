#!/usr/bin/env python3
"""Pull open roles straight from employers' hosted job boards and build a shortlist.

Usage:
    python3 find_jobs.py --board greenhouse:stripe --board lever:anthropic --board ashby:notion \
        --board smartrecruiters:Visa --amazon "MBA product manager intern" \
        --titles "product manager,product marketing,apm,rotational product" \
        --locations "Los Angeles,Remote,San Francisco,Seattle" \
        --days 45 --seen seen_jobs.json --score-against master_resume.md \
        --out shortlist.md --json shortlist.json

Board specs:  greenhouse:<slug>   lever:<slug>   ashby:<slug>   smartrecruiters:<CompanyId>
Find a company's slug with the discovery steps in references/sourcing.md (usually it is the
company name in lowercase: boards.greenhouse.io/<slug>, jobs.lever.co/<slug>, jobs.ashbyhq.com/<slug>).

What it does:
  1. Downloads every open posting from each board's public JSON feed. No scraping, no login;
     these are the same feeds the companies' own careers pages read.
  2. Keeps postings whose title matches any of --titles (case-insensitive substring) and, if
     --locations is given, whose location matches any of those (or is remote).
  3. Drops anything older than --days and anything already in the --seen file, so a repeat
     run shows only what is new. Writes the seen file back.
  4. With --score-against, fetches each surviving posting's description and runs the ATS
     scorer against the master resume, so the shortlist is ranked by fit, not by date.
  5. Writes a Markdown shortlist and a JSON file for the tracker step.

Network: this needs direct internet access (it works on a laptop or in Claude Code). In the
claude.ai sandbox there is no outbound network; use the fetch-tool playbook in
references/sourcing.md instead, which reads the same feed URLs.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

UA = {"User-Agent": "Mozilla/5.0 (compatible; Dossier job search; +https://jholm.co/dossier/)"}


def get_json(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf8", "ignore"))


def strip_html(html):
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html or "", flags=re.S | re.I)
    html = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>|</div>", "\n", html, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    import html as h
    return re.sub(r"[ \t]+", " ", h.unescape(text)).strip()


def parse_date(s):
    if not s:
        return None
    try:
        if isinstance(s, (int, float)):
            return datetime.fromtimestamp(s / 1000 if s > 1e11 else s, tz=timezone.utc)
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Feed readers: each yields dicts with the same keys.
# ---------------------------------------------------------------------------

def greenhouse(slug):
    data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
    for j in data.get("jobs", []):
        yield {
            "source": f"greenhouse:{slug}", "company": slug, "id": str(j["id"]),
            "title": j.get("title", ""), "location": (j.get("location") or {}).get("name", ""),
            "posted": parse_date(j.get("first_published") or j.get("updated_at")),
            "url": j.get("absolute_url"), "description": None,
            "_detail": f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{j['id']}",
        }


def greenhouse_detail(url):
    d = get_json(url)
    return strip_html(d.get("content", ""))


def lever(slug):
    data = get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    for j in data:
        cats = j.get("categories") or {}
        yield {
            "source": f"lever:{slug}", "company": slug, "id": j["id"],
            "title": j.get("text", ""), "location": cats.get("location", "") or ", ".join(j.get("allLocations", []) or []),
            "posted": parse_date(j.get("createdAt")),
            "url": j.get("hostedUrl"), "description": j.get("descriptionPlain") or strip_html(j.get("description", "")),
        }


def ashby(slug):
    data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    for j in data.get("jobs", []):
        if j.get("isListed") is False:
            continue
        loc = j.get("location", "")
        if j.get("isRemote"):
            loc = f"{loc} (Remote)" if loc else "Remote"
        yield {
            "source": f"ashby:{slug}", "company": slug, "id": j["id"],
            "title": j.get("title", ""), "location": loc,
            "posted": parse_date(j.get("publishedAt")),
            "url": j.get("jobUrl"), "description": j.get("descriptionPlain") or strip_html(j.get("descriptionHtml", "")),
        }


def smartrecruiters(company):
    offset, limit = 0, 100
    while True:
        data = get_json(f"https://api.smartrecruiters.com/v1/companies/{company}/postings?limit={limit}&offset={offset}")
        for j in data.get("content", []):
            loc = j.get("location") or {}
            yield {
                "source": f"smartrecruiters:{company}", "company": company, "id": j["id"],
                "title": j.get("name", ""), "location": ", ".join(x for x in [loc.get("city"), loc.get("region"), loc.get("country")] if x),
                "posted": parse_date(j.get("releasedDate")),
                "url": f"https://jobs.smartrecruiters.com/{company}/{j['id']}", "description": None,
                "_detail": f"https://api.smartrecruiters.com/v1/companies/{company}/postings/{j['id']}",
            }
        offset += limit
        if offset >= data.get("totalFound", 0):
            break


def smartrecruiters_detail(url):
    d = get_json(url)
    secs = (d.get("jobAd") or {}).get("sections") or {}
    return "\n".join(strip_html(v.get("text", "")) for v in secs.values() if isinstance(v, dict))


def amazon(query, location="United States", limit=100):
    q = urllib.parse.urlencode({"base_query": query, "loc_query": location, "result_limit": limit, "offset": 0})
    data = get_json(f"https://www.amazon.jobs/en/search.json?{q}")
    for j in data.get("jobs", []):
        yield {
            "source": "amazon", "company": "amazon", "id": str(j.get("id_icims") or j.get("id")),
            "title": j.get("title", ""), "location": j.get("location", "") or j.get("normalized_location", ""),
            "posted": parse_date(j.get("posted_date_iso") or None) or _amazon_date(j.get("posted_date")),
            "url": "https://www.amazon.jobs" + j.get("job_path", ""),
            "description": strip_html(" ".join(filter(None, [j.get("description"), j.get("basic_qualifications"), j.get("preferred_qualifications")]))),
        }


def _amazon_date(s):
    try:
        return datetime.strptime(s, "%B %d, %Y").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


READERS = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby, "smartrecruiters": smartrecruiters}
DETAIL = {"greenhouse": greenhouse_detail, "smartrecruiters": smartrecruiters_detail}


# ---------------------------------------------------------------------------

def matches_any(text, needles):
    t = (text or "").lower()
    return any(n in t for n in needles)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--board", action="append", default=[], help="greenhouse:<slug> | lever:<slug> | ashby:<slug> | smartrecruiters:<CompanyId>")
    ap.add_argument("--amazon", help="search query for amazon.jobs (their own feed)")
    ap.add_argument("--amazon-location", default="United States")
    ap.add_argument("--titles", required=True, help="comma-separated title keywords, any match keeps the posting")
    ap.add_argument("--exclude-titles", default="", help="comma-separated keywords that drop a posting (e.g. 'senior,director,staff')")
    ap.add_argument("--locations", default="", help="comma-separated location keywords; 'remote' matches remote roles")
    ap.add_argument("--days", type=int, default=60, help="ignore postings older than this many days (0 = no limit)")
    ap.add_argument("--seen", help="JSON file of already-seen posting URLs; new ones are appended")
    ap.add_argument("--score-against", help="master resume (.md/.docx/.txt) to rank by ATS fit")
    ap.add_argument("--out", help="Markdown shortlist path")
    ap.add_argument("--json", help="JSON shortlist path")
    args = ap.parse_args()

    titles = [t.strip().lower() for t in args.titles.split(",") if t.strip()]
    excl = [t.strip().lower() for t in args.exclude_titles.split(",") if t.strip()]
    locs = [t.strip().lower() for t in args.locations.split(",") if t.strip()]
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days) if args.days else None

    seen = set()
    if args.seen and Path(args.seen).exists():
        seen = set(json.loads(Path(args.seen).read_text()).get("urls", []))

    found, errors = [], []
    sources = [(b.split(":", 1)[0], b.split(":", 1)[1]) for b in args.board if ":" in b]
    for kind, slug in sources:
        if kind not in READERS:
            errors.append(f"unknown board type {kind}")
            continue
        try:
            n = 0
            for job in READERS[kind](slug):
                n += 1
                found.append(job)
            print(f"{kind}:{slug}: {n} open postings", file=sys.stderr)
        except urllib.error.HTTPError as e:
            errors.append(f"{kind}:{slug}: HTTP {e.code} (wrong slug? check references/sourcing.md)")
        except Exception as e:  # network, JSON
            errors.append(f"{kind}:{slug}: {type(e).__name__}: {str(e)[:80]}")
    if args.amazon:
        try:
            jobs = list(amazon(args.amazon, args.amazon_location))
            print(f"amazon: {len(jobs)} postings for '{args.amazon}'", file=sys.stderr)
            found += jobs
        except Exception as e:
            errors.append(f"amazon: {type(e).__name__}: {str(e)[:80]}")

    if not found and errors:
        print("No postings fetched. " + "; ".join(errors), file=sys.stderr)
        print("If every source failed with a network error, this environment has no internet access; "
              "use the fetch-tool playbook in references/sourcing.md instead.", file=sys.stderr)
        sys.exit(2)

    kept = []
    for j in found:
        if not matches_any(j["title"], titles):
            continue
        if excl and matches_any(j["title"], excl):
            continue
        if locs and not (matches_any(j["location"], locs) or ("remote" in locs and "remote" in (j["location"] or "").lower())):
            continue
        if cutoff and j["posted"] and j["posted"] < cutoff:
            continue
        if j["url"] in seen:
            continue
        kept.append(j)

    # Rank by fit if asked.
    if args.score_against and kept:
        from ats_score import score as ats_score
        from extract_text import extract
        resume_text = extract(Path(args.score_against))
        for j in kept:
            try:
                if j.get("description") is None and j.get("_detail"):
                    j["description"] = DETAIL[j["source"].split(":")[0]](j["_detail"])
                if j.get("description"):
                    r = ats_score(j["description"], resume_text, title=j["title"], company=j["company"], location=j["location"])
                    j["fit"] = r["score"]
                    j["required_coverage"] = r["required_coverage"]
                    j["top_missing"] = [t for t, _ in sorted(r["missing"].items(), key=lambda kv: -kv[1]["weight"])[:5]]
            except Exception as e:
                j["fit"] = None
                j["fit_error"] = str(e)[:80]
        kept.sort(key=lambda j: (-(j.get("fit") or -1), -(j["posted"].timestamp() if j["posted"] else 0)))
    else:
        kept.sort(key=lambda j: -(j["posted"].timestamp() if j["posted"] else 0))

    # Report.
    lines = [f"# Shortlist: {len(kept)} new postings", "",
             f"Titles: {', '.join(titles)}" + (f" | Locations: {', '.join(locs)}" if locs else "") + (f" | Last {args.days} days" if args.days else ""),
             f"Sources: {', '.join(args.board + (['amazon'] if args.amazon else []))}", ""]
    if errors:
        lines += ["Sources that failed: " + "; ".join(errors), ""]
    head = "| # | Company | Title | Location | Posted | " + ("Fit | Top gaps | " if args.score_against else "") + "Link |"
    sep = "|---|---|---|---|---|" + ("---|---|" if args.score_against else "") + "---|"
    lines += [head, sep]
    for i, j in enumerate(kept, 1):
        posted = j["posted"].strftime("%b %d") if j["posted"] else ""
        fit = ""
        if args.score_against:
            fit = f"{j.get('fit', '')}% | {', '.join(j.get('top_missing', []))} | " if j.get("fit") is not None else "n/a | | "
        lines.append(f"| {i} | {j['company']} | {j['title']} | {j['location']} | {posted} | {fit}[open]({j['url']}) |")
    lines += ["", "Fit = ATS keyword coverage of the master resume against the posting, before any tailoring. "
              "It ranks the list; it does not decide it. Dealbreakers (enrollment year, sponsorship, location) still need a read of the posting."]
    report = "\n".join(lines)
    if args.out:
        Path(args.out).write_text(report)
        print(f"Wrote {args.out}: {len(kept)} postings", file=sys.stderr)
    else:
        print(report)
    if args.json:
        out = [{k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in j.items() if k not in ("description", "_detail")} for j in kept]
        Path(args.json).write_text(json.dumps(out, indent=2))
    if args.seen:
        seen |= {j["url"] for j in kept if j["url"]}
        Path(args.seen).write_text(json.dumps({"updated": datetime.now(timezone.utc).isoformat(), "urls": sorted(seen)}, indent=2))


if __name__ == "__main__":
    main()
