import argparse
import csv
import html
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from . import analyzer, db, pagespeed


def fmt_ms(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f} ms"


def _metrics_from_row(row: Any) -> Dict[str, Any]:
    return {
        "performance_score": row["performance_score"],
        "fcp_ms": row["fcp_ms"],
        "lcp_ms": row["lcp_ms"],
        "tbt_ms": row["tbt_ms"],
        "cls": row["cls"],
        "speed_index_ms": row["speed_index_ms"],
        "ttfb_ms": row["ttfb_ms"],
    }


def _fmt_local_timestamp(value: Optional[str]) -> str:
    if not value:
        return "n/a"
    try:
        dt = datetime.fromisoformat(value)
        local_dt = dt.astimezone()
        return local_dt.strftime("%Y-%m-%d %I:%M:%S %p %Z")
    except Exception:
        return value


def _summary_domain(url: str) -> str:
    return url.replace("https://", "").rstrip("/")


def _fmt_csv_num(value: Optional[float], *, decimals: int = 0) -> str:
    if value is None:
        return ""
    if decimals <= 0:
        return f"{int(round(value)):,}"
    return f"{value:,.{decimals}f}"


def _write_bulk_summary_csv(
    output_path: Path,
    *,
    batch_summary: list[dict[str, Any]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "Site",
                "Lighthouse Performance score",
                "First Content Paint: when first visible content appears",
                "Largest Content Paint: when the largest visible element finishes rendering",
                "Total Blocking Time: time JavaScript blocked the main thread",
                "Time To First Byte: server response latency before content starts",
                "Warnings",
                "Errors",
                "ToDos",
            ]
        )
        for item in batch_summary:
            metrics = item["metrics"]
            writer.writerow(
                [
                    _summary_domain(item["url"]),
                    _fmt_csv_num(metrics.get("performance_score"), decimals=0),
                    _fmt_csv_num(metrics.get("fcp_ms"), decimals=0),
                    _fmt_csv_num(metrics.get("lcp_ms"), decimals=0),
                    _fmt_csv_num(metrics.get("tbt_ms"), decimals=0),
                    _fmt_csv_num(metrics.get("ttfb_ms"), decimals=0),
                    item["warnings"],
                    item["errors"],
                    item["todos"],
                ]
            )
        writer.writerow([])
        writer.writerow(["Score = Lighthouse Performance score"])
        writer.writerow(["FCP = First Content Paint: when first visible content appears"])
        writer.writerow(
            [
                "LCP = Largest Content Paint: when the largest visible element finishes rendering"
            ]
        )
        writer.writerow(
            ["TBT = Total Blocking Time: time JavaScript blocked the main thread"]
        )
        writer.writerow(
            ["TTFB = Time To First Byte: server response latency before content starts"]
        )
        writer.writerow(["Note: 1000 ms = 1 second"])


def _parse_csv_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _write_bulk_summary_html(
    output_path: Path,
    *,
    batch_summary: list[dict[str, Any]],
    strategy: str,
    generated_at: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    strategy_label = "Mobile" if strategy == "mobile" else "Desktop"
    rows_html: list[str] = []
    for item in batch_summary:
        metrics = item["metrics"]
        domain = _summary_domain(item["url"])
        score = _parse_csv_float(metrics.get("performance_score"))
        fcp = _parse_csv_float(metrics.get("fcp_ms"))
        lcp = _parse_csv_float(metrics.get("lcp_ms"))
        tbt = _parse_csv_float(metrics.get("tbt_ms"))
        ttfb = _parse_csv_float(metrics.get("ttfb_ms"))
        warnings = int(item.get("warnings", 0))
        errors = int(item.get("errors", 0))
        todos = int(item.get("todos", 0))
        rows_html.append(
            "<tr>"
            f"<td><a href='{html.escape(item['url'])}' target='_blank' rel='noopener noreferrer'>{html.escape(domain)} <span class='ext-icon' aria-hidden='true'>&#8599;</span></a></td>"
            f"<td data-sort='{'' if score is None else score}'>{'' if score is None else f'{score:.0f}'}</td>"
            f"<td data-sort='{'' if fcp is None else fcp}'>{_fmt_csv_num(fcp, decimals=0)}</td>"
            f"<td data-sort='{'' if lcp is None else lcp}'>{_fmt_csv_num(lcp, decimals=0)}</td>"
            f"<td data-sort='{'' if tbt is None else tbt}'>{_fmt_csv_num(tbt, decimals=0)}</td>"
            f"<td data-sort='{'' if ttfb is None else ttfb}'>{_fmt_csv_num(ttfb, decimals=0)}</td>"
            f"<td data-sort='{warnings}'>{warnings}</td>"
            f"<td data-sort='{errors}'>{errors}</td>"
            f"<td data-sort='{todos}'>{todos}</td>"
            "</tr>"
        )

    html_body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{strategy_label} Sites Test Report</title>
  <style>
    :root {{
      --bg: #f6f7fb;
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --line: #e5e7eb;
      --accent-soft: #ccfbf1;
    }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      color: var(--text);
      background: radial-gradient(circle at 10% 0%, #e6fffa, transparent 40%), var(--bg);
    }}
    .wrap {{
      max-width: 1200px;
      margin: 32px auto;
      padding: 0 16px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      overflow: hidden;
    }}
    .head {{
      padding: 20px 24px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(120deg, #f0fdfa, #f8fafc);
    }}
    .head h1 {{
      margin: 0 0 6px 0;
      font-size: 1.25rem;
    }}
    .head p {{
      margin: 0;
      color: var(--muted);
      font-size: 0.95rem;
    }}
    .table-wrap {{
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 980px;
    }}
    thead th {{
      background: #f9fafb;
      position: sticky;
      top: 0;
      z-index: 1;
      text-align: left;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }}
    thead th.sorting {{
      background: var(--accent-soft);
      color: #134e4a;
    }}
    tbody td {{
      padding: 11px 14px;
      border-bottom: 1px solid var(--line);
      white-space: nowrap;
    }}
    tbody tr:hover {{
      background: #f8fafc;
    }}
    .note {{
      padding: 14px 24px 20px;
      color: var(--muted);
      font-size: 0.9rem;
      line-height: 1.5;
    }}
    .note strong {{
      color: #374151;
    }}
    .note a {{
      color: #0f766e;
      text-decoration: none;
      border-bottom: 1px solid #99f6e4;
    }}
    tbody td a {{
      color: #0f766e;
      text-decoration: none;
      border-bottom: 1px solid #99f6e4;
    }}
    tbody td a:hover {{
      text-decoration: underline;
    }}
    .ext-icon {{
      font-size: 0.85em;
    }}
    .note a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="head">
        <h1>{strategy_label} Sites Test Report</h1>
        <p>Generated {html.escape(generated_at)}. Click any header to sort (high to low first).</p>
      </div>
      <div class="table-wrap">
        <table id="report">
          <thead>
            <tr>
              <th data-type="text">Site</th>
              <th data-type="number">Score</th>
              <th data-type="number">FCP (ms)</th>
              <th data-type="number">LCP (ms)</th>
              <th data-type="number">TBT (ms)</th>
              <th data-type="number">TTFB (ms)</th>
              <th data-type="number">Warnings</th>
              <th data-type="number">Errors</th>
              <th data-type="number">ToDos</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
      <div class="note">
        <strong>Metric key:</strong>
        <a href="https://developer.chrome.com/docs/lighthouse/performance/performance-scoring" target="_blank" rel="noopener noreferrer">Score</a>,
        <a href="https://developer.chrome.com/docs/lighthouse/performance/first-contentful-paint" target="_blank" rel="noopener noreferrer">FCP</a>,
        <a href="https://developer.chrome.com/docs/lighthouse/performance/speed-index" target="_blank" rel="noopener noreferrer">Speed Index</a>,
        <a href="https://developer.chrome.com/docs/lighthouse/performance/lighthouse-total-blocking-time" target="_blank" rel="noopener noreferrer">TBT</a>,
        <a href="https://developer.chrome.com/docs/lighthouse/performance/lighthouse-largest-contentful-paint" target="_blank" rel="noopener noreferrer">LCP</a>.
        1000 ms = 1 second.
      </div>
    </div>
  </div>
  <script>
    (() => {{
      const table = document.getElementById('report');
      const headers = Array.from(table.querySelectorAll('thead th'));
      const tbody = table.querySelector('tbody');
      let sortState = {{ col: -1, desc: true }};

      const getCellValue = (row, idx, type) => {{
        const cell = row.children[idx];
        const raw = cell?.dataset?.sort ?? cell?.textContent ?? '';
        if (type === 'number') {{
          const num = Number(raw);
          return Number.isFinite(num) ? num : Number.NEGATIVE_INFINITY;
        }}
        return String(raw).toLowerCase();
      }};

      const sortBy = (idx, type) => {{
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const desc = sortState.col === idx ? !sortState.desc : true;
        rows.sort((a, b) => {{
          const va = getCellValue(a, idx, type);
          const vb = getCellValue(b, idx, type);
          if (va < vb) return desc ? 1 : -1;
          if (va > vb) return desc ? -1 : 1;
          return 0;
        }});
        rows.forEach((row) => tbody.appendChild(row));
        sortState = {{ col: idx, desc }};
        headers.forEach((h, i) => {{
          h.classList.toggle('sorting', i === idx);
          const marker = i === idx ? (desc ? ' ▼' : ' ▲') : '';
          h.textContent = h.textContent.replace(/ [▲▼]$/, '') + marker;
        }});
      }};

      headers.forEach((th, idx) => {{
        th.addEventListener('click', () => sortBy(idx, th.dataset.type || 'text'));
      }});
    }})();
  </script>
</body>
</html>
"""
    output_path.write_text(html_body, encoding="utf-8")


def _read_bulk_summary_csv(csv_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with csv_path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            site = (row.get("Site") or "").strip()
            if not site:
                break
            # Footer notes are written in the "Site" column with empty metric columns.
            # Stop at the first such row so notes are not treated as sortable data rows.
            if site.startswith(("Score =", "FCP =", "LCP =", "TBT =", "TTFB =", "Note:")):
                break
            has_metrics = any(
                (row.get(col) or "").strip()
                for col in (
                    "Lighthouse Performance score",
                    "First Content Paint: when first visible content appears",
                    "Largest Content Paint: when the largest visible element finishes rendering",
                    "Total Blocking Time: time JavaScript blocked the main thread",
                    "Time To First Byte: server response latency before content starts",
                    "Warnings",
                    "Errors",
                    "ToDos",
                )
            )
            if not has_metrics:
                break
            rows.append(
                {
                    "url": f"https://{site}",
                    "metrics": {
                        "performance_score": _parse_csv_float(
                            row.get("Lighthouse Performance score")
                        ),
                        "fcp_ms": _parse_csv_float(
                            row.get(
                                "First Content Paint: when first visible content appears"
                            )
                        ),
                        "lcp_ms": _parse_csv_float(
                            row.get(
                                "Largest Content Paint: when the largest visible element finishes rendering"
                            )
                        ),
                        "tbt_ms": _parse_csv_float(
                            row.get(
                                "Total Blocking Time: time JavaScript blocked the main thread"
                            )
                        ),
                        "ttfb_ms": _parse_csv_float(
                            row.get(
                                "Time To First Byte: server response latency before content starts"
                            )
                        ),
                    },
                    "warnings": int(_parse_csv_float(row.get("Warnings")) or 0),
                    "errors": int(_parse_csv_float(row.get("Errors")) or 0),
                    "todos": int(_parse_csv_float(row.get("ToDos")) or 0),
                }
            )
    return rows


def _print_trend_lines(runs: Iterable[Any]) -> None:
    for run in runs:
        print(
            f"- Run at {_fmt_local_timestamp(run['fetched_at'])} "
            f"score={run['performance_score']} lcp={run['lcp_ms']} tbt={run['tbt_ms']} ttfb={run['ttfb_ms']}"
        )


def _print_trend_notes(runs: Iterable[Any]) -> None:
    print("")
    print("Notes for displayed runs:")
    for run in runs:
        note = run["run_note"] if run["run_note"] else "(none)"
        print(f'- Run note="{note}"')


def _latest_run_with_site(conn: Any, strategy: str) -> Optional[Any]:
    return conn.execute(
        """
        SELECT ar.*, s.url AS site_url
        FROM audit_runs ar
        JOIN sites s ON s.id = ar.site_id
        WHERE ar.strategy = ?
        ORDER BY ar.fetched_at DESC
        LIMIT 1
        """,
        (strategy,),
    ).fetchone()


def cmd_init_db(args: argparse.Namespace) -> None:
    conn = db.connect(Path(args.db))
    db.init_db(conn)
    print(f"Initialized database: {args.db}")


def cmd_import_sites(args: argparse.Namespace) -> None:
    conn = db.connect(Path(args.db))
    db.init_db(conn)
    lines = Path(args.file).read_text(encoding="utf-8").splitlines()
    created = db.import_sites(conn, lines)
    total = len(db.list_sites(conn, active_only=False))
    print(f"Imported {created} new site(s). Total tracked sites: {total}")


def cmd_add_site(args: argparse.Namespace) -> None:
    conn = db.connect(Path(args.db))
    db.init_db(conn)
    site_id = db.upsert_site(conn, args.url, label=args.label)
    print(f"Site ready (id={site_id}): {db.normalize_url(args.url)}")


def cmd_list_sites(args: argparse.Namespace) -> None:
    """
    List tracked sites from the SQLite database.

    Why this command exists:
    - It is a quick inventory view so you can confirm which sites are currently
      in the tracker before running audits.
    - It also shows active vs inactive state, which matters because other
      commands (for example `run --all`) only target active sites.

    Behavior:
    - Connects to the DB path from `args.db`.
    - Ensures the schema exists via `db.init_db(conn)` so the command can run
      safely even on a fresh database file.
    - Reads rows with `db.list_sites(...)`:
      - default: only active sites (`--all` not provided)
      - with `--all`: active + inactive sites
    - Prints each site on one line using a fixed-width domain column:
      `<domain>  <status>`
    - Prints a final `Total: N` summary.

    Arg expectations:
    - `args.db`: database file path (set by the top-level `--db` option)
    - `args.all`: boolean from `list-sites --all`; when True, include inactive
      sites in results
    """
    conn = db.connect(Path(args.db))
    db.init_db(conn)

    # `active_only=True` is the default list behavior.
    # Passing `--all` flips this to include inactive rows too.
    rows = db.list_sites(conn, active_only=not args.all)

    for row in rows:
        # Keep output compact by showing host-like domain text, not full URL.
        domain = row["url"].replace("https://", "").rstrip("/")
        # `sites.active` is stored as 1/0 in SQLite; map to readable text.
        status = "active" if row["active"] else "inactive"

        # Left-align domain in a 40-char column for scan-friendly CLI output.
        print(f"{domain:<40}  {status}")

    print(f"Total: {len(rows)}")


def _iter_target_sites(
    conn: Any,
    *,
    site: Optional[str],
    run_all: bool,
    limit: Optional[int],
    offset: int = 0,
) -> Iterable[Any]:
    """
    Yield the site rows that `cmd_run` should audit.

    Selection rules:
    - If `site` is provided, yield exactly that site (creating it if missing).
    - Else if `run_all` is True, yield all active sites, optionally capped by
      `limit`.
    - Else raise a ValueError because `run` requires one target mode.
    """
    if site:
        # Ad-hoc runs should work even when the site is not pre-registered.
        yield db.get_or_create_site(conn, site)
        return
    if run_all:
        # Bulk mode intentionally skips inactive sites.
        rows = db.list_sites(conn, active_only=True)
        if offset > 0:
            rows = rows[offset:]
        if limit:
            # Keep processing deterministic by taking the first N sorted rows.
            rows = rows[:limit]
        for row in rows:
            yield row
        return
    raise ValueError("Provide --site <url> or --all")


def cmd_run(args: argparse.Namespace) -> None:
    """
    Run PageSpeed/Lighthouse audits and store results in the database.

    Why this command exists:
    - It is the data-collection command for the whole app.
    - Other commands (`todo`, `trend`, `issue-brief`) read the runs created here.

    Behavior summary:
    - Connects to DB and ensures schema exists.
    - Resolves API key from `--api-key` first, then `PAGESPEED_API_KEY`.
    - Selects target sites from either:
      - `--site <url>`: one site (auto-created if missing), or
      - `--all`: all active sites, optionally capped by `--limit`.
    - For each target site:
      - fetches PageSpeed payload
      - snapshots host/cache headers
      - extracts metrics + LCP/cache context
      - builds prioritized TODO items
      - inserts one `audit_runs` row + replaces `run_todos`
      - prints metrics, warning/error counts, and TODO count
      - compares vs previous run (same site + strategy) and prints deltas
      - prints recent trend lines + attached run notes
    - Continues site-by-site on errors (prints `FAILED <url>: ...`).

    Arg expectations:
    - `args.db`: SQLite DB path
    - `args.site` / `args.all`: mutually exclusive target selection
    - `args.strategy`: `mobile` or `desktop`
    - `args.limit`: max sites when using `--all`
    - `args.offset`: starting index in active-site list when using `--all`
    - `args.trend_limit`: recent runs to print after each audit (fallback 5 if <= 0)
    - `args.delay_seconds`: seconds to sleep between site audits
    - `args.api_key`: optional override for API key
    - `args.note`: optional run note stored in `audit_runs.run_note`
    """
    conn = db.connect(Path(args.db))
    db.init_db(conn)
    # Prefer explicit CLI key over environment default.
    api_key = args.api_key or os.getenv("PAGESPEED_API_KEY")
    # Normalize blank notes to None so DB does not store empty-string noise.
    run_note = args.note.strip() if args.note else None
    batch_summary: list[dict[str, Any]] = []

    targets = list(
        _iter_target_sites(
            conn,
            site=args.site,
            run_all=args.all,
            limit=args.limit,
            offset=max(0, args.offset or 0),
        )
    )
    total_targets = len(targets)
    if total_targets == 0:
        print("No target sites selected (check --all/--limit/--offset and active sites).")
        return

    for idx, site in enumerate(targets, start=1):
        url = site["url"]
        print(f"\nAuditing [{idx}/{total_targets}] {url} ({args.strategy})...")
        try:
            payload = pagespeed.fetch_pagespeed(
                url, strategy=args.strategy, api_key=api_key
            )
            host_notes = pagespeed.snapshot_host_headers(url)
            cache_context = pagespeed.extract_cache_context(host_notes)
            lcp_context = pagespeed.extract_lcp_context(payload)
            metrics = pagespeed.extract_metrics(payload)
            counts = pagespeed.count_warnings_and_errors(payload)
            todos = analyzer.build_todos(payload, host_notes)

            run_id = db.insert_run(
                conn,
                site_id=site["id"],
                strategy=args.strategy,
                run_note=run_note,
                metrics=metrics,
                warning_count=counts["warning_count"],
                error_count=counts["error_count"],
                host_notes=host_notes,
                raw_payload=payload,
                cache_litespeed=cache_context.get("cache_litespeed"),
                cache_control=cache_context.get("cache_control"),
                lcp_element_snippet=lcp_context.get("lcp_element_snippet"),
                lcp_resource_url=lcp_context.get("lcp_resource_url"),
                lcp_ttfb_ms=lcp_context.get("lcp_ttfb_ms"),
                lcp_load_delay_ms=lcp_context.get("lcp_load_delay_ms"),
                lcp_load_time_ms=lcp_context.get("lcp_load_time_ms"),
                lcp_render_delay_ms=lcp_context.get("lcp_render_delay_ms"),
            )
            db.replace_run_todos(conn, run_id, todos)

            current_row = conn.execute(
                "SELECT * FROM audit_runs WHERE id = ?", (run_id,)
            ).fetchone()
            # Previous run is used for side-by-side delta reporting.
            prev = db.get_previous_run(
                conn, site["id"], args.strategy, current_row["fetched_at"]
            )
            print(f"Run saved: id={run_id}")
            if current_row["run_note"]:
                print(f"Note: {current_row['run_note']}")
            print(
                f"Score={metrics.get('performance_score')}  "
                f"FCP={fmt_ms(metrics.get('fcp_ms'))}  "
                f"LCP={fmt_ms(metrics.get('lcp_ms'))}  "
                f"TBT={fmt_ms(metrics.get('tbt_ms'))}  "
                f"TTFB={fmt_ms(metrics.get('ttfb_ms'))}"
            )
            print(
                f"Warnings={counts['warning_count']} Errors={counts['error_count']} TODOs={len(todos)}"
            )
            batch_summary.append(
                {
                    "url": url,
                    "metrics": metrics,
                    "warnings": counts["warning_count"],
                    "errors": counts["error_count"],
                    "todos": len(todos),
                }
            )

            if prev:
                delta = analyzer.compare_runs(metrics, _metrics_from_row(prev))
                if delta:
                    print("Delta vs previous:")
                    for key, change in delta.items():
                        print(f"  {key}: {change:+}")

            # Guard against invalid values from CLI; keep a sensible default.
            trend_limit = (
                args.trend_limit if args.trend_limit and args.trend_limit > 0 else 5
            )
            recent = db.get_recent_runs(
                conn, site["id"], args.strategy, limit=trend_limit
            )
            if recent:
                print("")
                print(
                    f"Recent trend for {site['url']} ({args.strategy}, last {len(recent)}):"
                )
                _print_trend_lines(recent)
                _print_trend_notes(recent)
                print("")

        except Exception as exc:
            print(f"FAILED {url}: {exc}")

        if args.delay_seconds and args.delay_seconds > 0 and idx < total_targets:
            print(f"Sleeping {args.delay_seconds:.1f}s before next site...")
            time.sleep(args.delay_seconds)

    if args.all and batch_summary:
        ts = datetime.now().astimezone().strftime("%Y-%m-%d %I:%M %p %Z")
        strategy_label = "Mobile" if args.strategy == "mobile" else "Desktop"
        strategy_mark = "M" if args.strategy == "mobile" else "D"
        width = max(len(_summary_domain(item["url"])) for item in batch_summary)
        score_vals = [
            "n/a"
            if item["metrics"].get("performance_score") is None
            else f"{float(item['metrics'].get('performance_score')):.1f}"
            for item in batch_summary
        ]
        fcp_vals = [fmt_ms(item["metrics"].get("fcp_ms")) for item in batch_summary]
        lcp_vals = [fmt_ms(item["metrics"].get("lcp_ms")) for item in batch_summary]
        tbt_vals = [fmt_ms(item["metrics"].get("tbt_ms")) for item in batch_summary]
        ttfb_vals = [fmt_ms(item["metrics"].get("ttfb_ms")) for item in batch_summary]
        warning_vals = [str(item["warnings"]) for item in batch_summary]
        error_vals = [str(item["errors"]) for item in batch_summary]
        todo_vals = [str(item["todos"]) for item in batch_summary]

        score_w = max(len(v) for v in score_vals)
        fcp_w = max(len(v) for v in fcp_vals)
        lcp_w = max(len(v) for v in lcp_vals)
        tbt_w = max(len(v) for v in tbt_vals)
        ttfb_w = max(len(v) for v in ttfb_vals)
        warning_w = max(len(v) for v in warning_vals)
        error_w = max(len(v) for v in error_vals)
        todo_w = max(len(v) for v in todo_vals)
        print("")
        print(f"{ts} - {strategy_label} Sites Tested:")
        for item in batch_summary:
            domain = _summary_domain(item["url"])
            label = f"{domain} ({strategy_mark}):"
            metrics = item["metrics"]
            score = metrics.get("performance_score")
            score_text = "n/a" if score is None else f"{float(score):.1f}"
            fcp_text = fmt_ms(metrics.get("fcp_ms"))
            lcp_text = fmt_ms(metrics.get("lcp_ms"))
            tbt_text = fmt_ms(metrics.get("tbt_ms"))
            ttfb_text = fmt_ms(metrics.get("ttfb_ms"))
            print(
                f"{label:<{width + 6}} "
                f"Score={score_text:<{score_w}}  "
                f"FCP={fcp_text:<{fcp_w}}  "
                f"LCP={lcp_text:<{lcp_w}}  "
                f"TBT={tbt_text:<{tbt_w}}  "
                f"TTFB={ttfb_text:<{ttfb_w}}  "
                f"Warnings={item['warnings']:<{warning_w}}  "
                f"Errors={item['errors']:<{error_w}}  "
                f"TODOs={item['todos']:<{todo_w}}"
            )
        print("")
        print("Score = Lighthouse Performance score")
        print("FCP = First Contentful Paint - when first visible content appears")
        print(
            "LCP = Largest Contentful Paint - when the largest visible element finishes rendering"
        )
        print("TBT = Total Blocking Time - time JavaScript blocked the main thread")
        print("TTFB = Time To First Byte - server response latency before content starts")
        print("Note: 1000 ms = 1 second")
        csv_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        csv_path = Path("reports") / f"{args.strategy}-batch-{csv_stamp}.csv"
        _write_bulk_summary_csv(
            csv_path,
            batch_summary=batch_summary,
        )
        print(f"Bulk CSV report written: {csv_path.resolve()}")
        html_path = csv_path.with_suffix(".html")
        _write_bulk_summary_html(
            html_path,
            batch_summary=batch_summary,
            strategy=args.strategy,
            generated_at=ts,
        )
        print(f"Interactive HTML report written: {html_path.resolve()}")


def cmd_todo(args: argparse.Namespace) -> None:
    conn = db.connect(Path(args.db))
    db.init_db(conn)
    if args.site:
        site = db.get_site(conn, args.site)
        run = db.get_latest_run(conn, site["id"], args.strategy)
    else:
        run = _latest_run_with_site(conn, args.strategy)
        if run:
            site = {"url": run["site_url"]}
        else:
            site = None
    if not run:
        if args.site:
            print("No runs found for this site/strategy.")
        else:
            print("No runs found yet. Run an audit first (or pass --site).")
        return
    todos = db.get_run_todos(conn, run["id"], limit=args.limit)
    print(f"Top TODOs for {site['url']} (run {run['id']}, {run['fetched_at']}):")
    for idx, item in enumerate(todos, start=1):
        print(
            f"{idx:>2}. [{item['audit_id']}] {item['title']} "
            f"(priority={item['priority']}, impact_ms={item['impact_ms']}, score={item['score']})"
        )


def cmd_trend(args: argparse.Namespace) -> None:
    conn = db.connect(Path(args.db))
    db.init_db(conn)
    if args.site:
        site = db.get_site(conn, args.site)
        runs = db.get_recent_runs(conn, site["id"], args.strategy, limit=args.limit)
    else:
        latest = _latest_run_with_site(conn, args.strategy)
        if not latest:
            print("No runs found yet. Run an audit first (or pass --site).")
            return
        site = {"url": latest["site_url"], "id": latest["site_id"]}
        runs = db.get_recent_runs(conn, site["id"], args.strategy, limit=args.limit)
    if not runs:
        print("No runs found.")
        return

    print(f"Trend for {site['url']} ({args.strategy}):")
    _print_trend_lines(runs)
    if args.show_notes:
        _print_trend_notes(runs)


def cmd_issue_brief(args: argparse.Namespace) -> None:
    conn = db.connect(Path(args.db))
    db.init_db(conn)
    if args.site:
        site = db.get_site(conn, args.site)
    else:
        latest = _latest_run_with_site(conn, args.strategy)
        if not latest:
            print("No runs found yet. Run an audit first (or pass --site).")
            return
        site = {"url": latest["site_url"], "id": latest["site_id"]}

    run = None
    if args.run_id:
        run = conn.execute(
            "SELECT * FROM audit_runs WHERE id = ?", (args.run_id,)
        ).fetchone()
    if not run:
        run = db.get_latest_run(conn, site["id"], args.strategy)
    if not run:
        print("No run found for issue brief.")
        return

    prev = db.get_previous_run(conn, site["id"], args.strategy, run["fetched_at"])
    todos = db.get_run_todos(conn, run["id"], limit=args.limit)
    host_notes = json.loads(run["host_notes_json"] or "{}")
    current_metrics = _metrics_from_row(run)
    delta = (
        analyzer.compare_runs(current_metrics, _metrics_from_row(prev)) if prev else {}
    )

    lines = [
        f"# Performance Issue Brief: {site['url']}",
        "",
        "## Context",
        f"- Run ID: {run['id']}",
        f"- Strategy: {run['strategy']}",
        f"- Timestamp (UTC): {run['fetched_at']}",
        f"- Note: {run['run_note'] or 'None'}",
        "",
        "## Current Metrics",
        f"- Performance Score: {run['performance_score']}",
        f"- FCP: {run['fcp_ms']} ms",
        f"- LCP: {run['lcp_ms']} ms",
        f"- TBT: {run['tbt_ms']} ms",
        f"- CLS: {run['cls']}",
        f"- Speed Index: {run['speed_index_ms']} ms",
        f"- TTFB: {run['ttfb_ms']} ms",
        "",
        "## Delta vs Previous Run",
    ]

    if delta:
        for key, change in delta.items():
            lines.append(f"- {key}: {change:+}")
    else:
        lines.append("- No previous run available for comparison.")

    lines.extend(["", "## Host/Cache Notes"])
    notes = host_notes.get("notes") or []
    if notes:
        for note in notes:
            lines.append(f"- {note}")
    else:
        lines.append("- No major host/cache concerns detected from headers snapshot.")

    lines.extend(["", "## Prioritized Issues"])
    for idx, todo in enumerate(todos, 1):
        lines.append(
            f"{idx}. {todo['title']} | audit={todo['audit_id']} | "
            f"priority={todo['priority']} | impact_ms={todo['impact_ms']} | score={todo['score']}"
        )

    lines.extend(
        [
            "",
            "## Ask",
            "Propose the most impactful optimization steps for a WordPress + Divi site, ordered by expected user-visible performance gains,",
            "and include what to test before/after so regressions are avoided.",
        ]
    )

    body = "\n".join(lines)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(body, encoding="utf-8")
        print(f"Issue brief written: {output}")
    else:
        print(body)


def cmd_render_report(args: argparse.Namespace) -> None:
    csv_path = Path(args.csv).expanduser().resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    strategy = "mobile" if "mobile" in csv_path.name.lower() else "desktop"
    summary = _read_bulk_summary_csv(csv_path)
    if not summary:
        raise ValueError("No summary rows found in CSV.")
    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else csv_path.with_suffix(".html")
    )
    generated_at = datetime.now().astimezone().strftime("%Y-%m-%d %I:%M %p %Z")
    _write_bulk_summary_html(
        output,
        batch_summary=summary,
        strategy=strategy,
        generated_at=generated_at,
    )
    print(f"Interactive HTML report written: {output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Website performance tracker (Lighthouse/PageSpeed based)",
        epilog=(
            "Tip: run `webperf <command> --help` for command-specific options.\n"
            "All optional flags by command:\n"
            "  Global:\n"
            "    --db <path>            SQLite database path\n"
            "  import-sites:\n"
            "    --file <path>          Source file of URLs/domains\n"
            "  add-site:\n"
            "    --label <text>         Optional site label\n"
            "  list-sites:\n"
            "    --all                  Include inactive sites\n"
            "  run:\n"
            "    --site <url>           Audit one site\n"
            "    --all                  Audit all active sites\n"
            "    --strategy <mode>      mobile | desktop\n"
            "    --limit <n>            Max sites when using --all\n"
            "    --offset <n>           Skip first N active sites when using --all\n"
            "    --trend-limit <n>      Recent runs shown per audited site\n"
            "    --delay-seconds <n>    Pause between site audits in batch mode\n"
            "    --api-key <key>        PageSpeed API key override\n"
            "    --note <text>          Run note saved with the audit\n"
            "  todo:\n"
            "    --site <url>           Optional; defaults to latest audited site\n"
            "    --strategy <mode>      mobile | desktop\n"
            "    --limit <n>            Max TODOs to show\n"
            "  trend:\n"
            "    --site <url>           Optional; defaults to latest audited site\n"
            "    --strategy <mode>      mobile | desktop\n"
            "    --limit <n>            Max runs to show\n"
            "    --show-notes           Include per-run notes\n"
            "  issue-brief:\n"
            "    --site <url>           Optional; defaults to latest audited site\n"
            "    --strategy <mode>      mobile | desktop\n"
            "    --run-id <id>          Use a specific run instead of latest\n"
            "    --limit <n>            Max issues to include\n"
            "    --output <path>        Write Markdown to file\n"
            "  sync-sites:\n"
            "    --file <path>          Sites list file (default: sites.txt)\n"
            "    --apply                Apply changes (default is dry-run)\n"
            "    --yes                  Skip confirmation prompt\n"
            "  render-report:\n"
            "    --csv <path>           Existing batch CSV to convert to HTML\n"
            "    --output <path>        Optional output HTML path\n"
            "Examples:\n"
            "  webperf run --site https://aprilbell.com --strategy mobile\n"
            "  webperf run --all --limit 3 --delay-seconds 10 --strategy mobile\n"
            "  webperf todo --site https://aprilbell.com\n"
            "  webperf trend --show-notes\n"
            "  webperf render-report --csv reports/mobile-batch-20260217-204532.csv"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--db", default="data/webperf.sqlite3", help="SQLite database path"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init-db", help="Initialize database")
    p.set_defaults(func=cmd_init_db)

    p = sub.add_parser("import-sites", help="Import sites from text file")
    p.add_argument(
        "--file",
        required=True,
        help="Path to file containing one site URL/domain per line",
    )
    p.set_defaults(func=cmd_import_sites)

    p = sub.add_parser("add-site", help="Add one site")
    p.add_argument("url")
    p.add_argument("--label")
    p.set_defaults(func=cmd_add_site)

    p = sub.add_parser("list-sites", help="List sites")
    p.add_argument("--all", action="store_true", help="Include inactive sites")
    p.set_defaults(func=cmd_list_sites)

    p = sub.add_parser("run", help="Run Lighthouse-like audit(s)")
    target = p.add_mutually_exclusive_group(required=True)
    target.add_argument("--site", help="Single site URL")
    target.add_argument("--all", action="store_true", help="Run all active sites")
    p.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    p.add_argument("--limit", type=int, help="Limit number of sites when using --all")
    p.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Skip first N active sites when using --all",
    )
    p.add_argument(
        "--trend-limit",
        type=int,
        default=5,
        help="How many recent runs to print after each audit",
    )
    p.add_argument(
        "--delay-seconds",
        type=float,
        default=0.0,
        help="Sleep N seconds between sites when auditing in batch mode",
    )
    p.add_argument(
        "--api-key", help="Google PageSpeed API key (or use PAGESPEED_API_KEY env var)"
    )
    p.add_argument("--note", help="Optional note about what changed before this run")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("todo", help="Show prioritized TODO list for latest run")
    p.add_argument(
        "--site", help="Optional site URL; defaults to most recently audited site"
    )
    p.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    p.add_argument("--limit", type=int, default=12)
    p.set_defaults(func=cmd_todo)

    p = sub.add_parser(
        "trend", help="Show recent run trend (use --show-notes to view attached notes)"
    )
    p.add_argument(
        "--site", help="Optional site URL; defaults to most recently audited site"
    )
    p.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    p.add_argument("--limit", type=int, default=8)
    p.add_argument(
        "--show-notes", action="store_true", help="Include per-run notes in output"
    )
    p.set_defaults(func=cmd_trend)

    p = sub.add_parser(
        "issue-brief", help="Generate a paste-ready issue brief for ChatGPT"
    )
    p.add_argument(
        "--site", help="Optional site URL; defaults to most recently audited site"
    )
    p.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    p.add_argument("--run-id", type=int)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--output", help="Write Markdown brief to file")
    p.set_defaults(func=cmd_issue_brief)

    # --- sync-sites command ---
    p_sync = sub.add_parser("sync-sites", help="Sync sites table to match sites.txt")
    p_sync.add_argument("--file", default="sites.txt", help="Path to sites.txt")
    p_sync.add_argument(
        "--apply", action="store_true", help="Apply changes (otherwise dry-run)"
    )
    p_sync.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    p_sync.set_defaults(func=cmd_sync_sites)

    p = sub.add_parser(
        "render-report", help="Convert a batch CSV report into an interactive HTML table"
    )
    p.add_argument("--csv", required=True, help="Path to batch CSV report")
    p.add_argument("--output", help="Optional output HTML path")
    p.set_defaults(func=cmd_render_report)

    return parser


def _read_sites_txt(path: Path) -> list[str]:
    # Read file lines.
    raw = path.read_text(encoding="utf-8").splitlines()

    urls: list[str] = []
    for line in raw:
        # Strip whitespace.
        s = line.strip()

        # Skip blanks and comments.
        if not s or s.startswith("#"):
            continue

        # Keep raw URL; db functions will normalize.
        urls.append(s)

    return urls


def cmd_sync_sites(args: argparse.Namespace) -> None:
    """
    Sync the `sites` table to exactly match URLs listed in a sites file.

    Why this command exists:
    - Maintains one canonical source of truth (`sites.txt` by default).
    - Makes activation state predictable without manually editing DB rows.

    Behavior:
    - Reads URLs from `--file` (default `sites.txt`), ignoring blanks/comments.
    - Normalizes URLs and compares file set vs DB set.
    - Computes and prints a plan:
      - ADD: in file, missing from DB
      - RE-ACTIVATE: in file, present but inactive in DB
      - DEACTIVATE: active in DB, missing from file
    - Default mode is dry-run (no DB writes).
    - With `--apply`, optionally asks for `YES` unless `--yes` is also set.
    - Apply step:
      - upserts every file URL (covers add + reactivate)
      - deactivates active DB URLs that are no longer in file

    Arg expectations:
    - `args.db`: SQLite DB path
    - `args.file`: path to sites list text file
    - `args.apply`: perform writes; otherwise preview only
    - `args.yes`: skip interactive confirmation (only relevant with `--apply`)
    """
    # Connect to DB.
    conn = db.connect(Path(args.db))
    db.init_db(conn)

    # Resolve sites.txt path.
    sites_path = Path(args.file).expanduser().resolve()

    # Load URLs from file.
    file_urls = _read_sites_txt(sites_path)

    # Normalize URLs into a set for comparison.
    file_set = {db.normalize_url(u) for u in file_urls}

    # Load DB sites (all, active and inactive).
    rows = conn.execute("SELECT url, active FROM sites").fetchall()
    db_set = {r["url"] for r in rows}
    db_active_set = {r["url"] for r in rows if int(r["active"]) == 1}
    db_inactive_set = {r["url"] for r in rows if int(r["active"]) == 0}

    # Compute changes.
    to_add = sorted(file_set - db_set)
    to_reactivate = sorted(file_set & db_inactive_set)
    to_deactivate = sorted(db_active_set - file_set)

    # Print plan.
    print(f"\nSync plan using: {sites_path}")
    print(f"ADD ({len(to_add)}):")
    for u in to_add[:200]:
        print(f"  + {u}")
    if len(to_add) > 200:
        print(f"  ... {len(to_add)-200} more")

    print(f"\nRE-ACTIVATE ({len(to_reactivate)}):")
    for u in to_reactivate[:200]:
        print(f"  ↑ {u}")
    if len(to_reactivate) > 200:
        print(f"  ... {len(to_reactivate)-200} more")

    print(f"\nDEACTIVATE ({len(to_deactivate)}):")
    for u in to_deactivate[:200]:
        print(f"  - {u}")
    if len(to_deactivate) > 200:
        print(f"  ... {len(to_deactivate)-200} more")

    # Dry-run by default.
    if not args.apply:
        print("\nDry run only. Re-run with --apply to make changes.")
        return

    # Optional confirmation prompt (skipped if --yes).
    if not args.yes:
        answer = input("\nApply these changes? Type y/yes to continue: ").strip()
        if answer.lower() not in {"y", "yes"}:
            print("Aborted.")
            return

    # Apply changes in a transaction.
    with conn:
        # Add and reactivate.
        for u in sorted(file_set):
            # Upsert ensures inserts + re-activations.
            db.upsert_site(conn, u)

        # Deactivate missing.
        for u in to_deactivate:
            db.set_site_active(conn, u, 0)

    print("\nDone.")


def main() -> None:
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    args = parser.parse_args()
    args.func(args)
