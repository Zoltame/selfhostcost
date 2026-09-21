# SelfHostCost runbook

Experiment: does a price-verified, honest cost-comparison micro-site earn organic traffic
and hosting-affiliate revenue within 60 days, at zero spend?

## Build and publish

```bash
python scripts/enrich_github.py        # refresh stars, licences, releases (monthly)
python scripts/check_staleness.py      # anything older than 45 days?
python scripts/build.py                # writes docs/, report in ops/build-report.json
git add -A && git commit -m "rebuild" && git push   # GitHub Pages serves docs/
```

Page dates (`datePublished`, `dateModified`, sitemap `lastmod`) come from `ops/page-dates.json`,
which stores a hash of each page. A rebuild only moves a page's modified date when its content
changed. Commit this file with every rebuild and never delete it, or every page is re-dated.

`strict_prices` must stay `true` in production. A comparison is only published when the
vendor price was read from the vendor's own page and recorded in
`scripts/apply_verified_prices.py`.

## Unlocking more pages (highest leverage first)

1. **Confirm Hetzner prices.** Fill `price_usd_month` in `data/providers.json`, set
   `price_status` to `verified`. Every server figure on the site gets cheaper and more credible.
2. **Confirm the 24 withheld wave-1 vendor prices** listed by `check_staleness.py`. Jira,
   Confluence, Intercom, Mixpanel and Bitwarden unlock the most pages. Add them to
   `apply_verified_prices.py` with the date, then rebuild.
3. **Wave 2** (`publish_wave: 2`): only after the day-30 gate says SCALE.

## Counting units and the monitoring category

Most categories are priced per person (`team_sizes`, reference 10 people). A category can name another
`unit` in `data/categories.json`; `site.config.json > units` holds its size ladder and reference size.
`infra-monitoring` uses `hosts` (5 to 500 monitored servers, reference 25), because Datadog and PRTG
charge per server or device, not per user. For a `hosts` tool, the `*_per_user` sizing keys mean per
monitored server. A comparison is only built when the tool and the product share a unit.

Unit wording lives in `i18n/ui/<lang>.json` under `unit.<unit>.*`, and unit-specific variants of page
titles and price labels end in `.<unit>` (for example `cost.title.many.hosts`).

`infra-monitoring` is prepared but unpublished (wave 2): Datadog and PRTG prices read 2026-09-21, Prometheus +
Grafana, Zabbix and Checkmk Community sized from their own documentation where it exists. New Relic is
withheld because it bills by user and data volume (see `ops/backlog-saas.md`). To look at it privately:

```bash
python scripts/build.py --out ../preview --include-category infra-monitoring
```

This never touches `docs/` or the date ledger. To publish it, set its category, tools and products to the
current wave (or publish wave 2), rebuild, and re-read the two vendor prices if they are over 45 days old.

## Languages

The site is published in English (site root), French (`/fr/`), German (`/de/`) and Spanish (`/es/`),
listed in `site.config.json > languages`. Every language renders the same computed figures; French
and German display euros at the dated rate in `fx`, English and Spanish display dollars.

| What | Where |
|------|-------|
| Page prose | `templates/<lang>/` (same variables in every language) |
| Shared layout, header, footer, form | `templates/shared/` |
| Short interface strings | `i18n/ui/<lang>.json` (same keys as `en.json`) |
| Translated dataset text | `data/i18n/<lang>.json` |
| Written pages (about, checklist, methodology, disclosure, privacy) | `scripts/lib/content_<lang>.py` |

The build report lists, per language, any interface string or data field that fell back to English.
Adding a tool or a price means translating its descriptive fields into each `data/i18n/<lang>.json`,
otherwise the translated pages show the English text for that field.

## Monetisation switches (require your own accounts)

- **Affiliates:** apply to DigitalOcean, then Hetzner, Vultr, Kamatera. Put each ID in
  `site.config.json > affiliate.providers.<slug>.id` and set `affiliate.enabled: true`.
  Links get `rel="sponsored"` and the disclosure appears automatically.
- **Lead capture:** one Tally form per language, each with an email field, a consent checkbox,
  hidden fields `tool` and `page`, and "Redirect on completion" set to that language's checklist
  (`/migration-checklist/`, `/fr/migration-checklist/`, `/de/migration-checklist/`,
  `/es/migration-checklist/`). Put each form ID in `lead_capture.form_ids.<lang>`. A language
  without a form ID shows no form at all, rather than an English form.
- **Analytics:** Umami Cloud or Plausible, cookie-free. Set `analytics.provider`, `site_id`, `script_url`.

## Tracking cadence

| When | Action |
|------|--------|
| Day 0 | Push, write the date to `ops/launch-date.txt`, add the property in Google Search Console, submit `sitemap.xml` |
| Every Monday | Export GSC "Pages" CSV, then `python scripts/velocity.py --gsc Pages.csv --indexed N --affiliate-clicks N --leads N` |
| Day 30 | `python scripts/velocity.py --report` and apply the gate |
| Day 60 | Same, final gate |

## Decision gates

| Gate | Condition | Decision |
|------|-----------|----------|
| Day 30 | Under 15% of pages indexed | Kill signal. Google is rejecting the pages. |
| Day 30 | 1,000+ impressions | Scale: publish wave 2. |
| Day 30 | Otherwise | Hold. Improve the ten pages with the most impressions. |
| Day 60 | 300+ clicks, or any revenue, or 10+ leads | Continue: buy a domain, activate affiliates, wave 3. |
| Day 60 | Otherwise | Stop. Archive and test the next niche. |

## Known limitations

- A `github.io` subdomain carries no authority and is shared. A custom domain (about $10 a year)
  is the first thing to buy if the day-30 gate passes. Change `base_url` and `base_path`,
  add `docs/CNAME`, rebuild.
- Only DigitalOcean prices are confirmed, so server costs are an upper bound.
- Storage-heavy tools (Nextcloud, Immich) need block-storage pricing before wave 2 can fully publish.
