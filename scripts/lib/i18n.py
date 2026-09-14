"""
Languages, locale-aware formatting and translation overlays for SelfHostCost.

Every language renders the same computed figures. Costs are computed once, in
US dollars, by lib.model. A Locale only changes how a number is written and,
for euro locales, converts it at the single dated rate that the methodology
page publishes. No figure is re-derived per language.

Text comes from three places:
  i18n/ui/<lang>.json        short interface strings with {placeholders}
  data/i18n/<lang>.json      translated descriptive fields of the dataset
  templates/<lang>/          page prose, written natively per language
English is the source for all three; a missing translation falls back to
English and is counted in the build report rather than silently shipped.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI_DIR = ROOT / "i18n" / "ui"
DATA_DIR = ROOT / "data" / "i18n"

DEFAULT_LANG = "en"
ORDER = ["en", "fr", "de", "es"]

LANGUAGES: dict[str, dict] = {
    "en": {"name": "English", "prefix": "", "currency": "USD", "og_locale": "en_US",
           "thousands": ",", "decimal": ".", "unit_gb": "GB", "unit_tb": "TB"},
    "fr": {"name": "Français", "prefix": "/fr", "currency": "EUR", "og_locale": "fr_FR",
           "thousands": " ", "decimal": ",", "unit_gb": "Go", "unit_tb": "To"},
    "de": {"name": "Deutsch", "prefix": "/de", "currency": "EUR", "og_locale": "de_DE",
           "thousands": ".", "decimal": ",", "unit_gb": "GB", "unit_tb": "TB"},
    "es": {"name": "Español", "prefix": "/es", "currency": "USD", "og_locale": "es_ES",
           "thousands": ".", "decimal": ",", "unit_gb": "GB", "unit_tb": "TB"},
}

# Dataset fields that are displayed on a page and therefore need translating.
# Fields that never reach a page are deliberately left out.
TEXT_FIELDS: dict[str, tuple[str, ...]] = {
    "categories": ("name", "intent"),
    "tools": ("sizing_note", "licence_caveat", "compatible_clients", "description_gh"),
    "saas": ("free_tier_note",),
    "providers": ("hq", "billing_note", "price_note", "strengths", "weaknesses"),
}


class MissingTranslation(KeyError):
    pass


def load_ui(lang: str) -> dict[str, str]:
    path = UI_DIR / f"{lang}.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


class Locale:
    def __init__(self, lang: str, config: dict, strict: bool = False):
        if lang not in LANGUAGES:
            raise ValueError(f"unsupported language {lang}")
        self.lang = lang
        self.meta = LANGUAGES[lang]
        self.config = config
        self.strict = strict
        self.fallback = load_ui(DEFAULT_LANG)
        self.ui = load_ui(lang)
        self.missing: set[str] = set()
        self.currency = self.meta["currency"]
        self.usd_per_eur = float(config["fx"]["rates_to_usd"]["EUR"])

    # ---- text -----------------------------------------------------------

    def t(self, key: str, **kw) -> str:
        if key in self.ui:
            text = self.ui[key]
        elif key in self.fallback:
            if self.lang != DEFAULT_LANG:
                self.missing.add(key)
                if self.strict:
                    raise MissingTranslation(f"{self.lang}: {key}")
            text = self.fallback[key]
        else:
            raise MissingTranslation(f"no string for key '{key}' in any language")
        return text.format(**kw) if kw else text

    def join(self, items: list[str]) -> str:
        return self.t("list.sep").join(items)

    # ---- numbers --------------------------------------------------------

    def number(self, v: float, decimals: int = 0) -> str:
        s = f"{abs(v):,.{decimals}f}"
        s = s.replace(",", "\x00").replace(".", self.meta["decimal"]).replace("\x00", self.meta["thousands"])
        return ("-" if v < 0 else "") + s

    def compact(self, v: float) -> str:
        """3.0 -> 3, 0.5 -> 0.5 (or 0,5), 1.25 -> 1.25."""
        v = float(v)
        if v.is_integer():
            return self.number(v, 0)
        if round(v, 1) == v:
            return self.number(v, 1)
        return self.number(v, 2)

    def to_display(self, usd: float) -> float:
        return usd / self.usd_per_eur if self.currency == "EUR" else usd

    def money(self, usd: float | None) -> str:
        if usd is None:
            return "n/a"
        v = self.to_display(usd)
        decimals = 0 if abs(v) >= 100 else 2
        sign = "-" if v < 0 else ""
        digits = self.number(abs(v), decimals)
        if self.lang == DEFAULT_LANG:
            return f"{sign}${digits}"
        if self.currency == "EUR":
            return f"{sign}{digits} €"
        return f"{sign}{digits} US$"

    def rate(self, usd_per_hour: float) -> str:
        """An hourly rate, shown in the locale currency."""
        return self.money(usd_per_hour)

    def native(self, amount: float, currency: str) -> str:
        """A vendor price in the currency the vendor quoted, for source tables."""
        return self.t("price.native", currency=currency, amount=self.number(amount, 2))

    def gb(self, v: float) -> str:
        if v >= 1024:
            return f"{self.number(v / 1024, 1)} {self.meta['unit_tb']}"
        if float(v).is_integer():
            return f"{int(v)} {self.meta['unit_gb']}"
        return f"{self.number(v, 1)} {self.meta['unit_gb']}"

    def months(self, v: float | None) -> str:
        if v is None:
            return self.t("months.never")
        if v < 1:
            return self.t("months.under_one")
        if v < 24:
            if v >= 2:
                return self.t("months.n", n=f"{v:.0f}")
            return self.t("months.about_one")
        return self.t("years.n", n=self.number(v / 12, 1))

    def hours(self, v: float) -> str:
        return self.compact(v)

    def size_label(self, users: int) -> str:
        return self.t("size.1") if users == 1 else self.t("size.n", n=users)

    # ---- urls -----------------------------------------------------------

    def path(self, url: str) -> str:
        """Site-relative URL for this language, e.g. /vs/x/ -> /fr/vs/x/."""
        return f"{self.meta['prefix']}{url}"


def load_overlay(lang: str) -> dict:
    path = DATA_DIR / f"{lang}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def localize_dataset(ds, lang: str):
    """Returns (dataset with translated text fields, list of missing field paths).

    Numbers, slugs, URLs and product names are never touched. English returns
    the dataset unchanged.
    """
    if lang == DEFAULT_LANG:
        return ds, []

    overlay = load_overlay(lang)
    out = copy.copy(ds)
    missing: list[str] = []

    for section, fields in TEXT_FIELDS.items():
        items = copy.deepcopy(getattr(ds, section))
        translated = overlay.get(section, {})
        for slug, item in items.items():
            entry = translated.get(slug, {})
            for field in fields:
                if item.get(field) in (None, "", []):
                    continue
                if field in entry and entry[field] not in (None, "", []):
                    item[field] = entry[field]
                else:
                    missing.append(f"{section}.{slug}.{field}")
        setattr(out, section, items)

    return out, missing
