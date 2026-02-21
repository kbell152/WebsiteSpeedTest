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
python3 -m pip install -r requirements.txt
python3 -m pip install .
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

On Python 3.14 setups like this one, use the module form to guarantee you are
running the latest local code:

```bash
python3 -m webperf_app <command> [args]
```

Example:

```bash
python3 -m webperf_app --db data/webperf.sqlite3 sync-sites --file sites.txt --apply
```

This avoids stale global `webperf` installs. If you see a prompt like
`Type YES to continue`, you are likely running an older installed command.

If you prefer a short command in this repo, use the local wrapper:

```bash
./webperf --db data/webperf.sqlite3 sync-sites --file sites.txt --apply
```

## After Code Changes

If you update Python source files, run a quick compile check:

```bash
python3 -m py_compile webperf_app/cli.py
```

For day-to-day development, no reinstall is required if you run commands as:

```bash
python3 -m webperf_app ...
```

If you want to use the short `webperf` command from the venv, reinstall after
changes so it points at current code:

```bash
python3 -m pip install --no-build-isolation .
```

If your environment is missing build tools, install them once:

```bash
python3 -m pip install setuptools wheel
```

If your install is non-editable (`python3 -m pip install .`), reinstall so the `webperf`
command picks up changes:

```bash
python3 -m pip install --no-build-isolation .
```

Editable installs (`python3 -m pip install -e .`) may fail on some Python 3.14
setups because hidden editable `.pth` files can be skipped.

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
