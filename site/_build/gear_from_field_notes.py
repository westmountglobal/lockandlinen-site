#!/usr/bin/env python3
"""Inject Field Notes products, a posts list, and a prolonged-blackout checklist
into the hand-authored gear showcase, without replacing the existing catalogue.

The gear page at site/public/guides/gear-wed-put-in-these-homes/ is preserved
across rebuilds. This module runs during the build:

  - patch_en() after write_field_notes() and before i18n_fr
  - patch_fr() after i18n_fr (and the FR article patches)

It reads public Field Notes pages only (no robots noindex). When flip_public.sh
makes a dream-home article public and rebuilds, that article's products and
post link appear here automatically. Unlisted pages are never linked.
"""
from __future__ import annotations

import re
from html import unescape
from pathlib import Path

ROOT = Path(__import__("os").environ.get("LL_SITE_ROOT", "/workspace/lockandlinen-site"))
PUBLIC = ROOT / "site" / "public"
AMAZON_TAG = "lockandlinen-20"
AMAZON_REL = 'rel="nofollow sponsored noopener noreferrer"'
AMAZON_IMG_HOST = "m.media-amazon.com"
START = "<!--ll-gear-fn-start-->"
END = "<!--ll-gear-fn-end-->"
CSS_START = "/* ll-gear-fn-css-start */"
CSS_END = "/* ll-gear-fn-css-end */"
ASIN_RE = re.compile(r"amazon\.com/dp/([A-Z0-9]{8,14})", re.I)
PRICE_RE = re.compile(
    r"(?:^|\s)(?:"
    r"Usually around\s+\$[\d,]+(?:\.\d{2})?"
    r"|Habituellement autour de\s+[\d\s\u00a0.,]+\s*\$\s*(?:US)?"
    r"|\$[\d,]+(?:\.\d{2})?(?:\s+as of [A-Za-z]+ \d{1,2},\s+\d{4})?"
    r"|[\d\u00a0 ]+(?:[.,]\d{2})?\s*\$\s*(?:US\s*)?"
    r"(?:au |en date du |à compter du |dès le )?[A-Za-zÉéûê\u00a0 ]*\d{0,2},?\s*\d{0,4}"
    r")\.?",
    re.I,
)
NOINDEX_RE = re.compile(r'name=["\']robots["\'][^>]*content=["\'][^"\']*noindex', re.I)


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def strip_price(text: str) -> str:
    cleaned = PRICE_RE.sub("", text)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+\.", ".", cleaned)
    cleaned = re.sub(r"\.\.+", ".", cleaned)
    return cleaned.strip()


def is_public(html: str) -> bool:
    return not NOINDEX_RE.search(html)


def page_title(html: str) -> str:
    m = re.search(r"<h1>(.*?)</h1>", html, re.S)
    return unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


def parse_cards(html: str) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for m in re.finditer(
        r'<article class="product"[^>]*>(.*?)</article>', html, re.S
    ):
        body = m.group(1)
        asin_m = ASIN_RE.search(body)
        if not asin_m:
            continue
        asin = asin_m.group(1)
        if asin in seen:
            continue
        seen.add(asin)
        img = re.search(
            r'<img[^>]+src="([^"]+)"[^>]*(?:alt="([^"]*)")?', body, re.I
        )
        if not img:
            img = re.search(
                r'<img[^>]+alt="([^"]*)"[^>]*src="([^"]+)"', body, re.I
            )
            src, alt = (img.group(2), img.group(1)) if img else ("", "")
        else:
            src, alt = img.group(1), img.group(2) or ""
        title_m = re.search(r"<h3>(.*?)</h3>", body, re.S)
        title = unescape(re.sub(r"<[^>]+>", "", title_m.group(1))).strip() if title_m else ""
        badge_m = re.search(r'class="ph-badge">(.*?)</span>', body, re.S)
        badge = unescape(re.sub(r"<[^>]+>", "", badge_m.group(1))).strip() if badge_m else ""
        ph = re.search(r'<div class="ph-body">(.*?)</div>', body, re.S)
        chunk = ph.group(1) if ph else body
        ps = re.findall(r"<p>(.*?)</p>", chunk, re.S)
        blurb = ""
        for p in ps:
            if 'class="ph-homes"' in p or 'class="ph-fn"' in p:
                continue
            blurb = unescape(re.sub(r"<[^>]+>", "", p)).strip()
            break
        out.append(
            {
                "asin": asin,
                "title": title,
                "image": src,
                "alt": unescape(alt),
                "badge": badge,
                "blurb": strip_price(blurb),
            }
        )
    return out


def existing_gear_asins(html: str) -> dict[str, str]:
    """ASIN -> first category id (privacy, window, power, entry, linen, emergency)."""
    found: dict[str, str] = {}
    for g in re.finditer(
        r'<div class="gear-group" id="([^"]+)"[^>]*>(.*?)(?=<div class="gear-group"|<!--ll-gear-fn-start-->|</section>)',
        html,
        re.S,
    ):
        cat, body = g.group(1), g.group(2)
        if cat.startswith("fn-") or cat in {"from-field-notes", "field-notes-posts", "blackout-checklist"}:
            continue
        for c in parse_cards(body):
            found.setdefault(c["asin"], cat)
    # Fallback if the regex missed some
    if not found:
        # Limit to catalogue by cutting at our injected block
        cut = html.split(START)[0]
        for c in parse_cards(cut):
            found.setdefault(c["asin"], "")
    return found


def index_slugs(lang: str) -> list[str]:
    if lang == "fr":
        path = PUBLIC / "fr" / "field-notes" / "index.html"
    else:
        path = PUBLIC / "field-notes" / "index.html"
    if not path.exists():
        return []
    html = path.read_text()
    slugs: list[str] = []
    for href in re.findall(r'href="([^"]+)"', html):
        m = re.search(r"field-notes/([a-z0-9-]+)/", href) or re.search(
            r"^([a-z0-9-]+)/index\.html$", href
        )
        if m:
            slug = m.group(1)
            if slug not in slugs:
                slugs.append(slug)
    return slugs


def collect_articles(lang: str) -> list[dict]:
    slugs = index_slugs(lang)
    root = PUBLIC / ("fr/field-notes" if lang == "fr" else "field-notes")
    en_root = PUBLIC / "field-notes"
    # Public status always comes from the English page (FR unlisted twins
    # have historically been missing noindex; do not trust FR robots).
    listed: list[dict] = []
    seen: set[str] = set()

    def consider(slug: str) -> None:
        if slug in seen:
            return
        en_path = en_root / slug / "index.html"
        if not en_path.exists():
            return
        en_html = en_path.read_text()
        if not is_public(en_html):
            return
        page = root / slug / "index.html"
        if not page.exists():
            return
        html = page.read_text() if lang == "fr" else en_html
        cards = parse_cards(html)
        # If the FR page has fewer cards, fall back to EN images/asins and FR text when present
        listed.append(
            {
                "slug": slug,
                "title": page_title(html) or page_title(en_html),
                "href": f"/fr/field-notes/{slug}/" if lang == "fr" else f"/field-notes/{slug}/",
                "cards": cards,
            }
        )
        seen.add(slug)

    for slug in slugs:
        consider(slug)
    # Any public article not on the index (should be rare)
    if en_root.exists():
        for p in sorted(en_root.iterdir()):
            if p.is_dir():
                consider(p.name)
    return listed


def amazon_url(asin: str) -> str:
    return f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"


def product_card_html(card: dict, featured_html: str, lang: str) -> str:
    url = amazon_url(card["asin"])
    badge = card.get("badge") or ("Carnets de terrain" if lang == "fr" else "Field Notes")
    alt = card.get("alt") or card["title"]
    btn = "Voir sur Amazon" if lang == "fr" else "View on Amazon"
    img = card["image"]
    return f"""        <article class="product" id="gear-{esc(card['asin'])}">
          <span class="ph-badge">{esc(badge)}</span>
          <a class="ph-img" href="{esc(url)}" {AMAZON_REL}>
            <img src="{esc(img)}" alt="{esc(alt)}" width="600" height="600" loading="lazy" decoding="async" referrerpolicy="no-referrer-when-downgrade" />
          </a>
          <div class="ph-body">
            <h3>{esc(card['title'])}</h3>
            <p>{esc(card['blurb'])}</p>
            <p class="ph-homes">{featured_html}</p>
            <a class="btn-soon btn-amazon" href="{esc(url)}" {AMAZON_REL}>{btn}</a>
          </div>
        </article>
"""


def product_mentions(articles: list[dict]) -> dict[str, list[dict]]:
    """ASIN -> articles that feature it, in article order."""
    m: dict[str, list[dict]] = {}
    for art in articles:
        seen: set[str] = set()
        for c in art["cards"]:
            if c["asin"] in seen:
                continue
            seen.add(c["asin"])
            m.setdefault(c["asin"], []).append(art)
    return m


def link_article(art: dict) -> str:
    return f'<a href="{esc(art["href"])}">{esc(art["title"])}</a>'


def extra_css() -> str:
    return f"""  {CSS_START}
  .gear-fn-extra {{
    margin: 3rem 0 2rem;
  }}
  .gear-fn-extra .gear-section {{
    max-width: 70ch;
    margin: 2.4rem 0 0.8rem;
  }}
  .gear-fn-extra .gear-section h2 {{
    font-size: clamp(1.35rem, 2.2vw, 1.7rem);
    font-weight: 500;
    letter-spacing: -0.01em;
    margin: 0.15rem 0 0.3rem;
  }}
  .gear-fn-extra .gear-section p,
  .fn-post-list,
  .blackout-checklist,
  .fn-already {{
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 0.92rem;
    color: var(--muted);
  }}
  .fn-post-list {{
    list-style: none;
    padding: 0;
    margin: 0.4rem 0 0;
    max-width: 70ch;
  }}
  .fn-post-list li {{
    margin: 0.35rem 0;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid var(--line);
  }}
  .fn-post-list a {{
    color: var(--ink);
    text-decoration: none;
    border-bottom: 1px solid var(--line);
  }}
  .fn-post-list a:hover {{ border-bottom-color: var(--ink); }}
  .fn-already {{
    margin: 0.6rem 0 1rem;
    max-width: 70ch;
  }}
  .blackout-checklist {{
    max-width: 70ch;
    color: var(--ink);
  }}
  .blackout-checklist h3 {{
    font-size: 1.08rem;
    font-weight: 500;
    margin: 1.6rem 0 0.35rem;
    scroll-margin-top: calc(var(--header-h) + 1rem);
  }}
  .blackout-checklist ul {{
    margin: 0.2rem 0 0;
    padding-left: 1.15rem;
  }}
  .blackout-checklist li {{
    margin: 0.4rem 0;
    color: var(--ink);
  }}
  .blackout-checklist .safety {{
    color: var(--ink);
  }}
  .blackout-checklist a {{
    color: var(--ink);
    text-decoration: none;
    border-bottom: 1px solid var(--line);
  }}
  .blackout-checklist a:hover {{ border-bottom-color: var(--ink); }}
  .gear-fn-toc {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem 1rem;
    margin: 0.8rem 0 0;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 0.85rem;
  }}
  .gear-fn-toc a {{ color: var(--ink); }}
  {CSS_END}
"""


def add_product_ids(html: str) -> str:
    def repl(m: re.Match) -> str:
        open_tag, body = m.group(1), m.group(2)
        asin_m = ASIN_RE.search(body)
        if not asin_m:
            return m.group(0)
        asin = asin_m.group(1)
        if re.search(r"\bid=", open_tag):
            return m.group(0)
        new_open = open_tag[:-1] + f' id="gear-{asin}">'
        return new_open + body + "</article>"

    return re.sub(
        r'(<article class="product"[^>]*>)(.*?)</article>',
        repl,
        html,
        flags=re.S,
    )


def posts_html(articles: list[dict], lang: str) -> str:
    if lang == "fr":
        label, heading, lede = (
            "Carnets de terrain",
            "Tous les textes parus dans les Carnets de terrain",
            "Les notes actuellement publiques, de la plus récente à la plus ancienne.",
        )
    else:
        label, heading, lede = (
            "Field Notes",
            "Field Notes posts so far",
            "Every Field Notes piece that is public now, newest first.",
        )
    items = "\n".join(
        f'        <li><a href="{esc(a["href"])}">{esc(a["title"])}</a></li>'
        for a in articles
    )
    return f"""    <div class="wrap" id="field-notes-posts">
      <div class="gear-section">
        <p class="section-label">{label}</p>
        <h2>{heading}</h2>
        <p>{lede}</p>
      </div>
      <ul class="fn-post-list">
{items}
      </ul>
    </div>
"""


def products_html(articles: list[dict], already: dict[str, str], lang: str) -> str:
    mentions = product_mentions(articles)
    emitted: set[str] = set(already)
    if lang == "fr":
        label, heading, lede, featured = (
            "Depuis les Carnets",
            "Les produits des Carnets de terrain",
            "Les objets dont on parle dans les notes publiques, regroupés par texte. Ceux qui sont déjà dans la vitrine plus haut sont indiqués avec un lien vers leur fiche ; on ne les dédouble pas. Quand un même objet apparaît dans deux notes, il n’est montré qu’une fois.",
            "Dans",
        )
        already_lbl = "Déjà dans la vitrine plus haut"
        also_lbl = "aussi dans"
    else:
        label, heading, lede, featured = (
            "From Field Notes",
            "Products from Field Notes",
            "Pieces we have written about in the public Field Notes, grouped by article. Items already in the showcase above are pointed to rather than repeated. When the same piece appears in more than one note, it is shown once.",
            "Featured in",
        )
        already_lbl = "Already in the showcase above"
        also_lbl = "also in"

    blocks: list[str] = [
        f"""    <div class="wrap" id="from-field-notes">
      <div class="gear-section">
        <p class="section-label">{label}</p>
        <h2>{heading}</h2>
        <p>{lede}</p>
      </div>
"""
    ]

    for art in articles:
        unique_cards = []
        seen: set[str] = set()
        for c in art["cards"]:
            if c["asin"] in seen:
                continue
            seen.add(c["asin"])
            unique_cards.append(c)
        if not unique_cards:
            continue
        new_cards = [c for c in unique_cards if c["asin"] not in emitted]
        old_cards = [c for c in unique_cards if c["asin"] in emitted]
        blocks.append(f"""      <div class="gear-section" id="fn-products-{esc(art['slug'])}">
        <p class="section-label">{esc(art['title'])}</p>
        <h2>{link_article(art)}</h2>
      </div>
""")
        if old_cards:
            bits = []
            for c in old_cards:
                bits.append(
                    f'<a href="#gear-{esc(c["asin"])}">{esc(c["title"])}</a>'
                )
            blocks.append(
                f'      <p class="fn-already">{already_lbl}\u00a0: {", ".join(bits)}.</p>\n'
            )
        if new_cards:
            cards_html = []
            for c in new_cards:
                arts = mentions.get(c["asin"], [art])
                primary = next((a for a in arts if a["slug"] == art["slug"]), art)
                others = [a for a in arts if a["slug"] != primary["slug"]]
                feat = f"{featured} {link_article(primary)}"
                if others:
                    feat += " \u2014 " + also_lbl + " " + ", ".join(link_article(a) for a in others)
                cards_html.append(product_card_html(c, feat, lang))
                emitted.add(c["asin"])
            blocks.append('      <div class="shop-grid">\n' + "".join(cards_html) + "      </div>\n")
    blocks.append("    </div>\n")
    return "".join(blocks)


def _hrefs(lang: str) -> dict[str, str]:
    def p(slug: str) -> str:
        return f"/fr/field-notes/{slug}/" if lang == "fr" else f"/field-notes/{slug}/"

    return {
        "woods": p("a-bath-in-the-woods"),
        "door": p("a-door-you-dont-own"),
        "closed": p("closed-up-for-the-evening"),
        "cameras": p("a-quiet-look-at-the-door"),
        "solar": p("a-quiet-share-of-the-sun"),
        "lavender": p("a-house-at-the-end-of-a-lavender-field"),
        "grassland": p("one-roof-on-the-grassland"),
        "pantry": p("the-quiet-pantry"),
        "water": p("water-filtration-guide"),
        "grid": p("when-the-grid-goes-dark"),
        "kit_en": "https://www.canada.ca/en/services/policing/emergencies/preparedness/get-prepared/emergency-kits/get-kit.html",
        "kit_fr": "https://www.canada.ca/fr/services/police/urgences/protection/preparez-vous/kits-urgence/obtenir-kit.html",
        "hc_en": "https://www.canada.ca/en/health-canada/services/food-drinking-water-safe-emergency.html",
        "hc_fr": "https://www.canada.ca/fr/sante-canada/services/salubrite-aliments-eau-potable-situation-urgence.html",
    }


def checklist_html(lang: str) -> str:
    h = _hrefs(lang)
    kit = h["kit_fr"] if lang == "fr" else h["kit_en"]
    hc = h["hc_fr"] if lang == "fr" else h["hc_en"]
    if lang == "fr":
        return f"""    <div class="wrap blackout-checklist" id="blackout-checklist">
      <div class="gear-section">
        <p class="section-label">À la maison</p>
        <h2>Liste pour une panne prolongée</h2>
        <p>Une panne qui s’étire se vit plus calmement quand quelques fournitures sont déjà à la maison. Le gouvernement du Canada, dans sa <a href="{kit}">liste de vérification pour une trousse d’urgence</a>, propose de prévoir de subvenir à ses besoins pendant au moins 72&nbsp;heures, et d’ajouter d’autres fournitures si on le peut, au cas où ça durerait plus longtemps. Voici une liste pratique pour une panne plus longue à la maison. Quand un objet figure déjà dans les Carnets de terrain ou dans la vitrine plus haut, on vous y mène. Le reste, ce sont des articles courants&nbsp;: on n’invente pas de nouveaux liens d’achat.</p>
      </div>
      <h3 id="blackout-water">Eau</h3>
      <ul>
        <li><strong>Entreposage.</strong> La trousse de base recommande deux litres d’eau emmagasinée ou embouteillée par personne par jour, pour boire, cuisiner et se laver, pendant au moins 72&nbsp;heures. <a href="{hc}">Santé Canada</a> suggère d’envisager deux litres de plus par personne par jour pour la préparation des aliments et l’hygiène. Prévoyez aussi quelques petites bouteilles, plus faciles à emporter.</li>
        <li><strong>Filtration.</strong> Les systèmes dont on parle dans <a href="{h['water']}">Ce qu’il y a dans le verre</a>, et le filtre personnel <a href="#gear-B006QF3TW4">LifeStraw</a> dans la vitrine, plus haut.</li>
        <li><strong>Purification, au-delà de la filtration.</strong> Santé Canada et la liste de fournitures supplémentaires mentionnent des comprimés de purification d’eau, ou de l’eau de Javel de maison non parfumée, si les autorités locales le demandent et que l’ébullition n’est pas possible. Suivez alors les consignes officielles, pas une recette improvisée.</li>
      </ul>
      <h3 id="blackout-food">Aliments</h3>
      <ul>
        <li><strong>Non périssables.</strong> Conserves, barres énergétiques et aliments déshydratés, à remplacer une fois l’an, selon la trousse de base. Pour le rangement au quotidien, voir <a href="{h['pantry']}">Le garde-manger tranquille</a>.</li>
        <li>Un ouvre-boîte manuel.</li>
        <li><strong>Cuisiner sans réseau.</strong> Parmi les fournitures supplémentaires, on trouve un petit réchaud à combustible et le combustible. La consigne officielle est de ne jamais les utiliser à l’intérieur d’un bâtiment, d’une tente ou d’un autre espace fermé, à cause du monoxyde de carbone. Après une panne, Santé Canada recommande aussi de limiter l’ouverture du réfrigérateur et du congélateur.</li>
      </ul>
      <h3 id="blackout-power">Courant de secours</h3>
      <ul>
        <li>Stations d’alimentation portatives et batteries d’appoint&nbsp;: la section <a href="#power">Trousse panne de courant</a> plus haut, et les notes <a href="{h['grid']}">Quand le réseau tombe en panne</a> et <a href="{h['solar']}">Une part tranquille du soleil</a>.</li>
        <li>Panneaux et contrôleurs solaires&nbsp;: dans <a href="{h['solar']}">Une part tranquille du soleil</a>.</li>
      </ul>
      <h3 id="blackout-heat">Chauffage et fraîcheur, autrement</h3>
      <ul>
        <li>Des couches de plus, une couverture chaude, des rideaux occultants pour retenir un peu de chaleur ou garder une pièce plus fraîche. Dans la vitrine&nbsp;: <a href="#linen">Lin douillet et lumière</a> et les <a href="#gear-B07R5FC3K1">rideaux occultants</a>.</li>
        <li class="safety"><strong>Sécurité.</strong> Ne faites jamais fonctionner une génératrice, un barbecue, un réchaud ou un appareil de chauffage à combustible à l’intérieur de la maison, d’un garage, d’une tente ou de tout autre espace fermé. Un détecteur de monoxyde de carbone en bon état est important dès qu’un appareil brûle un combustible.</li>
      </ul>
      <h3 id="blackout-light">Éclairage</h3>
      <ul>
        <li>Lampes, lanternes et chandelles déjà dans <a href="#linen">Lin douillet et lumière</a>, la lanterne solaire <a href="#gear-B07BMJPH8L">Goal Zero</a>, et, dans les Carnets, la <a href="#gear-B0CQ7RH7X1">lampe en papier de riz</a>, les <a href="#gear-B0F6YKFFG9">guirlandes extérieures</a> et le <a href="#gear-B0B2YYH3V1">photophore ouragan</a>.</li>
        <li>Une lampe de poche à piles ou à manivelle, prévue dans les trousses d’urgence, et des allumettes à l’épreuve de l’eau si vous gardez des chandelles, entreposées en lieu sûr.</li>
      </ul>
      <h3 id="blackout-comms">Communication</h3>
      <ul>
        <li>Une radio d’urgence à manivelle ou à énergie solaire, comme la <a href="#gear-B0G53Z8RD1">radio météo FosPower</a> dans la vitrine.</li>
        <li>Des téléphones chargés, et des <a href="#power">batteries d’appoint</a> pour les garder en vie.</li>
        <li>Une liste imprimée de coordonnées, une copie du plan d’urgence du foyer, et un lieu de rendez-vous convenu, comme le suggère la liste officielle des documents à mettre dans la trousse.</li>
      </ul>
      <h3 id="blackout-medical">Soins</h3>
      <ul>
        <li>Une trousse de premiers soins. Dans la vitrine&nbsp;: <a href="#gear-B06XVJDYSF">la trousse Swiss Safe</a>.</li>
        <li>Une réserve de vos médicaments sur ordonnance, selon vos besoins, et une liste de tous les médicaments, de la posologie et de l’usage, comme le prévoit la liste des documents importants.</li>
      </ul>
      <h3 id="blackout-sanitation">Salubrité et hygiène</h3>
      <ul>
        <li>Articles de toilette et fournitures menstruelles, selon les besoins du foyer.</li>
        <li>Désinfectant pour les mains et sacs à ordures, mentionnés parmi les fournitures supplémentaires.</li>
        <li>L’eau prévue plus haut sert aussi à se laver. Les <a href="{h['pantry']}">seaux de qualité alimentaire</a> du garde-manger peuvent servir à l’eau ou au ménage, si vous les réservez à cet usage.</li>
      </ul>
      <h3 id="blackout-tools">Outils</h3>
      <ul>
        <li>Des outils de base&nbsp;: marteau, tournevis, gants, couteau de poche.</li>
        <li>Ruban adhésif toilé, ciseaux et feuille de plastique, aussi inscrits parmi les fournitures supplémentaires.</li>
        <li>L’ouvre-boîte manuel, déjà nommé plus haut.</li>
      </ul>
      <h3 id="blackout-security">À la porte et aux fenêtres</h3>
      <ul>
        <li>Serrures, barres, alarmes et film pour fenêtres&nbsp;: les sections <a href="#entry">Entrée et portes</a> et <a href="#window">Fenêtres et vitrage</a>, et les notes <a href="{h['door']}">Une porte qui n’est pas à vous</a> et <a href="{h['closed']}">Fermée pour la soirée</a>.</li>
        <li>Caméras pour la maison&nbsp;: <a href="{h['cameras']}">Un regard tranquille sur la porte</a>.</li>
      </ul>
      <h3 id="blackout-documents">Documents et argent comptant</h3>
      <ul>
        <li>Des copies, papier et numériques, des pièces d’identité, des assurances et du plan d’urgence, à glisser dans la trousse.</li>
        <li>Un peu d’argent comptant en petites coupures, utile si les paiements par carte ne passent plus.</li>
        <li>Dans la vitrine, le <a href="#gear-B00KOO599O">coffret SentrySafe</a> pour les papiers.</li>
      </ul>
    </div>
"""
    return f"""    <div class="wrap blackout-checklist" id="blackout-checklist">
      <div class="gear-section">
        <p class="section-label">At home</p>
        <h2>A checklist for a prolonged blackout</h2>
        <p>A longer outage is easier to meet calmly when a few quiet supplies are already in the house. The Government of Canada’s <a href="{kit}">emergency kit checklist</a> is a good place to start: be ready to look after yourself for at least 72 hours, and add more supplies if you can, in case it lasts longer. What follows is a practical list for a longer outage at home. Where we already write about a piece, or already show it in the showcase above, we point you to it. The rest are ordinary household items — not a new shopping list.</p>
      </div>
      <h3 id="blackout-water">Water</h3>
      <ul>
        <li><strong>Storage.</strong> The basic kit calls for two litres of stored or bottled water per person per day, for drinking, cooking and hygiene, for at least 72 hours. <a href="{hc}">Health Canada</a> suggests thinking about two more litres per person per day for cooking and cleaning. Include some smaller bottles, which are easier to carry.</li>
        <li><strong>Filtration.</strong> The systems in <a href="{h['water']}">What’s in the Glass</a>, and the <a href="#gear-B006QF3TW4">LifeStraw</a> already in the showcase above.</li>
        <li><strong>Purification, beyond filtration.</strong> Health Canada and the additional-supplies list mention water-purifying tablets, or unscented household bleach, if local authorities say the tap is unsafe and boiling is not practical. Follow those official instructions, not a guess.</li>
      </ul>
      <h3 id="blackout-food">Food</h3>
      <ul>
        <li><strong>Non-perishables.</strong> Canned food, energy bars and dried foods, replaced once a year, per the basic kit. For everyday storage, see <a href="{h['pantry']}">The Quiet Pantry</a>.</li>
        <li>A manual can opener.</li>
        <li><strong>Cooking without grid power.</strong> The additional-supplies list includes a small fuel-operated stove and fuel. Official guidance is never to use them inside buildings, tents, or other closed spaces, because of carbon monoxide. After an outage, Health Canada also suggests opening the refrigerator and freezer only when you need to.</li>
      </ul>
      <h3 id="blackout-power">Emergency power</h3>
      <ul>
        <li>Portable power stations and power banks: the <a href="#power">Power-out kit</a> above, and the notes <a href="{h['grid']}">When the Grid Goes Dark</a> and <a href="{h['solar']}">A Quiet Share of the Sun</a>.</li>
        <li>Solar panels and controllers: in <a href="{h['solar']}">A Quiet Share of the Sun</a>.</li>
      </ul>
      <h3 id="blackout-heat">Heating and cooling, by other means</h3>
      <ul>
        <li>Extra layers, a warm blanket, and blackout curtains to hold a little heat or keep a room cooler. In the showcase: <a href="#linen">Cozy linen &amp; light</a> and the <a href="#gear-B07R5FC3K1">blackout curtains</a>.</li>
        <li class="safety"><strong>Safety.</strong> Never run a generator, a barbecue, a fuel stove, or a fuel heater inside the house, a garage, a tent, or any other closed space. A working carbon monoxide alarm matters whenever something burns fuel.</li>
      </ul>
      <h3 id="blackout-light">Lighting</h3>
      <ul>
        <li>Lamps, lanterns and candles already in <a href="#linen">Cozy linen &amp; light</a>, the <a href="#gear-B07BMJPH8L">Goal Zero solar lantern</a>, and, from Field Notes, the <a href="#gear-B0CQ7RH7X1">rice-paper floor lamp</a>, <a href="#gear-B0F6YKFFG9">outdoor string lights</a>, and the <a href="#gear-B0B2YYH3V1">hurricane candle holder</a>.</li>
        <li>A battery or crank flashlight, which official kits mention, and waterproof matches if you keep candles, stored safely.</li>
      </ul>
      <h3 id="blackout-comms">Communication</h3>
      <ul>
        <li>A crank or solar emergency radio, such as the <a href="#gear-B0G53Z8RD1">FosPower weather radio</a> in the showcase.</li>
        <li>Charged phones, and <a href="#power">power banks</a> to keep them going.</li>
        <li>A printed list of contacts, a copy of the household emergency plan, and an agreed meeting place, as the official document list suggests for the kit.</li>
      </ul>
      <h3 id="blackout-medical">Medical</h3>
      <ul>
        <li>A first aid kit. In the showcase: the <a href="#gear-B06XVJDYSF">Swiss Safe kit</a>.</li>
        <li>A supply of your prescription medicines, as you need them, and a list of every medicine, the dose, and what it is for, as the official document list asks.</li>
      </ul>
      <h3 id="blackout-sanitation">Sanitation and hygiene</h3>
      <ul>
        <li>Toiletries and menstrual supplies, according to who is in the house.</li>
        <li>Hand sanitizer and garbage bags, listed among the additional supplies.</li>
        <li>The water stored above also covers washing. The <a href="{h['pantry']}">food-grade buckets</a> in the pantry note can be set aside for water or cleaning, if you keep them for that.</li>
      </ul>
      <h3 id="blackout-tools">Tools</h3>
      <ul>
        <li>Basic tools: a hammer, screwdrivers, gloves, a pocket knife.</li>
        <li>Duct tape, scissors and plastic sheeting, also on the additional-supplies list.</li>
        <li>The manual can opener already named above.</li>
      </ul>
      <h3 id="blackout-security">Doors, windows and cameras</h3>
      <ul>
        <li>Locks, bars, alarms and window film: the <a href="#entry">Entry &amp; doors</a> and <a href="#window">Window &amp; glass</a> groups above, and the notes <a href="{h['door']}">A Door You Don’t Own</a> and <a href="{h['closed']}">Closed Up for the Evening</a>.</li>
        <li>Home cameras: <a href="{h['cameras']}">A Quiet Look at the Door</a>.</li>
      </ul>
      <h3 id="blackout-documents">Documents and cash</h3>
      <ul>
        <li>Paper and digital copies of identification, insurance and the emergency plan, kept with the kit.</li>
        <li>Some cash in small bills, useful if card payments are down.</li>
        <li>In the showcase, the <a href="#gear-B00KOO599O">SentrySafe document box</a> for papers.</li>
      </ul>
    </div>
"""


def toc_html(lang: str) -> str:
    if lang == "fr":
        items = [
            ("#field-notes-posts", "Les textes des Carnets de terrain"),
            ("#from-field-notes", "Les produits des Carnets"),
            ("#blackout-checklist", "Liste pour une panne prolongée"),
        ]
        label = "Plus bas sur la page"
    else:
        items = [
            ("#field-notes-posts", "Field Notes posts"),
            ("#from-field-notes", "Products from Field Notes"),
            ("#blackout-checklist", "Prolonged-blackout checklist"),
        ]
        label = "Further down this page"
    links = "\n".join(
        f'        <a href="{href}">{esc(label_)}</a>' for href, label_ in items
    )
    return f"""    <div class="wrap">
      <p class="section-label">{label}</p>
      <p class="gear-fn-toc">
{links}
      </p>
    </div>
"""


def extra_section(lang: str, articles: list[dict], already: dict[str, str]) -> str:
    return (
        f"{START}\n"
        f'  <section class="gear-fn-extra" id="from-field-notes-and-checklist" data-generated="field-notes-gear">\n'
        f"{toc_html(lang)}"
        f"{posts_html(articles, lang)}"
        f"{products_html(articles, already, lang)}"
        f"{checklist_html(lang)}"
        f"  </section>\n"
        f"{END}\n"
    )


def _replace_or_insert(html: str, block: str) -> str:
    if START in html and END in html:
        return re.sub(
            re.escape(START) + r".*?" + re.escape(END) + r"\n?",
            block,
            html,
            count=1,
            flags=re.S,
        )
    # Fall back: a previous build left the section but comments were stripped
    if 'id="from-field-notes-and-checklist"' in html:
        html = re.sub(
            r'[ \t]*<section class="gear-fn-extra" id="from-field-notes-and-checklist"[^>]*>.*?</section>\n?',
            block,
            html,
            count=1,
            flags=re.S,
        )
        return html
    if re.search(r"<footer>", html):
        return re.sub(r"[ \t]*<footer>", block + "  <footer>", html, count=1)
    raise SystemExit("gear page has no footer to insert the Field Notes block before")


def _upsert_css(html: str) -> str:
    css = extra_css()
    if CSS_START in html and CSS_END in html:
        return re.sub(
            re.escape(CSS_START) + r".*?" + re.escape(CSS_END),
            css.strip(),
            html,
            count=1,
            flags=re.S,
        )
    if "</style>" in html:
        return html.replace("</style>", css + "</style>", 1)
    return html


def assert_no_unlisted_leaks(html: str, path: Path) -> None:
    en_root = PUBLIC / "field-notes"
    if not en_root.exists():
        return
    for p in en_root.iterdir():
        if not p.is_dir() or not (p / "index.html").exists():
            continue
        if is_public((p / "index.html").read_text()):
            continue
        slug = p.name
        if f"/field-notes/{slug}/" in html or f"fn-products-{slug}" in html:
            raise SystemExit(
                f"{path}: leaked unlisted Field Notes slug {slug}"
            )


def _gear_paths(lang: str) -> Path:
    if lang == "fr":
        return PUBLIC / "fr" / "guides" / "gear-wed-put-in-these-homes" / "index.html"
    return PUBLIC / "guides" / "gear-wed-put-in-these-homes" / "index.html"


def patch(lang: str) -> dict:
    path = _gear_paths(lang)
    if not path.exists():
        raise SystemExit(f"missing gear page {path}")
    html = path.read_text()
    # Existing catalogue ASINs: read from the EN page when patching FR,
    # because ids are copied over, and we must not treat newly injected
    # Field Notes cards as "already in the showcase".
    en_html = _gear_paths("en").read_text()
    source_for_existing = en_html.split(START)[0] if START in en_html else en_html
    already = existing_gear_asins(source_for_existing)
    articles = collect_articles(lang)
    html = add_product_ids(html)
    html = _upsert_css(html)
    html = _replace_or_insert(html, extra_section(lang, articles, already))
    assert_no_unlisted_leaks(html, path)
    path.write_text(html)
    new_asins = []
    seen = set(already)
    for art in articles:
        for c in art["cards"]:
            if c["asin"] not in seen:
                new_asins.append(c["asin"])
                seen.add(c["asin"])
    return {
        "lang": lang,
        "posts": len(articles),
        "existing_cards": len(already),
        "new_cards": len(new_asins),
        "public_fn_products": sum(
            len({c["asin"] for c in art["cards"]}) for art in articles
        ),
        "titles": [a["title"] for a in articles],
    }


def patch_en() -> dict:
    return patch("en")


def patch_fr() -> dict:
    return patch("fr")


def main() -> None:
    en = patch_en()
    fr = patch_fr()
    print("gear Field Notes patch:", en, fr)


if __name__ == "__main__":
    main()
