# ATS rules

An applicant tracking system (Workday, Greenhouse, Lever, iCIMS, Taleo, SuccessFactors,
Ashby) does two things with a resume: it parses it into fields (name, employers, titles,
dates, skills), and it lets a recruiter search and sometimes rank on keywords. Most
rejections blamed on "the ATS" are really a recruiter spending seven seconds on a search
result. Both halves matter.

## Parsing: what breaks and what the builder already handles

`scripts/build_docx.py` produces single-column, table-free, header-free files with real
bullets and standard fonts. That covers the mechanical failures. What it cannot do for you:

- **Standard section names.** Use Experience, Education, Skills (or Skills & Certifications),
  Summary. Parsers map content to fields by heading text. "Where I've Made an Impact" maps
  to nothing. MBA formats often call the last section "Additional" or "Additional
  Information"; that is a recognized convention and the scorer accepts it. If the format
  allows, "Additional: Skills, Certifications, Interests" gets the best of both.
- **Dates on every role.** Month YYYY to Month YYYY (or Present), one format throughout.
  Degrees can carry a year alone or "Expected Month YYYY". Missing dates on roles break the
  timeline the parser builds, and gaps it cannot compute look worse than gaps it can.
- **Employer, title, location on predictable lines.** The builder puts employer and
  location on one line and title and dates on the next. Keep that order; parsers are
  trained on it.
- **Contact info in the body.** Name, city/state, email, phone, LinkedIn at the top, as text.
  No icons in place of labels.
- **File name without special characters.** `Jane Doe - Acme - PM - Resume.docx` is fine.
  Avoid `#`, `%`, `&`, emoji.
- **Spell out acronyms once.** "Customer Relationship Management (CRM)" on first use, then
  CRM. Recruiters search both ways.
- **No keyword stuffing.** White text, keyword blocks in 1pt font, and repeated terms are
  detected by modern systems and read as fraud by humans. The scorer caps credit at three
  mentions for this reason.

## Keywords: what the scorer does and does not know

`scripts/ats_score.py` extracts terms from the posting (tools, skills, certifications,
acronyms, repeated phrases), weights terms in the requirements section highest, and
reports which appear in the resume. It knows common synonyms (GTM / go-to-market, SFDC /
Salesforce). It does not know:

- **Context.** "Managed Salesforce" and "used Salesforce reports" both match. The recruiter
  can tell them apart. Tailoring is about putting the strongest true version forward.
- **Seniority.** Matching "roadmap" does not make a coordinator a product manager. The
  title check (`--title`) is a reminder to include the target title in the summary when it
  is a fair description, not permission to claim it.
- **Which gaps matter.** A missing "Power BI" when the user has Tableau is minor; a missing
  "SQL" for an analyst role is not. Rank gaps by whether a recruiter would filter on them.

## Targets

- Above 75% weighted coverage usually clears automated screens and recruiter searches.
- 55 to 75% is typical for a reasonable pivot; the cover letter and summary carry the story.
- Below 55% the parser sees a different job family. Either the master resume is missing
  true facts (go back to the profile) or the role is a stretch, which the user should know.

Coverage above 90% is a warning sign, not a goal. Re-read for padding.

## Length and density

One page for under ten years of experience or when the program format requires it; two
pages otherwise. Roughly 350 to 650 words fills one page at 10.5pt depending on layout; render the PDF and look rather than counting. Three to five bullets per
recent role, one to two for older ones. Each bullet: verb, what, how, measurable result.

## Fonts

The builder defaults to Calibri. Machines without Microsoft Office substitute a
metric-compatible font (Carlito), so the layout holds, but if the user's audience is mostly
Mac-without-Office, `--font Arial` removes the question entirely. Either parses identically.

## PDF or Word

Submit .docx when the portal accepts it; it parses most reliably and keeps the layout
editable. Submit PDF when the portal asks for it or when a human will read it first (email,
referral). The builder's `--pdf` flag produces both from the same source, so the content
never drifts between them.
