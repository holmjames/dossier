# Dossier

A Claude skill that runs your job applications end to end: finds postings, tailors an
ATS-safe resume and cover letter from facts you have verified, scores keyword coverage,
waits for your approval, then hands you a package per job and keeps a tracker up to date.

Built by James Holm (UCLA Anderson FEMBA '28) during his own search. Free to use and share.

## What you get per job

```
2026-10-21_adobe_pm-intern.zip
├── Jane Doe - Adobe - PM Intern - Resume.docx      (ATS-safe Word file)
├── Jane Doe - Adobe - PM Intern - Resume.pdf
├── Jane Doe - Adobe - PM Intern - Cover Letter.docx
├── Jane Doe - Adobe - PM Intern - Cover Letter.pdf
├── ats_report.md       (which posting terms you cover, which honest gaps remain)
├── changes.md          (every edit vs. your master resume, with the fact behind it)
├── warm_paths.md       (a few alumni or former colleagues there, and a draft note to send)
├── jd.txt              (the posting as it read the day you applied)
└── README.md
```

Plus `tracker.xlsx`, one row per application with status, score, next action, and links.

## Install (about two minutes)

**Claude.ai (web or desktop)**

1. Turn on code execution: Settings > Capabilities. (Team/Enterprise: an owner enables it
   under Organization settings > Plugins & skills.)
2. Go to Customize > Skills, click "+", then "Create skill", then "Upload a skill".
3. Upload `dossier.zip` (this folder, zipped, with `SKILL.md` at the top level inside
   a folder named `dossier`).
4. Toggle it on.

**Claude Code**

Copy the `dossier` folder into `~/.claude/skills/` (personal) or `.claude/skills/` inside a
project. That is the whole install.

## First run

Start a conversation and attach your current resume. Say something like:

> Set up Dossier. I'm targeting PM and product marketing internships for summer 2027,
> Bay Area or remote.

Claude will read your resume, ask what you are targeting (roles, companies, industries,
cities, timeline; it skips anything it already knows about you), then ask five to ten
questions about facts the resume leaves out (tools, metrics, projects, things you never
want claimed), and write a `profile.md`. Correct
anything wrong. That file is the only source the pipeline is allowed to draw from, which is
what keeps the output honest enough to send.

## Every run after that

Paste job links, or describe what you want:

> Find me product marketing manager roles in LA posted in the last month.

Searches read employers' own job feeds (Greenhouse, Lever, Ashby, SmartRecruiters, Amazon)
rather than a search engine, so the list is complete, the dates are real, and every link
goes to the company's own posting. The first search builds an index of which system each
of your target companies uses; after that, "anything new this week?" shows only postings
you have not seen, ranked by how well your current resume already covers them.

> Here are three postings. Tailor for all three. [links]

For each role you pick, Claude analyzes the posting, drafts the resume and letter, scores
them, shows you every change, and stops. Nothing final is produced until you say "approve."

It also looks for a few warm paths into the company: alumni from your schools, former
colleagues, people from your communities who work there now. It points you at LinkedIn's
alumni view (your login, your account) and your school's directory, supplements with web
search, and gives you three to five names with the shared connection and a draft note
under 120 words. You send it. It only ever uses public professional profiles and never
hunts for contact details beyond them.

## Why the approval gate matters

Resume tools that rewrite your experience without a review step are the ones people
complain about. Dossier shows you the before-and-after of every bullet and the fact that
justifies each added keyword. If a posting asks for something you do not have, it asks you
instead of guessing, and the gap shows up in the ATS report as a gap.

## What is in the folder

```
dossier/
├── SKILL.md                     the workflow Claude follows
├── README.md                    this file
├── references/
│   ├── ats-rules.md             what breaks parsers, what the score means
│   ├── resume-tailoring.md      the selection-and-translation method
│   ├── cover-letter.md          structure and voice rules
│   ├── sourcing.md              which job sites can be read, search playbook
│   └── warm-paths.md            finding alumni and former colleagues at a company, privately
├── scripts/
│   ├── extract_text.py          resume or posting file -> plain text
│   ├── find_jobs.py             employer job feeds -> filtered, de-duplicated, fit-ranked shortlist
│   ├── ats_score.py             posting + resume -> weighted keyword report
│   ├── build_docx.py            markdown -> ATS-safe .docx (and .pdf)
│   ├── tracker.py               add / update / list rows in tracker.xlsx
│   └── package.py               zip an application folder with a manifest
└── assets/
    └── profile_template.md      the fact-bank template
```

The scripts are plain Python (python-docx, openpyxl, optionally pdfplumber and LibreOffice
for PDF export). Each prints help with `--help`. You can also run them yourself:

```
python3 scripts/ats_score.py --jd posting.txt --resume "My Resume.docx" --company Adobe --title "Product Manager"
```

## Honest limits

- LinkedIn and Indeed block automated reading. Paste the text, or use the employer's own
  posting (the LinkedIn page links to it). Workday, Microsoft, Meta, and Google have no
  public feed, so those fall back to web search plus fetching each posting.
- In claude.ai, scripts cannot reach the internet, so the feed search runs through Claude's
  fetch tool instead of `find_jobs.py`. Same feeds, same results, a bit slower. In Claude
  Code the script runs directly.
- The ATS score is a keyword-coverage proxy, not a prediction. Above 75% usually clears
  screens; above 90% usually means padding.
- It drafts. You still read every line before you submit, because your name is on it.
- It does not submit applications. You upload the two files and answer the portal's
  questions yourself; that is the one step where a person should be the one clicking.

## Feedback

Tell James what broke or what you wish it did: open an issue on GitHub, or
linkedin.com/in/jamesholm3.
