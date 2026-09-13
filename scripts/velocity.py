"""
Phase 4 velocity log: one row per check-in, appended to ops/velocity.csv.

    python scripts/velocity.py                                  # snapshot from the last build only
    python scripts/velocity.py --gsc path/to/Pages.csv          # + Search Console "Pages" export
    python scripts/velocity.py --indexed 112 --affiliate-clicks 9 --leads 2 --revenue 0
    python scripts/velocity.py --report                         # print the log and the verdict

The Search Console export is the "Pages" CSV from Performance > Search results
> Export. Columns expected: Top pages, Clicks, Impressions, CTR, Position.
Indexed page count comes from Indexing > Pages and is entered by hand, because
it is not in that export.

Decision thresholds live in ops/RUNBOOK.md and are applied by --report.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "ops" / "velocity.csv"
REPORT = ROOT / "ops" / "build-report.json"
LAUNCH_FILE = ROOT / "ops" / "launch-date.txt"

FIELDS = [
    "date", "day", "pages_built", "comparisons", "indexed",
    "impressions", "clicks", "ctr", "avg_position", "pages_with_impressions",
    "affiliate_clicks", "leads", "revenue_usd", "notes",
]


def launch_day() -> date | None:
    if LAUNCH_FILE.exists():
        return date.fromisoformat(LAUNCH_FILE.read_text(encoding="utf-8").strip())
    return None


def parse_gsc(path: Path) -> dict:
    clicks = impressions = pages = 0
    weighted_pos = 0.0
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            c = int(float(row.get("Clicks", 0) or 0))
            i = int(float(row.get("Impressions", 0) or 0))
            pos = float(row.get("Position", 0) or 0)
            clicks += c
            impressions += i
            weighted_pos += pos * i
            pages += 1 if i else 0
    return {
        "clicks": clicks,
        "impressions": impressions,
        "ctr": round(clicks / impressions * 100, 2) if impressions else 0,
        "avg_position": round(weighted_pos / impressions, 1) if impressions else "",
        "pages_with_impressions": pages,
    }


def append(args) -> None:
    rep = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {}
    start = launch_day()
    row = {k: "" for k in FIELDS}
    row.update({
        "date": date.today().isoformat(),
        "day": (date.today() - start).days if start else "",
        "pages_built": rep.get("pages", ""),
        "comparisons": rep.get("comparisons", ""),
        "indexed": args.indexed if args.indexed is not None else "",
        "affiliate_clicks": args.affiliate_clicks if args.affiliate_clicks is not None else "",
        "leads": args.leads if args.leads is not None else "",
        "revenue_usd": args.revenue if args.revenue is not None else "",
        "notes": args.notes or "",
    })
    if args.gsc:
        row.update(parse_gsc(Path(args.gsc)))

    new = not LOG.exists()
    with open(LOG, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    print(f"  logged day {row['day'] if row['day'] != '' else '?'}: {row}")


def report() -> None:
    if not LOG.exists():
        print("  no velocity log yet")
        return
    rows = list(csv.DictReader(open(LOG, encoding="utf-8")))
    for r in rows:
        print(f"  {r['date']}  day {r['day']:>3}  indexed {r['indexed'] or '-':>4}  "
              f"impr {r['impressions'] or '-':>6}  clicks {r['clicks'] or '-':>4}  "
              f"pos {r['avg_position'] or '-':>5}  aff {r['affiliate_clicks'] or '-':>3}  leads {r['leads'] or '-':>3}")

    last = rows[-1]

    def num(key):
        try:
            return float(last[key])
        except (ValueError, TypeError, KeyError):
            return None

    day, built, indexed, impr, clicks = num("day"), num("pages_built"), num("indexed"), num("impressions"), num("clicks")
    print()
    if day is None:
        print("  verdict: set ops/launch-date.txt to get a verdict")
        return
    ratio = (indexed / built) if indexed is not None and built else None
    if day < 30:
        print(f"  verdict (day {int(day)}): too early. Watch the indexed ratio, target 30% by day 30"
              + (f", currently {ratio:.0%}" if ratio is not None else ""))
    elif day < 60:
        if ratio is not None and ratio < 0.15:
            print("  verdict (day 30 gate): KILL SIGNAL. Under 15% indexed; Google is not accepting the pages.")
        elif (impr or 0) >= 1000:
            print("  verdict (day 30 gate): SCALE. Publish wave 2 now.")
        else:
            print("  verdict (day 30 gate): HOLD. Indexing is happening but demand is unproven; improve the top 10 pages.")
    else:
        if (clicks or 0) >= 300 or (num("revenue_usd") or 0) > 0 or (num("leads") or 0) >= 10:
            print("  verdict (day 60 gate): CONTINUE. Buy a domain, activate affiliates, publish wave 3.")
        else:
            print("  verdict (day 60 gate): STOP. Archive the site and move to the next niche.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gsc")
    ap.add_argument("--indexed", type=int)
    ap.add_argument("--affiliate-clicks", type=int)
    ap.add_argument("--leads", type=int)
    ap.add_argument("--revenue", type=float)
    ap.add_argument("--notes")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.report:
        report()
    else:
        append(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
