#!/usr/bin/env python3
"""
Fetch FantasyPros rankings for multiple positions by parsing the embedded ecrData JSON
from the public rankings pages, then export to CSV files.

Positions covered: QB, RB, WR, TE, DST

Usage examples:
  python3 scripts/fantasypros_rankings.py
  python3 scripts/fantasypros_rankings.py --positions QB RB WR TE DST --out /workspace/data/fantasypros
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests


DEFAULT_POSITIONS = ["QB", "RB", "WR", "TE", "DST"]
BASE_URL = "https://www.fantasypros.com/nfl/rankings/{slug}.php"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class FetchResult:
    position: str
    csv_path: Optional[str]
    num_rows: int
    error: Optional[str] = None


def fetch_html(url: str, *, retries: int = 3, timeout: int = 20) -> str:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.fantasypros.com/",
        "Connection": "keep-alive",
    }
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            # Some CDN setups respond with 403 if no UA; we provide UA above.
            resp.raise_for_status()
            return resp.text
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if attempt < retries:
                time.sleep(min(2 * attempt, 5))
    assert last_err is not None
    raise last_err


def extract_ecr_data(html: str) -> Dict:
    # The page includes: var ecrData = { ... };
    # Use a DOTALL non-greedy match to capture the JSON object literal.
    match = re.search(r"var\s+ecrData\s*=\s*(\{.*?\});", html, re.DOTALL)
    if not match:
        raise ValueError("Could not locate ecrData JSON in page HTML")
    raw = match.group(1)

    # Attempt to parse JSON directly; if it fails, try a minimal cleanup for trailing commas
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = re.sub(r",\s*([}\]])", r"\1", raw)
        return json.loads(cleaned)


def write_players_csv(ecr_data: Dict, out_dir: str, requested_scoring: Optional[str] = None) -> tuple[str, int]:
    players: List[Dict] = ecr_data.get("players", [])
    if not players:
        raise ValueError("ecrData contains no players")

    # Build file name from metadata for clarity
    position = str(ecr_data.get("position_id", "pos")).lower()
    ranking_type = str(ecr_data.get("ranking_type_name", "weekly")).lower()
    # Prefer the requested scoring in output filenames so settings are reflected
    if requested_scoring:
        scoring = str(requested_scoring).lower()
    else:
        scoring = str(ecr_data.get("scoring", "std")).lower()
    week = str(ecr_data.get("week", "na"))
    year = str(ecr_data.get("year", "unknown"))

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir,
        f"{position}_rankings_{ranking_type}_{scoring}_week{week}_{year}.csv",
    )

    # Columns chosen to be broadly applicable across positions
    columns = [
        "rank_ecr",
        "player_name",
        "player_short_name",
        "player_team_id",
        "player_positions",
        "player_opponent",
        "pos_rank",
        "r2p_pts",
        "rank_min",
        "rank_max",
        "rank_ave",
        "rank_std",
        "player_bye_week",
        "player_owned_avg",
        "player_page_url",
        "player_id",
    ]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for p in players:
            row = {key: p.get(key, "") for key in columns}
            writer.writerow(row)

    return out_path, len(players)


def build_slug(position: str, scoring: str) -> str:
    pos = position.strip().lower()
    s = scoring.strip().upper()
    # FantasyPros exposes alternate slugs for PPR/Half-PPR for skill positions
    # Examples:
    #  - half-point-ppr-rb.php, ppr-rb.php
    #  - half-point-ppr-wr.php, ppr-wr.php
    #  - half-point-ppr-te.php, ppr-te.php
    # QB and DST typically do not vary by PPR, keep base slug
    if s == "HALF" and pos in {"rb", "wr", "te", "flx"}:
        return f"half-point-ppr-{pos}"
    if s == "PPR" and pos in {"rb", "wr", "te", "flx"}:
        return f"ppr-{pos}"
    return pos


def process_position(position: str, out_dir: str, scoring: str) -> FetchResult:
    pos_slug = position.strip().lower()
    scoring_param = scoring.strip().upper()
    slug = build_slug(pos_slug, scoring_param)
    url = BASE_URL.format(slug=slug)
    # Ensure the Overview view is requested (matches user's requested setting)
    connector = '&' if '?' in url else '?'
    url = f"{url}{connector}view=overview"
    try:
        html = fetch_html(url)
        ecr_data = extract_ecr_data(html)
        csv_path, num_rows = write_players_csv(ecr_data, out_dir, requested_scoring=scoring_param)
        return FetchResult(position=position.upper(), csv_path=csv_path, num_rows=num_rows)
    except Exception as exc:  # noqa: BLE001
        return FetchResult(position=position.upper(), csv_path=None, num_rows=0, error=str(exc))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Export FantasyPros rankings to CSVs")
    parser.add_argument(
        "--positions",
        nargs="*",
        default=DEFAULT_POSITIONS,
        help="Positions to fetch (default: QB RB WR TE DST)",
    )
    parser.add_argument(
        "--out",
        default="/workspace/data/fantasypros",
        help="Output directory for CSV files",
    )
    parser.add_argument(
        "--scoring",
        default="HALF",
        choices=["STD", "HALF", "PPR", "std", "half", "ppr"],
        help="Scoring format to request from FantasyPros (default: HALF)",
    )
    args = parser.parse_args(argv)

    out_dir = args.out
    scoring: str = args.scoring
    results: List[FetchResult] = []

    for idx, position in enumerate(args.positions, start=1):
        result = process_position(position, out_dir, scoring)
        results.append(result)
        # Be polite to remote server
        if idx < len(args.positions):
            time.sleep(0.6)

    any_error = False
    for res in results:
        if res.error:
            any_error = True
            print(f"[FAIL] {res.position}: {res.error}")
        else:
            print(f"[OK]   {res.position}: {res.num_rows} rows -> {res.csv_path}")

    return 1 if any_error else 0


if __name__ == "__main__":
    raise SystemExit(main())

