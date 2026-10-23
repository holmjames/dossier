# Sourcing job listings

The best source of postings is not a search engine. Most employers run their careers page on
a hosted applicant tracking system, and four of the big ones publish a public JSON feed of
every open role: title, location, date, link, and usually the full description. Reading
those feeds is complete (every role, not the ones a search engine happened to index), fresh
(posting dates are real), and gives the employer's own link every time. Web search is the
fallback for companies on systems without a feed.

## Two ways to read a feed

**With network access** (a laptop, Claude Code): `scripts/find_jobs.py` reads every board in
one command, filters by title and location, drops stale and already-seen postings, and ranks
what is left by ATS fit against the master resume. Prefer it whenever it runs.

**Without network access** (the claude.ai sandbox blocks outbound connections from scripts):
use the web fetch tool on the same feed URLs. It returns the JSON as text, and the prompt you
give it does the filtering. Pattern:

> Fetch `https://boards-api.greenhouse.io/v1/boards/<slug>/jobs` with the prompt: "JSON job
> feed. List every job whose title contains any of: product manager, product marketing, APM.
> For each give title, location.name, first_published, absolute_url. Then say how many jobs
> are in the feed in total."

Large boards get truncated at about 100,000 characters (roughly 150 postings on a Greenhouse
compact feed, fewer on Ashby, which includes descriptions). The tool's note says where it
stopped; call again with the offset it gives until it reports the end. Ask for the
remaining count each time so you know when you have the whole board.

To get a description for scoring, fetch the single-posting URL (patterns below) or the
public job page, save it as `jd.txt`, and run the scorer.

## Feed patterns

| System | List every open role | One posting | Notes |
|---|---|---|---|
| Greenhouse | `https://boards-api.greenhouse.io/v1/boards/<slug>/jobs` | `.../jobs/<id>` (has `content`, HTML) | Compact list; add `?content=true` to the list for descriptions (large). Public page: `boards.greenhouse.io/<slug>` or `job-boards.greenhouse.io/<slug>`. |
| Lever | `https://api.lever.co/v0/postings/<slug>?mode=json` | same list; each item has `descriptionPlain` | Public page: `jobs.lever.co/<slug>`. |
| Ashby | `https://api.ashbyhq.com/posting-api/job-board/<slug>` | same list; `descriptionPlain`, `isRemote`, `publishedAt` | Public page: `jobs.ashbyhq.com/<slug>`. |
| SmartRecruiters | `https://api.smartrecruiters.com/v1/companies/<CompanyId>/postings?limit=100&offset=0` | `.../postings/<id>` | CompanyId is case-sensitive (e.g. `Visa`). Page through with `offset`. |
| Amazon (own system) | `https://www.amazon.jobs/en/search.json?base_query=<query>&loc_query=United+States&result_limit=100` | `https://www.amazon.jobs<job_path>` | Query is free text; "MBA product manager intern" works. |
| Workday | no public list feed | `https://<tenant>.wd<N>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/job/<path>` returns JSON for a known job | Listing needs a POST, which the fetch tool cannot do. Use web search with `site:<tenant>.wd5.myworkdayjobs.com "<title>"` to find job URLs, then fetch each. Adobe, Salesforce, Workday itself, many large enterprises. |
| iCIMS, Taleo, SuccessFactors, Phenom, Eightfold | varies, usually none | public job pages usually fetch | Web search with `site:` on the careers domain. |
| Microsoft careers, Apple, Meta, Google | blocked or POST-only for the fetch tool | | Web search with `site:jobs.careers.microsoft.com`, `site:jobs.apple.com`, `site:metacareers.com`, `site:google.com/about/careers`, then fetch the individual job page. Google's and Meta's pages often render only partially; ask the user to paste the text if the fetch comes back thin. |
| LinkedIn, Indeed, Glassdoor, ZipRecruiter | blocked | blocked | Not a source. The LinkedIn posting links to the employer's own page under "Apply on company website"; use that. |
| University boards (12twenty, Handshake) | login required | | User pastes the text. These are worth asking about: school-only postings have small applicant pools. |

Endpoints change. If one returns an error, check the public careers page to see whether the
company moved systems, then update the user's board index.

## Building the user's board index (once, then maintained)

The targets interview produces a company list. Turn it into a board index in `profile.md`
under `## Board index`, one line per company:

```
## Board index
- Notion: ashby:notion
- Anthropic: lever:anthropic
- Stripe: greenhouse:stripe
- Visa: smartrecruiters:Visa
- Adobe: workday adobe.wd5 / external_experienced (search site:adobe.wd5.myworkdayjobs.com)
- Amazon: amazon.jobs feed, query "MBA product manager"
- Qualtrics: unknown yet
```

Finding a company's system and slug, in order of speed:

1. Guess the slug as the lowercase company name and fetch the Greenhouse, Lever, and Ashby
   list URLs. A 200 with jobs is the answer; a 404 means not that system or not that slug.
2. Fetch the company's careers page and look at where "View jobs" or "Apply" links point:
   the hostname names the system and the path names the slug.
3. Web search `"<company>" site:boards.greenhouse.io` (and lever, ashbyhq, myworkdayjobs).

Record what you find, including "own system" and "unknown," so the next run does not repeat
the discovery. Re-check "unknown" entries every few weeks; companies move systems.

For industries rather than named companies ("martech," "fintech in LA"), build the company
list first: ask the user for names they already know, add the obvious players, and use web
search for "top <industry> companies <city>" only to fill gaps. Then index each one. A feed
read of twenty indexed companies beats fifty search queries.

## Title expansion

Postings name the same job many ways. Expand the user's target titles before filtering, and
keep the expansion in the profile once they confirm it.

| User says | Also match |
|---|---|
| Product Manager | PM, Product Owner, Technical Product Manager, TPM (check: often program manager), Associate Product Manager, APM, Rotational Product Manager, RPM, Product Lead, MBA Product Intern |
| Product Marketing | PMM, Product Marketing Manager, Solutions Marketing, Portfolio Marketing, Go-to-Market Manager, GTM Lead, Technical Product Marketing, Launch Manager |
| Marketing Operations | Marketing Ops, MOps, Marketing Technology, MarTech, Marketing Automation, Demand Generation Operations, Revenue Operations, RevOps, GTM Operations, GTM Engineer, GTM Systems |
| Strategy and Ops | Strategy & Operations, BizOps, Business Operations, Chief of Staff, Strategic Finance (check), Program Manager |
| Brand Management | Brand Manager, Associate Brand Manager, ABM (collides with account-based marketing), Marketing Manager (CPG) |
| MBA internship | MBA Intern, Summer Associate, MBA Summer, Summer 2027, Class of 2028, Graduate Intern, Leadership Development Program, LDP |

Pass the expanded list to `--titles` (substring match, case-insensitive) and the seniority
words the user is not targeting to `--exclude-titles` ("senior, staff, principal, director,
vp, head of" for an early-career search; "intern, associate" for a senior one).

## Filters and freshness

- **Date.** Default to the last 45 days. Internship postings for a summer cycle can stay open
  for months, so for those use 120. Postings with no date are kept and marked.
- **Location.** Match on the user's cities plus "remote" when they will take remote. Hybrid
  postings list the office city; that is what matches. When a company has an office in the
  user's city but the posting says another city, note it in the fit column rather than
  dropping it; teams are often flexible for the right candidate.
- **Already seen.** `find_jobs.py --seen seen_jobs.json` keeps a list of every URL already
  shown. A repeat run shows only new postings, which makes "anything new this week?" a
  one-command question. Without the script, keep `seen_jobs.json` by hand: append every URL
  shown in a shortlist.
- **Dealbreakers** from the profile (sponsorship, enrollment year, must be full-time MBA)
  cannot be read from a title. Check them in the description before the shortlist, and
  flag rather than hide: the user may know something the posting does not say.

## Ranking by fit

With `--score-against master_resume.md`, each posting's description is scored by the ATS
scorer before any tailoring, and the shortlist is sorted by that number. It is a crude
ranking and that is fine: it reliably separates "this is your job family" from "this is a
different job," which is the decision the user needs to make across thirty rows. Show the
top missing terms per row; they are a preview of what tailoring would have to cover, and a
row whose gaps are all tools the user has never touched is a row to skip.

Without the script, score the handful of postings the user is actually considering rather
than every row: save each description as `jd.txt` and run the scorer by hand.

## Shortlist format

| # | Company | Title | Location / mode | Posted | Fit | Fit note | Flags |
|---|---|---|---|---|---|---|---|
| 1 | Adobe | 2027 MBA Intern, Product Manager | San Jose, CA / hybrid | Oct 2 | 71% | Marketo certs + PM title at Versured map to 4 of 6 must-haves | Requires full-time MBA enrollment |

Fit notes come from matching must-haves to `profile.md`, in one line. Flags are only hard
constraints the user named or the posting states. Links go to the employer's own posting,
never an aggregator. Group by company when there are several rows per company.

## A standing watch

Once the board index exists, the whole search is one command (or one fetch pass). Offer to
run it on a schedule: weekly is right for most searches, twice a week in peak recruiting
season. In Claude that is a scheduled task whose instruction is "run Dossier Stage 1 for
<user>, show only new postings, and stop at the shortlist." The user picks from the
shortlist when they are back; nothing is tailored or tracked until they do.

## Saving the posting

Save the fetched text to `applications/<date>_<company>_<role-slug>/jd.txt` immediately;
postings get taken down. Keep the section headings on their own lines (Responsibilities,
Requirements, Preferred), because the scorer uses them to weight terms. Strip navigation,
cookie banners, and the EEO paragraph. Record the metadata at the top in this exact form,
which the scorer knows to skip:

```
Source: https://...
Fetched: 2026-10-21
Title: ...
Company: ...
Location: ...

<posting text>
```
