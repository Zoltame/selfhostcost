"""
Páginas redactadas en español. Misma estructura y mismos cálculos que content.py;
solo cambia el texto. Los importes pasan por Locale y se muestran en dólares.
"""

from __future__ import annotations

from lib.dates import MODIFIED

from .i18n import Locale
from .model import Dataset, priced_providers


def static_pages(ds: Dataset, wave: int, strict: bool, built, pairs, base: str):
    loc = Locale("es", ds.config)
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
<h1>Lista de verificación para migrar al autoalojamiento</h1>

<p class="lead">
  Una lista de una página para pasar a un equipo de una herramienta de pago a una autoalojada. Cubre los pasos que
  deciden si la migración será aburrida o un desastre: la exportación de datos, el dimensionamiento, las copias de
  seguridad y el plan de vuelta atrás que casi todo el mundo olvida.
</p>

<div class="note caution">
  <p><strong>No canceles la suscripción hasta terminar la última sección.</strong> Mantén ambas herramientas en
  paralelo hasta haber restaurado una copia de seguridad y hasta que tu equipo haya usado la nueva para trabajo real.</p>
</div>

<h2>1. Antes de instalar nada</h2>
<ul>
  <li><strong>Exporta hoy mismo una copia real de tus datos.</strong> No una cuenta de prueba: tu espacio de trabajo
      real. Algunas exportaciones son parciales, están limitadas o solo existen en planes superiores. Mejor
      descubrirlo ahora que el día en que vence el contrato.</li>
  <li><strong>Abre la exportación y comprueba qué falta.</strong> Adjuntos, comentarios, historial, menciones y
      permisos son las bajas habituales.</li>
  <li><strong>Confirma que la herramienta nueva puede importar ese formato.</strong> Si no puede, reserva tiempo para
      convertirlo. Ese coste no aparece en ninguna cifra de este sitio.</li>
  <li><strong>Enumera las integraciones de las que dependes.</strong> SSO, notificaciones de chat, webhooks,
      sincronización de calendario. Comprueba que cada una existe en la herramienta autoalojada.</li>
  <li><strong>Revisa la licencia.</strong> Varias herramientas populares son de código disponible y no de código
      abierto, con límites al uso comercial. Cada página de herramienta de este sitio lo indica.</li>
  <li><strong>Nombra a un responsable.</strong> Un software autoalojado sin nadie encargado de las actualizaciones es
      la forma más habitual en que fracasan estos proyectos.</li>
</ul>

<h2>2. Dimensionamiento e instalación</h2>
<ul>
  <li><strong>Dimensiona el servidor con la página de coste de la herramienta para tu tamaño de equipo</strong> y
      conserva el {int(m['ram_headroom_ratio'] * 100)} % de margen de memoria. Un servidor ajustado al milímetro suele
      caerse en su primera actualización.</li>
  <li><strong>Usa el archivo Docker Compose del propio proyecto</strong> en lugar de uno de terceros, y fija la
      versión de la imagen en vez de usar <code>latest</code>.</li>
  <li><strong>Ponlo detrás de HTTPS y en su propio subdominio</strong> desde el primer día. Cambiar la dirección más
      tarde rompe enlaces, redirecciones de OAuth y aplicaciones móviles.</li>
  <li><strong>Configura el correo saliente</strong> con un servicio de envío transaccional. Sin él, los
      restablecimientos de contraseña y las notificaciones fallan en silencio, y la mayoría de las herramientas no avisan.</li>
  <li><strong>Cierra todos los puertos excepto el 80 y el 443</strong>, y nunca expongas la base de datos directamente.</li>
  <li><strong>Activa el SSO, o al menos la autenticación en dos pasos obligatoria</strong>, antes de invitar a nadie.</li>
</ul>

<h2>3. Copias de seguridad probadas</h2>
<ul>
  <li><strong>Respalda tanto la base de datos como los archivos subidos.</strong> Un volcado de la base de datos sin
      la carpeta de archivos restaura una herramienta llena de adjuntos rotos.</li>
  <li><strong>Guarda al menos una copia fuera del servidor</strong>, con otro proveedor o en otra región distinta a
      la del propio servidor.</li>
  <li><strong>Automatízalo y recibe una alerta si falla.</strong> Una tarea de copia que dejó de funcionar hace tres
      semanas es la forma habitual de descubrir que no había copia.</li>
  <li><strong>Restáurala en un servidor nuevo antes de la puesta en producción.</strong> Mide cuánto tarda. Esa cifra
      es tu tiempo real de recuperación, y hasta que no la tengas no tienes copias de seguridad, solo archivos.</li>
</ul>

<h2>4. El cambio</h2>
<ul>
  <li><strong>Elige un día tranquilo y anuncia una congelación de contenidos</strong> en la herramienta antigua
      durante la migración.</li>
  <li><strong>Haz una última exportación tras la congelación</strong>, impórtala y revisa una muestra de registros,
      adjuntos y permisos frente a la herramienta antigua.</li>
  <li><strong>Pasa primero a un grupo pequeño</strong> durante una semana de trabajo real antes de mover a todo el mundo.</li>
  <li><strong>Redirige o actualiza los marcadores</strong> allí donde estuviera enlazada la dirección antigua:
      documentación, chat, navegadores y aplicaciones móviles.</li>
</ul>

<h2>5. El plan de vuelta atrás que casi todo el mundo olvida</h2>
<ul>
  <li><strong>Escribe antes del cambio qué te haría volver atrás.</strong> Pérdida de datos, una función
      imprescindible que falta o caídas repetidas. Fija el umbral mientras estás tranquilo.</li>
  <li><strong>Mantén la suscripción antigua un ciclo de facturación más</strong> tras la puesta en producción, aunque
      parezca un derroche. Es el seguro más barato que vas a comprar.</li>
  <li><strong>Averigua cómo exportar desde la herramienta nueva</strong> a un formato que la antigua pueda leer.</li>
  <li><strong>Cancela la suscripción antigua solo cuando</strong> haya pasado una prueba de restauración, todo el
      equipo haya usado la nueva herramienta para trabajo real y nadie haya pedido volver a la antigua.</li>
</ul>

<h2>6. Después de la puesta en producción</h2>
<ul>
  <li><strong>Pon las actualizaciones en el calendario.</strong> Este sitio calcula entre
      {loc.hours(m['maintenance_hours_per_month_by_difficulty']['easy'])} y
      {loc.hours(m['maintenance_hours_per_month_by_difficulty']['hard'])} horas al mes según la herramienta. Lo que no
      se planifica no se hace.</li>
  <li><strong>Lee las notas de la versión antes de actualizar</strong>, sobre todo en versiones mayores con
      migraciones de base de datos.</li>
  <li><strong>Añade monitorización de disponibilidad</strong> para enterarte de una caída antes que tu equipo.</li>
  <li><strong>Repite la prueba de restauración</strong> cada pocos meses.</li>
</ul>

<h2>Antes de empezar</h2>
<p>
  Si todavía no has calculado el coste de la migración, comprueba si autoalojar ahorra dinero de verdad con tu tamaño
  de equipo. Con algunas herramientas no es así una vez contadas las horas anteriores.
  <a href="{base}/compare/">Ver todas las comparativas</a> o
  <a href="{base}/methodology/">leer cómo se calculan los costes</a>.
</p>
"""
    return (
        "migration-checklist",
        "Lista de verificación para migrar al autoalojamiento: antes de cancelar la suscripción",
        "Una lista práctica para pasar de una herramienta de pago a una autoalojada: exportación de datos, "
        "dimensionamiento, copias de seguridad probadas, cambio y plan de vuelta atrás.",
        body,
    )


def _about(ds: Dataset, built, base: str) -> tuple[str, str, str, str]:
    cfg = ds.config
    email = cfg.get("contact_email", "")
    repo = f"https://github.com/{cfg['github_owner']}/{cfg['repo']}"
    aff = cfg.get("affiliate", {})
    referral_on = bool(aff.get("enabled")) and any(p.get("id") for p in aff.get("providers", {}).values())
    verified = [s for s in ds.saas.values() if s.get("price_status") == "verified"]

    money_line = (
        "La única relación económica de este sitio con alguien a quien menciona es el enlace de referido estándar de "
        "DigitalOcean, que genera crédito de alojamiento cuando alguien se registra a través de él y paga sus primeros "
        "25 $. Está señalado en cada página que lo incluye y se describe en detalle en la "
        f"<a href=\"{base}/disclosure/\">página de transparencia</a>."
        if referral_on else
        "Ahora mismo el sitio no tiene enlaces de afiliado ni de referido y no gana nada. Si eso cambia, la "
        f"<a href=\"{base}/disclosure/\">página de transparencia</a> cambia ese mismo día."
    )

    body = f"""
<h1>Acerca de SelfHostCost</h1>

<p class="lead">
  SelfHostCost responde a una sola pregunta, herramienta por herramienta y tamaño de equipo por tamaño de equipo:
  ¿sale de verdad más barato ejecutar tú mismo una alternativa de código abierto que pagar por el software, una vez
  contados el servidor, las copias de seguridad y tus propias horas?
</p>

<h2>Por qué existe</h2>
<p>
  Casi todas las listas de «alternativas autoalojadas» se quedan en el precio de la licencia, lo que hace parecer
  gratis el autoalojamiento. Casi todas las comparativas de proveedores se quedan en las funciones, lo que hace
  parecer inevitable la suscripción. Ninguna calcula lo que de verdad decide la cuestión: un servidor tiene un mínimo
  alto y casi ninguna pendiente; un puesto no tiene mínimo pero sí una pendiente pronunciada. Este sitio calcula dónde
  se cruzan esas dos líneas y publica la respuesta incluso cuando es «sigue pagando».
</p>

<h2>Quién lo gestiona</h2>
<p>
  SelfHostCost es un proyecto independiente, lanzado el {cfg.get('launched_on', '')}. No pertenece a ningún
  proveedor de software, empresa de alojamiento ni proyecto de código abierto que aparezca en él, ninguno lo
  financia, y nadie paga por aparecer, por su posición ni por cómo se le describe.
</p>
<p>{money_line}</p>

<h2>Construido a la vista</h2>
<p>
  Cada página se genera a partir de un conjunto de datos y un modelo de costes que son públicos. Puedes leer el
  código, las cifras de dimensionamiento y los registros de precios con fecha en el
  <a href="{repo}" rel="noopener">repositorio de código en GitHub</a>, y el razonamiento de cada hipótesis en la
  <a href="{base}/methodology/">página de metodología</a>.
</p>
<p>
  Hoy eso supone {len(built)} comparativas publicadas, basadas en {len(verified)} precios leídos directamente en las
  páginas de precios de los proveedores. Las comparativas que dependerían de un precio sin comprobar se retienen en
  lugar de estimarse.
</p>

<h2>Correcciones</h2>
<p>
  Los precios cambian y a veces iremos por detrás. Si una cifra es incorrecta o está desactualizada, envía la
  dirección de la página y un enlace a la página del proveedor que muestre el precio actual. Volvemos a leer la
  página del proveedor, actualizamos el registro con la nueva fecha y regeneramos el sitio. Nunca corregimos nada
  solo porque alguien lo afirme, en ninguna dirección.
</p>

<h2>Contacto</h2>
<p>
  Para correcciones, sugerencias de herramientas o cualquier otra cosa:
  <a href="mailto:{email}">{email}</a>. Leemos todos los mensajes.
</p>
<p>
  No aceptamos posicionamientos pagados, reseñas patrocinadas ni peticiones para cambiar una conclusión, así que no
  hace falta preguntar.
</p>
"""
    return (
        "about",
        "Acerca de SelfHostCost y contacto",
        "Quién gestiona SelfHostCost, cómo se financia, cómo se mantienen honestos los datos, cómo avisar de un precio "
        "desactualizado y cómo contactar.",
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
        (s for s in ds.saas.values() if s.get("price_status") == "verified"),
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
        f"<td><a href=\"{s['pricing_url']}\" rel=\"nofollow noopener\">página del proveedor</a></td>"
        f"<td>{s['verified_on']}</td></tr>"
        for s in verified
    )
    priced_rows = "\n".join(
        f"<tr><td>{p['name']}</td><td>{len([x for x in p['plans'] if x.get('price_usd_month')])} planes</td>"
        f"<td><a href=\"{p['pricing_url']}\" rel=\"nofollow noopener\">página del alojamiento</a></td>"
        f"<td>{p['verified_on']}</td></tr>"
        for p in priced
    )
    unpriced_sentence = ""
    if unpriced:
        names = ", ".join(p["name"] for p in unpriced)
        unpriced_sentence = (
            f"La consecuencia más importante: {names} {'quedan' if len(unpriced) > 1 else 'queda'} fuera de todos los "
            "cálculos, y Hetzner en particular suele ser más barato por gigabyte de memoria que lo que citamos. Toma "
            "nuestros costes de servidor como un techo."
        )

    body = f"""
<h1>Metodología: cómo se obtiene cada cifra de este sitio</h1>

<p class="lead">
  Esta página existe para que puedas revisar nuestras cuentas, discrepar de nuestras hipótesis y ver exactamente qué
  precios hemos confirmado y cuáles no. Si una cifra de este sitio no se puede rastrear hasta algo de esta página, es
  un error.
</p>

<h2>La forma del problema</h2>
<p>
  El software por puesto no tiene mínimo pero sí una pendiente pronunciada. Un servidor tiene un mínimo alto pero casi
  ninguna pendiente. Cada comparativa de este sitio es el punto donde se cruzan esas dos líneas, y por eso la respuesta
  honesta nunca es «autoalojar es más barato», sino «más barato a partir de aproximadamente tantas personas, si tu
  tiempo vale aproximadamente tanto».
</p>

<h2>Dimensionar una herramienta autoalojada</h2>
<p>Para una herramienta y un tamaño de equipo, la memoria necesaria es:</p>
<pre><code>memoria = (ram_base + ram_por_usuario &times; usuarios) &times; {loc.number(1 + m['ram_headroom_ratio'], 2)}</code></pre>
<p>y el disco necesario es:</p>
<pre><code>disco = disco_base + disco_por_usuario &times; usuarios</code></pre>
<ul>
  <li><strong>ram_base</strong> cubre todo el stack en reposo, incluidos la base de datos y todos los contenedores
      auxiliares que el proyecto incluye en su archivo Compose de referencia. No es solo el proceso de la aplicación.</li>
  <li><strong>El {int(m['ram_headroom_ratio'] * 100)} % de margen</strong> es deliberado. Una máquina ajustada al
      milímetro es una máquina que se cae durante una actualización.</li>
  <li><strong>El número de vCPU</strong> se toma de la base del proyecto y <em>no</em> se escala con el tamaño del
      equipo. Con estas cargas, la memoria se agota primero. Es una simplificación, y preferimos decirlo antes que
      ocultarlo.</li>
</ul>
<p>
  Cuando un proyecto publica requisitos mínimos o recomendados, los valores base salen de ahí y la página lo indica.
  Cuando no, se deducen de los servicios de su stack Compose de referencia y la página los marca como estimación.
  <strong>Los incrementos por usuario son siempre nuestros.</strong> Se fijan con generosidad y no con optimismo,
  porque infradimensionar el servidor favorece al autoalojamiento y preferimos que el sesgo vaya en la dirección
  contraria.
</p>

<h2>Elegir el servidor</h2>
<p>
  Tomamos el plan más barato, entre los proveedores cuyos precios hemos leído nosotros mismos, cuya memoria y cuyo
  disco alcanzan o superan ambos la necesidad. Nada de encajes parciales, ni de fingir que una herramienta cabe en un
  plan al que le falta un gigabyte.
</p>
<p>
  <strong>Hoy solo confiamos en {len(priced)} proveedor{'' if len(priced) == 1 else 'es'}.</strong> Es una limitación
  real. Varios proveedores muestran sus precios en el navegador o detrás de un selector de región, y no publicamos un
  precio que no hayamos podido leer. {unpriced_sentence}
</p>
<div class="tablewrap"><table>
<thead><tr><th>Proveedor</th><th>Planes calculados</th><th>Fuente</th><th>Leído el</th></tr></thead>
<tbody>
{priced_rows}
</tbody></table></div>

<h2>Los tres costes de hacerlo tú mismo</h2>
<div class="tablewrap"><table>
<thead><tr><th>Concepto</th><th>Cómo se fija</th><th>Por qué</th></tr></thead>
<tbody>
<tr><td>Servidor</td><td>El plan elegido arriba, a precio de catálogo</td><td>No se asume ningún descuento por compromiso ni por pago anual.</td></tr>
<tr><td>Copias de seguridad</td><td>El {int(m['backup_cost_ratio'] * 100)} % del precio del servidor</td>
    <td>Aproximadamente lo que cuestan los snapshots del proveedor. Tratar las copias como opcionales vaciaría de sentido todas las cifras de este sitio.</td></tr>
<tr><td>Tu tiempo</td>
    <td>De {loc.hours(hm['easy'])} a {loc.hours(hm['hard'])} horas al mes según la exigencia, a {rate} la hora</td>
    <td>Suele ser la línea más grande, y omitirla es la forma más habitual en que estas comparativas engañan.</td></tr>
<tr><td>Puesta en marcha, una vez</td>
    <td>De {loc.hours(hs['easy'])} a {loc.hours(hs['hard'])} horas según la exigencia, a {rate} la hora</td>
    <td>Se amortiza con el ahorro mensual para obtener el punto de equilibrio.</td></tr>
</tbody></table></div>

<h3>La exigencia y lo que implica</h3>
<div class="tablewrap"><table>
<thead><tr><th>Nivel</th><th>Significado</th><th>Puesta en marcha</th><th>Al mes</th></tr></thead>
<tbody>
<tr><td>{loc.t('difficulty.easy')}</td><td>Un contenedor, sin dependencias externas y nada que hacer aparte de actualizar la imagen</td>
    <td>{loc.hours(hs['easy'])} h</td><td>{loc.hours(hm['easy'])} h</td></tr>
<tr><td>{loc.t('difficulty.medium')}</td><td>Stack de varios contenedores con una base de datos cuyo respaldo es responsabilidad tuya</td>
    <td>{loc.hours(hs['medium'])} h</td><td>{loc.hours(hm['medium'])} h</td></tr>
<tr><td>{loc.t('difficulty.hard')}</td><td>Varios servicios con estado, una ruta de actualización no trivial y un riesgo real de perder datos si vas con prisa</td>
    <td>{loc.hours(hs['hard'])} h</td><td>{loc.hours(hm['hard'])} h</td></tr>
</tbody></table></div>

<h3>Si tu tiempo es gratis</h3>
<p>
  Cada página muestra también la cifra sin contar el tiempo. Ambas cifras son reales. Cuál te aplica depende de si
  esas horas se habrían podido facturar o de si habrías pasado la tarde con ello por gusto de todos modos. Destacamos
  la cifra con el tiempo incluido porque es con la que debe planificar una empresa.
</p>

<h2>Calcular el lado comercial</h2>
<p>
  Comparamos con <strong>el plan más barato en el que un equipo acabaría de forma realista</strong>, no con el plan más
  barato que existe. Enfrentar el plan de entrada de un proveedor, con sus límites de respuestas y sus funciones que
  faltan, a un despliegue autoalojado completo sería deshonesto, y así es como la mayoría de las comparativas llegan a
  sus conclusiones. El plan utilizado se indica en cada página.
</p>
<p>
  Se respetan los mínimos de puestos. Cuando un proveedor no factura por puesto sino por tareas ejecutadas, usuarios
  activos mensuales o suscriptores, la página lo dice explícitamente en lugar de fingir que el tamaño del equipo es el
  eje correcto. Cuando el plan gratuito de un proveedor ya cubre al equipo en cuestión, la página también lo dice y no
  anuncia ningún ahorro. Cuando el precio por usuario baja con el tamaño del equipo, se lee para cada tamaño mostrado.
</p>

<h3>Los precios que hemos confirmado</h3>
<p>Leídos directamente en la página de precios del proveedor, en la fecha indicada:</p>
<div class="tablewrap"><table>
<thead><tr><th>Producto</th><th>Plan comparado</th><th>Fuente</th><th>Leído el</th></tr></thead>
<tbody>
{verified_rows}
</tbody></table></div>

<h3>Los precios que no hemos confirmado</h3>
<p>
  {len(unverified)} productos de nuestro conjunto de datos no tienen un precio confirmado.
  {'Como el modo estricto está activado, <strong>no se ha publicado ninguna página que dependa de alguno de ellos</strong>.' if strict else '<strong>El modo estricto está desactivado en esta versión, así que algunas cifras de este sitio pueden basarse en precios sin confirmar.</strong> Es un ajuste de desarrollo, no una versión para leer.'}
  Son: {', '.join(s['name'] for s in unverified) if unverified else 'ninguno'}.
</p>

<h3>Monedas</h3>
<p>
  Todos los cálculos se hacen en dólares estadounidenses, y esta versión en español los muestra en dólares. Algunos
  proveedores mostraban sus precios en euros: esos precios se convierten a dólares con un único tipo de cambio con
  fecha, <strong>1 EUR = {eur_rate} USD</strong>, el tipo de
  <a href="{fx['source_url']}" rel="nofollow noopener">{fx['source_name']}</a> del {fx['on']}. Toda página que lo use
  lo indica y enlaza aquí.
</p>

<h2>El horizonte y el punto de equilibrio</h2>
<p>
  Los totales abarcan <strong>{horizon} meses</strong>. El punto de equilibrio es el coste de puesta en marcha dividido
  entre el ahorro mensual:
</p>
<pre><code>meses_equilibrio = coste_puesta_en_marcha / (saas_mensual - autoalojado_mensual)</code></pre>
<p>
  Cuando el ahorro mensual es cero o negativo, no hay punto de equilibrio, y la página muestra «nunca» en lugar de
  omitir la fila sin decir nada.
</p>

<h2>Lo que este modelo ignora a propósito</h2>
<ul>
  <li><strong>El esfuerzo de migración.</strong> Sacar tus datos de la herramienta actual y meterlos en la nueva es
      trabajo real y no se cuenta en ninguna parte. Con un gran histórico puede superar con creces el coste de puesta
      en marcha.</li>
  <li><strong>La paridad de funciones.</strong> Las herramientas son casi sustitutas, no copias. El coste es un eje, y
      a menudo no el decisivo.</li>
  <li><strong>El riesgo.</strong> Una actualización fallida, una base de datos perdida o un fin de semana dedicado a una
      caída tienen un coste esperado que una hoja de cálculo no puede capturar con honestidad.</li>
  <li><strong>Los excesos de transferencia, las bases de datos gestionadas y el almacenamiento de objetos</strong> más
      allá de lo que incluye el plan elegido. Algunas herramientas necesitan de verdad almacenamiento de objetos
      externo, y sus páginas lo mencionan, pero no está incluido en el precio.</li>
  <li><strong>Los descuentos por pago anual o por compromiso</strong> en el alojamiento. Ambos lados se citan con la
      base que mostraba la página del proveedor, y la página indica cuál era.</li>
  <li><strong>Tu infraestructura actual.</strong> Si ya tienes un servidor con memoria libre, el coste marginal de un
      contenedor más es casi cero y ninguna de estas cifras te aplica.</li>
</ul>

<h2>Lo actualizada que está esta página</h2>
<p>
  Los precios son una instantánea con fecha, no un dato en tiempo real. Cada cifra enlaza a la página de la que
  procede, y la página del proveedor es la que manda. Un precio con más de unos 45 días debe tomarse como orientativo
  y volver a comprobarse antes de gastar dinero basándose en él.
</p>
<p>
  Ahora mismo: {len(built)} comparativas publicadas, oleada {wave}, tamaño de equipo de referencia {ref} personas,
  comprobación estricta de precios {'activada' if strict else '<strong>desactivada</strong>'}.
</p>
"""
    return (
        "methodology",
        "Metodología: cómo se calcula cada coste de este sitio",
        "El modelo de dimensionamiento, las hipótesis sobre el tiempo dedicado, las fuentes de precios exactas y con "
        "fecha, y todo lo que este modelo de costes deja fuera a propósito.",
        body,
    )


_REWARDS = {
    "digitalocean": (
        "Los enlaces de DigitalOcean de nuestras páginas son los enlaces de referido de la propia DigitalOcean. Si "
        "te registras a través de uno y pagas tus primeros 25 $, DigitalOcean nos da 25 $ de crédito en nuestra "
        "cuenta. No te cuesta nada, y es crédito de alojamiento, no dinero."
    ),
    "kamatera": (
        "Los enlaces de Kamatera de nuestras páginas son enlaces de afiliado. Si abres una cuenta de pago a través "
        "de uno, Kamatera nos paga una comisión única: 75 $ en la mayoría de los países, incluida España, y 10 $ en "
        "algunos otros. No te cuesta nada y no es recurrente."
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
        return (f"Los enlaces de {name} de nuestras páginas son enlaces de afiliado con seguimiento. Si te "
                f"registras a través de uno, podemos recibir una comisión. No te cuesta nada.")

    if tracked:
        items = "".join(f"<li>{reward_line(s)}</li>" for s in tracked)
        rest = ("<p>Los enlaces a todos los demás proveedores son enlaces normales, sin nada añadido.</p>"
                if len(tracked) < len(aff.get("providers", {})) else "")
        state = (
            "<p><strong>Ahora mismo hay enlaces de referido activos en este sitio.</strong></p>"
            f"<ul>{items}</ul>{rest}"
        )
    else:
        state = (
            "<p><strong>Ahora mismo no hay enlaces de afiliado en este sitio.</strong> Cada enlace de alojamiento "
            "es un enlace normal a la página del proveedor. Si eso cambia, esta página cambia con ello y el aviso "
            "aparece en cada página que incluya un enlace así.</p>"
        )

    body = f"""
<h1>Aviso sobre enlaces de referido y afiliación</h1>

<p class="lead">
  Los sitios de comparativas que ganan comisión con lo que recomiendan tienen un conflicto de intereses evidente. Así
  es exactamente como contenemos el nuestro.
</p>

{state}

<h2>Lo que una remuneración no puede influir</h2>
<ul>
  <li><strong>Qué proveedor recomienda una página.</strong> El servidor de cada página se elige con una sola regla: el
      plan más barato, entre los proveedores cuyos precios hemos leído, que cubre la memoria y el disco calculados. Esa
      regla está en el script de generación y no sabe lo que nadie nos paga.</li>
  <li><strong>Las cifras.</strong> Cada cifra se calcula con el <a href="{base}/methodology/">modelo publicado</a> y
      con fuentes de precios con fecha. Puedes reproducir cualquiera de ellas a mano.</li>
  <li><strong>La conclusión.</strong> Muchas páginas concluyen que el producto de pago es más barato y que no deberías
      autoalojar. Esas páginas no generan nada. Se quedan como están, porque una comparativa que siempre llega a la
      misma respuesta no es una comparativa.</li>
</ul>

<h2>Lo que una remuneración sí influye, con honestidad</h2>
<p>
  El orden en que comprobamos los precios de los proveedores no es del todo independiente de cuáles tienen un programa
  de referidos. Ahora mismo calculamos
  {', '.join(p['name'] for p in priced_providers(ds)) or 'ningún proveedor'}, y la
  <a href="{base}/hosting/">página de alojamiento</a> nombra a cada proveedor que no hemos podido calcular, incluidos
  los que creemos más baratos. Esa carencia se declara en lugar de ocultarse.
</p>

<h2>Sin posicionamiento pagado</h2>
<p>
  Ningún proveedor, empresa de software ni proyecto de código abierto ha pagado por aparecer aquí, por su posición ni
  por cómo se le describe. Nadie revisa una página antes de publicarse.
</p>

<h2>No es asesoramiento</h2>
<p>
  Son modelos de costes, no recomendaciones para tu empresa. Los precios cambian, nuestras instantáneas se quedan
  antiguas y la página del proveedor es siempre la que manda. Compruébalo antes de gastar.
</p>
"""
    return (
        "disclosure",
        "Aviso sobre enlaces de referido y cómo gestionamos el conflicto",
        "Si este sitio gana algo con los enlaces de alojamiento, qué puede y qué no puede influir eso, y las carencias "
        "que declaramos en lugar de ocultar.",
        body,
    )


def _privacy(ds: Dataset, base: str) -> tuple[str, str, str, str]:
    cfg = ds.config
    an = cfg.get("analytics", {})
    form_id = (cfg.get("lead_capture", {}).get("form_ids") or {}).get("es") if cfg.get("lead_capture", {}).get("enabled") else None
    tracking = (
        f"<p>Usamos <strong>{an['provider']}</strong> para medir la audiencia de forma agregada, configurado sin "
        "cookies ni identificadores entre sitios, así que no podemos usarlo para identificar a un visitante.</p>"
        if an.get("provider") not in (None, "", "none") else
        "<p><strong>No hay ningún script de analítica en este sitio.</strong> No se instalan cookies, no se guarda nada "
        "en tu navegador y no recogemos datos individuales de los visitantes.</p>"
    )
    lead = (
        "<p>Si envías el formulario de la lista de verificación de migración, la dirección de correo que introduces la "
        "trata nuestro proveedor de formularios para poder enviarte lo que has pedido. No se vende ni se cede a ningún "
        "proveedor de alojamiento.</p>"
        if form_id else
        "<p>Las páginas en español no incluyen ahora mismo ningún formulario, así que no hay nada que enviar ni nada que "
        "guardemos.</p>"
    )

    body = f"""
<h1>Privacidad</h1>

<p class="lead">
  Un sitio que habla de no entregar tus datos a otros debería tener cuidado con los tuyos. Esta página es corta porque
  hay muy poco que describir.
</p>

<h2>Analítica</h2>
{tracking}

<h2>Formularios</h2>
{lead}

<h2>Correo electrónico</h2>
<p>
  Si escribes a {cfg.get('contact_email', 'nosotros')}, tu dirección y tu mensaje se usan solo para responderte y, si
  se trata de una corrección, para comprobar la cifra que señalas. No se añaden a ninguna lista, no se venden y no se
  comparten con ningún proveedor. El buzón es una cuenta de Gmail normal, así que Google trata esos mensajes según sus
  propias condiciones.
</p>

<h2>Enlaces externos</h2>
<p>
  Los enlaces a proveedores de alojamiento, empresas de software y proyectos de código abierto llevan a sitios que no
  controlamos y cuyas prácticas de privacidad son las suyas. Cuando un enlace está remunerado, se marca como tal en el
  código de la página y se indica en la propia página; consulta el <a href="{base}/disclosure/">aviso sobre enlaces
  de referido</a>.
</p>

<h2>Alojamiento</h2>
<p>
  Este sitio son archivos estáticos servidos por GitHub Pages. GitHub trata los registros del servidor, incluidas las
  direcciones IP, para servirlo, según sus propias condiciones de privacidad y no las nuestras.
</p>

<h2>Sin recursos de terceros</h2>
<p>
  Cada página carga una hoja de estilos y un pequeño icono SVG desde este dominio. No hay fuentes web, ni gestores de
  etiquetas, ni vídeos incrustados, ni widgets sociales, así que no se contacta con ningún tercero al leer una
  página{', salvo con el proveedor de formularios en las páginas que lo incluyen' if form_id else ''}.
</p>

<p class="srcline">Última revisión: {MODIFIED}.</p>
"""
    return (
        "privacy",
        "Privacidad",
        "Lo que recoge este sitio, que es casi nada, y con qué terceros se contacta al leer una página.",
        body,
    )
