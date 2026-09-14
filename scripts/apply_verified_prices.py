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


# ---------------------------------------------------------------------------
# Batch read on 2026-09-14. Free plans with a seat cap are recorded as
# free_up_to_seats, because a team inside that cap pays nothing and the page
# must say so rather than quote the paid tier.
# ---------------------------------------------------------------------------
ON_0914 = "2026-09-14"

VERIFIED_0914 = {
    "bitwarden": {
        "compare_tier": "Teams", "billing_model": "per_seat_month",
        "tiers": [
            {"name": "Teams", "usd_per_seat_month": 4.0, "currency": "USD", "billing_basis": "annual"},
            {"name": "Enterprise", "usd_per_seat_month": 6.0, "currency": "USD", "billing_basis": "annual"},
        ],
    },
    "trello": {
        "compare_tier": "Standard", "billing_model": "per_seat_month", "free_up_to_seats": 10,
        "tiers": [
            {"name": "Standard", "usd_per_seat_month": 6.0, "currency": "USD", "billing_basis": "monthly",
             "note": "$5 per user per month on annual billing."},
            {"name": "Premium", "usd_per_seat_month": 12.5, "currency": "USD", "billing_basis": "monthly",
             "note": "$10 per user per month on annual billing."},
        ],
        "free_tier_note": "Trello's Free plan covers up to 10 collaborators per Workspace, with a limit of 10 boards. A team inside that limit pays nothing, so self-hosting a replacement saves nothing either.",
    },
    "asana": {
        "compare_tier": "Starter", "billing_model": "per_seat_month", "free_up_to_seats": 2,
        "tiers": [
            {"name": "Starter", "usd_per_seat_month": 13.49, "currency": "USD", "billing_basis": "monthly",
             "note": "$10.99 per user per month on annual billing."},
            {"name": "Advanced", "usd_per_seat_month": 30.49, "currency": "USD", "billing_basis": "monthly",
             "note": "$24.99 per user per month on annual billing."},
        ],
        "free_tier_note": "Asana's Personal plan is free for up to 2 seats. Beyond that, the Starter tier below applies.",
    },
    "fathom": {
        "compare_tier": "Starter", "billing_model": "flat_month",
        "tiers": [
            {"name": "Starter", "usd_month": 15.0, "currency": "USD", "billing_basis": "monthly",
             "note": "Up to 100,000 monthly page views. Annual billing includes two months free."},
        ],
        "note": "Fathom prices by monthly page views, not seats, so team size does not change its cost.",
    },
    "freshdesk": {
        "compare_tier": "Growth", "billing_model": "per_seat_month",
        "tiers": [
            {"name": "Growth", "usd_per_seat_month": 19.0, "currency": "USD", "billing_basis": "annual"},
            {"name": "Pro", "usd_per_seat_month": 55.0, "currency": "USD", "billing_basis": "annual"},
            {"name": "Enterprise", "usd_per_seat_month": 89.0, "currency": "USD", "billing_basis": "annual"},
        ],
    },
    "clerk": {
        "compare_tier": "Pro", "billing_model": "flat_month",
        "tiers": [
            {"name": "Pro", "usd_month": 25.0, "currency": "USD", "billing_basis": "monthly",
             "note": "Includes 50,000 monthly retained users, then $0.02 each. $20 a month on annual billing. The B2B organisations add-on is $100 a month more."},
        ],
        "note": "Clerk bills monthly retained users, not seats, so team size is a poor proxy and the page says so.",
        "free_tier_note": "Clerk's Hobby plan is free for up to 50,000 monthly retained users. An internal team will almost never exceed that, so for most readers the honest licence cost is zero and the paid comparison below only applies if you need what Pro adds.",
    },
    "okta": {
        "compare_tier": "Starter", "billing_model": "per_seat_month",
        "tiers": [
            {"name": "Starter", "usd_per_seat_month": 6.0, "currency": "USD", "billing_basis": "annual",
             "min_month": 125.0,
             "note": "Billed annually with a $1,500 minimum annual contract, which is $125 a month."},
            {"name": "Essentials", "usd_per_seat_month": 17.0, "currency": "USD", "billing_basis": "annual",
             "min_month": 125.0},
        ],
    },
    "surveymonkey": {
        "compare_tier": "Team Advantage", "billing_model": "per_seat_month",
        "tiers": [
            {"name": "Team Advantage", "eur_per_seat_month": 30.0, "currency": "EUR", "billing_basis": "annual", "min_seats": 3},
            {"name": "Team Premier", "eur_per_seat_month": 75.0, "currency": "EUR", "billing_basis": "annual", "min_seats": 3},
        ],
        "note": "Read from the European storefront in euros. Responses beyond the plan allowance cost EUR 0.10 each and are not included.",
    },
    "mixpanel": {
        "compare_tier": "Free", "billing_model": "free",
        "tiers": [{"name": "Free", "usd_month": 0.0, "currency": "USD"}],
        "note": "Mixpanel is free up to 1 million events a month, and its Growth plan starts at $0 and scales with event volume without a published fixed price.",
        "free_tier_note": "Mixpanel's free plan covers up to 1 million events a month, with no seat charge. Below that volume there is no licence cost to save, so this comparison is about who holds the data rather than what it costs.",
    },
    "amplitude": {
        "compare_tier": "Free", "billing_model": "free",
        "tiers": [{"name": "Free", "usd_month": 0.0, "currency": "USD"}],
        "note": "Amplitude is free up to 2 million events a month with unlimited seats; its Plus plan starts at $0 and scales with event volume.",
        "free_tier_note": "Amplitude's free plan covers up to 2 million events a month with unlimited seats. Below that volume there is no licence cost to save.",
    },
    "betteruptime": {
        "compare_tier": "Responder", "billing_model": "flat_month",
        "tiers": [
            {"name": "Responder", "usd_month": 34.0, "currency": "USD", "billing_basis": "monthly",
             "note": "$29 a month on yearly billing. Additional status pages are $15 a month each."},
        ],
        "free_tier_note": "Better Stack's free tier includes 10 monitors and heartbeats and 1 status page. If that covers you, there is nothing to save.",
    },
    "intercom": {
        "compare_tier": "Essential", "billing_model": "per_seat_month",
        "tiers": [
            {"name": "Essential", "usd_per_seat_month": 29.0, "currency": "USD", "billing_basis": "annual"},
            {"name": "Advanced", "usd_per_seat_month": 85.0, "currency": "USD", "billing_basis": "annual"},
            {"name": "Expert", "usd_per_seat_month": 132.0, "currency": "USD", "billing_basis": "annual"},
        ],
        "note": "Fin AI Agent is charged separately at $0.99 per outcome on every plan and is not included here, so the real Intercom bill is usually higher.",
    },
    "linear": {
        "compare_tier": "Basic", "billing_model": "per_seat_month",
        "tiers": [
            {"name": "Basic", "usd_per_seat_month": 10.0, "currency": "USD", "billing_basis": "annual"},
            {"name": "Business", "usd_per_seat_month": 16.0, "currency": "USD", "billing_basis": "annual"},
        ],
    },
    "retool": {
        "compare_tier": "Team", "billing_model": "per_seat_month",
        "tiers": [
            {"name": "Team", "eur_per_seat_month": 5.0, "currency": "EUR", "billing_basis": "unstated",
             "note": "EUR 5 per internal user. Builders, the people who create apps, cost EUR 9 each."},
            {"name": "Business", "eur_per_seat_month": 14.0, "currency": "EUR", "billing_basis": "unstated",
             "note": "EUR 14 per internal user; builders cost EUR 46 each."},
        ],
        "note": "Every seat here is priced as an internal user at the lower rate. Builders cost more, so the real Retool bill is higher than shown, which means this comparison does not flatter self-hosting.",
    },
    "pingdom": {
        "compare_tier": "Synthetic Monitoring", "billing_model": "flat_month",
        "tiers": [
            {"name": "Synthetic Monitoring", "eur_month": 14.33, "currency": "EUR", "billing_basis": "annual",
             "note": "Entry tier with 10 uptime checks, EUR 171.96 billed yearly."},
        ],
        "note": "Read from the European storefront in euros. Pingdom scales by number of checks, not seats.",
    },
}

VERIFIED_0914.update({
    "jira": {
        "compare_tier": "Standard", "billing_model": "per_seat_month", "free_up_to_seats": 10,
        "tiers": [
            {"name": "Standard", "currency": "USD", "billing_basis": "monthly",
             "seat_bands": [
                 {"max_seats": 100, "usd_per_seat_month": 9.05},
                 {"max_seats": None, "usd_per_seat_month": 8.21},
             ],
             "note": "Per-user rate read with the team-size field set to 1, 5, 10, 25, 50, 100 and 250 users on monthly billing: $9.05 up to 100 users, $8.21 at 250."},
            {"name": "Premium", "currency": "USD", "billing_basis": "monthly",
             "seat_bands": [
                 {"max_seats": 100, "usd_per_seat_month": 18.30},
                 {"max_seats": None, "usd_per_seat_month": 15.54},
             ]},
        ],
        "free_tier_note": "Jira's Free plan covers teams of up to 10 users. Inside that limit there is no licence cost, so self-hosting a replacement saves nothing.",
    },
    "confluence": {
        "compare_tier": "Standard", "billing_model": "per_seat_month", "free_up_to_seats": 10,
        "tiers": [
            {"name": "Standard", "currency": "USD", "billing_basis": "monthly",
             "seat_bands": [
                 {"max_seats": 100, "usd_per_seat_month": 6.70},
                 {"max_seats": None, "usd_per_seat_month": 5.74},
             ],
             "note": "Per-user rate read with the team-size field set to 1, 5, 10, 25, 50, 100 and 250 users on monthly billing: $6.70 up to 100 users, $5.74 at 250."},
            {"name": "Premium", "currency": "USD", "billing_basis": "monthly",
             "seat_bands": [
                 {"max_seats": 100, "usd_per_seat_month": 13.20},
                 {"max_seats": None, "usd_per_seat_month": 11.01},
             ]},
        ],
        "free_tier_note": "Confluence's Free plan covers teams of up to 10 users. Inside that limit there is no licence cost, so self-hosting a replacement saves nothing.",
    },
    "make": {
        "compare_tier": "Core", "billing_model": "flat_month",
        "tiers": [
            {"name": "Core", "usd_month": 10.0, "currency": "USD", "billing_basis": "monthly",
             "note": "10,000 credits a month. $9 a month on annual billing."},
            {"name": "Pro", "usd_month": 18.0, "currency": "USD", "billing_basis": "monthly",
             "note": "$16 a month on annual billing."},
            {"name": "Teams", "usd_month": 34.0, "currency": "USD", "billing_basis": "monthly",
             "note": "$29 a month on annual billing."},
        ],
        "note": "Make bills by credits consumed, not seats. The comparison holds the entry plan fixed and shows what the same spend buys as a server.",
    },
    "helpscout": {
        "compare_tier": "Standard", "billing_model": "per_seat_month", "free_up_to_seats": 5,
        "tiers": [
            {"name": "Standard", "usd_per_seat_month": 30.0, "currency": "USD", "billing_basis": "monthly",
             "note": "$25 per user per month on annual billing."},
            {"name": "Plus", "usd_per_seat_month": 54.0, "currency": "USD", "billing_basis": "monthly",
             "note": "$45 per user per month on annual billing."},
        ],
        "free_tier_note": "Help Scout's Free plan covers up to 5 users with one inbox and one Docs site. A small team that fits inside it pays nothing.",
    },
    "monday": {
        "compare_tier": "Standard", "billing_model": "per_seat_month",
        "tiers": [
            {"name": "Basic", "eur_per_seat_month": 9.0, "currency": "EUR", "billing_basis": "annual", "min_seats": 3},
            {"name": "Standard", "eur_per_seat_month": 12.0, "currency": "EUR", "billing_basis": "annual", "min_seats": 3,
             "note": "The page showed EUR 120 a month billed annually for 10 users, and states that plans start at 3 users."},
            {"name": "Pro", "eur_per_seat_month": 19.0, "currency": "EUR", "billing_basis": "annual", "min_seats": 3},
        ],
        "note": "Read from the French storefront in euros.",
    },
    "lastpass": {
        "compare_tier": "Teams / Business", "billing_model": "per_seat_month",
        "tiers": [
            {"name": "Teams / Business", "currency": "EUR", "billing_basis": "annual",
             "seat_bands": [
                 {"max_seats": 50, "eur_per_seat_month": 4.42},
                 {"max_seats": None, "eur_per_seat_month": 6.50},
             ],
             "note": "Teams is EUR 4.42 per user per month and is limited to 50 users; larger teams need Business at EUR 6.50. Both billed annually."},
            {"name": "Business Max", "eur_per_seat_month": 10.0, "currency": "EUR", "billing_basis": "annual"},
        ],
        "note": "Read from the French storefront in euros.",
    },
    "tableau": {
        "compare_tier": "Tableau Standard", "billing_model": "per_seat_month",
        "tiers": [
            {"name": "Tableau Standard", "usd_per_seat_month": 15.0, "currency": "USD", "billing_basis": "annual",
             "note": "Starting price per user. Roles that author content cost more, so a real Tableau bill with any creators is higher."},
            {"name": "Tableau Enterprise", "usd_per_seat_month": 35.0, "currency": "USD", "billing_basis": "annual"},
        ],
        "note": "Every seat is priced at the starting rate, which understates Tableau's cost and so does not flatter self-hosting.",
    },
})

UNPRICEABLE_0914 = {
    "mode": ("quote_only", "Mode publishes no prices; every plan is sold through a sales conversation. No comparison can be published without inventing a number."),
    "looker": ("not_published", "Looker Studio has been renamed Data Studio, and no Data Studio Pro price was published on Google's pages on 2026-09-14. Its documentation says pricing depends on subscription length."),
}


def main() -> None:
    doc = json.loads(TARGET.read_text(encoding="utf-8"))
    by_slug = {p["slug"]: p for p in doc["products"]}

    for on, batch in ((ON, VERIFIED), (ON_0914, VERIFIED_0914)):
        for slug, patch in batch.items():
            product = by_slug.get(slug)
            if product is None:
                print(f"  ! {slug} not present in saas.json")
                continue
            product.update(patch)
            product["price_status"] = "verified"
            product["verified_on"] = on
            print(f"  verified {slug:<14} tier={patch['compare_tier']}  on {on}")

    for slug, (status, note) in UNPRICEABLE_0914.items():
        product = by_slug.get(slug)
        if product is None:
            continue
        product["price_status"] = status
        product["verified_on"] = None
        product["price_note"] = note
        print(f"  {status:<14} {slug}")

    still_seed = [p["slug"] for p in doc["products"] if p.get("price_status") != "verified"]
    print(f"\n  verified: {len(doc['products']) - len(still_seed)} / {len(doc['products'])}")
    print(f"  still seed (blocked from publication in strict mode): {', '.join(still_seed)}")

    TARGET.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
