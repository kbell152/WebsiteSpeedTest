# AGENTS.md

## Purpose
This repo is used to audit and troubleshoot website performance with the `webperf` CLI.

## Working Rules
- Prefer the `webperf` CLI for day-to-day operations.
- Treat `LH_Reports_For_Chat/latest-test.json` as the source of truth for the latest single-site troubleshooting session.
- The default troubleshooting workflow assumes combined mobile + desktop analysis with `--strategy both`.
- Read `README.md` for setup and restart workflow details.
- If a site-specific handoff file exists in `reports/`, read it before starting deeper analysis.

## Preferred Files For Troubleshooting
- Primary: `LH_Reports_For_Chat/latest-test.json`
- Secondary: `LH_Reports_For_Chat/latest-test.md`
- Discussion brief: `reports/latest-test-issue-brief.md`
- Session handoff: `reports/*-handoff.md`

## Expected Troubleshooting Approach
When helping with a site performance issue:

1. Read the latest handoff file if present.
2. Read `LH_Reports_For_Chat/latest-test.json`.
3. Separate findings into:
   - shared mobile/desktop issues
   - mobile-only issues
   - desktop-only issues
4. Recommend exact first fixes with the highest likely impact.
5. Recommend what to re-test after each fix.

## CLI Expectations
- `webperf run` defaults to `--strategy both`
- `webperf todo` defaults to `--strategy both`
- `webperf trend` defaults to `--strategy both`
- `webperf issue-brief` defaults to `--strategy both`

## Conversation Restart Workflow
For a fresh conversation after stopping work:

1. Keep these files current:
   - `LH_Reports_For_Chat/latest-test.json`
   - `LH_Reports_For_Chat/latest-test.md`
   - `reports/latest-test-issue-brief.md`
2. Create or update a site-specific handoff file in `reports/`
3. Start the next conversation by referencing:
   - the handoff file
   - `LH_Reports_For_Chat/latest-test.json`

Recommended restart prompt:

```text
Please start with `reports/<site>-handoff.md` and treat `LH_Reports_For_Chat/latest-test.json` as the source of truth.
```

## Packaging Note
- If CLI behavior appears stale, verify the repo-local `webperf` command is using the current workspace code.
- Prefer the repo-local environment and documented install commands in `README.md`.
