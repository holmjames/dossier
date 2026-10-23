---
name: dossier
description: End-to-end job application pipeline. Sources job listings (from pasted URLs or a search by title and location), analyzes each posting, tailors an ATS-safe resume and cover letter from the user's verified career facts, scores keyword coverage, finds a few alumni or former colleagues at the company for the user to contact, pauses for the user's approval, then delivers a per-job package (Word + PDF resume, cover letter, ATS report, job snapshot) and updates a tracker spreadsheet. Use this whenever someone wants to apply to a job, tailor a resume or cover letter to a posting, find openings matching a target role, check a resume against an ATS, keep an application tracker, or find alumni or people they know at a company they are applying to, even if they do not say "dossier" or ask for the whole pipeline. Also use it when a user shares a job link and asks "am I a fit" or "help me apply".
---

# Dossier

Dossier turns a job posting into a complete, approved application package. The pipeline has
five stages and one hard rule.

**The hard rule: every claim in the output must trace to a fact the user has stated.** ATS
optimization is about mirroring the posting's language where it is true, and nothing else.
A keyword match that fails in the interview costs more than the screen it passed. When a
posting asks for something not in the user's fact bank, ask the user; never infer, round up,
or invent. This rule is what makes the output safe to send, so it is worth a pause.

The scripts live in `scripts/` next to this file. They are plain Python with python-docx and
openpyxl, and each one prints usage with `--help`. Reference files in `references/` hold the
detailed rules; read the one named at each stage.

**Path convention.** Every command below runs from the workspace root (the folder that holds
`profile.md`), and `$SKILL` stands for this skill's folder, wherever it was installed. Set it
once at the start of a session (`SKILL=/path/to/dossier`) and reference application files
by their path from the workspace root, like `applications/<folder>/jd.txt`. Mixed working
directories are the most common way a run goes wrong.

## Workspace layout

Keep everything for one user in one folder (ask where, or default to `dossier-workspace/`
in the working directory):

```
dossier-workspace/
├── profile.md              # the fact bank: verified career facts, targets, format prefs
├── master_resume.md        # the full, untailored resume in build_docx.py markdown
├── master_resume_source.*  # whatever the user originally uploaded (docx/pdf)
├── tracker.xlsx            # one row per application
├── seen_jobs.json          # every posting URL already shown, so repeat searches show only new ones
├── shortlist.md            # the latest search result
└── applications/
    └── 2026-10-21_adobe_pm-intern/
        ├── jd.txt                      # posting text, as fetched
        ├── jd_analysis.md              # must-haves, nice-to-haves, keywords, red flags
        ├── resume.md / cover_letter.md # the tailored markdown sources
        ├── changes.md                  # what changed vs master, and why
        ├── warm_paths.md               # a few alumni or former colleagues there, and a draft note
        ├── ats_report.md / ats.json
        └── <Name> - <Company> - <Role> - Resume.docx/.pdf, ... - Cover Letter.docx/.pdf
```

Check for `profile.md` and `master_resume.md` first. If both exist, skip to Stage 1. If the
user attaches a job link and nothing else, run Stage 0 before anything else; a tailored
resume with no fact bank is guesswork.

## Stage 0: Profile intake (first run only)

Goal: a `profile.md` that is the single source of truth for everything the resume may say.

1. Ask for the current resume (any format). Run `$SKILL/scripts/extract_text.py` on it and read the
   text.
1b. **Targets interview.** Before asking anything, check what is already known: an existing
   `profile.md`, and anything Claude's memory holds about this user's job search (target
   roles, companies, cities, timeline). Pre-fill the `## Targets` block from those, show it
   back in one short list ("Here is what I already have about what you're looking for"), and
   ask only for what is missing or stale. If nothing is known, ask these, in one message,
   grouped so the user can answer in a few lines rather than filling a form:
   - **Roles.** Which titles, in priority order? (Give an example from their resume's
     trajectory so they can say "yes, that" or correct it.) Internship or full-time, or both?
   - **Companies.** Any specific companies they want to work at, and why (product they love,
     a referral, a location)? Any they will not apply to, for any reason?
   - **Industries and company types.** Sectors they want or want to avoid; startup vs.
     enterprise; B2B vs. consumer. If their resume is all one industry, ask whether they want
     to stay in it or pivot out, since that changes how the summary line is written.
   - **Place and mode.** Cities, remote, hybrid, willingness to relocate, and whether a
     program or family constraint pins them somewhere.
   - **Timeline and dealbreakers.** When they need to be in seat, application deadlines, and
     hard filters (sponsorship, travel, minimum level). Salary floor only if they want it
     tracked; it is never written into a resume or letter.
   Record the answers under `## Targets` in `profile.md`. These drive the Stage 1 search
   queries, the shortlist fit notes, and the cover letter's "why this company" paragraph, so
   a vague target produces a vague search. Push gently for specifics ("martech" is better
   than "tech"; "Adobe, HubSpot, Braze" is better than "martech").

2. Convert the resume into `master_resume.md` using the markdown conventions at the top of
   `$SKILL/scripts/build_docx.py`. Keep every bullet, even weak ones; the master is the full
   inventory, and tailoring means selecting from it.
3. Interview for the facts the resume leaves out, since those are what tailoring draws on:
   tools used at each job (with how deeply), certifications and dates, metrics behind each
   bullet (the number, the baseline, the timeframe), start and end months for every role,
   projects and side work, publications or talks, languages, and anything they never want
   claimed. Also record their networks under `## Networks` (schools with program and class
   year, former employers, communities), which Stage 2b uses to find people at each company;
   pre-fill from the resume and from memory, and confirm. Ask about work authorization only to filter postings; it never goes on a resume
   or in a letter unless the user asks. Five to ten focused questions, not a form. Record
   answers as one fact per line.
4. Ask about format: do they have a required format (many MBA programs do), a font or
   one-page rule, a location convention (for example, listing a remote job under the office
   city), words or punctuation they avoid in their own voice. Record these under
   `## Format and voice`.
5. Write `profile.md` using `assets/profile_template.md`. Show it to the user and ask them to
   confirm or correct. Every later stage reads this file.

If the user updates a fact later ("actually that was $385K, not $380K"), edit `profile.md`
and `master_resume.md` in the same turn, so the correction carries forward.

## Stage 1: Source listings

Read `references/sourcing.md` before the first run; it has the feed URLs, the slug discovery
steps, the title-expansion table, and the fetch-tool fallback. The short version: most
employers publish a JSON feed of every open role (Greenhouse, Lever, Ashby, SmartRecruiters,
Amazon), and reading those beats web search on completeness, freshness, and link quality.
Web search is for the companies that do not have a feed (Workday shops, Microsoft, Meta).

Two modes; the user can mix them.

- **URLs.** The user pastes one or more job links. Fetch each. If a site blocks fetching
  (LinkedIn and Indeed always do), say so and ask for the employer's own link for the same
  role, which the LinkedIn page carries under "Apply on company website."

- **Search.** The user gives criteria, or says "find me roles" or "anything new?" Steps:

  1. **Targets.** Read `## Targets` in `profile.md`. If it is empty or thin, run the targets
     interview from Stage 0 first. A one-off narrowing ("just Texas this time") uses the
     narrower set without rewriting the profile.
  2. **Board index.** Read `## Board index` in `profile.md`. For any target company not yet
     indexed, discover its system and slug (sourcing.md, "Building the user's board index")
     and record it, including "own system" and "unknown." For industry targets without named
     companies, build the company list with the user first, then index it.
  3. **Expand titles** using the table in sourcing.md and confirm the expansion with the
     user once; store it under `## Targets` as the search title list, with the seniority
     words to exclude.
  4. **Read the feeds.** With network access, one command:
     ```
     python3 "$SKILL/scripts/find_jobs.py" --board greenhouse:<slug> --board lever:<slug> ... \
       --amazon "<query>" --titles "<expanded list>" --exclude-titles "<seniority words>" \
       --locations "<cities>,Remote" --days 45 --seen seen_jobs.json \
       --score-against master_resume.md --out shortlist.md --json shortlist.json
     ```
     If it exits saying there is no network (the claude.ai sandbox), read the same feed URLs
     with the web fetch tool using the prompt pattern in sourcing.md, and keep
     `seen_jobs.json` by hand. Use web search only for the companies without a feed, with
     `site:` operators on their careers domain, and fetch each posting found.
  5. **Shortlist.** Present the table from sourcing.md: company, title, location and mode,
     posted date, fit score where available, a one-line fit note drawn from `profile.md`,
     and flags for dealbreakers the posting states (enrollment year, sponsorship, location).
     Flag rather than hide; the user may know something the posting does not say. Links are
     always the employer's own posting. Ask which to pursue.
  6. **Offer the standing watch** once the index exists: a scheduled run that shows only new
     postings. Weekly is the default.

Add every pursued role to the tracker with status `Sourced`:

```
python3 "$SKILL/scripts/tracker.py" add --file tracker.xlsx --company "<Co>" --role "<Title>" \
  --location "<City, ST>" --url "<link>" --source "Feed|Search|URL|Referral|Board"
```

## Stage 2: Analyze the posting

For each selected role, create the application folder and save the posting as `jd.txt`
(plain text, headings on their own lines; the scorer uses headings to find the requirements
section). Then write `jd_analysis.md`:

- **Role in one sentence.** What the person will actually do.
- **Must-haves.** Each requirement on its own line, in the posting's exact words.
- **Nice-to-haves.** Same.
- **Keywords.** Run the scorer against the master resume to get the extracted term list and
  a baseline score:
  ```
  python3 "$SKILL/scripts/ats_score.py" --jd applications/<folder>/jd.txt \
    --resume master_resume.md --company "<Co>" --location "<City, ST>" \
    --title "<Title as posted>" --out applications/<folder>/ats_baseline.md
  ```
  Pass `--company` and `--location` so the company's name and city are not reported as
  skills to add. `--title` takes the title as posted; the scorer strips program and season
  words itself and checks for the core title ("product manager"). The missing-terms table is
  the tailoring to-do list, read with judgment: a few rows will be scorer noise (a product
  name, a fragment of boilerplate), and those are simply ignored.
- **Gaps.** Must-haves with no supporting fact in `profile.md`. These need the user's input
  before drafting (Stage 3 step 1), not a creative workaround.
- **Signals.** Anything that should shape the cover letter: the team's product, a named
  initiative, the hiring manager's stated priorities, culture language that is specific
  rather than boilerplate.

## Stage 2b: Warm paths

For each selected role, find three to five people at the company who share one of the
user's networks (same school and program first, then same school, then former colleagues,
then communities), using `references/warm-paths.md`. The primary source is LinkedIn's
alumni view in the user's own logged-in browser; web search is a supplement that needs
verification; the user's own memory ("do you know anyone there?") is often the best source
of all. Output is `warm_paths.md` in the application folder: name, current title, shared
affiliation, public link, why them, a suggested order, and a draft note under 120 words in
the user's voice. The user sends it.

Public professional information only: no contact details hunted from other sites, no
personal details, no inferences, no bulk reading of profiles, no messages sent by Claude.
Offer this step rather than forcing it; some users want the application in first. Done
well, the note goes out the same day as the application.

## Stage 3: Tailor

Read `references/resume-tailoring.md` and `references/cover-letter.md` before drafting.
`references/ats-rules.md` covers the formatting rules the builder enforces and the content
rules it cannot.

1. **Resolve gaps first.** If the analysis found must-haves without a supporting fact, ask the
   user in one message: "The posting asks for X. Do you have that? If yes, where and how?"
   Record answers in `profile.md` before continuing. If the answer is no, the gap stays a gap
   and the ATS report will show it.
2. **Resume.** Copy `master_resume.md` to the application folder as `resume.md` and edit it:
   reorder sections and bullets so the most relevant are first, rewrite bullets to use the
   posting's terms where the underlying fact supports them, trim what does not serve this
   role, and add a one- or two-line summary that contains the job title (if it is a fair
   description of the person) and the three most important matched keywords. Keep the
   user's format rules from `profile.md`.
3. **Cover letter.** Write `cover_letter.md`: under 350 words, specific to the posting's
   signals, built on two or three facts from the profile that map to must-haves. No
   restating the resume, no flattery of the company, no "I am writing to apply."
4. **Score and iterate.** Build a draft docx and score it:
   ```
   python3 "$SKILL/scripts/build_docx.py" applications/<folder>/resume.md --kind resume \
     --out applications/<folder>/draft.docx
   python3 "$SKILL/scripts/ats_score.py" --jd applications/<folder>/jd.txt \
     --resume applications/<folder>/draft.docx --company "<Co>" --location "<City, ST>" \
     --title "<Title as posted>" --out applications/<folder>/ats_report.md \
     --json applications/<folder>/ats.json
   ```
   Work the missing-terms table from the top. Stop when every remaining missing term is
   untrue of the user, irrelevant to the role, or scorer noise. A score in the 70s with
   honest gaps beats a 95 with padding. Fix every formatting warning. The length note in
   the report is a word count, not a page count; judge length by rendering the PDF
   (`--pdf`) and looking at it, and never add content just to reach a number.
5. **Write `changes.md`.** A short list: bullets moved, bullets rewritten (before and after),
   terms added and which fact justifies each, anything removed. This is what the user reviews.

## Stage 4: Approval gate

Do not produce final files, update the tracker to `Approved`, or package anything until the
user has explicitly approved. Present, in this order:

1. The ATS headline: score, required-section coverage, and the remaining missing terms with
   a one-word reason each (untrue / irrelevant / noise / needs your input).
2. `changes.md`, so they can see every edit against the master.
3. The full resume text and the full cover letter text, in the conversation, so nothing
   requires opening a file to review.
4. One question: "Approve as is, or tell me what to change?"

Apply requested edits, re-score, and present again. When they approve, set the tracker row
to `Approved`. If they say they already submitted, set it to `Applied`.

Two things happen at this gate often enough to plan for:

- **A new fact arrives.** "Oh, also mention I led the Tech Club trek." Add it to `profile.md`
  first, in the user's words, then to the draft. Write only what they said; the temptation
  is to round a new fact up into a stronger sentence than they gave you. The hard rule
  applies here exactly as it did in Stage 3.
- **Several roles in one session.** Present one role per message and get its approval
  before presenting the next. A single message with three resumes and three letters is
  unreviewable, and an unreviewed approval is not one.

## Stage 5: Package and deliver

1. Build final files with the naming convention `<Full Name> - <Company> - <Short Role> -
   Resume.docx` and `... - Cover Letter.docx`, with `--pdf` so both formats exist. Portals
   that accept .docx parse it most reliably; PDF is for humans and for portals that require
   it. Delete `draft.docx` and `draft.pdf`.
2. Re-run the scorer on the final docx so `ats_report.md` reflects what is shipping.
3. Update the tracker with the score and file names:
   ```
   python3 "$SKILL/scripts/tracker.py" update --file tracker.xlsx --company "<Co>" --role "<Title>" \
     --ats <score> --resume "<file>" --cover "<file>" --next "Submit on portal" --follow-up +14d
   ```
4. Zip the folder: `python3 "$SKILL/scripts/package.py" applications/<folder>`. By default
   the zip holds only deliverables (docx, pdf, ATS report, changes, posting snapshot, README);
   `--all` adds the working files if the user wants them. Send the user the zip (and the
   individual docx/pdf files if the interface shows them inline). Tell them, in two or three
   sentences, the score, the honest gaps, and the one thing to do next.

If the user runs several roles in one session, deliver each package as it is approved rather
than batching; they may want to submit the first while you draft the second. Dossier stops at the
package on purpose: the user submits, because portals ask questions only they should
answer and a wrong click there cannot be undone. If asked to submit, say that plainly,
hand over the files, and offer to walk them through the portal's questions in chat.

## Working style

- The user is often an MBA student or job seeker, not an engineer. Explain what a script
  did in plain words ("checked which of the posting's 33 key terms appear in your resume"),
  not by its name.
- Keep the user's voice. If `profile.md` says no em dashes or no particular phrases, that
  applies to every sentence you draft for them.
- Dates, titles, and employers are never adjusted to fit a posting. Scope language ("led"
  vs "supported") must match the fact as stated.
- When fetching postings, save the text immediately; postings get taken down, and the
  snapshot is what the tracker links back to.
- If the user asks for only one piece (just a cover letter, just an ATS check), run only
  the stages that piece needs, but still read `profile.md` first if it exists.
- Memory and the profile are different things. Claude's memory of the user may hold useful
  context about their search (companies they have mentioned, cities, a timeline); use it to
  pre-fill questions so they are not asked twice. But `profile.md` is the fact bank the
  resume draws from, and only facts the user has confirmed in this workspace go in it.
