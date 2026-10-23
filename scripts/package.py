#!/usr/bin/env python3
"""Zip one application folder (or the whole applications directory) for delivery.

Usage:
    python3 package.py <folder> [--out name.zip] [--all]

By default only deliverables go in: the .docx and .pdf files (not drafts),
ats_report.md, changes.md, jd.txt, and a generated README. Pass --all to
include the working files too (markdown sources, analysis, JSON).

Given  applications/2026-10-21_adobe_pm-intern/  it writes
       applications/2026-10-21_adobe_pm-intern.zip
containing the resume, cover letter, ATS report, JD snapshot, and a README
listing what is inside. Point it at applications/ to bundle everything plus
the tracker.
"""
import argparse
import zipfile
from datetime import datetime
from pathlib import Path

SKIP = {".DS_Store", "Thumbs.db"}
DELIVERABLE_NAMES = {"ats_report.md", "changes.md", "jd.txt", "tracker.xlsx"}


def is_deliverable(p: Path) -> bool:
    n = p.name.lower()
    if n.startswith("draft"):
        return False
    if p.suffix.lower() in (".docx", ".pdf"):
        return True
    return n in DELIVERABLE_NAMES


def describe(p: Path) -> str:
    n = p.name.lower()
    if "resume" in n and n.endswith(".docx"):
        return "Tailored resume (Word, ATS-safe)"
    if "resume" in n and n.endswith(".pdf"):
        return "Tailored resume (PDF, for humans and portals that prefer PDF)"
    if "cover" in n and n.endswith(".docx"):
        return "Cover letter (Word)"
    if "cover" in n and n.endswith(".pdf"):
        return "Cover letter (PDF)"
    if n.startswith("ats"):
        return "ATS keyword report"
    if n.startswith("jd"):
        return "Job description snapshot, as posted"
    if "tracker" in n:
        return "Application tracker"
    if n == "changes.md":
        return "What changed vs. the master resume, and why"
    if n in ("resume.md", "cover_letter.md"):
        return "Markdown source (edit this and rebuild)"
    if n == "jd_analysis.md":
        return "Posting analysis: must-haves, gaps, signals"
    if n.endswith(".json"):
        return "Machine-readable ATS summary"
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--out")
    ap.add_argument("--all", action="store_true", help="include working files, not just deliverables")
    args = ap.parse_args()
    folder = Path(args.folder).resolve()
    if not folder.is_dir():
        raise SystemExit(f"Not a folder: {folder}")
    out = Path(args.out) if args.out else folder.with_suffix(".zip")

    files = sorted(p for p in folder.rglob("*") if p.is_file() and p.name not in SKIP and p.suffix != ".zip"
                   and (args.all or is_deliverable(p)))
    manifest = [f"# {folder.name}", "", f"Packaged {datetime.now():%Y-%m-%d %H:%M}", "", "| File | What it is |", "|---|---|"]
    for p in files:
        manifest.append(f"| {p.relative_to(folder)} | {describe(p)} |")
    manifest += ["", "Open the ATS report first: it lists which job-posting terms the resume covers and which honest gaps remain.", ""]

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, arcname=str(Path(folder.name) / p.relative_to(folder)))
        z.writestr(str(Path(folder.name) / "README.md"), "\n".join(manifest))
    print(f"Wrote {out} ({len(files)} files + README.md)")


if __name__ == "__main__":
    main()
