#!/usr/bin/env python3
"""
02_export_api.py

Reads data/citations.json (raw scan results) and applies domain-based
heuristics to bucket each into one of the source categories from the
citation-tracking framework:
  media | legislative | funder | partner | advocacy | unclassified

This is intentionally coarse. It exists to pre-sort the easy cases so a
human only has to triage the "unclassified" pile, not all of them.

Usage:
  python scripts/02_export_api.py
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CITATIONS_PATH = os.path.join(ROOT, "data", "citations.json")
CLASSIFIED_PATH = os.path.join(ROOT, "data", "citations_classified.json")

# Known Chicago / education press domains. Extend this list as you notice gaps.
MEDIA_DOMAINS = [
    "chicagotribune.com", "suntimes.com", "wbez.org", "chalkbeat.org",
    "crainschicago.com", "chicagobusiness.com", "blockclubchicago.org",
    "illinoisanswers.org", "injusticewatch.org", "wttw.com", "npr.org",
    "axios.com", "politico.com", "usnews.com", "edweek.org",
    "the74million.org", "hechingerreport.org", "wgntv.com", "nbcchicago.com",
    "abc7chicago.com", "cbsnews.com/chicago", "dailyherald.com",
]

# Governmental / legislative record domains and URL patterns.
LEGISLATIVE_PATTERNS = [
    r"\.gov(/|$)", r"ilga\.gov", r"chicago\.gov", r"cps\.edu/board",
    r"legistar", r"chicityclerk", r"testimony", r"committee-hearing",
]

# Funder / philanthropy domain keywords.
FUNDER_PATTERNS = [
    r"foundation", r"philanthropy", r"grantmakers", r"\.trust\b",
    r"macfound\.org", r"mccormickfoundation\.org",
]

# Known partner / coalition orgs (extend as you identify recurring partners).
PARTNER_DOMAINS = [
    "advanceillinois.org", "raiseyourhandillinois.org", "uchicago.edu",
    "consortium.uchicago.edu", "urban.org", "cgcs.org",
    "illinoisreportcard.com",
]


def classify(display_link, url, title, snippet, category=""):
    # Partner-org queries are already targeted at a known partner — trust
    # the query category over domain-sniffing, since a partner's own
    # report PDF might not match any keyword pattern below.
    if category in ("partner_org_mention", "partner_org_report"):
        return "partner"

    text = f"{display_link} {url} {title} {snippet}".lower()

    for d in MEDIA_DOMAINS:
        if d in text:
            return "media"

    for pattern in LEGISLATIVE_PATTERNS:
        if re.search(pattern, text):
            return "legislative"

    for pattern in FUNDER_PATTERNS:
        if re.search(pattern, text):
            return "funder"

    for d in PARTNER_DOMAINS:
        if d in text:
            return "partner"

    return "unclassified"


def main():
    if not os.path.exists(CITATIONS_PATH):
        print("No citations.json found yet — run 01_scan.py first.")
        return

    with open(CITATIONS_PATH, "r", encoding="utf-8") as f:
        citations = json.load(f)

    classified = []
    for c in citations:
        bucket = classify(
            c.get("display_link", ""),
            c.get("url", ""),
            c.get("title", ""),
            c.get("snippet", ""),
            c.get("category", ""),
        )
        c = dict(c)  # copy
        c["source_bucket"] = bucket
        classified.append(c)

    # Most recent first
    classified.sort(key=lambda c: c.get("found_at", ""), reverse=True)

    os.makedirs(os.path.dirname(CLASSIFIED_PATH), exist_ok=True)
    with open(CLASSIFIED_PATH, "w", encoding="utf-8") as f:
        json.dump(classified, f, indent=2, ensure_ascii=False)

    counts = {}
    for c in classified:
        counts[c["source_bucket"]] = counts.get(c["source_bucket"], 0) + 1

    print(f"Classified {len(classified)} citations:")
    for bucket, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {bucket}: {n}")


if __name__ == "__main__":
    main()
