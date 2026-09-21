"""
Deutsche Textseiten. Gleiche Struktur und gleiche Berechnungen wie content.py;
nur der Text ändert sich. Beträge laufen über Locale und werden in Euro zum
datierten Kurs aus der Methodik angezeigt.
"""

from __future__ import annotations

from lib.dates import MODIFIED

from .i18n import Locale
from .model import Dataset, priced_providers


def static_pages(ds: Dataset, wave: int, strict: bool, built, pairs, base: str):
    loc = Locale("de", ds.config)
    return [
        _about(ds, built, base),
        _checklist(ds, base, loc),
        _methodology(ds, wave, strict, built, base, loc),
        _disclosure(ds, base),
        _privacy(ds, base),
    ]


def _checklist(ds: Dataset, base: str, loc: Locale) -> tuple[str, str, str, str]:
    m = ds.config["tco_model"]
    body = f"""
<h1>Checkliste für die Migration zum Self-Hosting</h1>

<p class="lead">
  Eine einseitige Vorabliste, um ein Team von einem kostenpflichtigen Tool auf ein selbst gehostetes umzustellen.
  Sie deckt die Schritte ab, die entscheiden, ob die Umstellung unspektakulär oder ein Desaster wird: Datenexport,
  Dimensionierung, Backups und den Rückfallplan, den die meisten vergessen.
</p>

<div class="note caution">
  <p><strong>Kündigen Sie das Abo erst, wenn der letzte Abschnitt erledigt ist.</strong> Betreiben Sie beide
  parallel, bis Sie ein Backup wiederhergestellt haben und Ihr Team das neue Tool für echte Arbeit genutzt hat.</p>
</div>

<h2>1. Bevor Sie etwas installieren</h2>
<ul>
  <li><strong>Exportieren Sie heute eine echte Kopie Ihrer Daten.</strong> Kein Testkonto, sondern Ihren echten
      Workspace. Manche Exporte sind unvollständig, gedrosselt oder nur in höheren Tarifen verfügbar. Finden Sie das
      jetzt heraus, nicht am Tag, an dem Ihr Vertrag endet.</li>
  <li><strong>Öffnen Sie den Export und prüfen Sie, was fehlt.</strong> Anhänge, Kommentare, Verlauf,
      Erwähnungen und Berechtigungen sind die üblichen Verluste.</li>
  <li><strong>Prüfen Sie, ob der Ersatz dieses Format importieren kann.</strong> Falls nicht, planen Sie Zeit für
      die Konvertierung ein. Diese Kosten stecken in keiner Zahl auf dieser Website.</li>
  <li><strong>Listen Sie die Integrationen auf, auf die Sie angewiesen sind.</strong> SSO, Chat-Benachrichtigungen,
      Webhooks, Kalendersynchronisation. Prüfen Sie für jede, ob es sie beim selbst gehosteten Tool gibt.</li>
  <li><strong>Prüfen Sie die Lizenz.</strong> Mehrere beliebte Tools sind source-available statt Open Source, mit
      Einschränkungen bei kommerzieller Nutzung. Jede Tool-Seite auf dieser Website weist darauf hin.</li>
  <li><strong>Benennen Sie eine verantwortliche Person.</strong> Selbst gehostete Software ohne jemanden, der für
      Updates zuständig ist, ist der häufigste Grund, warum solche Projekte scheitern.</li>
</ul>

<h2>2. Dimensionierung und Einrichtung</h2>
<ul>
  <li><strong>Dimensionieren Sie den Server anhand der Kostenseite des Tools für Ihre Teamgröße</strong> und behalten
      Sie die {int(m['ram_headroom_ratio'] * 100)} % Reserve beim Arbeitsspeicher bei. Ein Server, der genau auf den
      Bedarf zugeschnitten ist, fällt gern beim ersten Upgrade um.</li>
  <li><strong>Verwenden Sie die Docker-Compose-Datei des Projekts</strong> statt einer von Dritten, und legen Sie die
      Image-Version fest, statt <code>latest</code> zu nutzen.</li>
  <li><strong>Betreiben Sie es vom ersten Tag an hinter HTTPS auf einer eigenen Subdomain.</strong> Eine spätere
      Adressänderung bricht Links, OAuth-Rückleitungen und mobile Apps.</li>
  <li><strong>Richten Sie den E-Mail-Versand</strong> über einen Transaktions-Mailanbieter ein. Ohne ihn scheitern
      Passwort-Resets und Benachrichtigungen stillschweigend, und die meisten Tools warnen Sie nicht.</li>
  <li><strong>Schließen Sie alle Ports außer 80 und 443</strong> und stellen Sie die Datenbank nie direkt ins Netz.</li>
  <li><strong>Aktivieren Sie SSO oder mindestens verpflichtende Zwei-Faktor-Authentifizierung</strong>, bevor Sie
      jemanden einladen.</li>
</ul>

<h2>3. Getestete Backups</h2>
<ul>
  <li><strong>Sichern Sie sowohl die Datenbank als auch die hochgeladenen Dateien.</strong> Ein Datenbank-Dump ohne
      Upload-Verzeichnis stellt ein Tool voller kaputter Anhänge wieder her.</li>
  <li><strong>Bewahren Sie mindestens eine Kopie außerhalb des Servers auf</strong>, bei einem anderen Anbieter oder in
      einer anderen Region als der Server selbst.</li>
  <li><strong>Automatisieren Sie es und lassen Sie sich bei Fehlern alarmieren.</strong> Ein Backup-Job, der vor drei
      Wochen stehen geblieben ist, ist der übliche Weg, zu entdecken, dass man kein Backup hatte.</li>
  <li><strong>Stellen Sie es vor dem Start auf einem frischen Server wieder her.</strong> Messen Sie die Dauer. Diese
      Zahl ist Ihre echte Wiederherstellungszeit; solange Sie sie nicht kennen, haben Sie keine Backups, nur Dateien.</li>
</ul>

<h2>4. Die Umstellung</h2>
<ul>
  <li><strong>Wählen Sie einen ruhigen Tag und kündigen Sie einen Inhaltsstopp</strong> im alten Tool für die Dauer
      der Migration an.</li>
  <li><strong>Machen Sie nach dem Stopp einen letzten Export</strong>, importieren Sie ihn und prüfen Sie Stichproben
      von Datensätzen, Anhängen und Berechtigungen gegen das alte Tool.</li>
  <li><strong>Stellen Sie zuerst eine kleine Gruppe um</strong>, für eine Woche echter Arbeit, bevor alle wechseln.</li>
  <li><strong>Leiten Sie um oder aktualisieren Sie Lesezeichen</strong> überall, wo die alte Adresse verlinkt war:
      Dokumentation, Chat, Browser, mobile Apps.</li>
</ul>

<h2>5. Der Rückfallplan, den die meisten vergessen</h2>
<ul>
  <li><strong>Schreiben Sie vor der Umstellung auf, was Sie zurückwechseln ließe.</strong> Datenverlust, eine
      unverzichtbare fehlende Funktion oder wiederholte Ausfälle. Legen Sie die Schwelle fest, solange Sie ruhig sind.</li>
  <li><strong>Behalten Sie das alte Abo nach dem Start noch einen Abrechnungszeitraum</strong>, auch wenn es sich nach
      Verschwendung anfühlt. Es ist die günstigste Versicherung, die Sie kaufen werden.</li>
  <li><strong>Wissen Sie, wie Sie aus dem neuen Tool wieder exportieren</strong>, in ein Format, das das alte lesen kann.</li>
  <li><strong>Kündigen Sie das alte Abo erst</strong>, wenn ein Wiederherstellungstest bestanden ist, das ganze Team das
      neue Tool für echte Arbeit genutzt hat und niemand das alte zurückverlangt hat.</li>
</ul>

<h2>6. Nach dem Start</h2>
<ul>
  <li><strong>Tragen Sie Updates in den Kalender ein.</strong> Diese Website rechnet je nach Tool mit
      {loc.hours(m['maintenance_hours_per_month_by_difficulty']['easy'])} bis
      {loc.hours(m['maintenance_hours_per_month_by_difficulty']['hard'])} Stunden pro Monat. Was nicht eingeplant ist,
      passiert nicht.</li>
  <li><strong>Lesen Sie die Release Notes vor jedem Upgrade</strong>, besonders bei Hauptversionen mit
      Datenbankmigrationen.</li>
  <li><strong>Richten Sie Uptime-Monitoring ein</strong>, damit Sie von einem Ausfall erfahren, bevor Ihr Team es tut.</li>
  <li><strong>Wiederholen Sie den Wiederherstellungstest</strong> alle paar Monate.</li>
</ul>

<h2>Bevor Sie anfangen</h2>
<p>
  Wenn Sie die Umstellung noch nicht durchgerechnet haben, prüfen Sie, ob Self-Hosting bei Ihrer Teamgröße wirklich
  Geld spart. Bei manchen Tools ist das nicht der Fall, sobald die Stunden oben eingerechnet sind.
  <a href="{base}/compare/">Alle Vergleiche ansehen</a> oder
  <a href="{base}/methodology/">nachlesen, wie die Kosten berechnet werden</a>.
</p>
"""
    return (
        "migration-checklist",
        "Checkliste für die Migration zum Self-Hosting: bevor Sie das Abo kündigen",
        "Eine praktische Checkliste für den Wechsel von einem kostenpflichtigen zu einem selbst gehosteten Tool: "
        "Datenexport, Dimensionierung, getestete Backups, Umstellung und Rückfallplan.",
        body,
    )


def _about(ds: Dataset, built, base: str) -> tuple[str, str, str, str]:
    cfg = ds.config
    email = cfg.get("contact_email", "")
    repo = f"https://github.com/{cfg['github_owner']}/{cfg['repo']}"
    aff = cfg.get("affiliate", {})
    referral_on = bool(aff.get("enabled")) and any(p.get("id") for p in aff.get("providers", {}).values())
    verified = [s for s in ds.saas.values() if s.get("price_status") == "verified"
                and s.get("wave", 1) <= int(cfg.get("publish_wave", 1))]

    money_line = (
        "Die einzige finanzielle Beziehung dieser Website zu jemandem, den sie erwähnt, ist der normale "
        "Empfehlungslink von DigitalOcean. Er bringt Hosting-Guthaben, wenn sich jemand darüber anmeldet und seine "
        "ersten 25 $ bezahlt. Er ist auf jeder Seite gekennzeichnet, die ihn enthält, und auf der "
        f"<a href=\"{base}/disclosure/\">Hinweisseite</a> vollständig beschrieben."
        if referral_on else
        "Die Website hat derzeit keine Affiliate- oder Empfehlungslinks und verdient nichts. Wenn sich das ändert, "
        f"ändert sich die <a href=\"{base}/disclosure/\">Hinweisseite</a> am selben Tag."
    )

    body = f"""
<h1>Über SelfHostCost</h1>

<p class="lead">
  SelfHostCost beantwortet eine einzige Frage, Tool für Tool und Teamgröße für Teamgröße: Ist es wirklich
  günstiger, eine Open-Source-Alternative selbst zu betreiben, als für die Software zu zahlen, wenn Server, Backups
  und die eigenen Stunden eingerechnet sind?
</p>

<h2>Warum es diese Website gibt</h2>
<p>
  Die meisten Listen mit „selbst gehosteten Alternativen“ hören beim Lizenzpreis auf und lassen Self-Hosting kostenlos
  wirken. Die meisten Vergleichsseiten von Anbietern hören bei den Funktionen auf und lassen das Abo unvermeidlich
  wirken. Keine berechnet, was die Frage entscheidet: Ein Server hat einen hohen Sockel und kaum Steigung, ein Platz
  hat keinen Sockel, aber eine steile Steigung. Diese Website berechnet, wo sich diese Linien kreuzen, und
  veröffentlicht die Antwort auch dann, wenn sie „zahlen Sie weiter“ lautet.
</p>

<h2>Wer sie betreibt</h2>
<p>
  SelfHostCost ist ein unabhängiges Projekt, gestartet am {cfg.get('launched_on', '')}. Es gehört keinem
  Softwareanbieter, Hoster oder Open-Source-Projekt, das hier vorkommt, wird von keinem finanziert, und niemand zahlt
  dafür, aufgeführt, eingestuft oder auf eine bestimmte Weise beschrieben zu werden.
</p>
<p>{money_line}</p>

<h2>Offen gebaut</h2>
<p>
  Jede Seite wird aus einem Datensatz und einem Kostenmodell erzeugt, die beide öffentlich sind. Code,
  Dimensionierungswerte und datierte Preisaufzeichnungen finden Sie im
  <a href="{repo}" rel="noopener">Quell-Repository auf GitHub</a>, die Begründung jeder Annahme auf der
  <a href="{base}/methodology/">Methodik-Seite</a>.
</p>
<p>
  Aktuell sind das {len(built)} veröffentlichte Vergleiche auf Basis von {len(verified)} Preisen, die direkt von den
  Preisseiten der Anbieter abgelesen wurden. Vergleiche, die von einem ungeprüften Preis abhängen würden, werden
  zurückgehalten statt geschätzt.
</p>

<h2>Korrekturen</h2>
<p>
  Preise ändern sich, und wir werden manchmal hinterherhinken. Wenn eine Zahl falsch oder veraltet ist, schicken Sie
  die Seitenadresse und einen Link zur Anbieterseite mit dem aktuellen Preis. Wir lesen die Anbieterseite erneut,
  aktualisieren den Eintrag mit dem neuen Datum und erzeugen die Website neu. Korrekturen erfolgen nie allein auf
  Grundlage einer Behauptung, in keine Richtung.
</p>

<h2>Kontakt</h2>
<p>
  Für Korrekturen, Vorschläge für weitere Tools oder alles andere:
  <a href="mailto:{email}">{email}</a>. Jede Nachricht wird gelesen.
</p>
<p>
  Wir akzeptieren keine bezahlten Platzierungen, gesponserten Testberichte oder Bitten, ein Ergebnis zu ändern. Sie
  müssen also nicht fragen.
</p>
"""
    return (
        "about",
        "Über SelfHostCost und Kontakt",
        "Wer SelfHostCost betreibt, wie die Website finanziert wird, wie die Daten ehrlich bleiben, wie Sie einen "
        "veralteten Preis melden und wie Sie uns erreichen.",
        body,
    )


def _methodology(ds: Dataset, wave: int, strict: bool, built, base: str, loc: Locale) -> tuple[str, str, str, str]:
    cfg = ds.config
    m = cfg["tco_model"]
    rate = loc.money(m["engineer_hourly_usd"])
    horizon = m["horizon_months"]
    ref = cfg.get("reference_users", 10)
    fx = cfg["fx"]
    eur_rate = loc.number(fx["rates_to_usd"]["EUR"], 4)

    verified = sorted(
        (s for s in ds.saas.values() if s.get("price_status") == "verified" and s.get("wave", 1) <= wave),
        key=lambda s: s["name"].lower(),
    )
    unverified = sorted(
        (s for s in ds.saas.values() if s.get("price_status") != "verified"),
        key=lambda s: s["name"].lower(),
    )
    priced = priced_providers(ds)
    unpriced = [p for p in ds.providers.values() if p["price_status"] != "verified"]
    hm = m["maintenance_hours_per_month_by_difficulty"]
    hs = m["setup_hours_by_difficulty"]

    verified_rows = "\n".join(
        f"<tr><td>{s['name']}</td><td>{s['compare_tier']}</td>"
        f"<td><a href=\"{s['pricing_url']}\" rel=\"nofollow noopener\">Anbieterseite</a></td>"
        f"<td>{s['verified_on']}</td></tr>"
        for s in verified
    )
    priced_rows = "\n".join(
        f"<tr><td>{p['name']}</td><td>{len([x for x in p['plans'] if x.get('price_usd_month')])} Tarife</td>"
        f"<td><a href=\"{p['pricing_url']}\" rel=\"nofollow noopener\">Seite des Hosters</a></td>"
        f"<td>{p['verified_on']}</td></tr>"
        for p in priced
    )
    unpriced_sentence = ""
    if unpriced:
        names = ", ".join(p["name"] for p in unpriced)
        unpriced_sentence = (
            f"Die wichtigste Folge: {names} {'fehlen' if len(unpriced) > 1 else 'fehlt'} in allen Berechnungen, und "
            "gerade Hetzner ist pro Gigabyte Arbeitsspeicher meist günstiger als das, was wir angeben. Betrachten Sie "
            "unsere Serverkosten als Obergrenze."
        )

    body = f"""
<h1>Methodik: wie jede Zahl auf dieser Website entsteht</h1>

<p class="lead">
  Diese Seite existiert, damit Sie unsere Rechnung prüfen, unseren Annahmen widersprechen und genau sehen können,
  welche Preise wir bestätigt haben und welche nicht. Wenn sich eine Zahl auf dieser Website nicht auf etwas hier
  zurückführen lässt, ist das ein Fehler.
</p>

<h2>Die Form des Problems</h2>
<p>
  Software mit Preis pro Platz hat keinen Sockel, aber eine steile Steigung. Ein Server hat einen hohen Sockel, aber
  kaum Steigung. Jeder Vergleich hier ist der Punkt, an dem sich diese beiden Linien kreuzen. Deshalb lautet die
  ehrliche Antwort nie „Self-Hosting ist günstiger“, sondern „günstiger ab ungefähr so vielen Personen, wenn Ihre
  Zeit ungefähr so viel wert ist“.
</p>

<h2>Ein selbst gehostetes Tool dimensionieren</h2>
<p>Für ein Tool und eine Teamgröße ergibt sich der benötigte Arbeitsspeicher aus:</p>
<pre><code>arbeitsspeicher = (ram_basis + ram_pro_nutzer &times; nutzer) &times; {loc.number(1 + m['ram_headroom_ratio'], 2)}</code></pre>
<p>und der benötigte Speicherplatz aus:</p>
<pre><code>speicher = speicher_basis + speicher_pro_nutzer &times; nutzer</code></pre>
<ul>
  <li><strong>ram_basis</strong> umfasst den gesamten Stack im Ruhezustand, einschließlich Datenbank und aller
      Zusatzcontainer, die das Projekt in seiner Compose-Referenzdatei mitliefert. Es ist nicht nur der
      Anwendungsprozess.</li>
  <li><strong>Die {int(m['ram_headroom_ratio'] * 100)} % Reserve</strong> sind Absicht. Eine Maschine, die genau auf
      ihren Bedarf zugeschnitten ist, fällt beim Upgrade um.</li>
  <li><strong>Die vCPU-Zahl</strong> wird aus der Vorgabe des Projekts übernommen und <em>nicht</em> mit der
      Teamgröße skaliert. Bei diesen Lasten wird zuerst der Arbeitsspeicher knapp. Das ist eine Vereinfachung, und wir
      nennen sie lieber, als sie zu verstecken.</li>
</ul>
<p>
  Wenn ein Projekt Mindest- oder Empfehlungsanforderungen veröffentlicht, stammen die Grundwerte daraus, und die
  Seite sagt das. Andernfalls werden sie aus den Diensten seines Compose-Referenz-Stacks abgeleitet und als Schätzung
  gekennzeichnet. <strong>Die Zuschläge pro Nutzer stammen immer von uns.</strong> Sie sind großzügig statt
  optimistisch angesetzt, denn ein zu klein angesetzter Server lässt Self-Hosting besser aussehen, und wir wollen,
  dass die Verzerrung in die andere Richtung geht.
</p>

<h2>Den Server auswählen</h2>
<p>
  Wir nehmen den günstigsten Tarif unter den Anbietern, deren Preise wir selbst abgelesen haben, bei dem
  Arbeitsspeicher und Speicherplatz den Bedarf beide erreichen oder übertreffen. Keine Teillösungen, und kein So-tun,
  als passe ein Tool auf einen Tarif, dem ein Gigabyte fehlt.
</p>
<p>
  <strong>Wir vertrauen heute nur {len(priced)} {'Anbieter' if len(priced) == 1 else 'Anbietern'}.</strong> Das ist
  eine echte Einschränkung. Mehrere Hoster zeigen ihre Preise erst im Browser oder hinter einer Regionsauswahl an,
  und wir veröffentlichen keinen Preis, den wir nicht ablesen konnten. {unpriced_sentence}
</p>
<div class="tablewrap"><table>
<thead><tr><th>Anbieter</th><th>Berechnete Tarife</th><th>Quelle</th><th>Abgelesen am</th></tr></thead>
<tbody>
{priced_rows}
</tbody></table></div>

<h2>Die drei Kosten des Selbstbetriebs</h2>
<div class="tablewrap"><table>
<thead><tr><th>Posten</th><th>Wie er festgelegt wird</th><th>Warum</th></tr></thead>
<tbody>
<tr><td>Server</td><td>Der oben gewählte Tarif zum Listenpreis</td><td>Es werden keine Rabatte für Laufzeit oder Jahreszahlung angenommen.</td></tr>
<tr><td>Backups</td><td>{int(m['backup_cost_ratio'] * 100)} % des Serverpreises</td>
    <td>Ungefähr die Kosten von Anbieter-Snapshots. Backups als optional zu behandeln, würde jede Zahl auf dieser Website bedeutungslos machen.</td></tr>
<tr><td>Ihre Zeit</td>
    <td>{loc.hours(hm['easy'])} bis {loc.hours(hm['hard'])} Stunden pro Monat je nach Aufwand, zu {rate} pro Stunde</td>
    <td>Das ist meist der größte Posten, und ihn wegzulassen ist die häufigste Art, wie solche Vergleiche in die Irre führen.</td></tr>
<tr><td>Einrichtung, einmalig</td>
    <td>{loc.hours(hs['easy'])} bis {loc.hours(hs['hard'])} Stunden je nach Aufwand, zu {rate} pro Stunde</td>
    <td>Wird gegen die monatliche Ersparnis verrechnet und ergibt die Gewinnschwelle.</td></tr>
</tbody></table></div>

<h3>Der Aufwand und was er bedeutet</h3>
<div class="tablewrap"><table>
<thead><tr><th>Stufe</th><th>Bedeutung</th><th>Einrichtung</th><th>Pro Monat</th></tr></thead>
<tbody>
<tr><td>{loc.t('difficulty.easy')}</td><td>Ein Container, keine externen Abhängigkeiten, nichts zu tun außer Image-Updates</td>
    <td>{loc.hours(hs['easy'])} Std.</td><td>{loc.hours(hm['easy'])} Std.</td></tr>
<tr><td>{loc.t('difficulty.medium')}</td><td>Stack aus mehreren Containern mit einer Datenbank, deren Sicherung bei Ihnen liegt</td>
    <td>{loc.hours(hs['medium'])} Std.</td><td>{loc.hours(hm['medium'])} Std.</td></tr>
<tr><td>{loc.t('difficulty.hard')}</td><td>Mehrere zustandsbehaftete Dienste, ein nicht trivialer Upgrade-Pfad und ein echtes Risiko von Datenverlust bei Eile</td>
    <td>{loc.hours(hs['hard'])} Std.</td><td>{loc.hours(hm['hard'])} Std.</td></tr>
</tbody></table></div>

<h3>Wenn Ihre Zeit nichts kostet</h3>
<p>
  Jede Seite zeigt auch den Wert ohne Arbeitszeit. Beide Zahlen stimmen. Welche für Sie gilt, hängt davon ab, ob diese
  Stunden sonst abrechenbar gewesen wären oder ob Sie den Abend ohnehin zum Vergnügen damit verbracht hätten. Wir
  stellen den Wert mit Arbeitszeit voran, weil ein Unternehmen damit planen sollte.
</p>

<h2>Die kommerzielle Seite berechnen</h2>
<p>
  Wir vergleichen mit <strong>dem günstigsten Tarif, bei dem ein Team realistischerweise landen würde</strong>, nicht
  mit dem günstigsten Tarif, den es gibt. Den Einstiegstarif eines Anbieters mit seinen Antwortgrenzen und fehlenden
  Funktionen gegen ein vollständiges selbst gehostetes System zu stellen, wäre unehrlich, und genau so kommen die
  meisten Vergleichsseiten zu ihren Ergebnissen. Der verwendete Tarif wird auf jeder Seite genannt.
</p>
<p>
  Mindestanzahlen an Plätzen werden berücksichtigt. Wenn ein Anbieter nicht pro Platz abrechnet, sondern etwa nach
  ausgeführten Aufgaben, monatlich aktiven Nutzern oder Abonnenten, sagt die Seite das ausdrücklich, statt so zu tun,
  als sei die Teamgröße die richtige Achse. Wenn der kostenlose Tarif eines Anbieters das betreffende Team bereits
  abdeckt, sagt die Seite auch das und behauptet keine Ersparnis. Wenn der Preis pro Nutzer mit der Teamgröße sinkt,
  wird er für jede gezeigte Teamgröße abgelesen.
</p>

<h3>Preise, die wir bestätigt haben</h3>
<p>Direkt von der Preisseite des Anbieters abgelesen, am angegebenen Datum:</p>
<div class="tablewrap"><table>
<thead><tr><th>Produkt</th><th>Verglichener Tarif</th><th>Quelle</th><th>Abgelesen am</th></tr></thead>
<tbody>
{verified_rows}
</tbody></table></div>

<h3>Preise, die wir nicht bestätigt haben</h3>
<p>
  {len(unverified)} Produkte in unserem Datensatz haben keinen bestätigten Preis.
  {'Da der strenge Modus aktiv ist, <strong>wurde keine Seite veröffentlicht, die von einem davon abhängen würde</strong>.' if strict else '<strong>Der strenge Modus ist in diesem Build ausgeschaltet, daher können Zahlen auf dieser Website auf unbestätigten Preisen beruhen.</strong> Das ist eine Entwicklungseinstellung, keine Version zum Lesen.'}
  Es handelt sich um: {', '.join(s['name'] for s in unverified) if unverified else 'keine'}.
</p>

<h3>Währungen</h3>
<p>
  Alle Berechnungen erfolgen in US-Dollar. In dieser deutschen Version werden die Beträge anschließend in Euro
  angezeigt, zu einem einzigen datierten Kurs von <strong>1 EUR = {eur_rate} USD</strong>, dem Kurs von
  <a href="{fx['source_url']}" rel="nofollow noopener">{fx['source_name']}</a> vom {fx['on']}. Manche Anbieter
  zeigten ihre Preise bereits in Euro: Diese werden für die Berechnung zum selben Kurs in Dollar umgerechnet und für
  die Anzeige zurückgerechnet. Die Quellentabellen nennen den Preis immer in der ursprünglichen Währung.
</p>

<h2>Der Zeitraum und die Gewinnschwelle</h2>
<p>
  Summen beziehen sich auf <strong>{horizon} Monate</strong>. Die Gewinnschwelle sind die Einrichtungskosten geteilt
  durch die monatliche Ersparnis:
</p>
<pre><code>gewinnschwelle_monate = einrichtungskosten / (saas_monatlich - selbst_gehostet_monatlich)</code></pre>
<p>
  Wenn die monatliche Ersparnis null oder negativ ist, gibt es keine Gewinnschwelle, und die Seite zeigt „nie“, statt
  die Zeile stillschweigend wegzulassen.
</p>

<h2>Was dieses Modell bewusst ignoriert</h2>
<ul>
  <li><strong>Den Migrationsaufwand.</strong> Ihre bestehenden Daten aus dem bisherigen Tool heraus- und in den Ersatz
      hineinzubekommen, ist echte Arbeit und wird nirgends gezählt. Bei großen historischen Datenmengen kann er die
      Einrichtungskosten weit übersteigen.</li>
  <li><strong>Funktionsgleichheit.</strong> Die Tools sind nahe Ersatzprodukte, keine Kopien. Kosten sind eine Achse
      und oft nicht die entscheidende.</li>
  <li><strong>Risiko.</strong> Ein missglücktes Upgrade, eine verlorene Datenbank oder ein Wochenende mit einem Ausfall
      haben erwartbare Kosten, die eine Tabelle nicht ehrlich erfassen kann.</li>
  <li><strong>Traffic-Überschreitungen, verwaltete Datenbanken und Objektspeicher</strong> über das hinaus, was der
      gewählte Tarif enthält. Einige Tools brauchen tatsächlich externen Objektspeicher, und ihre Seiten nennen ihn,
      aber er ist nicht eingerechnet.</li>
  <li><strong>Rabatte für Jahreszahlung oder Laufzeit</strong> auf der Hosting-Seite. Beide Seiten werden auf der
      Basis angegeben, die die Anbieterseite zeigte, und die Seite nennt diese Basis.</li>
  <li><strong>Ihre vorhandene Infrastruktur.</strong> Wenn Sie bereits einen Server mit freiem Arbeitsspeicher
      betreiben, liegen die Grenzkosten eines weiteren Containers nahe null, und keine dieser Zahlen trifft auf Sie zu.</li>
</ul>

<h2>Wie aktuell diese Seite ist</h2>
<p>
  Preise sind eine datierte Momentaufnahme, kein Live-Feed. Jede Zahl verlinkt auf ihre Quelle, und maßgeblich ist die
  Seite des Anbieters. Ein Preis, der älter als etwa 45 Tage ist, sollte als Richtwert gelten und vor jeder Ausgabe
  erneut geprüft werden.
</p>
<p>
  Aktuell: {len(built)} veröffentlichte Vergleiche, Welle {wave}, Referenz-Teamgröße {ref} Personen, strenge
  Preisprüfung {'aktiv' if strict else '<strong>ausgeschaltet</strong>'}.
</p>
"""
    return (
        "methodology",
        "Methodik: wie jede Kostenzahl auf dieser Website berechnet wird",
        "Das Dimensionierungsmodell, die Annahmen zur Arbeitszeit, die genauen Preisquellen mit Datum und alles, was "
        "dieses Kostenmodell bewusst weglässt.",
        body,
    )


_REWARDS = {
    "digitalocean": (
        "Die DigitalOcean-Links auf unseren Seiten sind die Empfehlungslinks von DigitalOcean selbst. Wenn Sie "
        "sich über einen davon anmelden und Ihre ersten 25 $ bezahlen, schreibt uns DigitalOcean 25 $ Guthaben "
        "gut. Das kostet Sie nichts, und es ist Guthaben auf einem Hosting-Konto, kein Bargeld."
    ),
    "kamatera": (
        "Die Kamatera-Links auf unseren Seiten sind Affiliate-Links. Wenn Sie darüber ein kostenpflichtiges "
        "Konto eröffnen, zahlt uns Kamatera eine einmalige Provision: 75 $ in den meisten Ländern, darunter "
        "Deutschland, und 10 $ in einigen anderen. Das kostet Sie nichts und ist nicht wiederkehrend."
    ),
}


def _disclosure(ds: Dataset, base: str) -> tuple[str, str, str, str]:
    from .content import tracked_providers
    cfg = ds.config
    aff = cfg.get("affiliate", {})
    tracked = tracked_providers(cfg)

    def reward_line(slug: str) -> str:
        if slug in _REWARDS:
            return _REWARDS[slug]
        name = ds.providers.get(slug, {}).get("name", slug)
        return (f"Die {name}-Links auf unseren Seiten sind nachverfolgte Affiliate-Links. Wenn Sie sich über "
                f"einen davon anmelden, erhalten wir möglicherweise eine Provision. Das kostet Sie nichts.")

    if tracked:
        items = "".join(f"<li>{reward_line(s)}</li>" for s in tracked)
        rest = ("<p>Links zu allen anderen Anbietern sind einfache Links ohne Zusatz.</p>"
                if len(tracked) < len(aff.get("providers", {})) else "")
        state = (
            "<p><strong>Auf dieser Website sind derzeit Empfehlungslinks aktiv.</strong></p>"
            f"<ul>{items}</ul>{rest}"
        )
    else:
        state = (
            "<p><strong>Auf dieser Website gibt es derzeit keine Affiliate-Links.</strong> Jeder Hosting-Link "
            "hier ist ein einfacher Link zur Seite des Anbieters. Wenn sich das ändert, ändert sich diese Seite "
            "mit, und der Hinweis erscheint auf jeder Seite mit einem solchen Link.</p>"
        )

    body = f"""
<h1>Hinweis zu Empfehlungs- und Affiliate-Links</h1>

<p class="lead">
  Vergleichsseiten, die an dem verdienen, was sie empfehlen, haben einen offensichtlichen Interessenkonflikt. So
  halten wir unseren in Grenzen.
</p>

{state}

<h2>Was eine Vergütung nicht beeinflussen kann</h2>
<ul>
  <li><strong>Welcher Anbieter auf einer Seite empfohlen wird.</strong> Der Server auf jeder Seite wird nach einer
      einzigen Regel gewählt: der günstigste Tarif unter den Anbietern, deren Preise wir abgelesen haben, der den
      berechneten Bedarf an Arbeitsspeicher und Speicherplatz erfüllt. Diese Regel steht im Build-Skript und weiß nicht,
      was uns jemand zahlt.</li>
  <li><strong>Die Zahlen.</strong> Jede Zahl wird aus dem <a href="{base}/methodology/">veröffentlichten Modell</a>
      und datierten Preisquellen berechnet. Sie können jede davon von Hand nachrechnen.</li>
  <li><strong>Das Ergebnis.</strong> Viele Seiten kommen zu dem Schluss, dass das kostenpflichtige Produkt günstiger ist
      und Sie nicht selbst hosten sollten. Diese Seiten bringen nichts ein. Sie bleiben, wie sie sind, weil ein
      Vergleich, der immer zur selben Antwort kommt, kein Vergleich ist.</li>
</ul>

<h2>Was eine Vergütung ehrlicherweise beeinflusst</h2>
<p>
  Bei welchen Anbietern wir die Preise zuerst geprüft haben, ist nicht völlig unabhängig davon, welche ein
  Empfehlungsprogramm haben. Derzeit berechnen wir
  {', '.join(p['name'] for p in priced_providers(ds)) or 'keine Anbieter'}, und die
  <a href="{base}/hosting/">Hosting-Seite</a> nennt jeden Anbieter, den wir nicht berechnen konnten, auch solche, die wir
  für günstiger halten. Diese Lücke wird offengelegt statt verschwiegen.
</p>

<h2>Keine bezahlte Platzierung</h2>
<p>
  Kein Anbieter, Softwarehersteller oder Open-Source-Projekt hat dafür bezahlt, hier zu erscheinen, eingestuft oder
  auf eine bestimmte Weise beschrieben zu werden. Niemand darf eine Seite vor der Veröffentlichung prüfen.
</p>

<h2>Keine Beratung</h2>
<p>
  Dies sind Kostenmodelle, keine Empfehlungen für Ihr Unternehmen. Preise ändern sich, unsere Momentaufnahmen veralten,
  und maßgeblich ist immer die Seite des Anbieters. Prüfen Sie, bevor Sie Geld ausgeben.
</p>
"""
    return (
        "disclosure",
        "Hinweis zu Empfehlungslinks und wie wir mit dem Interessenkonflikt umgehen",
        "Ob diese Website an Hosting-Links verdient, was das beeinflussen kann und was nicht, und welche Lücken wir "
        "offenlegen statt verstecken.",
        body,
    )


def _privacy(ds: Dataset, base: str) -> tuple[str, str, str, str]:
    cfg = ds.config
    an = cfg.get("analytics", {})
    form_id = (cfg.get("lead_capture", {}).get("form_ids") or {}).get("de") if cfg.get("lead_capture", {}).get("enabled") else None
    tracking = (
        f"<p>Wir nutzen <strong>{an['provider']}</strong> für eine zusammengefasste Reichweitenmessung, konfiguriert "
        "ohne Cookies und ohne websiteübergreifende Kennungen. Wir können damit keine einzelnen Besucher identifizieren.</p>"
        if an.get("provider") not in (None, "", "none") else
        "<p><strong>Auf dieser Website gibt es überhaupt kein Analyse-Skript.</strong> Es werden keine Cookies gesetzt, "
        "nichts wird in Ihrem Browser gespeichert, und wir erheben keine Daten über einzelne Besucher.</p>"
    )
    lead = (
        "<p>Wenn Sie das Formular für die Migrations-Checkliste absenden, wird die eingegebene E-Mail-Adresse von unserem "
        "Formularanbieter verarbeitet, damit wir Ihnen senden können, was Sie angefordert haben. Sie wird nicht verkauft "
        "und an keinen Hosting-Anbieter weitergegeben.</p>"
        if form_id else
        "<p>Die deutschen Seiten enthalten derzeit kein Formular. Es gibt also nichts abzusenden und nichts, was wir "
        "speichern.</p>"
    )

    body = f"""
<h1>Datenschutz</h1>

<p class="lead">
  Eine Website, bei der es darum geht, Ihre Daten nicht anderen zu überlassen, sollte mit Ihren Daten sorgsam
  umgehen. Diese Seite ist kurz, weil es sehr wenig zu beschreiben gibt.
</p>

<h2>Reichweitenmessung</h2>
{tracking}

<h2>Formulare</h2>
{lead}

<h2>E-Mail</h2>
<p>
  Wenn Sie an {cfg.get('contact_email', 'uns')} schreiben, werden Ihre Adresse und Ihre Nachricht nur verwendet, um
  Ihnen zu antworten und, bei einer Korrektur, die gemeldete Zahl zu prüfen. Sie werden in keine Liste aufgenommen,
  nicht verkauft und mit keinem Anbieter oder Hoster geteilt. Das Postfach ist ein normales Gmail-Konto, daher
  verarbeitet Google diese Nachrichten nach seinen eigenen Bedingungen.
</p>

<h2>Externe Links</h2>
<p>
  Links zu Hostern, Softwareanbietern und Open-Source-Projekten führen zu Websites, die wir nicht kontrollieren und
  deren Datenschutzpraxis ihre eigene ist. Ist ein Link vergütet, ist er im Code der Seite entsprechend markiert und
  auf der Seite gekennzeichnet; siehe den <a href="{base}/disclosure/">Hinweis zu Empfehlungslinks</a>.
</p>

<h2>Hosting</h2>
<p>
  Diese Website besteht aus statischen Dateien, die von GitHub Pages ausgeliefert werden. GitHub verarbeitet dabei
  Server-Logs einschließlich IP-Adressen nach seinen eigenen Datenschutzbedingungen, nicht nach unseren.
</p>

<h2>Keine Inhalte von Dritten</h2>
<p>
  Jede Seite lädt ein Stylesheet und ein kleines SVG-Symbol von dieser Domain. Es gibt keine Webfonts, keine
  Tag-Manager, keine eingebetteten Videos und keine Social-Media-Widgets, sodass beim Lesen einer Seite kein Dritter
  kontaktiert wird{', abgesehen vom Formularanbieter auf Seiten mit Formular' if form_id else ''}.
</p>

<p class="srcline">Zuletzt geprüft: {MODIFIED}.</p>
"""
    return (
        "privacy",
        "Datenschutz",
        "Was diese Website erhebt, nämlich fast nichts, und welche Dritten kontaktiert werden, wenn Sie eine Seite lesen.",
        body,
    )
