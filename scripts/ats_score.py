#!/usr/bin/env python3
"""Score a resume against a job description the way an ATS keyword filter would.

Usage:
    python3 ats_score.py --jd jd.txt --resume resume.docx [--out ats_report.md] [--json ats.json]
                         [--extra-terms terms.txt] [--title "Product Manager"]

What it does, in plain terms:
  1. Reads the job description and pulls out the terms that matter: tools,
     skills, certifications, acronyms, and phrases the posting repeats.
  2. Weights them. Terms under "Requirements / Qualifications" count triple,
     "Preferred / Nice to have" double, everything else once.
  3. Checks which of those terms appear in the resume, allowing for plurals,
     acronyms, and common synonyms (GTM = go-to-market, SFDC = Salesforce).
  4. If the resume is a .docx, checks for formatting that breaks ATS parsers:
     tables, text boxes, images, multi-column layouts, contact info hidden
     in the header.
  5. Writes a Markdown report and a JSON summary.

The score is a weighted keyword coverage percentage. It is a proxy for how a
keyword filter sees the resume, not a judgment of the candidate. Honest gaps
should stay gaps; the report lists them so a human can decide.
"""
import argparse
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_text import extract  # noqa: E402

# ---------------------------------------------------------------------------
# Word lists. Edit these freely; they are the "taste" of the scorer.
# ---------------------------------------------------------------------------

STOPWORDS = set("""
a an and are as at be been but by for from has have in into is it its of on or
that the their this to was were will with you your we our us they them he she
his her i me my who whom which what when where why how all any both each few
more most other some such no nor not only own same so than too very can just
should now also about across after before between during through under over
up down out off above below again further then once here there if while
including include includes etc per via within without along among around
""".split())

# Words that show up in every job posting and tell you nothing about fit.
GENERIC = set("""
team teams experience experiences work working works role roles job jobs
company companies business businesses year years ability able strong
excellent skills skill required requirement requirements preferred plus
bonus responsibilities responsibility qualifications qualification candidate
candidates position opportunity opportunities environment fast paced
minimum basic degree bachelor bachelors master masters equivalent related
field knowledge understanding proven track record demonstrated successful
success day week month time new help support ensure drive deliver build
create develop manage lead own partner collaborate communicate join apply
people person employees employee benefits salary range compensation
location remote hybrid onsite office full part employment status equal
veteran disability gender race religion applicants applicant diverse
diversity inclusion inclusive law laws legal authorized authorization
sponsorship visa citizen citizenship united states us u.s nice great good
looking seeking want wants need needs like love passion passionate
excited exciting world class best growing grow growth culture mission
values value impact meaningful make making made using use used uses
across multiple various different level levels senior junior staff
type types high quality key stakeholders stakeholder internal external
area areas way ways thing things one two three plus years
summer winter fall spring intern interns internship internships program programs
product products marketing management design engineering engineers engineer
customer customers data platform platforms solution solutions system systems
service services process processes strategy strategies strategic operations
sales technical technology technologies tools tool software project projects
communication communications analytical leadership results goals initiatives
features feature function functions partners partnerships performance insights
decisions recommendations recommendation presentation presentations end
problem problems problem-solving solving user users
write writes writing written wrote read reads reading run runs running ran
ship ships shipping shipped present presents presenting presented define
defines defining defined analyze analyzes analyzing analyzed own owns owning
owned partner partners partnering partnered lead leads leading led build builds
building built create creates creating created develop develops developing
developed manage manages managing managed deliver delivers delivering delivered
drive drives driving driven identify identifies identifying identified
on-site in-office in-person relocation relocate
currently enrolled enrollment professional verbal prior comfort comfortable
familiarity familiar exposure hands-on proficiency proficient fluency fluent
preferably ideally typically regularly directly
""".split())

# Place names: a posting's city is not a skill. Add your region's cities freely.
LOCATIONS = set("""
san francisco bay area new york nyc los angeles la seattle austin boston chicago
denver atlanta dallas houston miami phoenix portland san diego san jose
mountain view menlo park palo alto sunnyvale redmond bellevue cupertino
santa monica culver city irvine lehi salt lake city provo washington dc
alabama alaska arizona arkansas california colorado connecticut delaware florida
georgia hawaii idaho illinois indiana iowa kansas kentucky louisiana maine
maryland massachusetts michigan minnesota mississippi missouri montana nebraska
nevada hampshire jersey mexico york carolina dakota ohio oklahoma oregon
pennsylvania rhode island tennessee texas utah vermont virginia wisconsin wyoming
london toronto vancouver dublin berlin paris amsterdam bangalore bengaluru
singapore sydney tel aviv united states usa canada uk europe emea apac
""".split())

# Lines that are legal boilerplate, not job content. Dropped before analysis.
BOILERPLATE = re.compile(
    r"equal opportunity|discriminat|veteran status|reasonable accommodation|"
    r"e-verify|background check|affirmative action|protected (class|characteristic)|"
    r"without regard to|sexual orientation|gender identity|pay transparency|"
    r"base (pay|salary) range|\$\d{2,3},\d{3}", re.I)

US_STATES = set("""al ak az ar ca co ct de fl ga hi id il in ia ks ky la me md ma mi mn ms mo
mt ne nv nh nj nm ny nc nd oh ok or pa ri sc sd tn tx ut vt va wa wv wi wy dc""".split())

# Known skills and tools, one per line. Matching one of these anywhere in the
# posting is a strong signal regardless of frequency. Lowercase. Add your own
# domain terms here (or pass --extra-terms at run time).
LEXICON = """
salesforce
sfdc
hubspot
marketo
marketo engage
pardot
eloqua
braze
iterable
klaviyo
mailchimp
outreach
salesloft
apollo
zoominfo
clay
6sense
demandbase
gong
clari
leandata
openprise
workato
zapier
mulesoft
mparticle
amplitude
mixpanel
pendo
fullstory
hotjar
google analytics
ga4
looker
tableau
power bi
metabase
snowflake
bigquery
redshift
databricks
dbt
fivetran
airflow
sql
python
javascript
typescript
java
swift
kotlin
html
css
react
node.js
excel
google sheets
powerpoint
figma
miro
lucidchart
jira
confluence
asana
monday.com
notion
trello
productboard
github
postman
openapi
rest api
apis
graphql
webhooks
sdk
etl
cdp
mdm
crm
erp
cms
okta
workday
netsuite
stripe
shopify
aws
gcp
azure
kubernetes
docker
terraform
product management
product manager
product marketing
product marketing manager
go-to-market
gtm
revops
revenue operations
marketing operations
sales operations
demand generation
lead generation
lead scoring
lead routing
attribution
multi-touch attribution
funnel
pipeline
forecasting
territory planning
quota
account-based marketing
abm
lifecycle marketing
nurture
email marketing
marketing automation
workflows
integrations
data governance
data quality
enrichment
segmentation
personalization
a/b testing
experimentation
user research
customer discovery
customer interviews
roadmap
prioritization
prd
user stories
backlog
agile
scrum
kanban
okrs
kpis
dashboards
north star
positioning
messaging
competitive analysis
market research
enablement
sales enablement
machine learning
artificial intelligence
generative ai
llm
large language models
prompt engineering
rag
agentic
mcp
model context protocol
evals
fine-tuning
nlp
data science
statistics
cohort analysis
ltv
cac
churn
retention
nps
saas
b2b
b2c
plg
product-led growth
mid-market
smb
stakeholder management
cross-functional
executive communication
project management
program management
change management
vendor management
p&l
financial modeling
business case
mba
pmp
csm
cspo
six sigma
salesforce certified administrator
marketo certified expert
hubspot certified
google ads
linkedin ads
paid media
paid search
seo
sem
content marketing
brand marketing
brand management
field marketing
partner marketing
customer marketing
compliance
soc 2
gdpr
ccpa
privacy
"""
LEXICON_SET = {line.strip() for line in LEXICON.strip().split("\n") if line.strip()}

# Synonyms: if the JD says the left side and the resume says anything on the
# right side (or vice versa), count it as a match. Keep these honest; a synonym
# should mean the same thing to a recruiter, not merely be adjacent.
SYNONYMS = {
    "go-to-market": ["gtm", "go to market"],
    "revenue operations": ["revops", "rev ops"],
    "marketing operations": ["marketing ops", "mops"],
    "sales operations": ["sales ops"],
    "salesforce": ["sfdc", "salesforce.com"],
    "a/b testing": ["ab testing", "a/b tests", "split testing", "experimentation"],
    "product manager": ["pm", "product management"],
    "product marketing manager": ["pmm", "product marketing"],
    "key performance indicators": ["kpis", "kpi"],
    "objectives and key results": ["okrs", "okr"],
    "customer relationship management": ["crm"],
    "customer data platform": ["cdp"],
    "master data management": ["mdm"],
    "account-based marketing": ["abm", "account based marketing"],
    "artificial intelligence": ["ai"],
    "machine learning": ["ml"],
    "large language models": ["llm", "llms"],
    "generative ai": ["genai", "gen ai"],
    "model context protocol": ["mcp"],
    "application programming interface": ["api", "apis"],
    "structured query language": ["sql"],
    "cross-functional": ["cross functional", "cross-functionally"],
    "demand generation": ["demand gen"],
    "lead generation": ["lead gen"],
    "software as a service": ["saas"],
    "business-to-business": ["b2b", "business to business"],
    "master of business administration": ["mba"],
    "product requirements document": ["prd", "prds"],
    "return on investment": ["roi"],
    "customer acquisition cost": ["cac"],
    "lifetime value": ["ltv", "clv"],
    "net promoter score": ["nps"],
    "product-led growth": ["plg", "product led growth"],
    "power bi": ["powerbi"],
    "google analytics": ["ga4"],
    "search engine optimization": ["seo"],
}

REQ_HEADINGS = re.compile(
    r"^\s*(minimum|basic|required|requirements?|qualifications?|what you('ll)? (bring|need|have)|"
    r"you (have|bring|are)|must[- ]haves?|who you are|about you|what we('re| are) looking for|"
    r"skills? (and|&) (experience|qualifications)|experience( required)?|your (background|profile))\b",
    re.I,
)
PREF_HEADINGS = re.compile(
    r"^\s*(preferred|nice[- ]to[- ]haves?|bonus|desired|ideally|it('s| is) a plus|"
    r"additional qualifications|extra credit|even better if|pluses)\b", re.I,
)
OTHER_HEADINGS = re.compile(
    r"^\s*(responsibilities|what you('ll)? do|the role|about (the role|us|the team)|"
    r"your impact|day to day|in this role|benefits|perks|compensation|pay|salary|"
    r"equal opportunity|eeo|how to apply|about the company|why join)\b", re.I,
)


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Lowercase, unify dashes and quotes, collapse whitespace."""
    text = text.lower()
    text = text.replace("–", "-").replace("—", "-").replace("’", "'")
    text = re.sub(r"[“”]", '"', text)
    text = re.sub(r"[ \t]+", " ", text)
    return text


IRREGULAR = {
    "wrote": "write", "written": "write", "writing": "write", "writes": "write",
    "led": "lead", "leading": "lead", "leads": "lead",
    "ran": "run", "running": "run", "runs": "run",
    "built": "build", "building": "build", "builds": "build",
    "drove": "drive", "driven": "drive", "driving": "drive",
    "grew": "grow", "grown": "grow", "growing": "grow",
    "sold": "sell", "selling": "sell",
    "taught": "teach", "teaching": "teach",
    "brought": "bring", "bringing": "bring",
    "won": "win", "winning": "win",
    "held": "hold", "holding": "hold",
    "shipped": "ship", "shipping": "ship", "ships": "ship",
    "analyses": "analysis", "analyzed": "analyze", "analysed": "analyze", "analyzing": "analyze",
    "cross-functionally": "cross-functional",
    "data": "data",
}


def stem(word: str) -> str:
    """A very small stemmer: enough to match 'dashboards' to 'dashboard' and
    'forecasting' to 'forecast' without a dependency."""
    w = word.lower()
    if w in IRREGULAR:
        return IRREGULAR[w]
    for suf in ("ations", "ation", "ings", "ing", "ies", "ers", "er", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            base = w[: -len(suf)]
            if suf == "ies":
                base += "y"
            return base
    return w


def tokens(text: str):
    return re.findall(r"[a-z0-9][a-z0-9+#./&'-]*[a-z0-9+#]|[a-z0-9]", normalize(text))


def stem_phrase(phrase: str) -> str:
    return " ".join(stem(t) for t in tokens(phrase))


def split_sections(jd: str):
    """Walk the JD line by line and label each line as req / pref / other
    based on the most recent heading-looking line."""
    labels = []
    current = "other"
    raw_lines = jd.split("\n")
    # Skip a leading "Key: value" metadata block (Source:, Fetched:, Title: ...)
    # that the sourcing step puts at the top of jd.txt. It is bookkeeping, not
    # posting content, and would otherwise be mined for keywords.
    start = 0
    meta_keys = r"^\s*(source|fetched|title|company|location|url|link|date|posted|role|employer|req(uisition)? ?id|job id)\s*:"
    while start < len(raw_lines) and re.match(meta_keys, raw_lines[start], re.I):
        start += 1
    if start and start < len(raw_lines) and not raw_lines[start].strip():
        start += 1
    if not start:
        start = 0
    for line in raw_lines[start:]:
        stripped = line.strip()
        if BOILERPLATE.search(stripped):
            continue
        is_heading_like = len(stripped) <= 80 and not stripped.endswith(".")
        if is_heading_like:
            if REQ_HEADINGS.search(stripped):
                current = "req"
            elif PREF_HEADINGS.search(stripped):
                current = "pref"
            elif OTHER_HEADINGS.search(stripped):
                current = "other"
        labels.append((current, line))
    return labels


# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------

def extract_keywords(jd: str, extra_terms=None, company=None, title=None, location=None):
    """Return {term: {"weight": int, "section": str, "count": int}}."""
    extra = {t.strip().lower() for t in (extra_terms or []) if t.strip()}
    company_words = set(tokens(company)) if company else set()
    # Words from the posted title and location, plus season/year words, so that
    # fragments like "mba intern summer 2027" or "san francisco ca" are not
    # reported as skills to add.
    noise_words = set(tokens(title or "")) | set(tokens(location or "")) | LOCATIONS | US_STATES | {
        "summer", "winter", "spring", "fall", "intern", "internship", "2025", "2026", "2027", "2028",
        "remote", "hybrid", "onsite", "full-time", "part-time"}
    lexicon = LEXICON_SET | extra
    labeled = split_sections(jd)
    norm_jd = normalize(jd)

    found = {}

    def add(term, section, count=1):
        base_weight = {"req": 3, "pref": 2, "other": 1}[section]
        if term in found:
            # Keep the strongest section seen.
            if base_weight > found[term]["weight"]:
                found[term]["weight"] = base_weight
                found[term]["section"] = section
            found[term]["count"] += count
        else:
            found[term] = {"weight": base_weight, "section": section, "count": count}

    # 1. Lexicon terms, per section.
    for section, line in labeled:
        nl = normalize(line)
        for term in lexicon:
            if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", nl):
                add(term, section)

    # 2. Acronyms (2-6 capital letters, possibly with digits) from original text.
    for section, line in labeled:
        for acr in re.findall(r"\b[A-Z][A-Z0-9&/]{1,5}\b", line):
            low = acr.lower()
            if low in GENERIC or low in US_STATES or acr in ("US", "USA", "EEO", "LLC", "INC", "AND", "OR", "THE", "ID", "PTO", "EST", "PST"):
                continue
            add(acr.lower(), section)

    # 3. Capitalised multiword names (e.g. "Marketo Engage", "Google Cloud Platform").
    for section, line in labeled:
        for m in re.findall(r"\b([A-Z][a-zA-Z0-9+]*(?:\.[a-z]+)?(?:\s+[A-Z][a-zA-Z0-9+]*(?:\.[a-z]+)?){1,3})\b", line):
            low = m.lower()
            words = low.split()
            if all(w in GENERIC or w in STOPWORDS for w in words):
                continue
            if low.split()[0] in ("the", "our", "we", "you", "this", "a", "an"):
                continue
            add(low, section)

    # 4. Noun phrases (1-3 grams). Lines are split on punctuation first so a
    # phrase never spans a comma or a parenthesis ("(Amplitude, Mixpanel)" must
    # not yield "amplitude mixpanel tools"). Grams containing a stopword or a
    # number are skipped; "comfort with sql" and "3+ years" are not skills.
    section_counts = defaultdict(Counter)
    for section, line in labeled:
        for chunk in re.split(r"[,;:()\[\]/|]| - | and | or ", normalize(line)):
            toks = tokens(chunk)
            for n in (1, 2, 3):
                for i in range(len(toks) - n + 1):
                    gram = toks[i:i + n]
                    if any(g in STOPWORDS or any(ch.isdigit() for ch in g) for g in gram):
                        continue
                    if all(g in GENERIC or g in STOPWORDS for g in gram):
                        continue
                    if n == 1 and (len(gram[0]) < 4 or gram[0] in GENERIC):
                        continue
                    section_counts[section][" ".join(gram)] += 1
    total = Counter()
    for c in section_counts.values():
        total.update(c)
    for gram, cnt in total.items():
        n_words = len(gram.split())
        in_req = bool(section_counts["req"][gram] or section_counts["pref"][gram])
        # Two-word phrases in the requirements block matter even when said once.
        words_ = gram.split()
        solid_pair = n_words == 2 and in_req and not any(w in GENERIC for w in words_)
        if cnt >= 2 or gram in lexicon or solid_pair:
            # Pick the strongest section it appears in.
            section = "other"
            for s in ("req", "pref"):
                if section_counts[s][gram]:
                    section = s
                    break
            add(gram, section, count=cnt - 1 if gram in found else cnt)

    # Clean-up: drop n-grams that are strict substrings of a longer kept term
    # with the same count (e.g. keep "marketing automation", drop "automation"
    # only if "automation" never appears alone). We keep both when the shorter
    # one also appears independently.
    keep = {}
    for term, info in found.items():
        words = term.split()
        if company_words and all(w in company_words for w in words):
            continue  # the hiring company's own name is not a skill
        if term not in lexicon and all(w in noise_words or w in STOPWORDS or w in GENERIC for w in words):
            continue  # title fragments, locations, seasons
        if term not in lexicon and n_words_generic(words):
            continue
        longer = [t for t in found if t != term and f" {term} " in f" {t} "]
        if longer and all(found[t]["count"] >= info["count"] for t in longer):
            continue
        keep[term] = info
    return keep


def n_words_generic(words):
    """A single bare verb or generic word on its own is not a keyword."""
    return len(words) == 1 and (words[0] in GENERIC or len(words[0]) < 3)


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def variants(term: str):
    """All spellings that should count as the same term."""
    out = {term}
    for canon, alts in SYNONYMS.items():
        group = {canon, *alts}
        if term in group:
            out |= group
    out |= {t.replace("-", " ") for t in list(out)}
    out |= {t.replace(" ", "-") for t in list(out)}
    return out


def term_in_text(term: str, norm_text: str, stem_text: str) -> bool:
    # "ai/ml" or "sql/python": count it if every part is present somewhere.
    if "/" in term and term not in SYNONYMS and not any(term in g for g in SYNONYMS.values()):
        parts = [p for p in term.split("/") if p]
        if len(parts) > 1 and all(term_in_text(p, norm_text, stem_text) for p in parts):
            return True
    for v in variants(term):
        if re.search(rf"(?<![a-z0-9]){re.escape(v)}(?![a-z0-9])", norm_text):
            return True
        sv = stem_phrase(v)
        if sv and re.search(rf"(?<![a-z0-9]){re.escape(sv)}(?![a-z0-9])", stem_text):
            return True
    return False


def short_title(title: str) -> str:
    """'2027 MBA Intern, Product Manager (Summer)' -> 'product manager'.
    Recruiters search the core title; the program and season words are noise."""
    t = normalize(title)
    t = re.sub(r"\(.*?\)", " ", t)
    t = re.sub(r"\b(20\d\d|mba|intern(ship)?|summer|winter|spring|fall|level|i{1,3}|iv|v|sr\.?|senior|junior|jr\.?|staff|principal|lead|associate|graduate|new grad|contract|remote|hybrid)\b", " ", t)
    t = re.sub(r"[,:/|-]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t or normalize(title)


def score(jd_text: str, resume_text: str, extra_terms=None, title=None, company=None, location=None):
    keywords = extract_keywords(jd_text, extra_terms, company, title, location)
    norm_res = normalize(resume_text)
    stem_res = " ".join(stem(t) for t in tokens(resume_text))

    matched, missing = {}, {}
    for term, info in keywords.items():
        (matched if term_in_text(term, norm_res, stem_res) else missing)[term] = info

    total_w = sum(i["weight"] * min(i["count"], 3) for i in keywords.values()) or 1
    got_w = sum(i["weight"] * min(i["count"], 3) for i in matched.values())
    pct = round(100 * got_w / total_w)

    req_terms = [t for t, i in keywords.items() if i["section"] == "req"]
    req_hit = [t for t in req_terms if t in matched]
    req_pct = round(100 * len(req_hit) / len(req_terms)) if req_terms else None

    title_hit = None
    core = short_title(title) if title else None
    if title:
        title_hit = term_in_text(core, norm_res, stem_res) or term_in_text(title.lower(), norm_res, stem_res)

    return {
        "score": pct,
        "required_coverage": req_pct,
        "title_present": title_hit,
        "core_title": core,
        "matched": matched,
        "missing": missing,
        "keyword_count": len(keywords),
    }


# ---------------------------------------------------------------------------
# Formatting checks for .docx (the part ATS parsers choke on)
# ---------------------------------------------------------------------------

def docx_format_checks(path: Path):
    warnings, notes = [], []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        doc = z.read("word/document.xml").decode("utf8", "ignore")
        headers = [n for n in names if n.startswith("word/header")]
        footers = [n for n in names if n.startswith("word/footer")]
        header_text = ""
        for h in headers:
            header_text += re.sub(r"<[^>]+>", " ", z.read(h).decode("utf8", "ignore"))
    if "<w:tbl>" in doc or "<w:tbl " in doc:
        warnings.append("Uses tables. Many ATS parsers read table cells out of order or skip them. Use plain paragraphs and tab stops instead.")
    if "txbxContent" in doc:
        warnings.append("Contains text boxes. Text boxes are frequently invisible to parsers. Move that text into the body.")
    if "<w:drawing" in doc or "<pic:pic" in doc:
        warnings.append("Contains images or graphics. Parsers ignore them, and anything written inside them is lost.")
    if re.search(r'<w:cols[^>]+w:num="([2-9])"', doc):
        warnings.append("Multi-column layout detected. Parsers often read across columns and scramble the order. Use a single column.")
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", header_text) or re.search(r"\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}", header_text):
        warnings.append("Contact info is in the page header. Some parsers skip headers; put name, email, and phone in the body at the top.")
    fonts = set(re.findall(r'w:ascii="([^"]+)"', doc))
    odd = {f for f in fonts if f.lower() not in {
        "calibri", "arial", "helvetica", "times new roman", "georgia", "garamond",
        "cambria", "verdana", "tahoma", "trebuchet ms", "book antiqua", "palatino linotype",
        "aptos", "segoe ui", "lato", "roboto", "open sans", "source sans pro", "symbol"}}
    if odd:
        notes.append(f"Fonts in use: {', '.join(sorted(fonts))}. Unusual fonts ({', '.join(sorted(odd))}) are fine for parsing but may not be installed where the file is opened; PDF export avoids that.")
    if "<w:sym " in doc:
        notes.append("Symbol characters found (often custom bullets). Standard bullets parse more reliably.")
    return warnings, notes


def text_format_checks(resume_text: str):
    warnings, notes = [], []
    low = resume_text.lower()
    std_sections = {
        "experience": r"\b(professional |work )?experience\b|\bemployment\b",
        "education": r"\beducation\b",
        "skills": r"\bskills\b|\btechnical proficiencies\b|\bcertifications?\b|\badditional\b|\bqualifications\b",
    }
    for name, pat in std_sections.items():
        if not re.search(pat, low):
            warnings.append(f"No standard '{name.title()}' heading found. Parsers map content by heading names; use the conventional word.")
    if not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", resume_text):
        warnings.append("No email address found in the body text.")
    if not re.search(r"\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}", resume_text):
        warnings.append("No phone number found in the body text.")
    dates = re.findall(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.? ?\d{4}\b|\b\d{1,2}/\d{4}\b|\b(?:19|20)\d{2}\b", low)
    if len(dates) < 2:
        warnings.append("Few or no dates detected. Each role needs a start and end date (Month YYYY) for the parser to build a timeline.")
    styles = set()
    if re.search(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]* \d{4}\b", low):
        styles.add("Month YYYY")
    if re.search(r"\b\d{1,2}/\d{4}\b", low):
        styles.add("MM/YYYY")
    if len(styles) > 1:
        notes.append(f"Mixed date formats ({', '.join(sorted(styles))}). Pick one.")
    words = len(resume_text.split())
    notes.append(f"Length: about {words} words of content. One-page resumes usually land between 350 and 650 words depending on layout; judge length by the rendered PDF, not by this count.")
    return warnings, notes


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def fmt_terms(d, limit=None):
    items = sorted(d.items(), key=lambda kv: (-kv[1]["weight"], -kv[1]["count"], kv[0]))
    if limit:
        items = items[:limit]
    return items


def render_report(result, fmt_warnings, fmt_notes, jd_name, resume_name, title):
    s = result
    lines = [f"# ATS report: {resume_name} vs {jd_name}", ""]
    verdict = "strong" if s["score"] >= 75 else "fair" if s["score"] >= 55 else "weak"
    lines.append(f"**Keyword coverage: {s['score']}%** ({verdict}). "
                 f"{len(s['matched'])} of {s['keyword_count']} weighted terms present.")
    if s["required_coverage"] is not None:
        lines.append(f"**Required-section coverage: {s['required_coverage']}%**")
    if title:
        lines.append(f"**Core title \"{s['core_title']}\" appears in resume:** {'yes' if s['title_present'] else 'no (add it to the summary line if it is a fair description of you; otherwise leave it)'}")
    lines += ["", "Scores above 75% usually clear automated screens. Below 55%, the resume likely "
              "reads as a different job family to the parser. The goal is not 100%: it is to "
              "close every gap that is true of you and leave the ones that are not.", ""]

    lines += ["## Missing terms (fix these first)", ""]
    miss = fmt_terms(s["missing"])
    if not miss:
        lines.append("None. Every extracted term is present.")
    else:
        lines.append("| Term | Where in JD | Mentions | Action |")
        lines.append("|---|---|---|---|")
        for term, info in miss:
            where = {"req": "Requirements", "pref": "Preferred", "other": "Body"}[info["section"]]
            action = "Add if true of you" if info["section"] == "req" else "Add if true and space allows"
            lines.append(f"| {term} | {where} | {info['count']} | {action} |")
    lines += ["", "Some listed terms will be scorer noise (a product name, a phrase from the posting's own boilerplate). Ignore those; they cost nothing.", "", "## Matched terms", ""]
    hit = fmt_terms(s["matched"])
    lines.append(", ".join(f"{t} ({'R' if i['section']=='req' else 'P' if i['section']=='pref' else 'B'})" for t, i in hit) or "None")
    lines += ["", "R = requirements section, P = preferred, B = body of posting.", ""]

    lines += ["## Formatting", ""]
    if fmt_warnings:
        for w in fmt_warnings:
            lines.append(f"- WARNING: {w}")
    else:
        lines.append("- No parser-breaking formatting detected.")
    for n in fmt_notes:
        lines.append(f"- Note: {n}")
    lines += ["", "## How to read this", "",
              "- Terms are weighted: requirements x3, preferred x2, body x1, and repeated terms count more (capped at 3 mentions).",
              "- Synonyms and acronyms count (GTM = go-to-market, SFDC = Salesforce). Spell out an acronym once and use the short form after, so both parsers and people match it.",
              "- Place the most important missing terms in the top third of the resume: summary line, skills block, and the most recent role.",
              "- Never add a term that is not true of you. A keyword match that fails in the interview costs more than the screen it passed.", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jd", required=True, help="job description (.txt/.md/.html/.pdf/.docx)")
    ap.add_argument("--resume", required=True, help="resume (.docx preferred, or .pdf/.txt)")
    ap.add_argument("--out", help="write Markdown report here")
    ap.add_argument("--json", help="write JSON summary here")
    ap.add_argument("--extra-terms", help="file with one extra keyword per line")
    ap.add_argument("--title", help="job title to check for")
    ap.add_argument("--company", help="hiring company name, excluded from keywords")
    ap.add_argument("--location", help="posted location, excluded from keywords")
    args = ap.parse_args()

    jd_path, res_path = Path(args.jd), Path(args.resume)
    jd_text = extract(jd_path)
    resume_text = extract(res_path)
    extra = Path(args.extra_terms).read_text().splitlines() if args.extra_terms else None

    result = score(jd_text, resume_text, extra, args.title, args.company, args.location)
    fmt_warnings, fmt_notes = [], []
    if res_path.suffix.lower() == ".docx":
        fmt_warnings, fmt_notes = docx_format_checks(res_path)
    tw, tn = text_format_checks(resume_text)
    fmt_warnings += tw
    fmt_notes += tn

    report = render_report(result, fmt_warnings, fmt_notes, jd_path.name, res_path.name, args.title)
    if args.out:
        Path(args.out).write_text(report)
    else:
        print(report)
    if args.json:
        summary = {
            "score": result["score"],
            "required_coverage": result["required_coverage"],
            "title_present": result["title_present"],
            "core_title": result["core_title"],
            "keyword_count": result["keyword_count"],
            "matched": sorted(result["matched"]),
            "missing": [{"term": t, "section": i["section"], "count": i["count"]} for t, i in fmt_terms(result["missing"])],
            "format_warnings": fmt_warnings,
            "format_notes": fmt_notes,
        }
        Path(args.json).write_text(json.dumps(summary, indent=2))
    if args.out:
        print(f"ATS score {result['score']}% | required coverage {result['required_coverage']}% | "
              f"{len(result['missing'])} missing | {len(fmt_warnings)} formatting warnings | report: {args.out}")


if __name__ == "__main__":
    main()
