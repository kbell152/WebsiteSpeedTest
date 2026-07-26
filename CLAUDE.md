# WebsiteSpeedTest (`webperf`)

Python CLI that audits website performance (Lighthouse-style via the Google PageSpeed
API), tracks run history in SQLite, and builds prioritized optimization TODOs across many
sites. See `README.md` for full usage; `AGENTS.md` holds agent-oriented notes.

## Setup
```
python3 -m venv .venv
.venv/bin/python3 -m pip install -r requirements.txt
.venv/bin/python3 -m pip install .
```
This installs a real `webperf` command. Optionally set `PAGESPEED_API_KEY` to avoid API
quota limits. (Editable installs `pip install -e .` can fail on some Python 3.14 setups.)

## Run
- `webperf ...` (after install), or `python3 -m webperf_app ...` from the repo.

## Layout
- `webperf_app/cli.py` — CLI entry (`webperf = webperf_app.cli:main`)
- `webperf_app/db.py` — SQLite history
- `webperf_app/pagespeed.py` — PageSpeed API client
- `webperf_app/analyzer.py` — opportunity/diagnostic → prioritized TODOs
- `pyproject.toml` — packaging (setuptools), `requires-python >=3.10`
- `sites.txt`, `test_sites.txt`, `all_sites.txt` — site lists
- `reports/`, `output/`, `data/`, `LH_Reports_For_Chat/` — generated artifacts

## Notes
- `.venv/` and `myenv/` are local envs (git-ignored); don't commit them.
