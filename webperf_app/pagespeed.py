import json
import time
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PAGESPEED_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


class PageSpeedError(RuntimeError):
    pass


def _http_get_json(url: str, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    query_pairs = []
    for key, value in params.items():
        if isinstance(value, list):
            for item in value:
                query_pairs.append((key, item))
        else:
            query_pairs.append((key, value))

    full_url = f"{url}?{urlencode(query_pairs)}"
    req = Request(full_url, headers={"User-Agent": "WebsiteSpeedTest/1.0"})

    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except HTTPError as exc:
        msg = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
        raise PageSpeedError(f"HTTP error {exc.code}: {msg[:200]}") from exc
    except URLError as exc:
        raise PageSpeedError(f"Network error: {exc.reason}") from exc


def fetch_pagespeed(url: str, strategy: str = "mobile", api_key: Optional[str] = None, timeout: int = 90) -> Dict[str, Any]:
    params = {
        "url": url,
        "strategy": strategy,
        "category": ["performance", "accessibility", "best-practices", "seo"],
    }
    if api_key:
        params["key"] = api_key

    payload = _http_get_json(PAGESPEED_ENDPOINT, params, timeout)
    if "lighthouseResult" not in payload:
        raise PageSpeedError("Unexpected PageSpeed response: missing lighthouseResult")
    return payload


def extract_metrics(payload: Dict[str, Any]) -> Dict[str, Optional[float]]:
    audits = payload["lighthouseResult"].get("audits", {})
    categories = payload["lighthouseResult"].get("categories", {})

    perf_score = categories.get("performance", {}).get("score")
    if perf_score is not None:
        perf_score = round(perf_score * 100, 1)

    def metric(name: str) -> Optional[float]:
        item = audits.get(name, {})
        value = item.get("numericValue")
        if value is None:
            return None
        return round(float(value), 1)

    return {
        "performance_score": perf_score,
        "fcp_ms": metric("first-contentful-paint"),
        "lcp_ms": metric("largest-contentful-paint"),
        "tbt_ms": metric("total-blocking-time"),
        "cls": audits.get("cumulative-layout-shift", {}).get("numericValue"),
        "speed_index_ms": metric("speed-index"),
        "ttfb_ms": metric("server-response-time"),
    }


def count_warnings_and_errors(payload: Dict[str, Any]) -> Dict[str, int]:
    audits = payload["lighthouseResult"].get("audits", {})
    warnings = 0
    errors = 0

    runtime_error = payload["lighthouseResult"].get("runtimeError")
    if runtime_error:
        errors += 1

    for audit in audits.values():
        mode = audit.get("scoreDisplayMode")
        if mode == "error":
            errors += 1
        warning_text = audit.get("warnings")
        if warning_text:
            if isinstance(warning_text, list):
                warnings += len(warning_text)
            else:
                warnings += 1

    return {"warning_count": warnings, "error_count": errors}


def snapshot_host_headers(url: str, timeout: int = 30) -> Dict[str, Any]:
    start = time.perf_counter()
    req = Request(url, headers={"User-Agent": "WebsiteSpeedTest/1.0"})

    try:
        with urlopen(req, timeout=timeout) as resp:
            elapsed_ms = (time.perf_counter() - start) * 1000
            headers = {k.lower(): v for k, v in resp.headers.items()}
            status_code = getattr(resp, "status", 200)
            final_url = resp.geturl()
    except Exception as exc:
        return {
            "status_code": None,
            "final_url": url,
            "elapsed_ms": None,
            "headers": {},
            "notes": [f"Host header probe failed: {exc}"],
        }

    cache_control = headers.get("cache-control", "")
    age = headers.get("age")

    cache_signals = {
        "cf-cache-status": headers.get("cf-cache-status"),
        "x-cache": headers.get("x-cache"),
        "x-served-by": headers.get("x-served-by"),
        "cache-control": cache_control,
        "age": age,
    }

    notes = []
    if "max-age" not in cache_control:
        notes.append("Response missing max-age; cache lifetime may be too short or absent.")
    if "no-cache" in cache_control or "no-store" in cache_control:
        notes.append("Cache-Control disables or weakens browser/proxy caching.")
    if not cache_signals.get("cf-cache-status") and not cache_signals.get("x-cache"):
        notes.append("No edge cache status header detected (host/CDN dependent).")

    return {
        "status_code": status_code,
        "final_url": final_url,
        "elapsed_ms": round(elapsed_ms, 1),
        "headers": cache_signals,
        "notes": notes,
    }
