"""
Static site generator for SelfHostCost.

    python scripts/build.py
    python scripts/build.py --wave 2          # publish a later wave
    python scripts/build.py --no-strict       # allow unverified prices (never for production)

Writes to docs/, which is what GitHub Pages serves. No build step beyond this
script and no JavaScript is required for any page to work.

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

from lib.model import (
    Dataset, compute_tco, gb, load_dataset, money, months, price_trust,
    priced_providers, saas_monthly, saas_tier, size_for, cheapest_plan, tier_native,
)
import lib.content as content

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
TODAY = date.today().isoformat()


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def jsonld_article(cfg: dict, page: dict, crumbs: list[dict]) -> str:
    base_url = cfg["base_url"]
    graph = [
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": c["name"],
                 "item": base_url + c["url"] if c.get("url") else base_url + page["url"]}
                for i, c in enumerate(crumbs)
            ],
        },
        {
            "@type": "Article",
            "headline": page["title"][:110],
            "description": page["description"],
            "url": base_url + page["url"],
            "datePublished": TODAY,
            "dateModified": TODAY,
            "isAccessibleForFree": True,
            "author": {"@type": "Organization", "name": cfg["brand"], "url": base_url + "/"},
            "publisher": {"@type": "Organization", "name": cfg["brand"], "url": base_url + "/"},
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


class Builder:
    def __init__(self, ds: Dataset, strict: bool, wave: int):
        self.ds = ds
        self.cfg = ds.config
        self.strict = strict
        self.wave = wave
        self.base = self.cfg["base_path"].rstrip("/")
        self.ref_users = int(self.cfg.get("reference_users", 10))
        self.sizes = self.cfg["team_sizes"]
        self.ref_size = next(s for s in self.sizes if s["users"] == self.ref_users)
        self.urls: list[tuple[str, str]] = []          # (url, priority)
        self.skipped: list[dict] = []
        self.affiliate_on = self._affiliate_on()

        self.env = Environment(
            loader=FileSystemLoader(str(ROOT / "templates")),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True, lstrip_blocks=True,
        )
        self.env.globals.update(
            cfg=self.cfg, base=self.base, money=money, gb=gb, months=months,
            nav_categories=[c for c in self.ds.categories.values() if c["wave"] <= self.wave],
            providers=self.ds.providers, hosting_link=self.hosting_link,
            affiliate_on=self.affiliate_on,
        )

    # ---- config-driven links -------------------------------------------

    def _affiliate_on(self) -> bool:
        aff = self.cfg.get("affiliate", {})
        if not aff.get("enabled"):
            return False
        return any(p.get("id") for p in aff.get("providers", {}).values())

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

    # ---- writing --------------------------------------------------------

    def write(self, url: str, template: str, ctx: dict, priority: str = "0.6") -> None:
        page = ctx["page"]
        page.setdefault("url", url)
        if page.get("crumbs"):
            page["jsonld"] = Markup(jsonld_article(self.cfg, page, page["crumbs"]))
        html = self.env.get_template(template).render(**ctx)
        dest = OUT / (url.lstrip("/") or "") / "index.html" if url != "/" else OUT / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        self.urls.append((url, priority))

    def skip(self, kind: str, ident: str, reason: str) -> None:
        self.skipped.append({"kind": kind, "id": ident, "reason": reason})

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

    # ---- page builders --------------------------------------------------

    def build_comparisons(self, pairs) -> list[dict]:
        built = []
        by_cat: dict[str, list[dict]] = {}
        for tool, product in pairs:
            slug = f"{product['slug']}-vs-{tool['slug']}"
            by_cat.setdefault(tool["category"], []).append(
                {"url": f"/vs/{slug}/", "name": f"{product['name']} vs {tool['name']}"}
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
                    "saas": money(r.saas_usd_month), "sh": money(r.selfhost_usd_month),
                    "sh_nl": money(r.selfhost_usd_month_no_labour),
                    "plan": f"{r.plan.plan['name']} ({gb(r.plan.plan['ram_gb'])})",
                    "delta": ("+" if r.savings_total > 0 else "") + money(r.savings_total),
                    "delta_pos": r.savings_total > 0,
                })

            tier = ref.saas_tier
            per, flat, cur = tier_native(tier)
            if product["billing_model"] == "free":
                price_label = "free at the standard tier"
            elif per is not None:
                price_label = f"{cur} {per:,.2f} per seat per month"
            else:
                price_label = f"{cur} {flat:,.2f} per month"

            page = {
                "title": f"{product['name']} vs self-hosted {tool['name']}: real cost at {self.ref_size['label']} ({date.today().year})",
                "description": (
                    f"{product['name']} costs {money(ref.saas_usd_month)} a month at {self.ref_size['label']}; "
                    f"self-hosting {tool['name']} costs {money(ref.selfhost_usd_month)} including the server, "
                    f"backups and maintenance time. Full breakdown at every team size."
                )[:300],
                "url": url, "og_type": "article",
                "crumbs": [
                    {"name": "Home", "url": "/"},
                    {"name": cat["name"], "url": f"/category/{cat['slug']}/"},
                    {"name": f"{product['name']} vs {tool['name']}", "url": url},
                ],
            }

            ctx = {
                "page": page, "tool": tool, "saas": product, "category": cat,
                "ref": ref, "rows": rows, "flip_at": flip_at,
                "never_flips": flip_at is None,
                "saas_price_label": price_label,
                "fx_used": self.fx_used(product),
                "siblings": [s for s in by_cat.get(tool["category"], []) if s["url"] != url][:6],
                **self.hosting_ctx(tool, self.ref_users, self.ref_size["label"]),
            }
            self.write(url, "vs.html", ctx, "0.9")
            built.append({"tool": tool, "saas": product, "tco": ref, "url": url})
        return built

    def build_alternatives(self, pairs) -> None:
        by_saas: dict[str, list[dict]] = {}
        for tool, product in pairs:
            by_saas.setdefault(product["slug"], []).append(tool)

        for saas_slug, tools in by_saas.items():
            product = self.ds.saas[saas_slug]
            cat = self.ds.categories[product["category"]]
            url = f"/alternatives/{saas_slug}/"
            alts = []
            for tool in tools:
                t = compute_tco(self.ds, tool, product, self.ref_users)
                if t:
                    alts.append({"tool": tool, "tco": t})
            alts.sort(key=lambda a: a["tco"].selfhost_usd_month)
            saas_month, tier, _ = saas_monthly(product, self.ref_users, self.cfg)

            page = {
                "title": f"Self-hosted {product['name']} alternatives, with real costs ({date.today().year})",
                "description": (
                    f"{len(alts)} open-source alternatives to {product['name']}, each priced at "
                    f"{self.ref_size['label']} including the server, backups and maintenance time. "
                    f"{product['name']} costs {money(saas_month)} a month at that size."
                )[:300],
                "url": url, "og_type": "article",
                "crumbs": [
                    {"name": "Home", "url": "/"},
                    {"name": cat["name"], "url": f"/category/{cat['slug']}/"},
                    {"name": f"{product['name']} alternatives", "url": url},
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
                "title": f"Self-hosting {tool['name']}: cost by team size ({date.today().year})",
                "description": (
                    f"What it costs to self-host {tool['name']} from one user to 250: memory and disk "
                    f"needed, the cheapest server plan that fits, backups, and the hours it takes to run."
                )[:300],
                "url": url, "og_type": "article",
                "crumbs": [
                    {"name": "Home", "url": "/"},
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
            page = {
                "title": f"Cost to self-host {tool['name']} for {s['users']} {'user' if s['users'] == 1 else 'users'}",
                "description": (
                    f"{tool['name']} for {s['users']} users needs {gb(sizing.ram_gb)} of memory and "
                    f"{gb(sizing.disk_gb)} of disk, which is {money(plan.price_usd_month)} a month of server. "
                    f"All in, with backups and maintenance time, {money(total)} a month."
                )[:300],
                "url": url, "og_type": "article",
                "prev_url": f"/cost/{tool['slug']}/{self.sizes[i-1]['slug']}/" if i else None,
                "next_url": f"/cost/{tool['slug']}/{self.sizes[i+1]['slug']}/" if i + 1 < len(self.sizes) else None,
                "crumbs": [
                    {"name": "Home", "url": "/"},
                    {"name": tool["name"], "url": f"/self-host/{tool['slug']}/"},
                    {"name": f"{s['users']} users", "url": url},
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
        m = self.cfg["tco_model"]
        comps_by_cat: dict[str, list[dict]] = {}
        for c in built_comparisons:
            comps_by_cat.setdefault(c["tool"]["category"], []).append(
                {"url": c["url"], "name": f"{c['saas']['name']} vs {c['tool']['name']}"}
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
                "title": f"Self-hosted {cat['name'].lower()}: costs compared ({date.today().year})",
                "description": f"{cat['intent']} {len(tools)} self-hosted options priced at {self.ref_size['label']}, against the commercial products they replace."[:300],
                "url": url,
                "crumbs": [{"name": "Home", "url": "/"}, {"name": cat["name"], "url": url}],
            }
            self.write(url, "category.html", {
                "page": page, "category": cat, "tools": tools, "paid": paid,
                "comparisons": sorted(comps_by_cat.get(cat["slug"], []), key=lambda x: x["name"]),
                "ref_label": self.ref_size["label"],
                "siblings": [c for c in live_cats if c["slug"] != cat["slug"]],
            }, "0.7")

    def build_providers(self) -> None:
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
                "title": f"{prov['name']} for self-hosting: plans and pricing ({date.today().year})",
                "description": f"{prov['name']} plans with vCPU, memory, disk and transfer, and which self-hosted tools fit on each at {self.ref_size['label']}."[:300],
                "url": url,
                "crumbs": [{"name": "Home", "url": "/"}, {"name": "Hosting", "url": "/hosting/"}, {"name": prov["name"], "url": url}],
            }
            self.write(url, "provider.html", {
                "page": page, "provider": prov, "plan_rows": plan_rows,
                "ref_label": self.ref_size["label"],
                "siblings": [p for p in provs if p["slug"] != prov["slug"]],
            }, "0.6")

    def build_indexes(self, built_comparisons) -> None:
        # /compare/
        groups: dict[str, list[dict]] = {}
        for c in sorted(built_comparisons, key=lambda x: x["saas"]["name"]):
            cat = self.ds.categories[c["tool"]["category"]]["name"]
            groups.setdefault(cat, []).append({
                "url": c["url"], "name": f"{c['saas']['name']} vs {c['tool']['name']}",
                "badge": None if c["tco"].savings_total > 0 else "paid wins",
                "badge_class": "warn",
            })
        self.write("/compare/", "listing.html", {
            "page": {
                "title": f"Every SaaS versus self-hosted cost comparison ({date.today().year})",
                "description": f"{len(built_comparisons)} comparisons between commercial software and its self-hosted alternative, each priced from a published sizing model and dated vendor prices.",
                "url": "/compare/",
                "crumbs": [{"name": "Home", "url": "/"}, {"name": "Comparisons", "url": "/compare/"}],
            },
            "listing": {
                "heading": "Every comparison",
                "lead": f"{len(built_comparisons)} paid products priced against their self-hosted alternatives at {self.ref_size['label']}. Anything tagged as paid-wins is a case where self-hosting costs more once your time is counted.",
                "groups": [{"name": k, "links":v} for k, v in sorted(groups.items())],
            },
        }, "0.8")

        # /self-host/
        tgroups: dict[str, list[dict]] = {}
        for tool in sorted(self.live_tools(), key=lambda t: t["name"].lower()):
            cat = self.ds.categories[tool["category"]]["name"]
            tgroups.setdefault(cat, []).append({
                "url": f"/self-host/{tool['slug']}/", "name": tool["name"],
                "badge": tool["difficulty"], "badge_class": "warn" if tool["difficulty"] == "hard" else "",
            })
        self.write("/self-host/", "listing.html", {
            "page": {
                "title": f"Every self-hosted tool we price ({date.today().year})",
                "description": "Self-hosted open-source tools with a published sizing model and a real monthly cost at every team size from one user to 250.",
                "url": "/self-host/",
                "crumbs": [{"name": "Home", "url": "/"}, {"name": "Tools", "url": "/self-host/"}],
            },
            "listing": {
                "heading": "Every tool we price",
                "lead": "Each tool has a sizing model, the cheapest server plan that fits it at each team size, and an honest estimate of the hours it takes to run. The badge is how heavy it is to operate.",
                "groups": [{"name": k, "links":v} for k, v in sorted(tgroups.items())],
            },
        }, "0.8")

        # /hosting/
        self.write("/hosting/", "listing.html", {
            "page": {
                "title": "Hosting providers for self-hosting, and which prices we trust",
                "description": "The hosting providers behind every cost figure on this site, which of their prices we have read ourselves, and which we have not.",
                "url": "/hosting/",
                "crumbs": [{"name": "Home", "url": "/"}, {"name": "Hosting", "url": "/hosting/"}],
            },
            "listing": {
                "heading": "Hosting providers",
                "lead": "Every server cost on this site comes from a provider in this list. Only the ones marked as confirmed feed a published figure.",
                "groups": [{
                    "name": "Providers",
                    "links":[{
                        "url": f"/hosting/{p['slug']}/", "name": p["name"],
                        "badge": "prices confirmed" if p["price_status"] == "verified" else "prices unconfirmed",
                        "badge_class": "ok" if p["price_status"] == "verified" else "warn",
                    } for p in self.ds.providers.values()],
                }],
                "note": "A provider marked as unconfirmed has specifications we trust and prices we could not read programmatically. Rather than estimate, we leave it out of the maths and say so on its page.",
            },
        }, "0.6")

    def build_static(self, built_comparisons, pairs) -> None:
        for slug, title, desc, body in content.static_pages(self.ds, self.wave, self.strict, built_comparisons, pairs):
            url = f"/{slug}/"
            self.write(url, "page.html", {
                "page": {
                    "title": title, "description": desc, "url": url,
                    "crumbs": [{"name": "Home", "url": "/"}, {"name": title.split(":")[0], "url": url}],
                },
                "body": Markup(body),
            }, "0.5")

    def build_home(self, built_comparisons) -> None:
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
                "title": f"{self.cfg['brand']} - what self-hosting actually costs, per tool and team size",
                "description": self.cfg["description"],
                "url": "/",
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

    # ---- site plumbing --------------------------------------------------

    def build_plumbing(self) -> None:
        base_url = self.cfg["base_url"]
        entries = "\n".join(
            f"  <url><loc>{base_url}{u}</loc><lastmod>{TODAY}</lastmod><priority>{p}</priority></url>"
            for u, p in sorted(set(self.urls))
        )
        (OUT / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{entries}\n</urlset>\n", encoding="utf-8")

        (OUT / "robots.txt").write_text(
            f"User-agent: *\nAllow: /\n\nSitemap: {base_url}/sitemap.xml\n", encoding="utf-8")

        (OUT / ".nojekyll").write_text("", encoding="utf-8")

        (OUT / "favicon.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
            '<rect width="32" height="32" rx="7" fill="#16604a"/>'
            '<path d="M8 21.5h4.2l1.6-5.2 2.1 7.2 2.3-11 1.7 6.4h4.4" fill="none" stroke="#fff" '
            'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>\n',
            encoding="utf-8")

        notfound = self.env.get_template("page.html").render(
            page={"title": "Page not found", "description": "That page does not exist.",
                  "url": "/404.html", "robots": "noindex"},
            body=Markup(
                "<h1>Page not found</h1><p>That URL does not exist on this site.</p>"
                f'<p><a href="{self.base}/compare/">All comparisons</a> &middot; '
                f'<a href="{self.base}/self-host/">All tools</a> &middot; '
                f'<a href="{self.base}/">Home</a></p>'
            ),
        )
        (OUT / "404.html").write_text(notfound, encoding="utf-8")

        dest = OUT / "assets"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(ROOT / "assets", dest)

    # ---- orchestration --------------------------------------------------

    def run(self) -> dict:
        if OUT.exists():
            keep = {}
            for name in ("CNAME",):
                f = OUT / name
                if f.exists():
                    keep[name] = f.read_text(encoding="utf-8")
            shutil.rmtree(OUT)
            OUT.mkdir(parents=True)
            for name, text in keep.items():
                (OUT / name).write_text(text, encoding="utf-8")
        else:
            OUT.mkdir(parents=True)

        pairs = self.publishable_pairs()
        built = self.build_comparisons(pairs)
        self.build_alternatives(pairs)
        self.build_tool_pages(pairs)
        self.build_categories(built)
        self.build_providers()
        self.build_indexes(built)
        self.build_static(built, pairs)
        self.build_home(built)
        self.build_plumbing()

        report = {
            "built_on": TODAY,
            "wave": self.wave,
            "strict_prices": self.strict,
            "reference_users": self.ref_users,
            "pages": len(self.urls),
            "comparisons": len(built),
            "tools_live": len(self.live_tools()),
            "affiliate_links_active": self.affiliate_on,
            "lead_capture_active": bool(self.cfg["lead_capture"]["enabled"] and self.cfg["lead_capture"]["form_id"]),
            "priced_providers": [p["slug"] for p in priced_providers(self.ds)],
            "verified_saas": sorted(s["slug"] for s in self.ds.saas.values() if s.get("price_status") == "verified"),
            "unverified_saas": sorted(s["slug"] for s in self.ds.saas.values() if s.get("price_status") != "verified"),
            "skipped": self.skipped,
            "urls": [u for u, _ in sorted(set(self.urls))],
        }
        (ROOT / "ops" / "build-report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return report


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

    wave = args.wave if args.wave is not None else int(ds.config["publish_wave"])
    strict = not args.no_strict and bool(ds.config["strict_prices"])

    report = Builder(ds, strict=strict, wave=wave).run()

    print(f"\n  wave {report['wave']}  strict={report['strict_prices']}  reference={report['reference_users']} users")
    print(f"  {report['pages']} pages written to docs/")
    print(f"  {report['comparisons']} comparison pages, {report['tools_live']} tools live")
    print(f"  hosting prices trusted: {', '.join(report['priced_providers']) or 'NONE'}")
    print(f"  vendor prices confirmed: {len(report['verified_saas'])} of "
          f"{len(report['verified_saas']) + len(report['unverified_saas'])}")
    print(f"  affiliate links: {'active' if report['affiliate_links_active'] else 'not configured'}"
          f"   lead capture: {'active' if report['lead_capture_active'] else 'not configured'}")

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
