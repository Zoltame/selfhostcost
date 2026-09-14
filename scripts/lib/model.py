"""
Data loading, validation and the TCO engine for SelfHostCost.

Design rules that the rest of the codebase depends on:

1. No figure is invented at render time. Every number on a page is either read
   from data/ or computed here from data/ by a documented formula.
2. A price that has not been read from the vendor's own page carries
   price_status "seed". In strict mode the build refuses to publish any page
   whose headline figure depends on a seed price.
3. Sizing is RAM- and disk-bound. vCPU is carried through from the project's
   own baseline and is not scaled with team size, because for these stacks
   memory is what forces the upgrade. This is stated on the methodology page.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------

def _read(name: str) -> dict:
    with open(DATA / name, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_config() -> dict:
    with open(ROOT / "site.config.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


@dataclass
class Dataset:
    config: dict
    categories: dict[str, dict]
    saas: dict[str, dict]
    tools: dict[str, dict]
    providers: dict[str, dict]
    warnings: list[str] = field(default_factory=list)

    def tools_in_category(self, slug: str) -> list[dict]:
        return sorted(
            (t for t in self.tools.values() if t["category"] == slug),
            key=lambda t: (t.get("stars") or 0),
            reverse=True,
        )

    def saas_in_category(self, slug: str) -> list[dict]:
        return [s for s in self.saas.values() if s["category"] == slug]

    def alternatives_for(self, saas_slug: str) -> list[dict]:
        return sorted(
            (t for t in self.tools.values() if saas_slug in t.get("replaces", [])),
            key=lambda t: (t.get("stars") or 0),
            reverse=True,
        )


def load_dataset() -> Dataset:
    config = load_config()
    cats = {c["slug"]: c for c in _read("categories.json")["categories"]}
    saas = {s["slug"]: s for s in _read("saas.json")["products"]}
    tools = {t["slug"]: t for t in _read("selfhosted.json")["tools"]}
    providers = {p["slug"]: p for p in _read("providers.json")["providers"]}

    ds = Dataset(config=config, categories=cats, saas=saas, tools=tools, providers=providers)
    validate(ds)
    return ds


def validate(ds: Dataset) -> None:
    """Structural integrity only. Price trust is enforced separately, per page."""
    for slug, tool in ds.tools.items():
        if tool["category"] not in ds.categories:
            ds.warnings.append(f"tool {slug}: unknown category {tool['category']}")
        for ref in tool.get("replaces", []):
            if ref not in ds.saas:
                ds.warnings.append(f"tool {slug}: replaces unknown saas '{ref}'")
        for key in ("base_ram_gb", "ram_per_user_mb", "base_disk_gb", "disk_per_user_gb", "base_vcpu"):
            if key not in tool:
                ds.warnings.append(f"tool {slug}: missing sizing key {key}")
        if tool.get("difficulty") not in ("easy", "medium", "hard"):
            ds.warnings.append(f"tool {slug}: bad difficulty {tool.get('difficulty')}")

    for slug, product in ds.saas.items():
        if product["category"] not in ds.categories:
            ds.warnings.append(f"saas {slug}: unknown category {product['category']}")
        if product["billing_model"] not in ("per_seat_month", "flat_month", "free"):
            ds.warnings.append(f"saas {slug}: unsupported billing_model {product['billing_model']}")
        if not product.get("tiers"):
            ds.warnings.append(f"saas {slug}: no tiers")

    for slug, prov in ds.providers.items():
        for plan in prov.get("plans", []):
            if plan.get("price_usd_month") is not None and prov["price_status"] != "verified":
                ds.warnings.append(
                    f"provider {slug} plan {plan['id']}: has a price but provider price_status is "
                    f"'{prov['price_status']}'. Flip the provider to verified or clear the price."
                )


# --------------------------------------------------------------------------
# sizing
# --------------------------------------------------------------------------

@dataclass
class Sizing:
    users: int
    raw_ram_gb: float
    ram_gb: float          # with headroom applied
    disk_gb: float
    vcpu: int
    headroom_ratio: float


def size_for(tool: dict, users: int, config: dict) -> Sizing:
    m = config["tco_model"]
    headroom = m["ram_headroom_ratio"]
    raw = tool["base_ram_gb"] + (tool["ram_per_user_mb"] * users) / 1024.0
    return Sizing(
        users=users,
        raw_ram_gb=round(raw, 2),
        ram_gb=round(raw * (1 + headroom), 2),
        disk_gb=round(tool["base_disk_gb"] + tool["disk_per_user_gb"] * users, 1),
        vcpu=int(tool["base_vcpu"]),
        headroom_ratio=headroom,
    )


@dataclass
class PlanChoice:
    provider_slug: str
    provider_name: str
    plan: dict
    price_usd_month: float
    fits_disk: bool


def priced_providers(ds: Dataset) -> list[dict]:
    """Providers whose prices are allowed to feed a published figure."""
    out = []
    for p in ds.providers.values():
        if p["price_status"] != "verified":
            continue
        if any(pl.get("price_usd_month") is not None for pl in p.get("plans", [])):
            out.append(p)
    return out


def cheapest_plan(ds: Dataset, sizing: Sizing) -> PlanChoice | None:
    """Smallest verified-price plan that satisfies both RAM and disk."""
    best: PlanChoice | None = None
    for prov in priced_providers(ds):
        for plan in prov["plans"]:
            price = plan.get("price_usd_month")
            if price is None:
                continue
            if plan["ram_gb"] < sizing.ram_gb:
                continue
            if plan["disk_gb"] < sizing.disk_gb:
                continue
            cand = PlanChoice(prov["slug"], prov["name"], plan, float(price), True)
            if best is None or cand.price_usd_month < best.price_usd_month:
                best = cand
    return best


# --------------------------------------------------------------------------
# SaaS side
# --------------------------------------------------------------------------

def saas_tier(product: dict) -> dict:
    want = product.get("compare_tier")
    for t in product["tiers"]:
        if t["name"] == want:
            return t
    return product["tiers"][-1]


def tier_native(tier: dict) -> tuple[float | None, float | None, str]:
    """Pulls the price out of a tier in whatever currency the vendor served.

    Returns (per_seat, flat, currency). Exactly one of per_seat / flat is set
    for a priced tier.
    """
    for cur in ("usd", "eur", "gbp"):
        per = tier.get(f"{cur}_per_seat_month")
        if per is not None:
            return float(per), None, cur.upper()
        flat = tier.get(f"{cur}_month")
        if flat is not None:
            return None, float(flat), cur.upper()
    return None, None, tier.get("currency", "USD")


def to_usd(amount: float, currency: str, config: dict) -> float:
    rate = config.get("fx", {}).get("rates_to_usd", {}).get(currency)
    if rate is None:
        raise ValueError(
            f"No dated exchange rate configured for {currency}. Add one to site.config.json "
            f"rather than guessing, or the published figure is not reproducible."
        )
    return amount * float(rate)


def saas_monthly(product: dict, users: int, config: dict) -> tuple[float, dict, str]:
    """Returns (monthly USD, tier used, human explanation).

    Handles, in order: products that are free outright, free plans capped at a
    seat count, volume-banded per-seat prices read at each team size, flat
    prices, per-seat prices with a seat minimum, and a minimum monthly spend
    (for vendors that sell on an annual contract floor).
    """
    tier = saas_tier(product)
    model = product["billing_model"]

    if model == "free":
        return 0.0, tier, "No licence cost at the standard tier."

    free_cap = product.get("free_up_to_seats")
    if free_cap and users <= int(free_cap):
        return 0.0, tier, (
            f"{product['name']}'s own free plan covers teams of up to {free_cap} users, "
            f"so a team of {users} pays nothing for the licence."
        )

    price_source = tier
    band_note = ""
    bands = tier.get("seat_bands")
    if bands:
        chosen = None
        for band in bands:
            cap = band.get("max_seats")
            if cap is None or users <= int(cap):
                chosen = band
                break
        if chosen is None:
            chosen = bands[-1]
        price_source = chosen
        band_note = (
            f" {product['name']} lowers the per-user price as teams grow; this is the rate its "
            f"pricing page showed for a team of this size."
        )

    per_native, flat_native, cur = tier_native(price_source)
    basis = tier.get("billing_basis")
    basis_note = ""
    if basis == "annual":
        basis_note = " This is the annually-billed rate, which is what the vendor's page displayed; paying monthly costs more."
    elif basis == "unstated":
        basis_note = " The vendor's page did not say whether this figure is the monthly or the annual rate."
    fx_note = ""
    if cur != "USD":
        fx_note = f" The vendor quoted {cur}, converted at the dated rate on the methodology page."

    if model == "flat_month":
        if flat_native is None:
            raise ValueError(f"saas {product['slug']}: flat_month tier '{tier['name']}' has no flat price")
        usd = to_usd(flat_native, cur, config)
        return usd, tier, (
            f"{product['name']} {tier['name']} is a flat {money(usd)} a month at this tier, "
            f"independent of seat count.{basis_note}{fx_note}"
        )

    if per_native is None:
        raise ValueError(f"saas {product['slug']}: per_seat tier '{tier['name']}' has no per-seat price")

    seats = max(users, int(tier.get("min_seats") or 1))
    per_usd = to_usd(per_native, cur, config)
    total = seats * per_usd
    note = f"{seats} seats at {money(per_usd)} each"
    if seats != users:
        note += f", because the {tier['name']} tier has a {tier['min_seats']}-seat minimum"

    floor_native = tier.get("min_month")
    if floor_native is not None:
        floor_usd = to_usd(float(floor_native), cur, config)
        if total < floor_usd:
            total = floor_usd
            note += (
                f", raised to {money(floor_usd)} a month because {product['name']} requires a minimum "
                f"contract of that value"
            )
    return total, tier, note + f".{band_note}{basis_note}{fx_note}"


# --------------------------------------------------------------------------
# TCO
# --------------------------------------------------------------------------

@dataclass
class Tco:
    users: int
    sizing: Sizing
    plan: PlanChoice
    horizon_months: int

    server_usd_month: float
    backup_usd_month: float
    labour_usd_month: float
    selfhost_usd_month: float          # incl. labour
    selfhost_usd_month_no_labour: float
    setup_usd_once: float
    setup_hours: float
    maintenance_hours_month: float

    saas_usd_month: float
    saas_tier: dict
    saas_explain: str

    saas_total: float
    selfhost_total: float
    selfhost_total_no_labour: float
    savings_total: float
    savings_total_no_labour: float
    breakeven_months: float | None
    breakeven_months_no_labour: float | None
    verdict: str
    is_free_saas: bool


def compute_tco(ds: Dataset, tool: dict, product: dict, users: int) -> Tco | None:
    cfg = ds.config
    m = cfg["tco_model"]
    sizing = size_for(tool, users, cfg)
    plan = cheapest_plan(ds, sizing)
    if plan is None:
        return None

    difficulty = tool["difficulty"]
    setup_hours = m["setup_hours_by_difficulty"][difficulty]
    maint_hours = m["maintenance_hours_per_month_by_difficulty"][difficulty]
    rate = float(m["engineer_hourly_usd"])
    horizon = int(m["horizon_months"])

    server = plan.price_usd_month
    backup = round(server * float(m["backup_cost_ratio"]), 2)
    labour = round(maint_hours * rate, 2)
    sh_month = round(server + backup + labour, 2)
    sh_month_nl = round(server + backup, 2)
    setup_once = round(setup_hours * rate, 2)

    saas_month, tier, explain = saas_monthly(product, users, cfg)
    is_free = saas_month == 0

    saas_total = round(saas_month * horizon, 2)
    sh_total = round(setup_once + sh_month * horizon, 2)
    sh_total_nl = round(sh_month_nl * horizon, 2)

    def be(monthly_sh: float, onetime: float) -> float | None:
        delta = saas_month - monthly_sh
        if delta <= 0:
            return None
        return round(onetime / delta, 1)

    breakeven = be(sh_month, setup_once)
    breakeven_nl = be(sh_month_nl, 0.0)

    savings = round(saas_total - sh_total, 2)
    savings_nl = round(saas_total - sh_total_nl, 2)

    if is_free:
        verdict = "no_cost_case"
    elif savings > 0:
        verdict = "selfhost_cheaper"
    elif savings_nl > 0:
        verdict = "selfhost_cheaper_only_without_labour"
    else:
        verdict = "saas_cheaper"

    return Tco(
        users=users, sizing=sizing, plan=plan, horizon_months=horizon,
        server_usd_month=server, backup_usd_month=backup, labour_usd_month=labour,
        selfhost_usd_month=sh_month, selfhost_usd_month_no_labour=sh_month_nl,
        setup_usd_once=setup_once, setup_hours=setup_hours, maintenance_hours_month=maint_hours,
        saas_usd_month=round(saas_month, 2), saas_tier=tier, saas_explain=explain,
        saas_total=saas_total, selfhost_total=sh_total, selfhost_total_no_labour=sh_total_nl,
        savings_total=savings, savings_total_no_labour=savings_nl,
        breakeven_months=breakeven, breakeven_months_no_labour=breakeven_nl,
        verdict=verdict, is_free_saas=is_free,
    )


# --------------------------------------------------------------------------
# trust gate
# --------------------------------------------------------------------------

def price_trust(ds: Dataset, product: dict) -> dict:
    """Whether a page built on this SaaS product may publish a headline figure."""
    provs = priced_providers(ds)
    return {
        "saas_verified": product.get("price_status") == "verified",
        "saas_verified_on": product.get("verified_on"),
        "hosting_verified": bool(provs),
        "hosting_sources": [{"name": p["name"], "url": p["pricing_url"], "on": p["verified_on"]} for p in provs],
        "publishable": product.get("price_status") == "verified" and bool(provs),
    }


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)


def money(v: float) -> str:
    if v is None:
        return "n/a"
    sign = "-" if v < 0 else ""
    a = abs(v)
    if a >= 100:
        return f"{sign}${a:,.0f}"
    return f"{sign}${a:,.2f}"


def gb(v: float) -> str:
    if v >= 1024:
        return f"{v / 1024:.1f} TB"
    if float(v).is_integer():
        return f"{int(v)} GB"
    return f"{v:.1f} GB"


def months(v: float | None) -> str:
    if v is None:
        return "never"
    if v < 1:
        return "under a month"
    if v < 24:
        return f"{v:.0f} months" if v >= 2 else "about a month"
    return f"{v / 12:.1f} years"
