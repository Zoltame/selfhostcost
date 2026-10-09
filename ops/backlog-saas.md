# Backlog: commercial products referenced but not yet priced

These were named as replacement targets by tools in the dataset but have no entry in
`data/saas.json`. Each one is a comparison page that cannot be built until its pricing
is read from the vendor's page and recorded. Ordered by how many tools want it.

- **teams** — wanted by: mattermost, rocketchat, zulip
- **qualtrics** — wanted by: formbricks, limesurvey
- **box** — wanted by: nextcloud, seafile
- **hellosign** — wanted by: documenso, docuseal
- **icloud-photos** — wanted by: immich, photoprism
- **slite** — wanted by: outline
- **miro** — wanted by: affine
- **ms-project** — wanted by: openproject
- **cognito** — wanted by: zitadel
- **google-forms** — wanted by: opnform
- **sendgrid-marketing** — wanted by: listmonk
- **convertkit** — wanted by: listmonk
- **hubspot-marketing** — wanted by: mautic
- **activecampaign** — wanted by: mautic
- **zoho-crm** — wanted by: espocrm
- **pandadoc** — wanted by: docuseal
- **bugsnag** — wanted by: glitchtip
- **rollbar** — wanted by: glitchtip
- **acuity** — wanted by: cal-com
- **savvycal** — wanted by: cal-com

## Not modelled

- **mailchimp** (Intuit), read 2026-10-09: EUR 18 a month at 500 contacts, EUR 90.02 at 5,000, EUR 207.05 at
  15,000, EUR 279.07 at 25,000. Priced per contact, so a per-seat page would quote EUR 18 to a team whose real
  bill is ten times that. Moved to wave 3 until the dataset can count contacts, the way infra-monitoring counts
  hosts. The prices are recorded in scripts/apply_verified_prices.py.
- **newrelic** (New Relic), read 2026-09-21: it does not charge per host. It charges per full-platform
  user ($349 a month on Pro, annual) plus $0.40 per GB of data beyond 100 GB a month. Its cost depends on data
  volume, not on the server count the monitoring category is priced by, so it would need an assumed
  GB-per-server figure. Withheld rather than guessed. Wanted by the infra-monitoring category.
- **datadog** is no longer a SigNoz target: Datadog is priced per monitored host and SigNoz per user in
  this dataset, and a comparison page needs both sides counted in the same unit.
