"""
Pages rédigées en français. Même structure et mêmes calculs que content.py ; seul
le texte change. Les montants passent par Locale, qui les affiche en euros au
taux daté publié dans la méthodologie.
"""

from __future__ import annotations

from lib.dates import MODIFIED

from .i18n import Locale
from .model import Dataset, priced_providers


def static_pages(ds: Dataset, wave: int, strict: bool, built, pairs, base: str):
    loc = Locale("fr", ds.config)
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
<h1>Checklist de migration vers l'auto-hébergement</h1>

<p class="lead">
  Une liste de contrôle d'une page pour faire passer une équipe d'un outil payant à un outil auto-hébergé. Elle
  couvre les étapes qui décident si la migration sera banale ou désastreuse : l'export des données, le
  dimensionnement, les sauvegardes, et le plan de retour arrière que la plupart des gens oublient.
</p>

<div class="note caution">
  <p><strong>Ne résiliez pas l'abonnement avant d'avoir terminé la dernière section.</strong> Faites tourner les
  deux en parallèle jusqu'à avoir restauré une sauvegarde et jusqu'à ce que l'équipe ait utilisé le nouvel outil
  pour du vrai travail.</p>
</div>

<h2>1. Avant d'installer quoi que ce soit</h2>
<ul>
  <li><strong>Exportez dès aujourd'hui une vraie copie de vos données.</strong> Pas un compte de test : votre
      espace de travail réel. Certains exports sont partiels, limités en débit ou réservés aux offres supérieures.
      Mieux vaut le découvrir maintenant que le jour où votre contrat se termine.</li>
  <li><strong>Ouvrez l'export et vérifiez ce qui manque.</strong> Pièces jointes, commentaires, historique,
      mentions d'utilisateurs et permissions sont les victimes habituelles.</li>
  <li><strong>Confirmez que le remplaçant sait importer ce format.</strong> Sinon, prévoyez le temps de
      conversion. Ce coût ne figure dans aucun chiffre de ce site.</li>
  <li><strong>Listez les intégrations dont vous dépendez.</strong> SSO, notifications de messagerie, webhooks,
      synchronisation d'agenda. Vérifiez que chacune existe pour l'outil auto-hébergé.</li>
  <li><strong>Vérifiez la licence.</strong> Plusieurs outils populaires sont en code source disponible plutôt
      qu'open source, avec des limites sur l'usage commercial. Chaque page outil de ce site le signale.</li>
  <li><strong>Nommez un responsable.</strong> Un logiciel auto-hébergé sans personne chargée des mises à jour,
      c'est la façon la plus courante dont ces projets échouent.</li>
</ul>

<h2>2. Dimensionnement et installation</h2>
<ul>
  <li><strong>Dimensionnez le serveur à partir de la page de coût de l'outil pour votre taille d'équipe</strong>,
      en gardant les {int(m['ram_headroom_ratio'] * 100)} % de marge de mémoire. Un serveur dimensionné au plus
      juste a tendance à tomber lors de sa première montée de version.</li>
  <li><strong>Utilisez le fichier Docker Compose du projet</strong> plutôt qu'un fichier tiers, et fixez la version
      de l'image au lieu d'utiliser <code>latest</code>.</li>
  <li><strong>Placez-le derrière HTTPS, sur son propre sous-domaine</strong>, dès le premier jour. Changer l'adresse
      plus tard casse les liens, les retours OAuth et les applications mobiles.</li>
  <li><strong>Configurez l'e-mail sortant</strong> via un service d'envoi transactionnel. Sans cela, les
      réinitialisations de mot de passe et les notifications échouent sans bruit, et la plupart des outils ne vous
      préviennent pas.</li>
  <li><strong>Fermez tous les ports sauf 80 et 443</strong>, et n'exposez jamais la base de données directement.</li>
  <li><strong>Activez le SSO, ou au minimum la double authentification obligatoire</strong>, avant d'inviter qui
      que ce soit.</li>
</ul>

<h2>3. Des sauvegardes testées</h2>
<ul>
  <li><strong>Sauvegardez à la fois la base de données et les fichiers envoyés.</strong> Un dump de base sans le
      dossier des fichiers restaure un outil rempli de pièces jointes cassées.</li>
  <li><strong>Gardez au moins une copie hors du serveur</strong>, chez un autre fournisseur ou dans une autre
      région que le serveur lui-même.</li>
  <li><strong>Automatisez-les, et soyez alerté en cas d'échec.</strong> Une tâche de sauvegarde arrêtée depuis
      trois semaines, c'est la façon normale de découvrir qu'on n'avait pas de sauvegarde.</li>
  <li><strong>Restaurez-la sur un serveur neuf avant la mise en service.</strong> Chronométrez l'opération. Ce
      chiffre est votre vrai temps de reprise ; tant que vous ne l'avez pas, vous n'avez pas de sauvegardes, seulement
      des fichiers.</li>
</ul>

<h2>4. La bascule</h2>
<ul>
  <li><strong>Choisissez un jour calme et annoncez un gel des contenus</strong> sur l'ancien outil pendant la
      migration.</li>
  <li><strong>Faites un dernier export après le gel</strong>, importez-le, et contrôlez un échantillon
      d'enregistrements, de pièces jointes et de permissions par rapport à l'ancien outil.</li>
  <li><strong>Faites passer un petit groupe d'abord</strong>, pour une semaine de vrai travail, avant tout le
      monde.</li>
  <li><strong>Redirigez ou mettez à jour les favoris</strong> partout où l'ancienne adresse était référencée :
      documentation, messagerie, navigateurs, applications mobiles.</li>
</ul>

<h2>5. Le plan de retour arrière que la plupart des gens oublient</h2>
<ul>
  <li><strong>Écrivez avant la bascule ce qui vous ferait revenir en arrière.</strong> Perte de données, fonction
      indispensable manquante, pannes à répétition. Fixez le seuil pendant que vous êtes calme.</li>
  <li><strong>Gardez l'ancien abonnement un cycle de facturation de plus</strong> après la mise en service, même si
      cela semble du gaspillage. C'est l'assurance la moins chère que vous achèterez.</li>
  <li><strong>Sachez comment réexporter depuis le nouvel outil</strong> vers un format que l'ancien sait lire.</li>
  <li><strong>Ne résiliez l'ancien abonnement qu'une fois</strong> un test de restauration réussi, l'équipe entière
      passée sur le nouvel outil pour du vrai travail, et personne n'ayant réclamé l'ancien.</li>
</ul>

<h2>6. Après la mise en service</h2>
<ul>
  <li><strong>Inscrivez les mises à jour à l'agenda.</strong> Ce site prévoit de
      {loc.hours(m['maintenance_hours_per_month_by_difficulty']['easy'])} à
      {loc.hours(m['maintenance_hours_per_month_by_difficulty']['hard'])} heures par mois selon l'outil. Ce qui n'est
      pas planifié n'est pas fait.</li>
  <li><strong>Lisez les notes de version avant chaque mise à jour</strong>, surtout pour les versions majeures avec
      migration de base de données.</li>
  <li><strong>Ajoutez une supervision de disponibilité</strong> pour apprendre une panne avant votre équipe.</li>
  <li><strong>Refaites le test de restauration</strong> tous les quelques mois.</li>
</ul>

<h2>Avant de commencer</h2>
<p>
  Si vous n'avez pas encore chiffré la migration, vérifiez que l'auto-hébergement fait vraiment économiser de
  l'argent pour votre taille d'équipe. Pour certains outils, ce n'est pas le cas une fois les heures ci-dessus
  comptées. <a href="{base}/compare/">Voir tous les comparatifs</a> ou
  <a href="{base}/methodology/">lire comment les coûts sont calculés</a>.
</p>
"""
    return (
        "migration-checklist",
        "Checklist de migration vers l'auto-hébergement : avant de résilier l'abonnement",
        "Une checklist pratique pour passer d'un outil payant à un outil auto-hébergé : export des données, "
        "dimensionnement, sauvegardes testées, bascule et plan de retour arrière.",
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
        "La seule relation financière de ce site avec qui que ce soit qu'il mentionne est le lien de parrainage "
        "standard de DigitalOcean, qui rapporte du crédit d'hébergement quand quelqu'un s'inscrit par ce lien et "
        "paie ses premiers 25 $. Il est signalé sur chaque page qui le contient et décrit en détail sur la "
        f"<a href=\"{base}/disclosure/\">page de transparence</a>."
        if referral_on else
        "Le site n'a actuellement aucun lien d'affiliation ni de parrainage et ne rapporte rien. Si cela change, la "
        f"<a href=\"{base}/disclosure/\">page de transparence</a> change le jour même."
    )

    body = f"""
<h1>À propos de SelfHostCost</h1>

<p class="lead">
  SelfHostCost répond à une seule question, outil par outil et taille d'équipe par taille d'équipe : faire tourner
  soi-même une alternative open source coûte-t-il vraiment moins cher que payer le logiciel, une fois comptés le
  serveur, les sauvegardes et vos propres heures ?
</p>

<h2>Pourquoi ce site existe</h2>
<p>
  La plupart des listes d'« alternatives auto-hébergées » s'arrêtent au prix de la licence, ce qui fait paraître
  l'auto-hébergement gratuit. La plupart des comparatifs d'éditeurs s'arrêtent aux fonctionnalités, ce qui fait
  paraître l'abonnement inévitable. Aucun ne chiffre ce qui tranche la question : un serveur a un plancher élevé et
  presque pas de pente, un siège n'a pas de plancher mais une pente raide. Ce site calcule où ces deux droites se
  croisent, et publie la réponse même quand elle est « continuez à payer ».
</p>

<h2>Qui le gère</h2>
<p>
  SelfHostCost est un projet indépendant, lancé le {cfg.get('launched_on', '')}. Il n'appartient à aucun éditeur de
  logiciel, hébergeur ou projet open source présent sur le site, n'est financé par aucun d'eux, et personne ne paie
  pour être listé, classé ou décrit d'une certaine façon.
</p>
<p>{money_line}</p>

<h2>Construit en toute transparence</h2>
<p>
  Chaque page est générée à partir d'un jeu de données et d'un modèle de coûts tous deux publics. Vous pouvez lire
  le code, les chiffres de dimensionnement et les relevés de prix datés dans le
  <a href="{repo}" rel="noopener">dépôt source sur GitHub</a>, et le raisonnement derrière chaque hypothèse sur la
  <a href="{base}/methodology/">page méthodologie</a>.
</p>
<p>
  Aujourd'hui, cela représente {len(built)} comparatifs publiés, fondés sur {len(verified)} prix relevés directement
  sur les pages tarifaires des éditeurs. Les comparatifs qui dépendraient d'un prix non vérifié sont retenus plutôt
  qu'estimés.
</p>

<h2>Corrections</h2>
<p>
  Les prix changent et nous aurons parfois du retard. Si un chiffre est faux ou périmé, envoyez l'adresse de la page
  et un lien vers la page de l'éditeur montrant le prix actuel. Nous relisons la page de l'éditeur, mettons à jour le
  relevé avec la nouvelle date, puis régénérons le site. Aucune correction n'est faite sur la seule base d'une
  affirmation, dans un sens comme dans l'autre.
</p>

<h2>Contact</h2>
<p>
  Pour une correction, une suggestion d'outil à ajouter, ou toute autre question :
  <a href="mailto:{email}">{email}</a>. Chaque message est lu.
</p>
<p>
  Nous n'acceptons ni placement payant, ni article sponsorisé, ni demande de modification d'une conclusion : inutile
  de demander.
</p>
"""
    return (
        "about",
        "À propos de SelfHostCost et contact",
        "Qui gère SelfHostCost, comment le site est financé, comment les données restent honnêtes, comment signaler "
        "un prix périmé et comment nous contacter.",
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
        f"<td><a href=\"{s['pricing_url']}\" rel=\"nofollow noopener\">page de l'éditeur</a></td>"
        f"<td>{s['verified_on']}</td></tr>"
        for s in verified
    )
    priced_rows = "\n".join(
        f"<tr><td>{p['name']}</td><td>{len([x for x in p['plans'] if x.get('price_usd_month')])} offres</td>"
        f"<td><a href=\"{p['pricing_url']}\" rel=\"nofollow noopener\">page de l'hébergeur</a></td>"
        f"<td>{p['verified_on']}</td></tr>"
        for p in priced
    )
    unpriced_sentence = ""
    if unpriced:
        names = ", ".join(p["name"] for p in unpriced)
        unpriced_sentence = (
            f"Conséquence la plus importante : {names} "
            f"{'sont absents' if len(unpriced) > 1 else 'est absent'} de tous les calculs, et Hetzner en particulier est "
            "généralement moins cher par gigaoctet de mémoire que ce que nous citons. Considérez nos coûts de serveur "
            "comme un plafond."
        )

    body = f"""
<h1>Méthodologie : comment chaque chiffre de ce site est produit</h1>

<p class="lead">
  Cette page existe pour que vous puissiez vérifier nos calculs, contester nos hypothèses, et voir exactement quels
  prix nous avons confirmés et lesquels nous n'avons pas confirmés. Si un chiffre de ce site ne peut pas être relié
  à quelque chose ici, c'est un bug.
</p>

<h2>La forme du problème</h2>
<p>
  Un logiciel facturé au siège n'a pas de plancher mais une pente raide. Un serveur a un plancher élevé mais presque
  pas de pente. Chaque comparatif ici est le point où ces deux droites se croisent : c'est pourquoi la réponse
  honnête n'est jamais « l'auto-hébergement est moins cher », mais « moins cher au-delà d'à peu près tant de
  personnes, si votre temps vaut à peu près tant ».
</p>

<h2>Dimensionner un outil auto-hébergé</h2>
<p>Pour un outil et une taille d'équipe, la mémoire nécessaire est :</p>
<pre><code>mémoire = (ram_base + ram_par_utilisateur &times; utilisateurs) &times; {loc.number(1 + m['ram_headroom_ratio'], 2)}</code></pre>
<p>et le disque nécessaire est :</p>
<pre><code>disque = disque_base + disque_par_utilisateur &times; utilisateurs</code></pre>
<ul>
  <li><strong>ram_base</strong> couvre toute la pile au repos, y compris la base de données et chaque conteneur
      annexe fourni par le projet dans son fichier Compose de référence. Ce n'est pas le seul processus applicatif.</li>
  <li><strong>Les {int(m['ram_headroom_ratio'] * 100)} % de marge</strong> sont délibérés. Une machine dimensionnée
      au plus juste est une machine qui tombe pendant une mise à jour.</li>
  <li><strong>Le nombre de vCPU</strong> est repris de la base du projet et <em>n'augmente pas</em> avec la taille
      de l'équipe. Pour ces charges, la mémoire s'épuise en premier. C'est une simplification, et nous préférons la
      nommer plutôt que la cacher.</li>
</ul>
<p>
  Quand un projet publie une configuration minimale ou recommandée, les valeurs de base en viennent et la page le
  dit. Sinon, elles sont déduites des services de sa pile Compose de référence et la page les signale comme une
  estimation. <strong>Les incréments par utilisateur sont toujours les nôtres.</strong> Ils sont fixés généreusement
  plutôt qu'avec optimisme, car sous-dimensionner le serveur flatte l'auto-hébergement et nous préférons que le biais
  aille dans l'autre sens.
</p>

<h2>Choisir le serveur</h2>
<p>
  Nous prenons l'offre la moins chère, parmi les hébergeurs dont nous avons relevé les prix nous-mêmes, dont la
  mémoire et le disque atteignent ou dépassent tous deux le besoin. Pas d'ajustement partiel, et pas question de
  prétendre qu'un outil tiendra sur une offre à laquelle il manque un gigaoctet.
</p>
<p>
  <strong>Nous ne nous fions aujourd'hui qu'à {len(priced)} hébergeur{'' if len(priced) == 1 else 's'}.</strong>
  C'est une vraie limite. Plusieurs hébergeurs affichent leurs prix via le navigateur ou derrière un sélecteur de
  région, et nous ne publions pas un prix que nous n'avons pas pu lire. {unpriced_sentence}
</p>
<div class="tablewrap"><table>
<thead><tr><th>Hébergeur</th><th>Offres chiffrées</th><th>Source</th><th>Relevé le</th></tr></thead>
<tbody>
{priced_rows}
</tbody></table></div>

<h2>Les trois coûts de l'auto-hébergement</h2>
<div class="tablewrap"><table>
<thead><tr><th>Poste</th><th>Comment il est fixé</th><th>Pourquoi</th></tr></thead>
<tbody>
<tr><td>Serveur</td><td>L'offre choisie ci-dessus, au prix catalogue</td><td>Aucune remise d'engagement ou annuelle n'est supposée.</td></tr>
<tr><td>Sauvegardes</td><td>{int(m['backup_cost_ratio'] * 100)} % du prix du serveur</td>
    <td>À peu près le coût des snapshots de l'hébergeur. Traiter les sauvegardes comme optionnelles rendrait tous les chiffres de ce site vides de sens.</td></tr>
<tr><td>Votre temps</td>
    <td>De {loc.hours(hm['easy'])} à {loc.hours(hm['hard'])} heures par mois selon la difficulté, à {rate} de l'heure</td>
    <td>C'est en général la ligne la plus lourde, et l'oublier est la façon la plus courante dont ces comparatifs induisent en erreur.</td></tr>
<tr><td>Mise en place, une fois</td>
    <td>De {loc.hours(hs['easy'])} à {loc.hours(hs['hard'])} heures selon la difficulté, à {rate} de l'heure</td>
    <td>Amortie sur l'économie mensuelle pour donner le seuil de rentabilité.</td></tr>
</tbody></table></div>

<h3>La difficulté, et ce qu'elle implique</h3>
<div class="tablewrap"><table>
<thead><tr><th>Niveau</th><th>Signification</th><th>Mise en place</th><th>Par mois</th></tr></thead>
<tbody>
<tr><td>{loc.t('difficulty.easy')}</td><td>Un seul conteneur, aucune dépendance externe, rien à faire au-delà de la mise à jour de l'image</td>
    <td>{loc.hours(hs['easy'])} h</td><td>{loc.hours(hm['easy'])} h</td></tr>
<tr><td>{loc.t('difficulty.medium')}</td><td>Pile multi-conteneurs avec une base de données dont vous assurez la sauvegarde</td>
    <td>{loc.hours(hs['medium'])} h</td><td>{loc.hours(hm['medium'])} h</td></tr>
<tr><td>{loc.t('difficulty.hard')}</td><td>Plusieurs services avec état, une montée de version non triviale, et un vrai risque de perte de données en cas de précipitation</td>
    <td>{loc.hours(hs['hard'])} h</td><td>{loc.hours(hm['hard'])} h</td></tr>
</tbody></table></div>

<h3>Si votre temps est gratuit</h3>
<p>
  Chaque page montre aussi le chiffre sans le temps passé. Les deux chiffres sont réels. Celui qui vous concerne
  dépend de si ces heures auraient pu être facturées, ou si vous y auriez de toute façon passé la soirée par plaisir.
  Nous mettons en avant le chiffre avec le temps compté, car c'est celui sur lequel une entreprise doit se fonder.
</p>

<h2>Chiffrer le côté commercial</h2>
<p>
  Nous comparons avec <strong>l'offre la moins chère sur laquelle une équipe atterrirait réellement</strong>, pas
  avec l'offre la moins chère qui existe. Opposer l'offre d'entrée d'un éditeur, avec ses plafonds de réponses et ses
  fonctions manquantes, à un déploiement auto-hébergé complet serait malhonnête, et c'est ainsi que la plupart des
  comparatifs arrivent à leurs conclusions. L'offre utilisée est nommée sur chaque page.
</p>
<p>
  Les minimums de sièges sont respectés. Quand un éditeur facture autre chose que des sièges, comme des tâches
  exécutées, des utilisateurs actifs mensuels ou des abonnés, la page le dit explicitement au lieu de faire comme si
  la taille de l'équipe était le bon axe. Quand l'offre gratuite d'un éditeur couvre déjà l'équipe concernée, la page
  le dit aussi, et n'annonce aucune économie. Quand le prix par utilisateur baisse avec la taille de l'équipe, il est
  relevé pour chaque taille présentée.
</p>

<h3>Les prix que nous avons confirmés</h3>
<p>Relevés directement sur la page tarifaire de l'éditeur, à la date indiquée :</p>
<div class="tablewrap"><table>
<thead><tr><th>Produit</th><th>Offre comparée</th><th>Source</th><th>Relevé le</th></tr></thead>
<tbody>
{verified_rows}
</tbody></table></div>

<h3>Les prix que nous n'avons pas confirmés</h3>
<p>
  {len(unverified)} produits de notre base n'ont pas de prix confirmé.
  {'Le mode strict étant activé, <strong>aucune page qui dépendrait de l’un d’eux n’a été publiée</strong>.' if strict else '<strong>Le mode strict est désactivé dans cette version : des chiffres de ce site peuvent reposer sur des prix non confirmés.</strong> C’est un réglage de développement, pas une version à lire.'}
  Il s'agit de : {', '.join(s['name'] for s in unverified) if unverified else 'aucun'}.
</p>

<h3>Devises</h3>
<p>
  Tous les calculs sont faits en dollars américains. Sur cette version française, les montants sont ensuite affichés
  en euros au taux unique et daté de <strong>1 EUR = {eur_rate} USD</strong>, le taux
  <a href="{fx['source_url']}" rel="nofollow noopener">{fx['source_name']}</a> du {fx['on']}. Certains éditeurs
  affichaient déjà leurs prix en euros : ces prix sont convertis en dollars au même taux pour le calcul, puis
  reconvertis pour l'affichage. Les tableaux de sources indiquent toujours le prix dans la devise d'origine.
</p>

<h2>L'horizon et le seuil de rentabilité</h2>
<p>
  Les totaux portent sur <strong>{horizon} mois</strong>. Le seuil de rentabilité est le coût de mise en place divisé
  par l'économie mensuelle :
</p>
<pre><code>seuil_en_mois = cout_mise_en_place / (saas_mensuel - auto_heberge_mensuel)</code></pre>
<p>
  Quand l'économie mensuelle est nulle ou négative, il n'y a pas de seuil, et la page affiche « jamais » plutôt que
  d'omettre la ligne en silence.
</p>

<h2>Ce que ce modèle ignore délibérément</h2>
<ul>
  <li><strong>L'effort de migration.</strong> Sortir vos données de l'outil en place et les faire entrer dans le
      remplaçant est un vrai travail, compté nulle part. Pour un historique volumineux, il peut dépasser de loin le
      coût de mise en place.</li>
  <li><strong>La parité fonctionnelle.</strong> Les outils sont des quasi-substituts, pas des copies. Le coût est un
      axe parmi d'autres, et souvent pas le décisif.</li>
  <li><strong>Le risque.</strong> Une mise à jour ratée, une base perdue ou un week-end passé sur une panne ont un coût
      probable qu'un tableur ne peut pas capturer honnêtement.</li>
  <li><strong>Les dépassements de trafic, les bases managées et le stockage objet</strong> au-delà de ce qu'inclut
      l'offre choisie. Quelques outils ont réellement besoin d'un stockage objet externe, et leurs pages le nomment,
      mais il n'est pas chiffré.</li>
  <li><strong>Les remises annuelles ou d'engagement</strong> côté hébergement. Les deux côtés sont cités sur la base
      qu'affichait la page de l'éditeur, et la page précise laquelle.</li>
  <li><strong>Votre infrastructure existante.</strong> Si vous avez déjà un serveur avec de la mémoire libre, le coût
      marginal d'un conteneur de plus est proche de zéro, et aucun de ces chiffres ne vous concerne.</li>
</ul>

<h2>Fraîcheur de cette page</h2>
<p>
  Les prix sont un relevé daté, pas un flux en direct. Chaque chiffre renvoie à la page d'où il vient, et la page de
  l'éditeur fait foi. Un prix vieux de plus de 45 jours environ doit être considéré comme indicatif et revérifié
  avant toute dépense.
</p>
<p>
  Actuellement : {len(built)} comparatifs publiés, vague {wave}, taille d'équipe de référence {ref} personnes, contrôle
  strict des prix {'activé' if strict else '<strong>désactivé</strong>'}.
</p>
"""
    return (
        "methodology",
        "Méthodologie : comment chaque coût de ce site est calculé",
        "Le modèle de dimensionnement, les hypothèses sur le temps passé, les sources de prix exactes et datées, et "
        "tout ce que ce modèle de coûts laisse délibérément de côté.",
        body,
    )


_REWARDS = {
    "digitalocean": (
        "Les liens DigitalOcean de nos pages sont les liens de parrainage de DigitalOcean. Si vous vous inscrivez "
        "par l'un d'eux et payez vos premiers 25 $, DigitalOcean nous accorde 25 $ de crédit sur notre compte. "
        "Cela ne vous coûte rien, et il s'agit de crédit d'hébergement, pas d'argent."
    ),
    "kamatera": (
        "Les liens Kamatera de nos pages sont des liens d'affiliation. Si vous ouvrez un compte payant par "
        "l'un d'eux, Kamatera nous verse une commission unique : 75 $ dans la plupart des pays, dont la France, "
        "et 10 $ dans quelques autres. Cela ne vous coûte rien et ce n'est pas récurrent."
    ),
    "vpsserver": (
        "Les liens VPSServer de nos pages sont des liens d'affiliation du même programme que ceux de Kamatera, "
        "et les conditions de VPSServer le rattachent au même groupe que Kamatera. Une inscription par l'un "
        "d'eux peut nous rapporter une commission, mais le programme n'en indique pas le montant pour VPSServer. "
        "Cela ne vous coûte rien."
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
        return (f"Les liens {name} de nos pages sont des liens d'affiliation tracés. Si vous vous inscrivez par "
                f"l'un d'eux, nous pouvons percevoir une commission. Cela ne vous coûte rien.")

    if tracked:
        items = "".join(f"<li>{reward_line(s)}</li>" for s in tracked)
        rest = ("<p>Les liens vers tous les autres hébergeurs sont de simples liens, sans rien attaché.</p>"
                if len(tracked) < len(aff.get("providers", {})) else "")
        state = (
            "<p><strong>Des liens de parrainage sont actuellement actifs sur ce site.</strong></p>"
            f"<ul>{items}</ul>{rest}"
        )
    else:
        state = (
            "<p><strong>Il n'y a actuellement aucun lien d'affiliation sur ce site.</strong> Chaque lien "
            "d'hébergement ici est un simple lien vers la page de l'hébergeur. Si cela change, cette page change "
            "avec, et la mention apparaît sur chaque page qui contient un tel lien.</p>"
        )

    body = f"""
<h1>Transparence sur l'affiliation</h1>

<p class="lead">
  Les sites de comparaison qui touchent une commission sur ce qu'ils recommandent ont un conflit d'intérêts évident.
  Voici exactement comment le nôtre est contenu.
</p>

{state}

<h2>Ce que la rémunération ne peut pas influencer</h2>
<ul>
  <li><strong>L'hébergeur recommandé par une page.</strong> Le serveur de chaque page est choisi par une seule règle :
      l'offre la moins chère, parmi les hébergeurs dont nous avons relevé les prix, qui satisfait le besoin calculé en
      mémoire et en disque. Cette règle est dans le script de génération, et elle ignore ce que quiconque nous verse.</li>
  <li><strong>Les chiffres.</strong> Chaque chiffre est calculé à partir du
      <a href="{base}/methodology/">modèle publié</a> et de sources de prix datées. Vous pouvez tous les refaire à la
      main.</li>
  <li><strong>La conclusion.</strong> Bon nombre de pages concluent que le produit payant est moins cher et que vous
      ne devriez pas auto-héberger. Ces pages ne rapportent rien. Elles restent telles quelles, car un comparatif qui
      arrive toujours à la même réponse n'est pas un comparatif.</li>
</ul>

<h2>Ce que la rémunération influence, honnêtement</h2>
<p>
  L'ordre dans lequel nous avons vérifié les prix des hébergeurs n'est pas parfaitement indépendant de l'existence
  d'un programme de parrainage. Nous chiffrons actuellement
  {', '.join(p['name'] for p in priced_providers(ds)) or 'aucun hébergeur'}, et la
  <a href="{base}/hosting/">page hébergement</a> nomme chaque hébergeur que nous n'avons pas pu chiffrer, y compris
  ceux que nous pensons moins chers. Cet écart est signalé plutôt que passé sous silence.
</p>

<h2>Aucun placement payant</h2>
<p>
  Aucun hébergeur, éditeur ou projet open source n'a payé pour apparaître ici, être classé ou être décrit d'une
  certaine façon. Personne ne relit une page avant sa publication.
</p>

<h2>Pas un conseil</h2>
<p>
  Ce sont des modèles de coûts, pas des recommandations pour votre entreprise. Les prix changent, nos relevés
  vieillissent, et la page de l'éditeur fait toujours foi. Vérifiez avant de dépenser.
</p>
"""
    return (
        "disclosure",
        "Transparence sur l'affiliation et gestion du conflit d'intérêts",
        "Si ce site touche une rémunération sur les liens d'hébergement, ce que cela peut et ne peut pas influencer, "
        "et les écarts que nous signalons plutôt que de les cacher.",
        body,
    )


def _privacy(ds: Dataset, base: str) -> tuple[str, str, str, str]:
    cfg = ds.config
    an = cfg.get("analytics", {})
    form_id = (cfg.get("lead_capture", {}).get("form_ids") or {}).get("fr") if cfg.get("lead_capture", {}).get("enabled") else None
    tracking = (
        f"<p>Nous utilisons <strong>{an['provider']}</strong> pour une mesure d'audience agrégée, configurée sans "
        "cookies ni identifiant inter-sites : nous ne pouvons pas nous en servir pour identifier un visiteur.</p>"
        if an.get("provider") not in (None, "", "none") else
        "<p><strong>Il n'y a aucun script de mesure d'audience sur ce site.</strong> Aucun cookie n'est déposé, rien "
        "n'est stocké dans votre navigateur, et nous ne collectons aucune donnée individuelle sur les visiteurs.</p>"
    )
    lead = (
        "<p>Si vous remplissez le formulaire proposant une checklist de migration, l'adresse e-mail saisie est traitée "
        "par notre prestataire de formulaires afin de vous envoyer ce que vous avez demandé. Elle n'est pas vendue et "
        "n'est transmise à aucun hébergeur.</p>"
        if form_id else
        "<p>Les pages en français ne contiennent actuellement aucun formulaire : il n'y a donc rien à envoyer, et rien "
        "que nous stockions.</p>"
    )

    body = f"""
<h1>Confidentialité</h1>

<p class="lead">
  Un site qui parle de ne pas confier vos données à d'autres se doit d'être prudent avec les vôtres. Cette page est
  courte, car il y a très peu à décrire.
</p>

<h2>Mesure d'audience</h2>
{tracking}

<h2>Formulaires</h2>
{lead}

<h2>E-mail</h2>
<p>
  Si vous écrivez à {cfg.get('contact_email', 'nous')}, votre adresse et votre message servent uniquement à vous
  répondre et, s'il s'agit d'une correction, à vérifier le chiffre signalé. Ils ne sont ajoutés à aucune liste, ni
  vendus, ni partagés avec un éditeur ou un hébergeur. La boîte est un compte Gmail standard : Google traite donc ces
  messages selon ses propres conditions.
</p>

<h2>Liens sortants</h2>
<p>
  Les liens vers les hébergeurs, éditeurs et projets open source mènent à des sites que nous ne contrôlons pas et dont
  les pratiques de confidentialité leur appartiennent. Quand un lien est rémunéré, il est marqué comme tel dans le
  code de la page et signalé sur la page ; voir la <a href="{base}/disclosure/">page de transparence</a>.
</p>

<h2>Hébergement</h2>
<p>
  Ce site est composé de fichiers statiques servis par GitHub Pages. GitHub traite les journaux de serveur, y compris
  les adresses IP, pour le distribuer, selon ses propres conditions de confidentialité et non les nôtres.
</p>

<h2>Aucune ressource tierce</h2>
<p>
  Chaque page charge une feuille de style et une petite icône SVG depuis ce domaine. Il n'y a ni polices web, ni
  gestionnaire de balises, ni vidéo intégrée, ni widget social : aucun tiers n'est contacté quand vous lisez une
  page{' en dehors du prestataire de formulaires sur les pages qui en contiennent un' if form_id else ''}.
</p>

<p class="srcline">Dernière révision : {MODIFIED}.</p>
"""
    return (
        "privacy",
        "Confidentialité",
        "Ce que ce site collecte, c'est-à-dire presque rien, et quels tiers sont contactés quand vous lisez une page.",
        body,
    )
