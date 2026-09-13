"""
Audits how old every published fact is.

    python scripts/check_staleness.py              # report
    python scripts/check_staleness.py --fail       # exit 1 if anything is stale (for CI)

A price older than MAX_PRICE_DAYS is flagged for re-reading from the vendor
page. GitHub facts older than MAX_GITHUB_DAYS are flagged for a re-run of
enrich_github.py. Nothing is changed automatically: a stale price needs a
human to look at the vendor page, not a script to guess.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.model import load_dataset  # noqa: E402

MAX_PRICE_DAYS = 45
MAX_GITHUB_DAYS = 30
MAX_FX_DAYS = 45


def age(iso: str | None) -> int | None:
    if not iso:
        return None
    return (date.today() - date.fromisoformat(iso)).days


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail", action="store_true")
    args = ap.parse_args()

    ds = load_dataset()
    wave = int(ds.config["publish_wave"])
    problems: list[str] = []

    print(f"\n  Vendor prices (limit {MAX_PRICE_DAYS} days)")
    for s in sorted(ds.saas.values(), key=lambda s: s["slug"]):
        if s.get("price_status") != "verified":
            continue
        d = age(s.get("verified_on"))
        flag = "STALE" if d is None or d > MAX_PRICE_DAYS else "ok"
        print(f"    {flag:<5} {s['slug']:<18} {s.get('verified_on')}  ({d} days)  {s['pricing_url']}")
        if flag != "ok":
            problems.append(f"price {s['slug']}")

    print(f"\n  Hosting prices (limit {MAX_PRICE_DAYS} days)")
    for p in ds.providers.values():
        d = age(p.get("verified_on"))
        status = p["price_status"]
        flag = "STALE" if status == "verified" and (d is None or d > MAX_PRICE_DAYS) else ("ok" if status == "verified" else "unpriced")
        print(f"    {flag:<8} {p['slug']:<14} {status:<10} {p.get('verified_on')}  {p['pricing_url']}")
        if flag == "STALE":
            problems.append(f"hosting {p['slug']}")

    d = age(ds.config["fx"]["on"])
    flag = "STALE" if d is None or d > MAX_FX_DAYS else "ok"
    print(f"\n  Exchange rate: {flag}  {ds.config['fx']['on']} ({d} days)")
    if flag != "ok":
        problems.append("fx rate")

    old_gh = [t["slug"] for t in ds.tools.values()
              if t.get("wave", 1) <= wave and t.get("repo")
              and (age(t.get("github_checked_on")) or 10**6) > MAX_GITHUB_DAYS]
    print(f"\n  GitHub facts older than {MAX_GITHUB_DAYS} days: {len(old_gh)}")
    if old_gh:
        print(f"    re-run: python scripts/enrich_github.py --only {','.join(old_gh)}")
        problems.append(f"github x{len(old_gh)}")

    archived = [t["slug"] for t in ds.tools.values() if t.get("archived")]
    if archived:
        print(f"\n  ARCHIVED repositories still in the dataset: {', '.join(archived)}")
        problems.append("archived repos")

    unverified_live = [s["slug"] for s in ds.saas.values()
                       if s.get("wave", 1) <= wave and s.get("price_status") != "verified"]
    print(f"\n  Unconfirmed prices in the current wave (pages withheld): {len(unverified_live)}")
    print(f"    {', '.join(sorted(unverified_live))}")

    print(f"\n  {'NOTHING STALE' if not problems else 'NEEDS ATTENTION: ' + ', '.join(problems)}\n")
    return 1 if (problems and args.fail) else 0


if __name__ == "__main__":
    sys.exit(main())
