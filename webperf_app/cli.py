import argparse
import json
import os
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
    conn = db.connect(Path(args.db))
    db.init_db(conn)
    rows = db.list_sites(conn, active_only=not args.all)
    for row in rows:
        print(f"{row['id']:>3}  {row['url']}")
    print(f"Total: {len(rows)}")


def _iter_target_sites(conn: Any, *, site: Optional[str], run_all: bool, limit: Optional[int]) -> Iterable[Any]:
    if site:
        yield db.get_site(conn, site)
        return
    if run_all:
        rows = db.list_sites(conn, active_only=True)
        if limit:
            rows = rows[:limit]
        for row in rows:
            yield row
        return
    raise ValueError("Provide --site <url> or --all")


def cmd_run(args: argparse.Namespace) -> None:
    conn = db.connect(Path(args.db))
    db.init_db(conn)
    api_key = args.api_key or os.getenv("PAGESPEED_API_KEY")
    run_note = args.note.strip() if args.note else None

    for site in _iter_target_sites(conn, site=args.site, run_all=args.all, limit=args.limit):
        url = site["url"]
        print(f"\nAuditing {url} ({args.strategy})...")
        try:
            payload = pagespeed.fetch_pagespeed(url, strategy=args.strategy, api_key=api_key)
            host_notes = pagespeed.snapshot_host_headers(url)
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
            )
            db.replace_run_todos(conn, run_id, todos)

            current_row = conn.execute("SELECT * FROM audit_runs WHERE id = ?", (run_id,)).fetchone()
            prev = db.get_previous_run(conn, site["id"], args.strategy, current_row["fetched_at"])
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
            print(f"Warnings={counts['warning_count']} Errors={counts['error_count']} TODOs={len(todos)}")

            if prev:
                delta = analyzer.compare_runs(metrics, _metrics_from_row(prev))
                if delta:
                    print("Delta vs previous:")
                    for key, change in delta.items():
                        print(f"  {key}: {change:+}")

        except Exception as exc:
            print(f"FAILED {url}: {exc}")


def cmd_todo(args: argparse.Namespace) -> None:
    conn = db.connect(Path(args.db))
    db.init_db(conn)
    site = db.get_site(conn, args.site)
    run = db.get_latest_run(conn, site["id"], args.strategy)
    if not run:
        print("No runs found for this site/strategy.")
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
    site = db.get_site(conn, args.site)
    runs = db.get_recent_runs(conn, site["id"], args.strategy, limit=args.limit)
    if not runs:
        print("No runs found.")
        return

    print(f"Trend for {site['url']} ({args.strategy}):")
    for run in runs:
        print(
            f"- run={run['id']} at {run['fetched_at']} "
            f"score={run['performance_score']} lcp={run['lcp_ms']} tbt={run['tbt_ms']} ttfb={run['ttfb_ms']}"
        )
        if run["run_note"]:
            print(f'- note="{run["run_note"]}"')


def cmd_issue_brief(args: argparse.Namespace) -> None:
    conn = db.connect(Path(args.db))
    db.init_db(conn)
    site = db.get_site(conn, args.site)

    run = None
    if args.run_id:
        run = conn.execute("SELECT * FROM audit_runs WHERE id = ?", (args.run_id,)).fetchone()
    if not run:
        run = db.get_latest_run(conn, site["id"], args.strategy)
    if not run:
        print("No run found for issue brief.")
        return

    prev = db.get_previous_run(conn, site["id"], args.strategy, run["fetched_at"])
    todos = db.get_run_todos(conn, run["id"], limit=args.limit)
    host_notes = json.loads(run["host_notes_json"] or "{}")
    current_metrics = _metrics_from_row(run)
    delta = analyzer.compare_runs(current_metrics, _metrics_from_row(prev)) if prev else {}

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Website performance tracker (Lighthouse/PageSpeed based)")
    parser.add_argument("--db", default="data/webperf.sqlite3", help="SQLite database path")

    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init-db", help="Initialize database")
    p.set_defaults(func=cmd_init_db)

    p = sub.add_parser("import-sites", help="Import sites from text file")
    p.add_argument("--file", required=True, help="Path to file containing one site URL/domain per line")
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
    p.add_argument("--api-key", help="Google PageSpeed API key (or use PAGESPEED_API_KEY env var)")
    p.add_argument("--note", help="Optional note about what changed before this run")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("todo", help="Show prioritized TODO list for latest run")
    p.add_argument("--site", required=True)
    p.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    p.add_argument("--limit", type=int, default=12)
    p.set_defaults(func=cmd_todo)

    p = sub.add_parser("trend", help="Show recent run trend")
    p.add_argument("--site", required=True)
    p.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    p.add_argument("--limit", type=int, default=8)
    p.set_defaults(func=cmd_trend)

    p = sub.add_parser("issue-brief", help="Generate a paste-ready issue brief for ChatGPT")
    p.add_argument("--site", required=True)
    p.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    p.add_argument("--run-id", type=int)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--output", help="Write Markdown brief to file")
    p.set_defaults(func=cmd_issue_brief)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
