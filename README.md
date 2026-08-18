# K1C Citation Monitor

Tracks external mentions of Kids First Chicago, links to kidsfirstchicago.org,
and mentions of K1C staff/board members — auto-scanned daily and published
as a browsable dashboard.

## How it works

1. **`scripts/01_scan.py`** — runs a set of Google Custom Search queries
   (org name, site backlinks, each staff/board member + K1C qualifier),
   dedupes against previously-seen URLs, and appends new hits to
   `data/citations.json`.
2. **`scripts/02_export_api.py`** — buckets each citation into
   `media / legislative / funder / partner / unclassified` using domain
   heuristics, writes `data/citations_classified.json`.
3. **`scripts/03_render_dashboard.py`** — renders a static, filterable HTML
   dashboard to `docs/index.html`.
4. GitHub Actions runs all three daily, commits the updated data files, and
   publishes `docs/` to GitHub Pages.

## One-time setup

### 1. Get a Google Custom Search API key + Search Engine ID

- Go to [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
  and create a new search engine. Under **Sites to search**, choose
  **"Search the entire web"** (not restricted to specific sites) — this is
  required for the org/backlink/person queries to work.
- Copy the **Search engine ID** (this is your `cx`).
- Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials),
  enable the **Custom Search API**, and create an **API key**.
- Free tier = 100 queries/day. This repo's default query list uses ~48/day.

### 2. Add GitHub secrets

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

- `GOOGLE_CSE_API_KEY` — the API key from above
- `GOOGLE_CSE_CX` — the search engine ID from above

### 3. Enable GitHub Pages

**Settings → Pages → Build and deployment → Source: GitHub Actions**

### 4. Push this repo and run it once manually

Go to the **Actions** tab → **K1C Citation Scan** → **Run workflow**, to
confirm it works before waiting for the daily cron.

## Editing the watch list

Edit `config/entities.json`:

- `org_queries` — the base org-name and backlink searches.
- `people` — every staff/board member currently being watched. Each entry
  is queried as `"{name}" ("Kids First Chicago" OR "K1C")`, which filters
  out most unrelated people who share a name.
- Directors Emeritus are excluded by default (common names → high noise).
  Add specific ones back into `people` if you want them tracked.

**Query budget:** every entry in `org_queries` + every entry in `people`
= 1 quota unit/day. Keep the total under ~90 to leave headroom on the
100/day free tier.

## Known limitations — read before relying on this

- **This is search-engine coverage, not a backlink index.** It will catch
  most news, blog, and public-web mentions that Google indexes within the
  7-day lookback window. It will **not** reliably catch: PDFs behind
  login walls, private Slack/email mentions, testimony transcripts not
  yet posted online, or very recent items Google hasn't indexed yet.
- **Auto-classification is a rough first pass.** The `unclassified` bucket
  will likely be the largest category at first — that's expected. Extend
  `MEDIA_DOMAINS`, `LEGISLATIVE_PATTERNS`, `FUNDER_PATTERNS`, and
  `PARTNER_DOMAINS` in `02_export_api.py` as you notice recurring sources
  landing in the wrong (or no) bucket.
- **Parent and ally advocacy actions are not covered by this tool.**
  Public comment, board-meeting testimony, and grassroots citation
  generally aren't searchable this way — that gap needs a self-report
  channel (a simple form), not a scraper. This tool is built to close the
  *media* and *hyperlink* gaps specifically; it deliberately does not
  attempt to solve the advocacy-tracking problem.
- **Common names will still produce some false positives** even with the
  K1C qualifier (e.g. another "Sam Schneider" quoted in an unrelated
  Chicago story that also happens to mention K1C elsewhere in the same
  page). Treat the dashboard as a triage queue, not a verified log.

## Local testing without waiting for the cron

```bash
export GOOGLE_CSE_API_KEY="..."
export GOOGLE_CSE_CX="..."
python scripts/01_scan.py
python scripts/02_export_api.py
python scripts/03_render_dashboard.py
open docs/index.html   # or just open the file in a browser
```
