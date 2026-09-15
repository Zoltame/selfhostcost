"""Stable publication dates for every page.

Pages are rendered with placeholder dates, hashed, and compared with the ledger
in ops/page-dates.json. A page keeps its dates until its content changes, so a
rebuild with no real change does not tell search engines every page was updated.
"""

import hashlib
import json
from pathlib import Path

PUBLISHED = "__SHC_DATE_PUBLISHED__"
MODIFIED = "__SHC_DATE_MODIFIED__"


class DateLedger:
    def __init__(self, path: Path, today: str, first_run_date: str):
        self.path = path
        self.today = today
        self.existing = path.exists()
        self.old = json.loads(path.read_text(encoding="utf-8")) if self.existing else {}
        # Without a ledger, pages already live are dated to the launch, not to this build.
        self.first_run_date = first_run_date
        self.new: dict[str, dict] = {}

    def stamp(self, url: str, html: str) -> str:
        digest = hashlib.sha256(html.encode("utf-8")).hexdigest()[:16]
        prev = self.old.get(url)
        if prev and prev["hash"] == digest:
            entry = prev
        elif prev:
            entry = {"published": prev["published"], "modified": self.today, "hash": digest}
        elif not self.existing:
            entry = {"published": self.first_run_date, "modified": self.first_run_date, "hash": digest}
        else:
            entry = {"published": self.today, "modified": self.today, "hash": digest}
        self.new[url] = entry
        return html.replace(PUBLISHED, entry["published"]).replace(MODIFIED, entry["modified"])

    def modified(self, url: str) -> str:
        return self.new[url]["modified"]

    def save(self) -> None:
        self.path.write_text(json.dumps(self.new, indent=1, sort_keys=True) + "\n", encoding="utf-8")
