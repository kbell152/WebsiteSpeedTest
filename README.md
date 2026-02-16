# WebsiteSpeedTest App (MVP)

This project now includes a CLI app to audit website performance (Lighthouse-style via Google PageSpeed API), track run history, and prioritize optimization work across many sites.

## What it does

- Tracks a portfolio of websites in SQLite.
- Runs performance audits (`mobile` or `desktop`) site-by-site or in batch.
- Stores full run history so you can compare improvements/regressions over time.
- Builds prioritized TODOs from Lighthouse opportunities and diagnostics.
- Captures basic host/cache header signals (cache-control, CDN cache headers).
- Generates a Markdown issue brief you can paste into ChatGPT.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install .
```

(Optional) set an API key to avoid PageSpeed API quota issues:

```bash
export PAGESPEED_API_KEY="your_key_here"
```

This installs a real `webperf` command (no `.zshrc` alias/function needed).
For contributors who want live code edits without reinstalling, `pip install -e .`
is optional, but on some Python 3.14 environments editable installs can fail.

If you want `webperf` available globally without manually activating a venv, use:

```bash
pipx install .
```

## Quick start

1. Initialize database:

```bash
webperf --db data/webperf.sqlite3 init-db
```

2. Import your current list:

```bash
webperf --db data/webperf.sqlite3 import-sites --file all_sites.txt
```

3. Run one site first:

```bash
webperf --db data/webperf.sqlite3 run --site https://aprilbell.com --strategy mobile
```

Add a change note to track what you modified before the run:

```bash
webperf --db data/webperf.sqlite3 run --site https://aprilbell.com --strategy mobile --note "Enabled LiteSpeed cache + compressed hero image"
```

4. View prioritized TODOs:

```bash
webperf --db data/webperf.sqlite3 todo --site https://aprilbell.com --strategy mobile
```

5. View recent trend:

```bash
webperf --db data/webperf.sqlite3 trend --site https://aprilbell.com --strategy mobile
```

6. Generate issue brief for ChatGPT:

```bash
webperf --db data/webperf.sqlite3 issue-brief --site https://aprilbell.com --output reports/aprilbell-brief.md
```

## Batch mode (when ready)

```bash
webperf --db data/webperf.sqlite3 run --all --strategy mobile
```

Use `--limit` for gradual rollout:

```bash
webperf --db data/webperf.sqlite3 run --all --limit 5
```

## Notes

- First run for a site creates baseline metrics.
- Later runs show deltas vs previous runs.
- This MVP is CLI-first. A web dashboard can be added next using the same DB.
