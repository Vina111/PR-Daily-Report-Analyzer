#!/usr/bin/env python3
"""Query Google Custom Search JSON API using environment-based credentials."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://customsearch.googleapis.com/customsearch/v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Search an existing Google Programmable Search Engine and emit "
            "normalized JSON. Requires GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID."
        )
    )
    parser.add_argument("--query", required=True, help="Google search query")
    parser.add_argument(
        "--date-restrict",
        help="Relative date filter such as d1, w1, m1, or y1",
    )
    parser.add_argument("--gl", help="Two-letter country boost, such as us")
    parser.add_argument(
        "--lr",
        help="Language restriction, such as lang_en or lang_zh-CN",
    )
    parser.add_argument(
        "--num",
        type=int,
        default=10,
        choices=range(1, 11),
        metavar="1-10",
        help="Results per request (default: 10)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="One-based start index (default: 1)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Request timeout in seconds (default: 20)",
    )
    return parser.parse_args()


def fail(message: str, code: int = 2) -> None:
    print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
    raise SystemExit(code)


def main() -> None:
    args = parse_args()
    api_key = os.environ.get("GOOGLE_CSE_API_KEY")
    engine_id = os.environ.get("GOOGLE_CSE_ID")
    if not api_key or not engine_id:
        fail(
            "Missing GOOGLE_CSE_API_KEY or GOOGLE_CSE_ID. "
            "Configure credentials as environment variables."
        )

    params: dict[str, str | int] = {
        "key": api_key,
        "cx": engine_id,
        "q": args.query,
        "num": args.num,
        "start": args.start,
        "safe": "active",
    }
    if args.date_restrict:
        params["dateRestrict"] = args.date_restrict
    if args.gl:
        params["gl"] = args.gl
    if args.lr:
        params["lr"] = args.lr

    request = urllib.request.Request(
        f"{ENDPOINT}?{urllib.parse.urlencode(params)}",
        headers={"Accept": "application/json", "User-Agent": "pr-media-intelligence/1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        fail(f"Google Search API returned HTTP {exc.code}.", 1)
    except urllib.error.URLError as exc:
        fail(f"Google Search API request failed: {exc.reason}", 1)
    except (TimeoutError, json.JSONDecodeError) as exc:
        fail(f"Google Search API response could not be processed: {exc}", 1)

    results = []
    for item in payload.get("items", []):
        pagemap = item.get("pagemap") or {}
        metatags = pagemap.get("metatags") or []
        metadata = metatags[0] if metatags else {}
        results.append(
            {
                "title": item.get("title"),
                "url": item.get("link"),
                "display_url": item.get("displayLink"),
                "snippet": item.get("snippet"),
                "mime": item.get("mime"),
                "published_at": (
                    metadata.get("article:published_time")
                    or metadata.get("og:published_time")
                    or metadata.get("date")
                ),
            }
        )

    output = {
        "ok": True,
        "provider": "google_cse",
        "query": args.query,
        "estimated_total_results": (
            payload.get("searchInformation", {}).get("totalResults")
        ),
        "results": results,
    }
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
