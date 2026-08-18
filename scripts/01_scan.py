#!/usr/bin/env python3
"""
01_scan.py

Queries Google Programmable Search (Custom Search JSON API) for mentions of
Kids First Chicago, its site, and its staff/board members. Appends any new
(not-previously-seen) results to data/citations.json.

Requires environment variables:
  GOOGLE_CSE_API_KEY  - Custom Search API key
  GOOGLE_CSE_CX       - Custom Search Engine ID (must be configured to search
                         "the entire web", not a restricted site list)

Usage:
  python scripts/01_scan.py
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config", "entities.json")
CITATIONS_PATH = os.path.join(ROOT, "data", "citations.json")
SEEN_PATH = os.path.join(ROOT, "data", "seen_urls.json")

CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"

# How far back each run looks. d7 = last 7 days. Overlapping window + URL
# dedupe means a daily cron won't miss things even if indexing lags a day or two.
DATE_RESTRICT = "d7"
RESULTS_PER_QUERY = 10  # 1 page = 1 quota unit per query


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_queries(config):
    """Returns a flat list of {id, query, category, entity} dicts."""
    queries = []

    for oq in config["org_queries"]:
        queries.append({
            "id": oq["id"],
            "query": oq["query"],
            "category": oq["category"],
            "entity": "Kids First Chicago (org)",
        })

    own_domain = config["own_domain"]

    for org in config.get("partner_orgs", []):
        name = org["name"]
        domain = org["domain"]
        slug = name.lower().replace(" ", "_")

        # General mention: catches news-style pages, blog posts, staff bios, etc.
        queries.append({
            "id": f"partner_general_{slug}",
            "query": f'"{name}" ("Kids First Chicago" OR "K1C") -site:{own_domain}',
            "category": "partner_org_mention",
            "entity": name,
        })

        # Site-restricted: catches PDFs, reports, and pages a general search
        # ranks poorly (e.g. a footnote in a 40-page report).
        queries.append({
            "id": f"partner_site_{slug}",
            "query": f'site:{domain} ("Kids First Chicago" OR "K1C")',
            "category": "partner_org_report",
            "entity": name,
        })

    for person in config["people"]:
        name = person["name"]
        q = f'"{name}" ("Kids First Chicago" OR "K1C") -site:{own_domain}'
        queries.append({
            "id": f"person_{name.lower().replace(' ', '_')}",
            "query": q,
            "category": f"person_mention_{person['group']}",
            "entity": name,
        })

    return queries


def run_query(api_key, cx, query_text):
    params = {
        "key": api_key,
        "cx": cx,
        "q": query_text,
        "num": RESULTS_PER_QUERY,
        "dateRestrict": DATE_RESTRICT,
    }
    url = f"{CSE_ENDPOINT}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "k1c-citation-monitor/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        print(f"  ERROR {e.code} for query [{query_text}]: {detail[:300]}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  ERROR for query [{query_text}]: {e}", file=sys.stderr)
        return []

    return body.get("items", [])


def main():
    api_key = os.environ.get("GOOGLE_CSE_API_KEY")
    cx = os.environ.get("GOOGLE_CSE_CX")
    if not api_key or not cx:
        print("Missing GOOGLE_CSE_API_KEY or GOOGLE_CSE_CX environment variables.", file=sys.stderr)
        sys.exit(1)

    config = load_json(CONFIG_PATH, None)
    if config is None:
        print(f"Could not find config at {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    citations = load_json(CITATIONS_PATH, [])
    seen_urls = set(load_json(SEEN_PATH, []))

    queries = build_queries(config)
    print(f"Running {len(queries)} queries (quota units)...")

    new_count = 0
    scanned_at = datetime.now(timezone.utc).isoformat()

    for i, q in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] {q['entity']} :: {q['query'][:80]}")
        items = run_query(api_key, cx, q["query"])

        for item in items:
            link = item.get("link", "")
            if not link or link in seen_urls:
                continue

            citations.append({
                "url": link,
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "display_link": item.get("displayLink", ""),
                "entity": q["entity"],
                "category": q["category"],
                "query_id": q["id"],
                "found_at": scanned_at,
            })
            seen_urls.add(link)
            new_count += 1

        # Be polite to the API even though quota, not rate, is the real limiter.
        time.sleep(0.2)

    save_json(CITATIONS_PATH, citations)
    save_json(SEEN_PATH, sorted(seen_urls))

    print(f"\nDone. {new_count} new citation(s) found. Total on file: {len(citations)}.")


if __name__ == "__main__":
    main()
