"""
Static site generator for SelfHostCost.

    python scripts/build.py
    python scripts/build.py --wave 2          # publish a later wave
    python scripts/build.py --no-strict       # allow unverified prices (never for production)

Writes to docs/, which is what GitHub Pages serves. No build step beyond this
script and no JavaScript is required for any page to work.

Languages: every language listed in site.config.json "languages" is rendered
from the same computed figures. English sits at the site root and every other
language under /<lang>/, with identical slugs so hreflang alternates always
point at a page that exists. Page prose lives in templates/<lang>/, shared
structure in templates/shared/, short strings in i18n/ui/<lang>.json and
translated dataset text in data/i18n/<lang>.json.

Publication gates, in order:
  1. A tool must be in the current wave.
  2. A comparison page additionally requires the commercial product's price to
     have been read from the vendor's page, and at least one hosting provider
     with a verified price. In strict mode a failure here skips the page and
     records the reason in the build report rather than guessing a number.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from lib.i18n import DEFAULT_LANG, LANGUAGES, Locale, localize_dataset
from lib.model import (
    Dataset, cheapest_plan, compute_tco, load_dataset, price_trust, priced_providers,
    saas_monthly, saas_tier, size_for, tier_native,
)
import lib.content as content
from lib.dates import MODIFIED, PUBLISHED, DateLedger

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
TEMPLATES = ROOT / "templates"
TODAY = date.today().isoformat()
YEAR = date.today().year


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def jsonld_article(cfg: dict, page: dict, crumbs: list[dict], loc: Locale, multilingual: bool) -> str:
    base_url = cfg["base_url"]
    article = {
        "@type": "Article",
        "headline": page["title"][:110],
        "description": page["description"],
        "url": base_url + page["url"],
        "datePublished": PUBLISHED,
        "dateModified": MODIFIED,
        "isAccessibleForFree": True,
        "author": {"@type": "Organization", "name": cfg["brand"], "url": base_url + "/"},
        "publisher": {"@type": "Organization", "name": cfg["brand"], "url": base_url + "/"},
    }
    if multilingual:
        article["inLanguage"] = loc.lang
    graph = [
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": c["name"],
                 "item": base_url + loc.path(c["url"]) if c.get("url") else base_url + page["url"]}
                for i, c in enumerate(crumbs)
            ],
        },
        article,
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


class Builder:
    """Renders every page of the site in one language."""

    def __init__(self, ds: Dataset, strict: bool, wave: int, lang: str, languages: list[str],
                 ledger: DateLedger):
        self.ledger = ledger
        self.lang = lang
        self.languages = languages
        self.multilingual = len(languages) > 1
        self.loc = Locale(lang, ds.config)
        self.ds, missing = localize_dataset(ds, lang)
        self.cfg = ds.config
        self.strict = strict
        self.wave = wave

        prefix = self.loc.meta["prefix"]
        self.root = self.cfg["base_path"].rstrip("/")
        self.base = self.root + prefix
        self.out = OUT / prefix.lstrip("/") if prefix else OUT

        self.ref_users = int(self.cfg.get("reference_users", 10))
        self.sizes = [dict(s, label=self.loc.size_label(s["users"])) for s in self.cfg["team_sizes"]]
        self.ref_size = next(s for s in self.sizes if s["users"] == self.ref_users)
        self.urls: list[tuple[str, str]] = []          # (language-neutral url, priority)
        self.skipped: list[dict] = []
        self.affiliate_on = self._affiliate_on()
        self.missing_data = [m for m in missing if self._is_live_field(m)]

        self.env = Environment(
            loader=FileSystemLoader([str(TEMPLATES / lang), str(TEMPLATES / "shared")]),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True, lstrip_blocks=True,
        )
        L = self.loc
        self.env.globals.update(
            cfg=self.cfg, base=self.base, root=self.root, lang=lang, loc=L, t=L.t,
            money=L.money, gb=L.gb, months=L.months, hours=L.hours, number=L.number,
            nav_categories=[c for c in self.ds.categories.values() if c["wave"] <= self.wave],
            providers=self.ds.providers, hosting_link=self.hosting_link,
            affiliate_on=self.affiliate_on, lead_form_id=self._lead_form_id(),
        )

    # ---- config-driven links -------------------------------------------

    def _affiliate_on(self) -> bool:
        aff = self.cfg.get("affiliate", {})
        if not aff.get("enabled"):
            return False
        return any(p.get("id") for p in aff.get("providers", {}).values())

    def _lead_form_id(self) -> str | None:
        """The Tally form for this language, or None so no form is rendered.

        A language without its own form gets no form at all, rather than an
        English form that redirects to the English checklist.
        """
        lc = self.cfg.get("lead_capture", {})
        if not lc.get("enabled"):
            return None
        ids = lc.get("form_ids") or {}
        if ids.get(self.lang):
            return ids[self.lang]
        if self.lang == DEFAULT_LANG:
            return lc.get("form_id") or None
        return None

    def hosting_link(self, provider_slug: str) -> str:
        """Affiliate URL when an ID is configured, otherwise the plain vendor page.

        Never fabricates a tracking parameter: a missing ID falls back cleanly.
        """
        prov = self.ds.providers.get(provider_slug, {})
        plain = prov.get("pricing_url") or prov.get("site") or "/"
        aff = self.cfg.get("affiliate", {})
        if not aff.get("enabled"):
            return plain
        entry = aff.get("providers", {}).get(provider_slug) or {}
        if entry.get("id") and entry.get("template"):
            return entry["template"].replace("{id}", entry["id"])
        return plain

    def unpriced_provider_names(self) -> list[str]:
        return [p["name"] for p in self.ds.providers.values() if p["price_status"] != "verified"]

    def _is_live_field(self, path: str) -> bool:
        section, slug = path.split(".")[:2]
        if section == "categories":
            return self.ds.categories[slug]["wave"] <= self.wave
        if section == "tools":
            return self.ds.tools[slug].get("wave", 1) <= self.wave
        if section == "saas":
            p = self.ds.saas[slug]
            return p.get("wave", 1) <= self.wave and p.get("price_status") == "verified"
        return True

    # ---- writing --------------------------------------------------------

    def write(self, url: str, template: str, ctx: dict, priority: str = "0.6") -> None:
        page = ctx["page"]
        page["path"] = url
        page["url"] = self.loc.path(url)
        for key in ("prev_url", "next_url"):
            if page.get(key):
                page[key] = self.loc.path(page[key])
        if self.multilingual:
            base_url = self.cfg["base_url"]
            page["alternates"] = [
                {"lang": l, "name": LANGUAGES[l]["name"], "current": l == self.lang,
                 "href": base_url + LANGUAGES[l]["prefix"] + url}
                for l in self.languages
            ]
            page["x_default"] = base_url + LANGUAGES[DEFAULT_LANG]["prefix"] + url
            page["og_locale"] = self.loc.meta["og_locale"]
        if page.get("crumbs"):
            page["jsonld"] = Markup(jsonld_article(self.cfg, page, page["crumbs"], self.loc, self.multilingual))
        html = self.ledger.stamp(page["url"], self.env.get_template(template).render(**ctx))
        dest = self.out / url.lstrip("/") / "index.html" if url != "/" else self.out / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        self.urls.append((url, priority))

    def skip(self, kind: str, ident: str, reason: str) -> None:
        self.skipped.append({"kind": kind, "id": ident, "reason": reason})

    def crumb_home(self) -> dict:
        return {"name": self.loc.t("crumb.home"), "url": "/"}

    # ---- gating ---------------------------------------------------------

    def live_tools(self) -> list[dict]:
        return [t for t in self.ds.tools.values() if t.get("wave", 1) <= self.wave]

    def publishable_pairs(self) -> list[tuple[dict, dict]]:
        """(tool, saas) pairs that clear every gate."""
        pairs = []
        for tool in self.live_tools():
            for saas_slug in tool.get("replaces", []):
                product = self.ds.saas[saas_slug]
                if product.get("wave", 1) > self.wave:
                    self.skip("comparison", f"{saas_slug}-vs-{tool['slug']}", f"product is wave {product.get('wave')}")
                    continue
                trust = price_trust(self.ds, product)
                if self.strict and not trust["publishable"]:
                    why = "price not read from vendor page" if not trust["saas_verified"] else "no hosting provider with a verified price"
                    self.skip("comparison", f"{saas_slug}-vs-{tool['slug']}", why)
                    continue
                if compute_tco(self.ds, tool, product, self.ref_users) is None:
                    self.skip("comparison", f"{saas_slug}-vs-{tool['slug']}", "no server plan fits the sizing")
                    continue
                pairs.append((tool, product))
        return pairs

    # ---- shared context -------------------------------------------------

    def hosting_ctx(self, tool: dict, users: int, label: str) -> dict:
        sizing = size_for(tool, users, self.cfg)
        plan = cheapest_plan(self.ds, sizing)
        return {
            "sizing_ram": sizing.ram_gb, "sizing_disk": sizing.disk_gb,
            "cta_label": label, "cta_plan": plan,
            "unpriced_providers": self.unpriced_provider_names(),
        }

    def fx_used(self, product: dict) -> bool:
        _, _, cur = tier_native(saas_tier(product))
        return cur != "USD"

    def price_label(self, product: dict, tier: dict) -> str:
        L = self.loc
        per, flat, cur = tier_native(tier)
        if product["billing_model"] == "free":
            label = L.t("price_label.free")
        elif tier.get("seat_bands"):
            parts = []
            for band in tier["seat_bands"]:
                b_per, _, b_cur = tier_native(band)
                price = L.native(b_per, b_cur)
                cap = band.get("max_seats")
                parts.append(L.t("price_label.band", price=price, cap=cap) if cap else L.t("price_label.band_last", price=price))
            label = L.t("price_label.bands", bands=L.join(parts))
        elif per is not None:
            label = L.t("price_label.per_seat", price=L.native(per, cur))
        elif flat is not None:
            label = L.t("price_label.flat", price=L.native(flat, cur))
        else:
            label = L.t("price_label.unknown")
        if tier.get("min_month") is not None:
            label += L.t("price_label.min", price=L.native(float(tier["min_month"]), cur))
        if product.get("free_up_to_seats"):
            label += L.t("price_label.free_cap", n=product["free_up_to_seats"])
        return label

    # ---- page builders --------------------------------------------------

    def build_comparisons(self, pairs) -> list[dict]:
        L = self.loc
        built = []
        by_cat: dict[str, list[dict]] = {}
        for tool, product in pairs:
            slug = f"{product['slug']}-vs-{tool['slug']}"
            by_cat.setdefault(tool["category"], []).append(
                {"url": f"/vs/{slug}/", "name": L.t("vs.crumb", saas=product["name"], tool=tool["name"])}
            )

        for tool, product in pairs:
            cat = self.ds.categories[tool["category"]]
            slug = f"{product['slug']}-vs-{tool['slug']}"
            url = f"/vs/{slug}/"
            ref = compute_tco(self.ds, tool, product, self.ref_users)
            ref.label = self.ref_size["label"]

            rows, flip_at = [], None
            for s in self.sizes:
                r = compute_tco(self.ds, tool, product, s["users"])
                if r is None:
                    continue
                if flip_at is None and r.verdict == "selfhost_cheaper":
                    flip_at = s["label"]
                rows.append({
                    "users": s["users"], "slug": s["slug"], "label": s["label"],
                    "saas": L.money(r.saas_usd_month), "sh": L.money(r.selfhost_usd_month),
                    "sh_nl": L.money(r.selfhost_usd_month_no_labour),
                    "plan": L.t("vs.plan_cell", plan=r.plan.plan["name"], ram=L.gb(r.plan.plan["ram_gb"])),
                    "delta": ("+" if r.savings_total > 0 else "") + L.money(r.savings_total),
                    "delta_pos": r.savings_total > 0,
                })

            page = {
                "title": L.t("vs.title", saas=product["name"], tool=tool["name"], size=self.ref_size["label"], year=YEAR),
                "description": L.t(
                    "vs.description", saas=product["name"], tool=tool["name"], size=self.ref_size["label"],
                    saas_cost=L.money(ref.saas_usd_month), sh_cost=L.money(ref.selfhost_usd_month),
                )[:300],
                "og_type": "article",
                "crumbs": [
                    self.crumb_home(),
                    {"name": cat["name"], "url": f"/category/{cat['slug']}/"},
                    {"name": L.t("vs.crumb", saas=product["name"], tool=tool["name"]), "url": url},
                ],
            }

            ctx = {
                "page": page, "tool": tool, "saas": product, "category": cat,
                "ref": ref, "rows": rows, "flip_at": flip_at,
                "never_flips": flip_at is None,
                "saas_price_label": self.price_label(product, ref.saas_tier),
                "fx_used": self.fx_used(product),
                "siblings": [s for s in by_cat.get(tool["category"], []) if s["url"] != url][:6],
                **self.hosting_ctx(tool, self.ref_users, self.ref_size["label"]),
            }
            self.write(url, "vs.html", ctx, "0.9")
            built.append({"tool": tool, "saas": product, "tco": ref, "url": url})
        return built

    def build_alternatives(self, pairs) -> None:
        L = self.loc
        by_saas: dict[str, list[dict]] = {}
        for tool, product in pairs:
            by_saas.setdefault(product["slug"], []).append(tool)

        for saas_slug, tools in by_saas.items():
            product = self.ds.saas[saas_slug]
            cat = self.ds.categories[product["category"]]
            if cat["wave"] > self.wave:
                # The product's own category is not published yet; file the page
                # under the category of the tools that replace it instead.
                cat = self.ds.categories[tools[0]["category"]]
            url = f"/alternatives/{saas_slug}/"
            alts = []
            for tool in tools:
                t = compute_tco(self.ds, tool, product, self.ref_users)
                if t:
                    alts.append({"tool": tool, "tco": t})
            alts.sort(key=lambda a: a["tco"].selfhost_usd_month)
            saas_month, tier, _ = saas_monthly(product, self.ref_users, self.cfg)

            page = {
                "title": L.t("alt.title", saas=product["name"], year=YEAR),
                "description": L.t(
                    "alt.description", n=len(alts), saas=product["name"], size=self.ref_size["label"],
                    cost=L.money(saas_month),
                )[:300],
                "og_type": "article",
                "crumbs": [
                    self.crumb_home(),
                    {"name": cat["name"], "url": f"/category/{cat['slug']}/"},
                    {"name": L.t("alt.crumb", saas=product["name"]), "url": url},
                ],
            }
            self.write(url, "alternatives.html", {
                "page": page, "saas": product, "category": cat, "alts": alts,
                "ref_label": self.ref_size["label"], "saas_month": saas_month,
                "saas_tier": tier, "saas_fx": self.fx_used(product),
                "sibling_saas": [s for s in self.ds.saas_in_category(cat["slug"])
                                 if s["slug"] != saas_slug and s["slug"] in by_saas][:5],
            }, "0.8")

    def build_tool_pages(self, pairs) -> None:
        L = self.loc
        pairs_by_tool: dict[str, list[dict]] = {}
        for tool, product in pairs:
            pairs_by_tool.setdefault(tool["slug"], []).append(product)

        m = self.cfg["tco_model"]
        for tool in self.live_tools():
            cat = self.ds.categories[tool["category"]]
            url = f"/self-host/{tool['slug']}/"

            rows = []
            for s in self.sizes:
                sizing = size_for(tool, s["users"], self.cfg)
                plan = cheapest_plan(self.ds, sizing)
                if plan is None:
                    continue
                maint = m["maintenance_hours_per_month_by_difficulty"][tool["difficulty"]]
                total = plan.price_usd_month * (1 + m["backup_cost_ratio"]) + maint * m["engineer_hourly_usd"]
                rows.append({
                    "slug": s["slug"], "label": s["label"], "ram": sizing.ram_gb, "disk": sizing.disk_gb,
                    "plan_name": plan.plan["name"], "provider": plan.provider_name,
                    "server": plan.price_usd_month, "total": round(total, 2),
                })
            if not rows:
                self.skip("tool", tool["slug"], "no server plan fits at any team size")
                continue

            replaced = []
            for product in pairs_by_tool.get(tool["slug"], []):
                t = compute_tco(self.ds, tool, product, self.ref_users)
                if t:
                    replaced.append({"saas": product, "tco": t})
            replaced.sort(key=lambda r: -r["tco"].saas_usd_month)

            page = {
                "title": L.t("sh.title", tool=tool["name"], year=YEAR),
                "description": L.t("sh.description", tool=tool["name"])[:300],
                "og_type": "article",
                "crumbs": [
                    self.crumb_home(),
                    {"name": cat["name"], "url": f"/category/{cat['slug']}/"},
                    {"name": tool["name"], "url": url},
                ],
            }
            self.write(url, "selfhost.html", {
                "page": page, "tool": tool, "category": cat, "rows": rows,
                "replaced": replaced, "ref_label": self.ref_size["label"],
                "headroom": m["ram_headroom_ratio"],
                "setup_hours": m["setup_hours_by_difficulty"][tool["difficulty"]],
                "maint_hours": m["maintenance_hours_per_month_by_difficulty"][tool["difficulty"]],
                "siblings": [t for t in self.ds.tools_in_category(cat["slug"])
                             if t["slug"] != tool["slug"] and t.get("wave", 1) <= self.wave][:5],
                **self.hosting_ctx(tool, self.ref_users, self.ref_size["label"]),
            }, "0.8")

            self.build_cost_pages(tool, cat, pairs_by_tool.get(tool["slug"], []))

    def build_cost_pages(self, tool: dict, cat: dict, products: list[dict]) -> None:
        L = self.loc
        m = self.cfg["tco_model"]
        setup_hours = m["setup_hours_by_difficulty"][tool["difficulty"]]
        maint_hours = m["maintenance_hours_per_month_by_difficulty"][tool["difficulty"]]
        rate = m["engineer_hourly_usd"]

        for i, s in enumerate(self.sizes):
            sizing = size_for(tool, s["users"], self.cfg)
            plan = cheapest_plan(self.ds, sizing)
            if plan is None:
                self.skip("cost", f"{tool['slug']}/{s['slug']}", "no server plan fits the sizing")
                continue

            backup = round(plan.price_usd_month * m["backup_cost_ratio"], 2)
            labour = round(maint_hours * rate, 2)
            url = f"/cost/{tool['slug']}/{s['slug']}/"

            comparisons = []
            for product in products:
                t = compute_tco(self.ds, tool, product, s["users"])
                if t:
                    comparisons.append({"saas": product, "tco": t})
            comparisons.sort(key=lambda c: -c["tco"].saas_usd_month)

            total = round(plan.price_usd_month + backup + labour, 2)
            title_key = "cost.title.one" if s["users"] == 1 else "cost.title.many"
            page = {
                "title": L.t(title_key, tool=tool["name"], n=s["users"]),
                "description": L.t(
                    "cost.description", tool=tool["name"], n=s["users"],
                    ram=L.gb(sizing.ram_gb), disk=L.gb(sizing.disk_gb),
                    server=L.money(plan.price_usd_month), total=L.money(total),
                )[:300],
                "og_type": "article",
                "prev_url": f"/cost/{tool['slug']}/{self.sizes[i-1]['slug']}/" if i else None,
                "next_url": f"/cost/{tool['slug']}/{self.sizes[i+1]['slug']}/" if i + 1 < len(self.sizes) else None,
                "crumbs": [
                    self.crumb_home(),
                    {"name": tool["name"], "url": f"/self-host/{tool['slug']}/"},
                    {"name": L.t("cost.crumb", n=s["users"]), "url": url},
                ],
            }
            self.write(url, "cost.html", {
                "page": page, "tool": tool, "category": cat, "size": s, "sizing": sizing, "plan": plan,
                "backup_month": backup, "labour_month": labour, "total_month": total,
                "no_labour_month": round(plan.price_usd_month + backup, 2),
                "setup_once": round(setup_hours * rate, 2),
                "setup_hours": setup_hours, "maint_hours": maint_hours,
                "per_user_ram_gb": round(tool["ram_per_user_mb"] * s["users"] / 1024.0, 2),
                "comparisons": comparisons, "all_sizes": self.sizes,
                "prev_size": self.sizes[i-1] if i else None,
                "next_size": self.sizes[i+1] if i + 1 < len(self.sizes) else None,
                **self.hosting_ctx(tool, s["users"], s["label"]),
            }, "0.6")

    def build_categories(self, built_comparisons) -> None:
        L = self.loc
        m = self.cfg["tco_model"]
        comps_by_cat: dict[str, list[dict]] = {}
        for c in built_comparisons:
            comps_by_cat.setdefault(c["tool"]["category"], []).append(
                {"url": c["url"], "name": L.t("vs.crumb", saas=c["saas"]["name"], tool=c["tool"]["name"])}
            )

        live_cats = [c for c in self.ds.categories.values() if c["wave"] <= self.wave]
        for cat in live_cats:
            url = f"/category/{cat['slug']}/"
            tools = []
            for tool in self.ds.tools_in_category(cat["slug"]):
                if tool.get("wave", 1) > self.wave:
                    continue
                sizing = size_for(tool, self.ref_users, self.cfg)
                plan = cheapest_plan(self.ds, sizing)
                if plan is None:
                    continue
                maint = m["maintenance_hours_per_month_by_difficulty"][tool["difficulty"]]
                tools.append({
                    "tool": tool, "ram": sizing.ram_gb, "server": plan.price_usd_month,
                    "total": round(plan.price_usd_month * (1 + m["backup_cost_ratio"]) + maint * m["engineer_hourly_usd"], 2),
                })
            if not tools:
                self.skip("category", cat["slug"], "no priced tools in the current wave")
                continue

            paid = []
            for product in self.ds.saas_in_category(cat["slug"]):
                if self.strict and product.get("price_status") != "verified":
                    continue
                if product.get("wave", 1) > self.wave:
                    continue
                amount, tier, _ = saas_monthly(product, self.ref_users, self.cfg)
                paid.append({"saas": product, "tier": tier, "month": amount})
            paid.sort(key=lambda p: -p["month"])

            page = {
                "title": L.t("cat.title", name=cat["name"], name_lower=cat["name"].lower(), year=YEAR),
                "description": L.t("cat.description", intent=cat["intent"], n=len(tools), size=self.ref_size["label"])[:300],
                "crumbs": [self.crumb_home(), {"name": cat["name"], "url": url}],
            }
            self.write(url, "category.html", {
                "page": page, "category": cat, "tools": tools, "paid": paid,
                "comparisons": sorted(comps_by_cat.get(cat["slug"], []), key=lambda x: x["name"]),
                "ref_label": self.ref_size["label"],
                "siblings": [c for c in live_cats if c["slug"] != cat["slug"]],
            }, "0.7")

    def build_providers(self) -> None:
        L = self.loc
        provs = list(self.ds.providers.values())
        for prov in provs:
            url = f"/hosting/{prov['slug']}/"
            plan_rows, claimed = [], set()
            for plan in sorted(prov.get("plans", []), key=lambda p: (p["ram_gb"], p["disk_gb"])):
                fits = []
                if prov["price_status"] == "verified":
                    for tool in self.live_tools():
                        if tool["slug"] in claimed:
                            continue
                        sizing = size_for(tool, self.ref_users, self.cfg)
                        if sizing.ram_gb <= plan["ram_gb"] and sizing.disk_gb <= plan["disk_gb"]:
                            fits.append({"slug": tool["slug"], "name": tool["name"]})
                            claimed.add(tool["slug"])
                plan_rows.append({"plan": plan, "fits": sorted(fits, key=lambda f: f["name"])})

            page = {
                "title": L.t("prov.title", name=prov["name"], year=YEAR),
                "description": L.t("prov.description", name=prov["name"], size=self.ref_size["label"])[:300],
                "crumbs": [
                    self.crumb_home(),
                    {"name": L.t("prov.crumb_hosting"), "url": "/hosting/"},
                    {"name": prov["name"], "url": url},
                ],
            }
            self.write(url, "provider.html", {
                "page": page, "provider": prov, "plan_rows": plan_rows,
                "ref_label": self.ref_size["label"],
                "siblings": [p for p in provs if p["slug"] != prov["slug"]],
            }, "0.6")

    def build_indexes(self, built_comparisons) -> None:
        L = self.loc
        n = len(built_comparisons)

        groups: dict[str, list[dict]] = {}
        for c in sorted(built_comparisons, key=lambda x: x["saas"]["name"]):
            cat = self.ds.categories[c["tool"]["category"]]["name"]
            groups.setdefault(cat, []).append({
                "url": c["url"], "name": L.t("vs.crumb", saas=c["saas"]["name"], tool=c["tool"]["name"]),
                "badge": None if c["tco"].savings_total > 0 else L.t("idx.compare.badge_paid_wins"),
                "badge_class": "warn",
            })
        self.write("/compare/", "listing.html", {
            "page": {
                "title": L.t("idx.compare.title", year=YEAR),
                "description": L.t("idx.compare.description", n=n),
                "crumbs": [self.crumb_home(), {"name": L.t("idx.compare.crumb"), "url": "/compare/"}],
            },
            "listing": {
                "heading": L.t("idx.compare.heading"),
                "lead": L.t("idx.compare.lead", n=n, size=self.ref_size["label"]),
                "groups": [{"name": k, "links": v} for k, v in sorted(groups.items())],
            },
        }, "0.8")

        tgroups: dict[str, list[dict]] = {}
        for tool in sorted(self.live_tools(), key=lambda t: t["name"].lower()):
            cat = self.ds.categories[tool["category"]]["name"]
            tgroups.setdefault(cat, []).append({
                "url": f"/self-host/{tool['slug']}/", "name": tool["name"],
                "badge": L.t(f"difficulty.{tool['difficulty']}"),
                "badge_class": "warn" if tool["difficulty"] == "hard" else "",
            })
        self.write("/self-host/", "listing.html", {
            "page": {
                "title": L.t("idx.tools.title", year=YEAR),
                "description": L.t("idx.tools.description"),
                "crumbs": [self.crumb_home(), {"name": L.t("idx.tools.crumb"), "url": "/self-host/"}],
            },
            "listing": {
                "heading": L.t("idx.tools.heading"),
                "lead": L.t("idx.tools.lead"),
                "groups": [{"name": k, "links": v} for k, v in sorted(tgroups.items())],
            },
        }, "0.8")

        self.write("/hosting/", "listing.html", {
            "page": {
                "title": L.t("idx.hosting.title"),
                "description": L.t("idx.hosting.description"),
                "crumbs": [self.crumb_home(), {"name": L.t("idx.hosting.crumb"), "url": "/hosting/"}],
            },
            "listing": {
                "heading": L.t("idx.hosting.heading"),
                "lead": L.t("idx.hosting.lead"),
                "groups": [{
                    "name": L.t("idx.hosting.group"),
                    "links": [{
                        "url": f"/hosting/{p['slug']}/", "name": p["name"],
                        "badge": L.t("idx.hosting.badge_ok") if p["price_status"] == "verified" else L.t("idx.hosting.badge_warn"),
                        "badge_class": "ok" if p["price_status"] == "verified" else "warn",
                    } for p in self.ds.providers.values()],
                }],
                "note": L.t("idx.hosting.note"),
            },
        }, "0.6")

    def build_static(self, built_comparisons, pairs) -> None:
        pages = content.static_pages(
            self.ds, self.wave, self.strict, built_comparisons, pairs, lang=self.lang, base=self.base,
        )
        for slug, title, desc, body in pages:
            url = f"/{slug}/"
            self.write(url, "page.html", {
                "page": {
                    "title": title, "description": desc,
                    "crumbs": [self.crumb_home(), {"name": title.split(":")[0], "url": url}],
                },
                "body": Markup(body),
            }, "0.5")

    def build_home(self, built_comparisons) -> None:
        L = self.loc
        wins = sorted([c for c in built_comparisons if c["tco"].savings_total > 0],
                      key=lambda c: -c["tco"].savings_total)
        losses = sorted([c for c in built_comparisons if c["tco"].savings_total <= 0],
                        key=lambda c: c["tco"].savings_total)
        verified = [s for s in self.ds.saas.values() if s.get("price_status") == "verified"]

        cats = []
        for cat in self.ds.categories.values():
            if cat["wave"] > self.wave:
                continue
            tool_count = len([t for t in self.ds.tools_in_category(cat["slug"]) if t.get("wave", 1) <= self.wave])
            if not tool_count:
                continue
            cats.append({
                "cat": cat, "tool_count": tool_count,
                "comparison_count": len([c for c in built_comparisons if c["tool"]["category"] == cat["slug"]]),
            })

        self.write("/", "home.html", {
            "page": {
                "title": L.t("home.title", brand=self.cfg["brand"]),
                "description": L.t("site.description"),
            },
            "stats": {
                "comparisons": len(built_comparisons),
                "tools": len(self.live_tools()),
                "verified_saas": len(verified),
                "verified_on": max((s.get("verified_on") or "") for s in verified) or TODAY,
                "saas_wins": len(losses),
            },
            "biggest": wins[:8], "honest": losses[:8], "categories": cats,
            "ref_label": self.ref_size["label"],
        }, "1.0")

    def render_404(self) -> str:
        L = self.loc
        return self.env.get_template("page.html").render(
            page={"title": L.t("404.title"), "description": L.t("404.description"),
                  "url": "/404.html", "robots": "noindex"},
            body=Markup(
                f"<h1>{L.t('404.heading')}</h1><p>{L.t('404.body')}</p>"
                f'<p><a href="{self.base}/compare/">{L.t("404.all_comparisons")}</a> &middot; '
                f'<a href="{self.base}/self-host/">{L.t("404.all_tools")}</a> &middot; '
                f'<a href="{self.base}/">{L.t("404.home")}</a></p>'
            ),
        )

    # ---- orchestration --------------------------------------------------

    def run(self) -> dict:
        pairs = self.publishable_pairs()
        built = self.build_comparisons(pairs)
        self.build_alternatives(pairs)
        self.build_tool_pages(pairs)
        self.build_categories(built)
        self.build_providers()
        self.build_indexes(built)
        self.build_static(built, pairs)
        self.build_home(built)
        return {
            "lang": self.lang,
            "pages": len(self.urls),
            "comparisons": len(built),
            "missing_ui_keys": sorted(self.loc.missing),
            "missing_data_fields": len(self.missing_data),
            "missing_data_sample": self.missing_data[:25],
            "lead_capture_active": bool(self._lead_form_id()),
        }


# --------------------------------------------------------------------------
# site-wide output
# --------------------------------------------------------------------------

def clean_out() -> None:
    keep = {}
    if OUT.exists():
        for name in ("CNAME",):
            f = OUT / name
            if f.exists():
                keep[name] = f.read_text(encoding="utf-8")
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for name, text in keep.items():
        (OUT / name).write_text(text, encoding="utf-8")


def write_plumbing(cfg: dict, builders: list[Builder]) -> None:
    base_url = cfg["base_url"]
    languages = [b.lang for b in builders]

    if len(languages) == 1:
        entries = "\n".join(
            f"  <url><loc>{base_url}{u}</loc><lastmod>{builders[0].ledger.modified(builders[0].loc.path(u))}</lastmod>"
            f"<priority>{p}</priority></url>"
            for u, p in sorted(set(builders[0].urls))
        )
        sitemap = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{entries}\n</urlset>\n"
        )
    else:
        lines = []
        for b in builders:
            for u, p in sorted(set(b.urls)):
                alts = "".join(
                    f'<xhtml:link rel="alternate" hreflang="{l}" href="{base_url}{LANGUAGES[l]["prefix"]}{u}"/>'
                    for l in languages
                )
                alts += f'<xhtml:link rel="alternate" hreflang="x-default" href="{base_url}{u}"/>'
                lines.append(
                    f"  <url><loc>{base_url}{b.loc.path(u)}</loc><lastmod>{b.ledger.modified(b.loc.path(u))}</lastmod>"
                    f"<priority>{p}</priority>{alts}</url>"
                )
        sitemap = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(lines) + "\n</urlset>\n"
        )
    (OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {base_url}/sitemap.xml\n", encoding="utf-8")

    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    (OUT / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<rect width="32" height="32" rx="7" fill="#16604a"/>'
        '<path d="M8 21.5h4.2l1.6-5.2 2.1 7.2 2.3-11 1.7 6.4h4.4" fill="none" stroke="#fff" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>\n',
        encoding="utf-8")

    default = next(b for b in builders if b.lang == DEFAULT_LANG)
    (OUT / "404.html").write_text(default.render_404(), encoding="utf-8")

    dest = OUT / "assets"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT / "assets", dest)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wave", type=int, default=None)
    ap.add_argument("--no-strict", action="store_true", help="publish pages built on unverified prices")
    args = ap.parse_args()

    ds = load_dataset()
    if ds.warnings:
        print("  data warnings:")
        for w in ds.warnings:
            print(f"    - {w}")

    cfg = ds.config
    wave = args.wave if args.wave is not None else int(cfg["publish_wave"])
    strict = not args.no_strict and bool(cfg["strict_prices"])
    languages = [l for l in cfg.get("languages", [DEFAULT_LANG]) if l in LANGUAGES]
    if DEFAULT_LANG not in languages:
        languages.insert(0, DEFAULT_LANG)

    clean_out()
    ledger = DateLedger(ROOT / "ops" / "page-dates.json", TODAY, cfg.get("launched_on", TODAY))
    builders, per_lang = [], []
    for lang in languages:
        b = Builder(ds, strict=strict, wave=wave, lang=lang, languages=languages, ledger=ledger)
        per_lang.append(b.run())
        builders.append(b)
    write_plumbing(cfg, builders)
    ledger.save()

    default = builders[0]
    report = {
        "built_on": TODAY,
        "wave": wave,
        "strict_prices": strict,
        "reference_users": default.ref_users,
        "languages": languages,
        "pages": sum(r["pages"] for r in per_lang),
        "comparisons": per_lang[0]["comparisons"],
        "tools_live": len(default.live_tools()),
        "affiliate_links_active": default.affiliate_on,
        "lead_capture_active": per_lang[0]["lead_capture_active"],
        "priced_providers": [p["slug"] for p in priced_providers(ds)],
        "verified_saas": sorted(s["slug"] for s in ds.saas.values() if s.get("price_status") == "verified"),
        "unverified_saas": sorted(s["slug"] for s in ds.saas.values() if s.get("price_status") != "verified"),
        "per_language": per_lang,
        "skipped": default.skipped,
        "urls": sorted(b.loc.path(u) for b in builders for u, _ in set(b.urls)),
    }
    (ROOT / "ops" / "build-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\n  wave {report['wave']}  strict={report['strict_prices']}  reference={report['reference_users']} users")
    print(f"  {report['pages']} pages written to docs/ across {len(languages)} language(s)")
    print(f"  {report['comparisons']} comparison pages, {report['tools_live']} tools live")
    print(f"  hosting prices trusted: {', '.join(report['priced_providers']) or 'NONE'}")
    print(f"  vendor prices confirmed: {len(report['verified_saas'])} of "
          f"{len(report['verified_saas']) + len(report['unverified_saas'])}")
    print(f"  affiliate links: {'active' if report['affiliate_links_active'] else 'not configured'}"
          f"   lead capture: {'active' if report['lead_capture_active'] else 'not configured'}")
    for r in per_lang:
        flags = []
        if r["missing_ui_keys"]:
            flags.append(f"{len(r['missing_ui_keys'])} interface strings fall back to English")
        if r["missing_data_fields"]:
            flags.append(f"{r['missing_data_fields']} data fields fall back to English")
        if not r["lead_capture_active"]:
            flags.append("no lead form")
        print(f"    [{r['lang']}] {r['pages']} pages" + (f"  ({'; '.join(flags)})" if flags else ""))

    if report["skipped"]:
        by_reason: dict[str, int] = {}
        for s in report["skipped"]:
            by_reason[s["reason"]] = by_reason.get(s["reason"], 0) + 1
        print(f"\n  {len(report['skipped'])} pages withheld:")
        for reason, n in sorted(by_reason.items(), key=lambda kv: -kv[1]):
            print(f"    {n:>4}  {reason}")
    print("\n  report: ops/build-report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
