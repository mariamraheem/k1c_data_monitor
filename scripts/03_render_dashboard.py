#!/usr/bin/env python3
"""
03_render_dashboard.py

Renders data/citations_classified.json into a static HTML dashboard at
docs/index.html, meant to be served via GitHub Pages.

Usage:
  python scripts/03_render_dashboard.py
"""

import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLASSIFIED_PATH = os.path.join(ROOT, "data", "citations_classified.json")
OUT_PATH = os.path.join(ROOT, "docs", "index.html")

BUCKET_LABELS = {
    "media": "Media coverage",
    "legislative": "Legislative record",
    "funder": "Funder / grant",
    "partner": "Partner org",
    "partner_org_mention": "Partner org mention",
    "partner_org_report": "Partner org report/PDF",
    "advocacy": "Parent & ally advocacy",
    "unclassified": "Needs manual review",
    "org_mention": "Org mention",
    "hyperlink_mention": "Site link mention",
}


def load_classified():
    if not os.path.exists(CLASSIFIED_PATH):
        return []
    with open(CLASSIFIED_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def render_card(c):
    bucket = c.get("source_bucket", "unclassified")
    label = BUCKET_LABELS.get(bucket, bucket)
    found_at = c.get("found_at", "")[:10]
    title = c.get("title") or c.get("url")
    snippet = c.get("snippet", "")
    entity = c.get("entity", "")
    display_link = c.get("display_link", "")
    url = c.get("url", "#")

    return f"""
    <article class="card" data-bucket="{bucket}" data-entity="{entity}">
      <div class="card-meta">
        <span class="badge badge-{bucket}">{label}</span>
        <span class="date">{found_at}</span>
      </div>
      <h3><a href="{url}" target="_blank" rel="noopener">{title}</a></h3>
      <p class="snippet">{snippet}</p>
      <div class="card-footer">
        <span class="entity">Matched: {entity}</span>
        <span class="domain">{display_link}</span>
      </div>
    </article>
    """


def main():
    citations = load_classified()

    buckets_present = sorted(set(c.get("source_bucket", "unclassified") for c in citations))
    entities_present = sorted(set(c.get("entity", "") for c in citations))

    filter_buttons = "".join(
        f'<button class="filter-btn" data-filter="{b}">{BUCKET_LABELS.get(b, b)} '
        f'({sum(1 for c in citations if c.get("source_bucket") == b)})</button>'
        for b in buckets_present
    )

    entity_options = "".join(
        f'<option value="{e}">{e}</option>' for e in entities_present
    )

    cards_html = "\n".join(render_card(c) for c in citations)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>K1C Citation Monitor</title>
<style>
  :root {{
    --navy: #0b2e4f;
    --teal: #1c7d84;
    --gold: #d9a441;
    --bg: #f6f7f9;
    --card-bg: #ffffff;
    --border: #e2e5ea;
    --text: #1f2933;
    --muted: #6b7684;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
  }}
  header {{
    background: var(--navy);
    color: white;
    padding: 24px 32px;
  }}
  header h1 {{ margin: 0 0 4px 0; font-size: 22px; }}
  header p {{ margin: 0; color: #cbd8e3; font-size: 13px; }}
  .controls {{
    max-width: 1000px;
    margin: 20px auto 0 auto;
    padding: 0 16px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }}
  .filter-btn {{
    border: 1px solid var(--border);
    background: white;
    border-radius: 999px;
    padding: 6px 14px;
    font-size: 13px;
    cursor: pointer;
    color: var(--text);
  }}
  .filter-btn.active {{
    background: var(--teal);
    color: white;
    border-color: var(--teal);
  }}
  select, input[type=text] {{
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
  }}
  main {{
    max-width: 1000px;
    margin: 20px auto 60px auto;
    padding: 0 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
  }}
  .card-meta {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }}
  .badge {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    padding: 3px 9px;
    border-radius: 999px;
    background: #eef1f4;
    color: var(--muted);
  }}
  .badge-media {{ background: #fdecc8; color: #7a4e00; }}
  .badge-legislative {{ background: #dbe9f7; color: #114a7a; }}
  .badge-funder {{ background: #e3f0e1; color: #2b6e2f; }}
  .badge-partner {{ background: #efe3f7; color: #5a2b8c; }}
  .badge-unclassified {{ background: #f7dede; color: #a13030; }}
  .date {{ font-size: 12px; color: var(--muted); }}
  .card h3 {{ margin: 4px 0 6px 0; font-size: 16px; }}
  .card h3 a {{ color: var(--navy); text-decoration: none; }}
  .card h3 a:hover {{ text-decoration: underline; }}
  .snippet {{ margin: 0 0 8px 0; font-size: 14px; color: #3d4753; line-height: 1.4; }}
  .card-footer {{
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: var(--muted);
  }}
  .empty {{
    text-align: center;
    color: var(--muted);
    padding: 40px 0;
  }}
  footer {{
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    padding: 20px 0 40px 0;
  }}
</style>
</head>
<body>

<header>
  <h1>Kids First Chicago — Citation Monitor</h1>
  <p>Tracking external mentions of K1C, kidsfirstchicago.org, and staff/board members. Generated {generated_at}.</p>
</header>

<div class="controls">
  <button class="filter-btn active" data-filter="all">All ({len(citations)})</button>
  {filter_buttons}
  <select id="entityFilter">
    <option value="">All entities</option>
    {entity_options}
  </select>
  <input type="text" id="searchBox" placeholder="Search title/snippet...">
</div>

<main id="cardContainer">
{cards_html if citations else '<div class="empty">No citations recorded yet. Run 01_scan.py to start populating this dashboard.</div>'}
</main>

<footer>K1C Citation Monitor · auto-generated, not a substitute for human review of "unclassified" items</footer>

<script>
  const buttons = document.querySelectorAll('.filter-btn');
  const entitySelect = document.getElementById('entityFilter');
  const searchBox = document.getElementById('searchBox');
  const cards = document.querySelectorAll('.card');
  let activeBucket = 'all';

  function applyFilters() {{
    const entityVal = entitySelect.value;
    const searchVal = searchBox.value.toLowerCase();
    cards.forEach(card => {{
      const bucketMatch = activeBucket === 'all' || card.dataset.bucket === activeBucket;
      const entityMatch = !entityVal || card.dataset.entity === entityVal;
      const textMatch = !searchVal || card.innerText.toLowerCase().includes(searchVal);
      card.style.display = (bucketMatch && entityMatch && textMatch) ? '' : 'none';
    }});
  }}

  buttons.forEach(btn => {{
    btn.addEventListener('click', () => {{
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeBucket = btn.dataset.filter;
      applyFilters();
    }});
  }});

  entitySelect.addEventListener('change', applyFilters);
  searchBox.addEventListener('input', applyFilters);
</script>

</body>
</html>
"""

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard written to {OUT_PATH} ({len(citations)} citations rendered).")


if __name__ == "__main__":
    main()
