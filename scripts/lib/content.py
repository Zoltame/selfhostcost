"""
The site's written pages. Kept in Python rather than in templates because most
of their content is generated from the live dataset: the methodology page has
to state which prices are actually confirmed today, not what was true when
someone last edited a paragraph.
"""

from __future__ import annotations

from datetime import date

from .model import Dataset, money, priced_providers


def static_pages(ds: Dataset, wave: int, strict: bool, built, pairs):
    return [
        _methodology(ds, wave, strict, built),
        _disclosure(ds),
        _privacy(ds),
    ]


def _methodology(ds: Dataset, wave: int, strict: bool, built) -> tuple[str, str, str, str]:
    cfg = ds.config
    m = cfg["tco_model"]
    rate = m["engineer_hourly_usd"]
    horizon = m["horizon_months"]
    ref = cfg.get("reference_users", 10)

    verified = sorted(
        (s for s in ds.saas.values() if s.get("price_status") == "verified"),
        key=lambda s: s["name"].lower(),
    )
    unverified = sorted(
        (s for s in ds.saas.values() if s.get("price_status") != "verified"),
        key=lambda s: s["name"].lower(),
    )
    priced = priced_providers(ds)
    unpriced = [p for p in ds.providers.values() if p["price_status"] != "verified"]

    verified_rows = "\n".join(
        f"<tr><td>{s['name']}</td><td>{s['compare_tier']}</td>"
        f"<td><a href=\"{s['pricing_url']}\" rel=\"nofollow noopener\">vendor page</a></td>"
        f"<td>{s['verified_on']}</td></tr>"
        for s in verified
    )
    priced_rows = "\n".join(
        f"<tr><td>{p['name']}</td><td>{len([x for x in p['plans'] if x.get('price_usd_month')])} plans</td>"
        f"<td><a href=\"{p['pricing_url']}\" rel=\"nofollow noopener\">vendor page</a></td>"
        f"<td>{p['verified_on']}</td></tr>"
        for p in priced
    )

    body = f"""
<h1>Methodology: how every figure on this site is produced</h1>

<p class="lead">
  This page exists so you can check our arithmetic, disagree with our assumptions, and see exactly which
  prices we have confirmed and which we have not. If a number on this site cannot be traced back to
  something here, it is a bug.
</p>

<h2>The shape of the problem</h2>
<p>
  Per-seat software has no floor and a steep slope. A server has a high floor and almost no slope. Every
  comparison here is the point where those two lines cross, which is why the honest answer is never
  "self-hosting is cheaper" but "cheaper above roughly this many people, assuming your time is worth
  roughly this much".
</p>

<h2>Sizing a self-hosted tool</h2>
<p>For a tool and a team size, the required memory is:</p>
<pre><code>memory = (base_ram + ram_per_user &times; users) &times; {1 + m['ram_headroom_ratio']:.2f}</code></pre>
<p>and the required disk is:</p>
<pre><code>disk = base_disk + disk_per_user &times; users</code></pre>
<ul>
  <li><strong>base_ram</strong> covers the entire stack at rest, including the database and every sidecar
      container the project ships in its own reference Compose file. It is not the application process alone.</li>
  <li><strong>The {int(m['ram_headroom_ratio'] * 100)}% headroom</strong> is deliberate. A box sized exactly to its
      working set is a box that dies during an upgrade.</li>
  <li><strong>vCPU</strong> is carried through from the project's baseline and is <em>not</em> scaled with team
      size. For these workloads memory runs out first. This is a simplification and we would rather name it
      than hide it.</li>
</ul>
<p>
  Where a project publishes a minimum or recommended specification, the base figures come from that and the
  page says so. Where it does not, the base figures are derived from the services in its reference Compose
  stack and the page labels them an estimate. <strong>The per-user increments are always ours.</strong> They
  are set generously rather than optimistically, because undersizing the server flatters self-hosting and
  we would rather the bias ran the other way.
</p>

<h2>Picking the server</h2>
<p>
  We take the cheapest plan, among providers whose prices we have read ourselves, whose memory and disk both
  meet or exceed the requirement. No partial fits, and no pretending a tool will squeeze onto a plan that is
  a gigabyte short.
</p>
<p>
  <strong>We only trust {len(priced)} provider{'' if len(priced) == 1 else 's'} today.</strong>
  That is a real limitation. Several hosts render their prices client-side or gate them behind a region
  selector, and we do not publish a price we could not read.
  {'The most important consequence: ' + ', '.join(p['name'] for p in unpriced) + ' ' + ('are' if len(unpriced) > 1 else 'is') + ' absent from every calculation, and Hetzner in particular is usually cheaper per gigabyte of memory than what we quote. Treat our server costs as an upper bound.' if unpriced else ''}
</p>
<div class="tablewrap"><table>
<thead><tr><th>Provider</th><th>Plans priced</th><th>Source</th><th>Read on</th></tr></thead>
<tbody>
{priced_rows}
</tbody></table></div>

<h2>The three costs of running it yourself</h2>
<div class="tablewrap"><table>
<thead><tr><th>Line</th><th>How it is set</th><th>Why</th></tr></thead>
<tbody>
<tr><td>Server</td><td>The plan chosen above, at list price</td><td>No committed-use or annual discounts are assumed.</td></tr>
<tr><td>Backups</td><td>{int(m['backup_cost_ratio'] * 100)}% of the server price</td>
    <td>Roughly what provider snapshots cost. Treating backups as optional would make every figure on this site meaningless.</td></tr>
<tr><td>Your time</td>
    <td>{m['maintenance_hours_per_month_by_difficulty']['easy']} to {m['maintenance_hours_per_month_by_difficulty']['hard']} hours a month by difficulty, at ${rate} an hour</td>
    <td>This is usually the largest line, and leaving it out is the single most common way these comparisons mislead.</td></tr>
<tr><td>Setup, once</td>
    <td>{m['setup_hours_by_difficulty']['easy']} to {m['setup_hours_by_difficulty']['hard']} hours by difficulty, at ${rate} an hour</td>
    <td>Amortised against the monthly saving to give the break-even point.</td></tr>
</tbody></table></div>

<h3>Difficulty, and what it implies</h3>
<div class="tablewrap"><table>
<thead><tr><th>Rating</th><th>Meaning</th><th>Setup</th><th>Per month</th></tr></thead>
<tbody>
<tr><td>easy</td><td>One container, no external dependencies, nothing to do beyond keeping the image current</td>
    <td>{m['setup_hours_by_difficulty']['easy']} h</td><td>{m['maintenance_hours_per_month_by_difficulty']['easy']} h</td></tr>
<tr><td>medium</td><td>Multi-container stack with a database you are responsible for backing up</td>
    <td>{m['setup_hours_by_difficulty']['medium']} h</td><td>{m['maintenance_hours_per_month_by_difficulty']['medium']} h</td></tr>
<tr><td>hard</td><td>Several stateful services, a non-trivial upgrade path, and a real risk of data loss if you rush it</td>
    <td>{m['setup_hours_by_difficulty']['hard']} h</td><td>{m['maintenance_hours_per_month_by_difficulty']['hard']} h</td></tr>
</tbody></table></div>

<h3>If your time is free</h3>
<p>
  Every page also shows the figure without labour. Both numbers are real. Which one applies to you depends
  on whether those hours would otherwise have been billable, or whether you would have spent the evening on
  it for fun anyway. We lead with labour included because that is the number a business should plan against.
</p>

<h2>Pricing the commercial side</h2>
<p>
  We compare against <strong>the cheapest tier a team would realistically land on</strong>, not the cheapest
  tier that exists. Quoting a vendor's entry plan, with its response caps and missing features, against a
  full self-hosted deployment would be dishonest, and it is how most comparison pages arrive at their
  conclusions. The tier used is named on every page.
</p>
<p>
  Seat minimums are honoured. Where a vendor bills something other than seats, such as tasks executed,
  monthly active users, or subscriber count, the page says so explicitly rather than pretending team size is
  the right axis. Where a vendor's free tier already covers the team in question, the page says that too,
  and makes no savings claim.
</p>

<h3>Prices we have confirmed</h3>
<p>Read directly from the vendor's own pricing page on the date shown:</p>
<div class="tablewrap"><table>
<thead><tr><th>Product</th><th>Tier compared</th><th>Source</th><th>Read on</th></tr></thead>
<tbody>
{verified_rows}
</tbody></table></div>

<h3>Prices we have not confirmed</h3>
<p>
  {len(unverified)} products in our dataset have no confirmed price.
  {'Because strict mode is on, <strong>no page that would depend on one of them has been published</strong>.' if strict else '<strong>Strict mode is off in this build, so figures on this site may rest on unconfirmed prices.</strong> That is a development setting and should not be how you are reading this.'}
  They are: {', '.join(s['name'] for s in unverified) if unverified else 'none'}.
</p>

<h3>Currency</h3>
<p>
  Some vendors served their pricing page in euros. Those figures are converted at a single dated rate,
  <strong>1 EUR = {cfg['fx']['rates_to_usd']['EUR']} USD</strong>, the
  <a href="{cfg['fx']['source_url']}" rel="nofollow noopener">{cfg['fx']['source_name']}</a> rate for
  {cfg['fx']['on']}. Any page using it says so and links here.
</p>

<h2>The horizon and the break-even</h2>
<p>
  Totals run over <strong>{horizon} months</strong>. The break-even point is the setup cost divided by the
  monthly saving:
</p>
<pre><code>break_even_months = setup_cost / (saas_monthly - selfhosted_monthly)</code></pre>
<p>
  When the monthly saving is zero or negative there is no break-even, and the page says "never" rather than
  quietly omitting the row.
</p>

<h2>What this model deliberately ignores</h2>
<ul>
  <li><strong>Migration effort.</strong> Getting your existing data out of the incumbent and into the
      replacement is real work and is not counted anywhere. For a large historical dataset it can dwarf the
      setup figure.</li>
  <li><strong>Feature parity.</strong> The tools are near-substitutes, not identical. Cost is one axis and
      often not the deciding one.</li>
  <li><strong>Risk.</strong> A bad upgrade, a lost database, or a weekend spent on an outage has an expected
      cost that a spreadsheet cannot capture honestly.</li>
  <li><strong>Bandwidth overages, managed databases and object storage</strong> beyond what the chosen plan
      includes. A few tools genuinely need external object storage and their pages name it, but it is not
      priced in.</li>
  <li><strong>Annual and committed-use discounts</strong> on the hosting side. Both sides are quoted at the
      basis the vendor's page displayed, and the page states which that was.</li>
  <li><strong>Your existing infrastructure.</strong> If you already run a server with spare memory, the
      marginal cost of one more container is close to zero and none of these figures apply to you.</li>
</ul>

<h2>How stale is this page</h2>
<p>
  Prices are a snapshot with a date attached, not a live feed. Every figure links to the page it came from,
  and the vendor's page is the authority. A price older than about 45 days should be treated as indicative
  and re-checked before anyone spends money on the strength of it.
</p>
<p>
  Currently: {len(built)} comparison pages published, wave {wave}, reference team size {ref} people,
  strict price checking {'on' if strict else '<strong>off</strong>'}.
</p>
"""
    return (
        "methodology",
        "Methodology: how every cost figure here is calculated",
        "The sizing model, the labour assumptions, the exact price sources with dates, and everything this "
        "cost model deliberately leaves out.",
        body,
    )


def _disclosure(ds: Dataset) -> tuple[str, str, str, str]:
    cfg = ds.config
    aff = cfg.get("affiliate", {})
    active = bool(aff.get("enabled")) and any(p.get("id") for p in aff.get("providers", {}).values())

    state = (
        "<p><strong>Affiliate links are currently active on this site.</strong> When you follow a hosting "
        "link from one of our pages and later become a customer, we may receive a commission from that "
        "provider at no cost to you.</p>"
        if active else
        "<p><strong>There are no affiliate links on this site at the moment.</strong> Every hosting link "
        "here is a plain link to the provider's own page. If that changes, this page changes with it and "
        "the disclosure appears on every page carrying such a link.</p>"
    )

    body = f"""
<h1>Affiliate disclosure</h1>

<p class="lead">
  Comparison sites that earn commission on the thing they recommend have an obvious conflict of interest.
  Here is exactly how ours is contained.
</p>

{state}

<h2>What commission cannot influence</h2>
<ul>
  <li><strong>Which provider a page recommends.</strong> The server on every page is chosen by one rule:
      the cheapest plan, among providers whose prices we have read, that meets the computed memory and disk
      requirement. That rule is in the build script and it does not know what anyone pays us.</li>
  <li><strong>The numbers.</strong> Every figure is computed from
      <a href="{cfg['base_path']}/methodology/">the published model</a> and dated price sources. You can
      reproduce any of them by hand.</li>
  <li><strong>The conclusion.</strong> A good number of pages here conclude that the paid product is cheaper
      and that you should not self-host. Those pages earn nothing. They stay as they are because a
      comparison that always reaches the same answer is not a comparison.</li>
</ul>

<h2>What commission does influence, honestly</h2>
<p>
  Which providers we prioritised verifying prices for is not perfectly independent of which ones have a
  referral programme. We currently price
  {', '.join(p['name'] for p in priced_providers(ds)) or 'no providers'}, and the
  <a href="{cfg['base_path']}/hosting/">hosting page</a> names every provider we have not been able to
  price, including ones we expect to be cheaper. That gap is disclosed rather than quietly left out.
</p>

<h2>No paid placement</h2>
<p>
  No provider, vendor or open-source project has paid to appear here, to be ranked, or to be described in a
  particular way. No one gets to review a page before it goes up.
</p>

<h2>Not advice</h2>
<p>
  These are cost models, not recommendations about your business. Prices change, our snapshots go stale, and
  the vendor's own page is always the authority. Check before you spend.
</p>
"""
    return (
        "disclosure",
        "Affiliate disclosure and how we handle the conflict",
        "Whether this site earns commission on hosting links, what that can and cannot influence, and the "
        "gaps we disclose rather than hide.",
        body,
    )


def _privacy(ds: Dataset) -> tuple[str, str, str, str]:
    cfg = ds.config
    an = cfg.get("analytics", {})
    tracking = (
        f"<p>We use <strong>{an['provider']}</strong> for aggregate traffic measurement. It is configured "
        "without cookies and without cross-site identifiers, and we cannot use it to identify an individual "
        "visitor.</p>"
        if an.get("provider") not in (None, "", "none") else
        "<p><strong>There is no analytics script on this site at all.</strong> No cookies are set, nothing "
        "is stored in your browser, and no visitor-level data is collected by us.</p>"
    )
    lead = (
        "<p>If you submit the form offering a migration checklist, the email address you enter is processed "
        "by our form provider so we can send you the thing you asked for. It is not sold, and it is not "
        "passed to any hosting provider.</p>"
        if cfg["lead_capture"].get("enabled") and cfg["lead_capture"].get("form_id") else
        "<p>There are no forms on this site, so there is nothing for you to submit and nothing for us to "
        "store.</p>"
    )

    body = f"""
<h1>Privacy</h1>

<p class="lead">
  A site about not handing your data to other people ought to be careful with yours. This page is short
  because there is very little to describe.
</p>

<h2>Analytics</h2>
{tracking}

<h2>Forms</h2>
{lead}

<h2>Outbound links</h2>
<p>
  Links to hosting providers, vendors and open-source projects lead to sites we do not control and whose
  privacy practices are their own. Where a link is a commissioned one it is marked as such in the page
  markup and disclosed on the page; see the
  <a href="{cfg['base_path']}/disclosure/">affiliate disclosure</a>.
</p>

<h2>Hosting</h2>
<p>
  This site is static files served by GitHub Pages. GitHub processes server logs, including IP addresses,
  as part of delivering it, under its own privacy terms rather than ours.
</p>

<h2>No third-party assets</h2>
<p>
  Every page loads one stylesheet and one small inline SVG icon from this domain. There are no web fonts, no
  tag managers, no embedded videos and no social widgets, so no third party is contacted when you read a
  page{' apart from the form provider on pages carrying the form' if cfg['lead_capture'].get('form_id') else ''}.
</p>

<p class="srcline">Last reviewed {date.today().isoformat()}.</p>
"""
    return (
        "privacy",
        "Privacy",
        "What this site collects, which is close to nothing, and who else is contacted when you read a page.",
        body,
    )
