"""
Enriches data/selfhosted.json with facts pulled from the GitHub API.

Everything this writes is an observable fact about a repository, never an
opinion: stars, licence, primary language, last push, archived flag, release
tag. Uses the authenticated `gh` CLI so the rate limit is 5000 requests an
hour rather than 60.

    python scripts/enrich_github.py            # enrich all
    python scripts/enrich_github.py --dry-run  # show what would change

Fields written carry a github_checked_on date so the staleness audit can see
how old they are.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "selfhosted.json"

FIELDS = (
    "stars", "license", "license_spdx", "language", "last_push",
    "archived", "open_issues", "latest_release", "description_gh",
    "github_checked_on",
)


def gh_api(path: str) -> dict | None:
    try:
        out = subprocess.run(
            ["gh", "api", path],
            capture_output=True, text=True, timeout=45, check=False,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"    ! {path}: {exc}")
        return None
    if out.returncode != 0:
        msg = (out.stderr or "").strip().splitlines()
        print(f"    ! {path}: {msg[0] if msg else 'failed'}")
        return None
    try:
        return json.loads(out.stdout or "null")
    except json.JSONDecodeError:
        return None


def fetch(repo: str) -> dict | None:
    meta = gh_api(f"repos/{repo}")
    if not meta:
        return None

    lic = meta.get("license") or {}
    rec = {
        "stars": meta.get("stargazers_count"),
        "license": lic.get("name"),
        "license_spdx": lic.get("spdx_id"),
        "language": meta.get("language"),
        "last_push": (meta.get("pushed_at") or "")[:10] or None,
        "archived": bool(meta.get("archived")),
        "open_issues": meta.get("open_issues_count"),
        "description_gh": meta.get("description"),
        "github_checked_on": date.today().isoformat(),
    }

    rel = gh_api(f"repos/{repo}/releases/latest")
    rec["latest_release"] = (rel or {}).get("tag_name")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="comma-separated tool slugs")
    args = ap.parse_args()

    doc = json.loads(TARGET.read_text(encoding="utf-8"))
    only = {s.strip() for s in args.only.split(",")} if args.only else None

    ok = failed = 0
    for tool in doc["tools"]:
        if only and tool["slug"] not in only:
            continue
        repo = tool.get("repo")
        if not repo:
            continue
        print(f"  {tool['slug']:<16} {repo}")
        rec = fetch(repo)
        if rec is None:
            failed += 1
            continue
        ok += 1
        if rec.get("archived"):
            print(f"    ! {tool['slug']} is ARCHIVED on GitHub - review before publishing")
        # The curated 'language' in the dataset wins over GitHub's guess only
        # when GitHub returns nothing; otherwise trust the API.
        if not rec.get("language"):
            rec.pop("language")
        tool.update(rec)

    print(f"\n  enriched {ok}, failed {failed}")
    if args.dry_run:
        print("  --dry-run: nothing written")
        return 0

    TARGET.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
