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
.venv/bin/python3 -m pip install -r requirements.txt
.venv/bin/python3 -m pip install .
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

## Command Style (Recommended)

Use the `webperf` command directly (from any directory) for day-to-day work.

Preferred day-to-day command:

```bash
webperf <command> [args]
```

Example:

```bash
webperf --db data/webperf.sqlite3 sync-sites --file sites.txt --apply
```

This avoids stale global `webperf` installs. If you see a prompt like
`Type YES to continue`, you are likely running an older installed command.

Direct module fallback (also no activation required):

```bash
.venv/bin/python3 -m webperf_app --db data/webperf.sqlite3 sync-sites --file sites.txt --apply
```

## After Code Changes

Use this default command after editing code:

```bash
.venv/bin/python3 -m pip install --no-build-isolation .
```

Then run commands normally:

```bash
webperf ...
```

Quick verify that `webperf` points to the updated command:

```bash
which webperf
webperf --help | grep render-report
```

Only if needed:
- If build tools are missing:

```bash
.venv/bin/python3 -m pip install setuptools wheel
```
- Avoid editable installs on this Python 3.14 setup (`pip install -e .`), since they can fail.

## Quick start

1. Initialize database:

```bash
webperf --db data/webperf.sqlite3 init-db
```

2. Import your current list:

```bash
webperf --db data/webperf.sqlite3 import-sites --file all_sites.txt
```

## Editing `sites.txt` (recommended workflow)

`sites.txt` is your source-of-truth list for active tracked sites.

Format rules:
- One site per line.
- You can use either full URLs (`https://example.com`) or bare domains (`example.com`).
- Blank lines are ignored.
- Lines starting with `#` are treated as comments and ignored.
- Trailing `/` is normalized automatically.

Example:

```txt
# Production sites
aprilbell.com
https://storycatcher.app

# Staging
speedtest.aprilbell.com
```

After editing `sites.txt`, sync it to the database:

1. Preview changes (dry run):

```bash
webperf --db data/webperf.sqlite3 sync-sites --file sites.txt
```

2. Apply changes:

```bash
webperf --db data/webperf.sqlite3 sync-sites --file sites.txt --apply
```

3. Skip confirmation prompt (optional):

```bash
webperf --db data/webperf.sqlite3 sync-sites --file sites.txt --apply --yes
```

What sync does:
- Adds new sites found in `sites.txt`
- Re-activates sites that exist but are inactive
- Deactivates active DB sites that are no longer in `sites.txt`

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
webperf --db data/webperf.sqlite3 run --all --strategy mobile --delay-seconds 10
```

Use `--limit` and `--offset` for gradual rollout:

```bash
webperf --db data/webperf.sqlite3 run --all --limit 5 --offset 15 --delay-seconds 10
```

## Notes

- First run for a site creates baseline metrics.
- Later runs show deltas vs previous runs.
- This MVP is CLI-first. A web dashboard can be added next using the same DB.
