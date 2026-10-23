# Stage 2b: Warm paths (alumni and former colleagues at the company)

A referral or a fifteen-minute conversation with someone inside the company changes the
odds more than any resume edit. This stage finds a few people the user has a real
connection to, shows them, and drafts the first note. The user sends it.

## What counts as a warm path

Someone who works at the target company now and shares one of the user's networks, in
rough order of warmth:

1. Same school and same program, overlapping or recent years (an Anderson FEMBA at Adobe
   for an Anderson FEMBA applying to Adobe)
2. Same school, any program
3. Former colleague: worked at one of the user's past employers, now at the target company
4. Same professional community (user group, fellowship, service program, military unit)
5. Same function at the company, with no shared affiliation (a courtesy "I'm applying to
   your team" note; weaker, but it is how hiring managers hear names)

`## Networks` in `profile.md` lists the user's affiliations. If it is empty, ask: schools
with program and class year (undergrad and graduate), former employers, communities. Also
ask whether they prefer to reach out to recent grads (more likely to reply) or senior
people (more likely to refer), since that changes who gets listed first.

## Privacy rules, which are not optional

- **Public professional information only**: name, current title, company, the shared
  affiliation, and the link to the public profile or page where that was found. Nothing
  else. No email addresses or phone numbers dug up from other sites, no personal details,
  no inferences about the person. If the user wants a contact method, the answer is
  LinkedIn's message or connection request, or the school's alumni directory, where the
  person chose to be reachable.
- **A few matches, not a list.** Three to five people per company. This is a shortlist for
  outreach, not a map of the org.
- **Stored in the application folder only** (`warm_paths.md`), alongside the posting it was
  found for, and deleted if the user drops the application. The tracker gets a one-line
  note ("warm path: 2 Anderson alumni identified"), not the names.
- **The user does the outreach.** Claude drafts; it does not send messages, connection
  requests, or emails, and does not create or log into accounts.
- **No bulk reading.** Reading the first page of an alumni search in the user's own browser
  is what that tool exists for. Paging through hundreds of profiles or exporting them is not,
  and it gets accounts restricted.

## Where to look, in order

### 1. LinkedIn's alumni tool, in the user's own browser (best source)

LinkedIn's school pages have an alumni view with filters for current company, title, and
graduation year. It only works logged in, and it is the user's own account, so the user
opens it. Give them the exact page:

```
https://www.linkedin.com/school/<school-slug>/people/?keywords=<Company>
```

For UCLA Anderson the slug is `ucla-anderson-school-of-management`; for a university it is
usually the name with hyphens (`purdue-university`). If unsure, have them search the school
on LinkedIn and click "Alumni" on its page. On the alumni page they type the company name in
the search box, then narrow with "What they do" (Product Management, Marketing).

If Claude in Chrome is present and the user asks, Claude can open that page in a new tab and
read the first page of results, which saves the user transcribing names. Read once; do not
scroll through more than the first twenty or so results, do not open each profile, and do
not use the connect or message buttons.

Also point the user at their school's own resources, which often beat LinkedIn for reply
rates: the alumni directory (every business school has one, login required), the career
center's platform (12twenty, Handshake), and club Slack channels. Anderson's alumni
directory and the Andertech Slack are both better than a cold LinkedIn note for an Anderson
student.

### 2. Web search (supplement; always verify)

Open web search finds public bios that mention both affiliations: company blog author
pages, school news stories ("alum joins Adobe"), conference speaker bios, Product School
and similar profiles, press releases. It is noisy and misses most people. Run three or four
phrasings and fetch any promising page to confirm the person works there now:

```
"<School>" "<Company>" product manager
"<School short name>" alumni "<Company>" <function>
"formerly at <Former employer>" "<Company>"
"<Former employer>" "<Company>" site:linkedin.com/in
"<Community name>" "<Company>"
```

A search hit is a lead, not a match. The page it points to must show the current company
and the shared affiliation before the person goes on the list. Titles go stale; note the
date on the source page.

### 3. The user's own memory

Ask: "Do you already know anyone at <Company>, or anyone who used to work there?" People
forget their own networks. A second-degree connection the user can name is worth more than
anything a search finds.

## Output: `warm_paths.md` in the application folder

```
# Warm paths: Adobe, 2027 MBA Intern, Product Manager

Found 2026-10-22 from public profiles. Titles may be stale; confirm on the profile before writing.

| # | Name | Current title | Shared with you | Found at | Why first |
|---|---|---|---|---|---|
| 1 | <Name> | Product Manager, Marketo Engage | Anderson FEMBA '25 | linkedin.com/in/... | Same program, same product you named as the target |
| 2 | <Name> | Sr. PMM, Digital Experience | Anderson MBA '19 | business.adobe.com/blog/authors/... | Same school, in the group that posted the role |
| 3 | <Name> | Group PM | MX Technologies 2021-2023 | linkedin.com/in/... | Former colleague; can refer |

Suggested order: 1, then 3 (referral-eligible), then 2.

Not yet checked: the Anderson alumni directory and the Andertech Slack. Both are logged-in
tools; ten minutes there usually turns up one or two more.

## Draft note to #1 (you send it; edit freely)

Hi <First name>, I'm a FEMBA '28 at Anderson and I just applied to the Marketo Engage PM
internship. I administered Marketo at three companies and co-led the SLC user group, so
the Email Designer launch has been fun to follow. Would you have 15 minutes in the next
couple of weeks to tell me how the PM team works with the Marketo product? Happy to work
around your calendar. Thanks, <Name>
```

## The note

Under 120 words. Lead with the shared affiliation in the first sentence, name the specific
role in the second, give one concrete reason the user is a credible candidate in the third,
ask for fifteen minutes in the fourth. No attachments, no "pick your brain," no asking for
a referral in the first message (ask for the conversation; the referral comes up naturally
if the conversation goes well). Written in the user's voice per `## Format and voice` and
their outreach style under `## Networks`, with their sign-off.

For a former colleague the tone is warmer and shorter; for a courtesy note to a hiring
manager with no shared affiliation, it is three sentences and does not ask for time.

## When it runs

After the user has picked a role in Stage 1 and before or alongside tailoring in Stage 3,
so the outreach can go out the same day as the application; recruiters notice when a
referral lands within a day or two of the application. Offer it; some users want the
application in first. For a company the user is applying to repeatedly, reuse the previous
`warm_paths.md` and only look for additions.

## Tracker

Update the application's tracker row with a one-line note and a follow-up date for the
outreach, which is separate from the application follow-up:

```
python3 "$SKILL/scripts/tracker.py" update --file tracker.xlsx --company "<Co>" --role "<Title>" \
  --notes "Warm paths: 3 found (2 Anderson, 1 ex-MX); note drafted for #1" --next "Send outreach note" --follow-up +3d
```
