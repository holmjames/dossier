# Resume tailoring

Tailoring is selection and translation, not invention. The master resume holds every true
bullet; the tailored resume shows the ones this role cares about, in this role's language.

## Order of operations

1. **Read the must-haves** from `jd_analysis.md`. For each, find the fact in `profile.md`
   or `master_resume.md` that answers it. Write the mapping down before touching the resume:

   | Must-have (posting's words) | Supporting fact | Where it will appear |
   |---|---|---|
   | "experience with marketing automation platforms (Marketo, HubSpot)" | Marketo admin at Acme Software, Northwind, Fieldstone; HubSpot at Brightline | Summary + Brightline bullet 1 + Skills |
   | "comfort with SQL and dashboards" | SQL reporting at Brightline; weekly COO readout | Brightline bullet 2 |
   | "shipped product" | Three App Store apps | Projects line |

   A must-have with an empty middle column is a gap. Ask the user; do not fill it.

2. **Summary line.** Two lines at most, right under contact info. Pattern: who they are in
   the posting's title language (if fair), years and domain, then the three strongest matched
   terms. "Marketing operations leader with 7 years in B2B SaaS, certified in Marketo and
   Salesforce, moving into product management after shipping three consumer apps." The
   summary exists because recruiters read the top third and parsers weight it.

3. **Reorder.** Sections: whatever the user's format requires (MBA formats usually put
   Education first). Within Experience, roles stay chronological; bullets within a role are
   reordered so the ones answering must-haves come first.

4. **Translate bullets.** For each bullet that supports a must-have, rewrite it so the
   posting's term appears naturally, keeping the original fact, scope, and number intact.

   Before: "Built an AI agent suite for BDR and GTM Ops teams; projected $385K annual savings"
   Posting asks for: "AI/ML products", "agentic workflows", "cross-functional"
   After: "Built an agentic AI suite for BDR and GTM Ops teams with engineering and RevOps;
   200+ weekly users and a projected $385K in annual savings"

   Allowed: synonyms the user would use themselves, adding a true detail that the posting
   cares about, splitting one dense bullet into two. Not allowed: changing the verb's scope
   (built vs. contributed to), the number, the team size, the timeframe, or the title.

5. **Trim.** Remove bullets that do not serve this role until the page fits. Older roles can
   drop to one bullet or title-only. Never remove a role entirely to hide a gap; shorten it.

6. **Skills block.** List tools and certifications in the posting's spelling ("Marketo
   Engage" if the posting says that, "Power BI" not "PowerBI"). Group by type (Tools,
   Certifications, Methods) so a human can scan it. Only tools the user has actually used;
   `profile.md` says how deeply, and anything marked "exposure only" stays out of a role
   that lists it as a core requirement.

7. **Projects and side work.** For career pivots these often carry the must-haves the job
   history cannot. One line each: what it is, what it proves, a number. Link only if the
   user's format allows links.

## Checks before scoring

- Every number in the tailored resume appears in `profile.md` or the master.
- Job titles, employers, dates, and locations are unchanged (except a stated location
  convention in `profile.md`, such as listing a remote job under the office city).
- No bullet starts with "Responsible for." Verbs: built, led, designed, launched, owned,
  cut, grew, migrated, negotiated, automated.
- The user's voice rules are respected (punctuation, banned words, spelling).
- The summary contains the target title only if the user would say it about themselves.

## Writing `changes.md`

The user approves against this file, so make it scannable:

```
# Changes vs. master resume: Adobe, 2027 MBA Intern, Product Manager

## Added
- Summary line (new): "..." Justified by: Marketo certs, Harbor Labs PM title, three shipped apps.
- "agentic" in Brightline bullet 1. Justified by: profile line "Brightline agents used scoped API permissions and guardrails."

## Rewritten
- Brightline bullet 2, before: "..." after: "..." Why: posting asks for dashboards and executive presentation.

## Reordered
- Education moved above Experience (McCombs format). Harbor Labs role moved up one bullet.

## Removed
- Fieldstone bullet 3 (event logistics): not relevant, needed the space.

## Still missing after tailoring
- Power BI: not true (Tableau only). Left out.
- Salesforce Marketing Cloud: not true. Left out.
```
