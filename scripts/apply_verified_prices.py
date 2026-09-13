"""
One-shot patch that writes the SaaS prices read from vendor pricing pages on
2026-09-12 into data/saas.json and flips those products to price_status
"verified".

Kept in the repository on purpose: it is the audit trail for where each
published number came from. Re-running it is idempotent. When a price is
re-checked later, add a new block here rather than editing history, so the
provenance of every figure stays readable.

Prices are recorded in the currency the vendor's page actually served, along
with whether the figure was the monthly-billed or annually-billed rate.
Mixing an annual rate into a monthly comparison without saying so is the most
common way these comparisons mislead, so billing_basis is mandatory.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "saas.json"
ON = "2026-09-12"

VERIFIED = {
    "1password": {
        "pricing_url": "https://1password.com/business-pricing",
        "compare_tier": "Business",
        "billing_model": "per_seat_month",
        "tiers": [
            {"name": "Teams Starter Pack", "usd_month": 24.95, "currency": "USD",
             "billing_basis": "annual", "max_seats": 10,
             "note": "Flat rate covering 10 members. Additional seats are $4.99 each per month on annual billing, up to 10 more."},
            {"name": "Business", "usd_per_seat_month": 8.99, "currency": "USD",
             "billing_basis": "annual",
             "note": "$107.88 per user per year. The page did not display a separate monthly-billed rate."},
        ],
    },
    "notion": {
        "pricing_url": "https://www.notion.com/pricing",
        "compare_tier": "Business",
        "billing_model": "per_seat_month",
        "tiers": [
            {"name": "Plus", "eur_per_seat_month": 9.50, "currency": "EUR", "billing_basis": "monthly"},
            {"name": "Business", "eur_per_seat_month": 19.50, "currency": "EUR", "billing_basis": "monthly"},
        ],
        "note": "Notion served this pricing page in euros. The figures are converted to US dollars using the dated reference rate published on the methodology page.",
    },
    "zapier": {
        "pricing_url": "https://zapier.com/pricing",
        "compare_tier": "Professional",
        "billing_model": "flat_month",
        "tiers": [
            {"name": "Professional", "usd_month": 29.99, "currency": "USD", "billing_basis": "monthly",
             "note": "750 tasks a month. $19.99 a month on annual billing."},
            {"name": "Team", "usd_month": 103.50, "currency": "USD", "billing_basis": "monthly",
             "note": "2,000 tasks a month and unlimited users. $69.00 a month on annual billing."},
        ],
        "note": "Zapier bills by task volume, not by seat. The comparison holds the plan fixed and shows what the same monthly spend buys as a server, which is the honest way to read it.",
    },
    "typeform": {
        "pricing_url": "https://www.typeform.com/pricing/",
        "compare_tier": "Plus",
        "billing_model": "flat_month",
        "tiers": [
            {"name": "Basic", "usd_month": 28.0, "currency": "USD", "billing_basis": "monthly",
             "note": "Capped at 100 responses a month, which is what pushes most teams up a tier. $25 a month on annual billing."},
            {"name": "Plus", "usd_month": 56.0, "currency": "USD", "billing_basis": "monthly",
             "note": "1,000 responses a month. $50 a month on annual billing."},
            {"name": "Business", "usd_month": 91.0, "currency": "USD", "billing_basis": "monthly",
             "note": "10,000 responses a month. $83 a month on annual billing."},
        ],
    },
    "zendesk": {
        "pricing_url": "https://www.zendesk.com/pricing/",
        "compare_tier": "Suite Team",
        "billing_model": "per_seat_month",
        "tiers": [
            {"name": "Suite Team", "eur_per_seat_month": 55.0, "currency": "EUR", "billing_basis": "annual"},
            {"name": "Suite Professional", "eur_per_seat_month": 115.0, "currency": "EUR", "billing_basis": "annual"},
        ],
        "note": "Read from the European storefront, which Zendesk redirected to, and quoted in euros on annual billing. The Suite Growth tier that older comparisons cite no longer appears on the price list.",
    },
    "statuspage": {
        "pricing_url": "https://www.atlassian.com/software/statuspage/pricing",
        "compare_tier": "Startup",
        "billing_model": "flat_month",
        "tiers": [
            {"name": "Hobby", "usd_month": 29.0, "currency": "USD", "billing_basis": "monthly",
             "note": "250 subscribers, 5 team members."},
            {"name": "Startup", "usd_month": 99.0, "currency": "USD", "billing_basis": "monthly",
             "note": "1,000 subscribers, 10 team members."},
            {"name": "Business", "usd_month": 399.0, "currency": "USD", "billing_basis": "monthly",
             "note": "5,000 subscribers, 25 team members."},
        ],
        "note": "Statuspage prices by subscriber count and team members rather than by seat, and a free tier covers 100 subscribers.",
        "free_tier_note": "A free tier covers 100 subscribers, 25 components and two team members. Below that ceiling there is nothing to save.",
    },
    "auth0": {
        "pricing_url": "https://auth0.com/pricing",
        "compare_tier": "Essentials (B2B)",
        "billing_model": "flat_month",
        "tiers": [
            {"name": "Essentials (B2C)", "usd_month": 35.0, "currency": "USD", "billing_basis": "monthly",
             "note": "500 monthly active users included."},
            {"name": "Essentials (B2B)", "usd_month": 150.0, "currency": "USD", "billing_basis": "monthly",
             "note": "500 monthly active users, with organisations and enterprise connections."},
            {"name": "Professional (B2C)", "usd_month": 240.0, "currency": "USD", "billing_basis": "monthly"},
        ],
        "note": "Auth0 bills monthly active users, not seats, so team size is a poor proxy and the page says so.",
        "free_tier_note": "Auth0's free tier covers up to 25,000 monthly active users. Below that ceiling, and without needing the paid B2B features, self-hosting an identity provider saves nothing at all. The paid comparison below only applies once you need what the Essentials tier adds.",
    },
}


def main() -> None:
    doc = json.loads(TARGET.read_text(encoding="utf-8"))
    by_slug = {p["slug"]: p for p in doc["products"]}

    for slug, patch in VERIFIED.items():
        product = by_slug.get(slug)
        if product is None:
            print(f"  ! {slug} not present in saas.json")
            continue
        product.update(patch)
        product["price_status"] = "verified"
        product["verified_on"] = ON
        print(f"  verified {slug:<14} tier={patch['compare_tier']}")

    still_seed = [p["slug"] for p in doc["products"] if p.get("price_status") != "verified"]
    print(f"\n  verified: {len(doc['products']) - len(still_seed)} / {len(doc['products'])}")
    print(f"  still seed (blocked from publication in strict mode): {', '.join(still_seed)}")

    TARGET.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
