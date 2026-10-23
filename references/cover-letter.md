# Cover letter

A cover letter has one job: give the reader a reason to open the resume with a favorable
prior. It is read by a human, usually a recruiter or hiring manager, usually in under a
minute. It is rarely parsed for keywords, so it is the place for the story the resume
cannot tell, not a second keyword list.

Some companies state that they do not read them (Amazon's recruiters say this at events).
When `jd_analysis.md` or the user says so, skip the letter and spend the effort on the resume
summary and the portal's short-answer questions instead.

## Structure (under 350 words, four short paragraphs)

1. **The hook, two or three sentences.** The specific reason this role, from the posting's
   signals: the product, the team's stated problem, a named initiative. Then the one fact
   about the user that makes them the obvious person for it. Not "I am writing to apply for"
   and not a compliment about the company's culture.

2. **Proof, one paragraph.** One story that maps to the posting's most important must-have.
   Situation in a clause, what they did, the result with a number. Draw it from
   `profile.md`; do not restate a resume bullet verbatim, expand the one that matters.

3. **Second proof or the bridge, one paragraph.** For a straight-line application, a second
   story against the second must-have. For a pivot, this is where to name the pivot plainly
   and show the transferable evidence: "I have not held a PM title at a large company. I have
   shipped three apps to the App Store, owned a roadmap for a Salesforce product, and written
   the PRDs for an agent suite 200 people use." Naming the gap first takes it off the table.

4. **Close, two sentences.** What they would want to work on in the role, specifically, and a
   plain thank-you. No "I look forward to discussing how my skills align."

## Voice

- Write in the user's register, per `profile.md`. Confident, concrete, no superlatives
  about themselves ("passionate," "results-driven," "proven track record" are banned).
- First person, active verbs, short sentences. One idea per paragraph.
- Address a named person if the posting or the user's notes give one; otherwise "Dear
  [Company] [Team] Hiring Team" or "Dear Hiring Manager." Never "To Whom It May Concern."
- Mention the company name two or three times at most. Mention the role title once, in
  the first paragraph, exactly as posted.
- Respect any punctuation or word rules the user set (for example, no em dashes).

## Markdown format for `build_docx.py --kind letter`

```
# Jane Doe
Austin, TX | jane@email.com | (512) 555-0100 | linkedin.com/in/janedoe

Date: October 21, 2026

Dear Adobe Product Management Hiring Team,

Paragraph one.

Paragraph two.

Paragraph three.

Paragraph four.

Sincerely,
Jane Doe
```

Use the sign-off recorded under "Format and voice" in `profile.md` if there is one ("Best,
Jane" and "Sincerely, Jane Doe" are both fine; what matters is that it is theirs).

Each line inside a block is kept as its own line, so "Sincerely," and the name stay
separate. Blank lines add paragraph spacing.

## Before approval

- Every fact in the letter appears in `profile.md`.
- Word count under 350 (`wc -w cover_letter.md`).
- The first sentence would make sense only for this company and role. If it could be pasted
  into another letter unchanged, rewrite it.
