from typing import Any, Dict, List


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_todos(payload: Dict[str, Any], host_notes: Dict[str, Any]) -> List[Dict[str, Any]]:
    audits = payload["lighthouseResult"].get("audits", {})
    todos: List[Dict[str, Any]] = []

    for audit_id, audit in audits.items():
        mode = audit.get("scoreDisplayMode")
        if mode in {"notApplicable", "informative", "manual"}:
            continue

        score = audit.get("score")
        if score is None:
            continue

        details = audit.get("details") or {}
        impact_ms = 0.0
        if details.get("type") == "opportunity":
            impact_ms = _safe_float(details.get("overallSavingsMs"))
        if not impact_ms and audit.get("numericValue") is not None and score < 0.9:
            impact_ms = _safe_float(audit.get("numericValue"))

        # Priority intentionally weights both impact and poor score.
        priority = max(0.0, impact_ms) + (1.0 - _safe_float(score)) * 1000
        if priority <= 100:
            continue

        todos.append(
            {
                "audit_id": audit_id,
                "title": audit.get("title", audit_id),
                "description": audit.get("description", ""),
                "category": details.get("type", "audit"),
                "score": _safe_float(score),
                "impact_ms": round(impact_ms, 1),
                "priority": round(priority, 1),
            }
        )

    for host_note in host_notes.get("notes", []):
        todos.append(
            {
                "audit_id": "host-cache-check",
                "title": "Host/cache configuration review",
                "description": host_note,
                "category": "hosting",
                "score": 0.0,
                "impact_ms": 0.0,
                "priority": 450.0,
            }
        )

    todos.sort(key=lambda t: t["priority"], reverse=True)
    return todos


def compare_runs(current: Dict[str, Any], previous: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["performance_score", "fcp_ms", "lcp_ms", "tbt_ms", "cls", "speed_index_ms", "ttfb_ms"]
    delta = {}
    for key in keys:
        cur = current.get(key)
        prev = previous.get(key)
        if cur is None or prev is None:
            continue
        delta[key] = round(cur - prev, 2)
    return delta
