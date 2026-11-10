#!/usr/bin/env python3
"""Build Lock & Linen static site into site/public/ from mockup + published reels only."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from PIL import Image

ROOT = Path("/workspace/lockandlinen-site")
PUBLIC = ROOT / "site" / "public"
SITE_URL = "https://lockandlinen.com"
# Shop module stays off until Lex/Elias greenlight live Amazon links.
SHOP_MODULE_ENABLED = False
SHOP_COPY = {
    "en": {
        "label": "Inspired by this look",
        "heading": "Inspired by this look",
        "subline": "Similar products, not the exact items in this AI-rendered concept.",
        "commission": "We earn a commission if you buy through these links.",
        "btn": "Affiliate link coming soon",
    },
    "fr": {
        "heading": "Inspiré de ce décor",
        "subline": "Produits similaires, pas les articles exacts de ce concept généré par IA.",
        "commission": "Nous touchons une commission sur les achats faits via ces liens.",
    },
}
AMAZON_DISCLOSURE_EN = "As an Amazon Associate I earn from qualifying purchases."
AMAZON_DISCLOSURE_FR = "En tant que Partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises."
GEAR_PAGE_HREF = "/guides/gear-wed-put-in-these-homes/"
GEAR_PAGE_REL = {  # prefix-relative from a story page
    "../../": "../../guides/gear-wed-put-in-these-homes/index.html",
}
# Optional tasteful picks for story pages that clearly match the showcase (name + ASIN).
GEAR_PICKS = {
    "cliffside": [
        ("SLNT leather phone sleeve", "B07GXZM5PM"),
        ("Puzipha cordless wood & linen lamp", "B0GFDJ4X22"),
        ("LLB ivory sheepskin", "B09BYXV2FR"),
    ],
    "missile-silo": [
        ("Mission Darkness Faraday phone bag", "B09BGTVBKG"),
        ("FosPower NOAA weather radio", "B0G53Z8RD1"),
        ("Luminara flameless pillars", "B09S24TQVP"),
    ],
    "bunker-lodge": [
        ("Mission Darkness Faraday phone bag", "B09BGTVBKG"),
        ("FosPower NOAA weather radio", "B0G53Z8RD1"),
        ("DaranEner portable power station", "B0GKGFWY69"),
    ],
    "fjord-boathouse": [
        ("Puzipha cordless wood & linen lamp", "B0GFDJ4X22"),
        ("LLB ivory sheepskin", "B09BYXV2FR"),
    ],
    "glacier-cabin": [
        ("FosPower NOAA weather radio", "B0G53Z8RD1"),
        ("LLB ivory sheepskin", "B09BYXV2FR"),
    ],
    "mountain-homestead": [
        ("Barebones Edison Light Stick", "B0D46PQT2C"),
        ("LLB ivory sheepskin", "B09BYXV2FR"),
    ],
    "canyon": [
        ("Twelve South PowerCapsule", "B0GMRFYVZ9"),
        ("Barebones Edison Light Stick", "B0D46PQT2C"),
    ],
    "island-home": [
        ("Twelve South PowerCapsule", "B0GMRFYVZ9"),
        ("Luminara flameless pillars", "B09S24TQVP"),
    ],
    "cave-dwelling": [
        ("Barebones Edison Light Stick", "B0D46PQT2C"),
        ("Luminara flameless pillars", "B09S24TQVP"),
    ],
    "black-aframe": [
        ("FosPower NOAA weather radio", "B0G53Z8RD1"),
        ("Twelve South PowerCapsule", "B0GMRFYVZ9"),
    ],
}

def gear_section_html(slug: str, prefix: str) -> str:
    """Tasteful end-of-story CTA linking to the gear showcase."""
    href = f"{prefix}guides/gear-wed-put-in-these-homes/index.html"
    picks = GEAR_PICKS.get(slug) or []
    picks_html = ""
    if picks:
        items = []
        for name, asin in picks[:3]:
            url = f"https://www.amazon.com/dp/{asin}?tag=lockandlinen-20"
            items.append(
                f'<li><a href="{esc(url)}" rel="nofollow sponsored noopener noreferrer">{esc(name)}</a></li>'
            )
        picks_html = (
            '<p class="gear-picks-label">A few pieces that fit this look</p>\n'
            f'<ul class="gear-picks">\n{chr(10).join(items)}\n</ul>\n'
        )
    return f"""
  <section class="gear-cta" aria-label="Get the gear">
    <div class="wrap gear-cta-inner">
      <p class="section-label">Shop the look</p>
      <h2>Get the gear</h2>
      <p class="gear-cta-copy">Soft power and quiet privacy pieces inspired by these concept homes — similar products, not the exact items in the AI render.</p>
{picks_html}      <p class="gear-cta-actions"><a class="gear-cta-btn" href="{esc(href)}">Browse the gear showcase</a></p>
    </div>
  </section>
"""

DEFAULT_AI_NOTE = "Visuals on this site are AI-generated concept renders from Lock & Linen reels. These are illustrative concept homes, not real listings or buildable plans."
MOCKUP_IMG = ROOT / "mockup" / "images"
NC = Path("/workspace/meta-reel-generator/projects/new_concepts")
FORMULA01 = Path("/workspace/meta-reel-generator/projects/desert-compound-test/formula01")
BATCH2 = Path("/workspace/meta-reel-generator/projects/desert-compound-test/formula-batch2")
CONCEPTS = json.loads((NC / "concepts.json").read_text())

MAX_W = 1400
MAX_BYTES = 200_000
JPEG_Q_START = 82

# Published reels with real YouTube IDs (post-queue + youtube metadata).
# Skipped: unposted queue items; cliffside/silo re-cuts (not approved).
STORIES = [
    {
        "slug": "island-home",
        "yt": "9825XUqfoOE",
        "title": "The Island Home",
        "eyebrow": "Concept home · Stories",
        "tagline": "Nearest neighbor: two hundred kilometers of ocean.",
        "h2": "One dock. One lagoon. Quiet fortification.",
        "body": [
            "Nearest neighbor: two hundred kilometers of ocean. This Lock & Linen concept sits alone on a small tropical island — a low teak-and-coral-stone house on stilts above a shallow turquoise lagoon, with a butterfly roof of solar panels feeding rain into a rock-cut cistern below.",
            "One teak dock is the only way in, ending at a covered boat lift beside a small desalinator shed on the shore. Behind the house, a food forest of coconut, banana, and taro runs along a shell path. Inside: teak floors, a linen sofa, and louvered storm shutters open to the lagoon breeze. Motion-sensor lights wake as you move. Behind the warm teak, every wall is Faraday-lined.",
            "Island living, rendered as a concept — private, self-sufficient, and quietly fortified.",
        ],
        "aside": [
            "Single teak dock entry with boat lift",
            "Butterfly roof rain catch + solar",
            "Rock-cut cistern under the house",
            "Faraday-lined walls behind the teak",
            "Food forest: coconut · banana · taro",
        ],
        "gallery": [
            ("gallery-living.jpg", "Living room — teak floors, linen sofa, lagoon breeze", "wide"),
            ("gallery-living-close.jpg", "Open shutters to open water", ""),
            ("gallery-food-forest.jpg", "Food forest — coconut · banana · taro", ""),
            ("gallery-dock.jpg", "One way in — dock, boat lift, desalinator", ""),
            ("gallery-cistern.jpg", "Below — rock-cut cistern & cellar", ""),
            ("gallery-faraday.jpg", "Behind the teak — Faraday-lined walls", ""),
        ],
        "hero_alt": "Aerial view of a teak stilt house on a turquoise lagoon with a butterfly solar roof and long dock",
        "shop": [
            ("Linen slipcover sofa", "Soft neutrals for the open living room."),
            ("Teak outdoor lounge set", "Deck chairs for lagoon-facing evenings."),
            ("Ceiling fan, warm wood", "Quiet air for tropical interiors."),
            ("Louvered storm shutters", "Teak-look privacy with breeze control."),
        ],
        "ai_note": "Visuals on this page are AI-generated concept renders (same materials as the Lock & Linen Island reel). This is an illustrative concept home, not a real listing or buildable plan.",
        "card_blurb": "Teak stilt house on its own lagoon — one dock in, rain-catch roof, rock-cut cistern.",
        "source": "mockup",
    },
]


def vo_paragraphs(vo_list, closer: str) -> list[str]:
    """Turn VO lines into 2–3 short paragraphs without inventing facts."""
    lines = [v.strip() for v in vo_list if v and v.strip()]
    if len(lines) >= 5:
        p1 = " ".join(lines[:2])
        p2 = " ".join(lines[2:4])
        p3 = " ".join(lines[4:])
        return [p1, p2, p3]
    if len(lines) >= 3:
        return [" ".join(lines[:2]), " ".join(lines[2:])]
    return [" ".join(lines)] if lines else [closer]


def features_from_concept(c: dict) -> list[str]:
    bits = []
    if c.get("entry_short"):
        bits.append(c["entry_short"][0].upper() + c["entry_short"][1:] if c["entry_short"] else "")
    # Prefer short concrete bits from labels-style phrasing in concept fields
    for key in ("feature", "under", "lifestyle", "interior"):
        val = c.get(key) or ""
        # take a short clause
        if not val:
            continue
    # Build from known short fields + caption-like bullets
    out = []
    if c.get("entry"):
        # first clause only
        clause = c["entry"].split(";")[0].strip()
        if len(clause) > 90:
            clause = clause[:87].rsplit(" ", 1)[0] + "…"
        out.append(clause[0].upper() + clause[1:])
    if "Faraday" in (c.get("vo") and " ".join(c["vo"]) or "") or True:
        out.append("Faraday-lined walls")
    under = c.get("under") or ""
    if under:
        # first noun phrase
        first = under.split(",")[0].split(":")[-1].strip()
        if len(first) > 80:
            first = first[:77].rsplit(" ", 1)[0] + "…"
        out.append(first[0].upper() + first[1:])
    life = c.get("lifestyle") or ""
    if life:
        first = life.split(":")[0].strip()
        if len(first) > 80:
            first = first[:77].rsplit(" ", 1)[0] + "…"
        out.append(first[0].upper() + first[1:])
    feat = c.get("feature") or ""
    if feat and len(out) < 5:
        first = feat.split(",")[0].strip()
        if len(first) > 80:
            first = first[:77].rsplit(" ", 1)[0] + "…"
        out.append(first[0].upper() + first[1:])
    # Dedup and cap
    seen = set()
    clean = []
    for x in out:
        k = x.lower()
        if k not in seen:
            seen.add(k)
            clean.append(x)
    return clean[:5]


def shop_from_materials(materials: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return materials


def add_nc_story(slug, yt, concept_key, still_map, shop, hero_letter="A", ig=None, fb=None, home_num=None):
    c = CONCEPTS[concept_key]
    title = {
        "n01_island": "The Island Home",
        "n02_cliffside": "The Cliffside Glass House",
        "n03_treehouse": "The Canopy Treehouse",
        "n04_bunker_lodge": "The Bunker Lodge",
        "n05_aframe": "The Black A-Frame",
        "n06_canyon": "The Hidden Canyon House",
        "n07_lighthouse": "The Lighthouse Hideout",
        "n08_missile_silo": "The Missile Silo Home",
        "n09_fjord_boathouse": "The Fjord Boathouse",
        "n10_marsh_stilt": "The Marsh Stilt House",
        "n11_volcanic_plateau": "The Volcanic Plateau House",
        "n13_glacier_cabin": "The Glacier Cabin",
        "n17_cave_dwelling": "The Cave Dwelling",
        "n18_cliff_monastery": "The Cliff Monastery",
    }[concept_key]
    hook = " ".join(c["hook"].split())
    tagline = hook
    # h2 from first two VO lines or hook
    vo = c["vo"]
    h2 = vo[0] if vo else hook
    if len(vo) > 1 and len(h2) < 40:
        h2 = f"{vo[0]} {vo[1]}" if not vo[0].endswith(".") else vo[0]
    # Prefer a punchy h2 from hook lines
    hook_lines = [ln.strip() for ln in c["hook"].split("\n") if ln.strip()]
    if len(hook_lines) >= 2:
        h2 = f"{hook_lines[0]} {hook_lines[1]}"
    elif hook_lines:
        h2 = hook_lines[0]

    caption_path = NC / concept_key / "caption.txt"
    caption = caption_path.read_text().strip() if caption_path.exists() else ""
    body = vo_paragraphs(vo, caption.split("\n")[1] if caption else hook)
    # Ensure body stays within VO/caption — already is.

    gallery = []
    # wide first from interior or aerial close
    for i, (letter, cap, wide) in enumerate(still_map):
        gallery.append((f"gallery-{i+1}.jpg", cap, "wide" if wide else ""))

    aside = features_from_concept(c)
    # Prefer label strings when available for aside
    labels_path = NC / concept_key / "labels.json"
    if labels_path.exists():
        labs = json.loads(labels_path.read_text()).get("labels") or []
        if labs:
            aside = [lab["s"] for lab in labs[:5]]

    card = (c.get("house") or "")[:110]
    if len(c.get("house") or "") > 110:
        card = card.rsplit(" ", 1)[0] + "…"
    # Better card from caption second line
    caps = [ln for ln in caption.split("\n") if ln.strip()]
    if len(caps) >= 2:
        card = caps[1]

    STORIES.append(
        {
            "slug": slug,
            "yt": yt,
            "title": title,
            "eyebrow": "Concept home · Stories",
            "tagline": tagline,
            "h2": h2,
            "body": body,
            "aside": aside,
            "gallery": gallery,
            "hero_alt": f"{title} — AI-generated concept render",
            "shop": shop,
            "ai_note": f"Visuals on this page are AI-generated concept renders (same materials as the Lock & Linen {c['title']} reel). This is an illustrative concept home, not a real listing or buildable plan.",
            "card_blurb": card,
            "source": "nc",
            "concept_key": concept_key,
            "still_map": still_map,
            "hero_letter": hero_letter,
            "ig": ig,
            "fb": fb,
            "home_num": home_num,
        }
    )


# still_map: (letter, caption, is_wide)
add_nc_story(
    "cliffside",
    "9bEXIGhS8DE",
    "n02_cliffside",
    [
        ("I", "Living room — warm oak, fire, ocean under your feet", True),
        ("A", "Cantilevered glass above the surf", False),
        ("K", "Funicular — the only way in", False),
        ("F", "Clifftop herb terrace", False),
        ("U", "Rock-cut cellar behind the glass", False),
        ("X", "X-ray view — Faraday-lined walls", False),
    ],
    [
        ("Low oak lounge chair", "Warm wood for the concrete-and-glass living room."),
        ("Minimal fireplace set", "Quiet evenings above the surf."),
        ("Herb planter boxes", "Wind-sheltered terrace greens."),
        ("Wool throw blanket", "Soft texture against board-formed walls."),
    ],
    ig="https://www.instagram.com/reel/DfU92JVgnje/",
    fb="https://www.facebook.com/reel/2448967132507389/",
)

add_nc_story(
    "canyon",
    "ZgWRvfa4y6A",
    "n06_canyon",
    [
        ("I", "Cool interior — thick rammed-earth walls, clay and linen", True),
        ("A", "Earth-walled house flush with the canyon rock", False),
        ("K", "Hidden rammed-earth gate", False),
        ("F", "Fig-tree courtyard", False),
        ("U", "Rock-cut water tank & cellar", False),
        ("X", "X-ray view — Faraday-lined walls", False),
    ],
    [
        ("Linen window-seat cushion", "Soft seating for deep earth walls."),
        ("Clay tableware set", "Earthy tones for the courtyard table."),
        ("Shade sail canopy", "Soft light over the fig courtyard."),
        ("Herb garden kit", "Courtyard greens in desert heat."),
    ],
)

add_nc_story(
    "lighthouse",
    "gSWq9obuqys",
    "n07_lighthouse",
    [
        ("I", "Keeper's living room — stove, window seat, wool throws", True),
        ("A", "Whitewashed lighthouse on a rocky headland", False),
        ("K", "Gravel causeway — one way in", False),
        ("F", "Walled kitchen garden", False),
        ("U", "Granite-cut storeroom below", False),
        ("X", "X-ray view — Faraday-lined keeper's house", False),
    ],
    [
        ("Cast-iron stove set", "Warmth for thick stone walls."),
        ("Wool throw blanket", "Cozy window-seat evenings."),
        ("Raised garden bed kit", "Sheltered greens in the lee of the house."),
        ("Storm lantern lamp", "Soft light for Atlantic nights."),
    ],
)

add_nc_story(
    "missile-silo",
    "RGxkwxiMu7w",
    "n08_missile_silo",
    [
        ("I", "Cylindrical living room — oak panelling, skylight shaft", True),
        ("A", "Prairie farmhouse above the silo", False),
        ("K", "Flush concrete silo hatch", False),
        ("F", "Raised-bed prairie garden", False),
        ("U", "Cross-section — living and pantry levels down the shaft", False),
        ("X", "X-ray view — Faraday-lined farmhouse at night", False),
    ],
    [
        ("Sectional sofa", "Soft seating for the curved living room."),
        ("Oak wall panel sample", "Warmth against concrete curves."),
        ("Raised garden bed kit", "Tomatoes and sunflowers on the prairie."),
        ("Reading floor lamp", "Quiet light from the skylight shaft."),
    ],
    ig="https://www.instagram.com/reel/DfVtDVFg-pG/",
    fb="https://www.facebook.com/reel/2508866756276014",
)

add_nc_story(
    "fjord-boathouse",
    "HXxaLpD79EM",
    "n09_fjord_boathouse",
    [
        ("I", "Timber living room — wood stove, sheepskins, glass floor to the boat", True),
        ("A", "Dark timber boathouse on dry-stone piers", False),
        ("K", "Cliff stair — one way in by land", False),
        ("F", "Fjord-side timber sauna", False),
        ("U", "Wall of preserves inside", False),
        ("X", "X-ray view — Faraday-lined walls", False),
    ],
    [
        ("Sheepskin throw", "Soft texture for the timber lounge."),
        ("Wood stove accessories", "Evenings above the boat bay."),
        ("Sauna bucket & ladle", "Steam before a fjord dip."),
        ("Wool lounge chair", "Nordic calm over dark water."),
    ],
)



add_nc_story(
    "volcanic-plateau",
    "R-vMFsLcU4Y",
    "n11_volcanic_plateau",
    [
        ("I", "Stone walls, a sunken fire, and the volcano in the window", True),
        ("A", "Low basalt-and-charred-timber house on black sand", False),
        ("K", "Basalt-walled carport — one gravel track in", False),
        ("F", "Geothermal hot pool beside the moss roof", False),
        ("U", "Storerooms cut into the lava", False),
        ("X", "X-ray view — Faraday-lined walls", False),
    ],
    [
        ("Stone fire set", "A quiet hearth for basalt interiors."),
        ("Charred timber stool", "Warm seating against dark stone."),
        ("Wool throw blanket", "Soft evenings after the black-sand wind."),
        ("Outdoor soaking lantern", "Soft light by the hot pool."),
    ],
    ig="https://www.instagram.com/reel/DfXi69JgRO4/",
    fb="https://www.facebook.com/reel/2481023519373150/",
)

add_nc_story(
    "treehouse",
    "46AJHK3bYk4",
    "n03_treehouse",
    [
        ("I", "Morning in a timber pod — the jungle at the window", True),
        ("A", "Four rounded timber pods high in the canopy", False),
        ("K", "Spiral stair — one way up", False),
        ("F", "Canopy kitchen garden", False),
        ("U", "Vault down in the roots", False),
        ("X", "X-ray view — Faraday-lined pods", False),
    ],
    [
        ("Rope hammock", "Soft rest between the rope bridges."),
        ("Timber stool set", "Simple seating for the canopy pods."),
        ("Rain barrel", "Catch what the living roofs already gather."),
        ("Wool throw blanket", "Cool evenings fifteen meters up."),
    ],
    ig="https://www.instagram.com/reel/DfYTHqkgPvH/",
    fb="https://www.facebook.com/reel/997783876017483",
)

add_nc_story(
    "cliff-monastery",
    "pIgluQAbM8U",
    "n18_cliff_monastery",
    [
        ("I", "Whitewashed vaults, a fire, and the gorge through an arched window", True),
        ("A", "Whitewashed retreat stacked down the cliff", False),
        ("K", "Three hundred steps — one stair in", False),
        ("F", "Terraced herb gardens on the ledge", False),
        ("U", "Rock-cut stores in the cliff", False),
        ("X", "X-ray view — Faraday-lined stone walls", False),
    ],
    [
        ("Herb planter boxes", "Greens for the walled terrace garden."),
        ("Wool throw blanket", "Soft evenings in the whitewashed vaults."),
        ("Clay tableware set", "Simple meals after the climb."),
        ("Storm lantern lamp", "Warm light down the cliff stair."),
    ],
    ig="https://www.instagram.com/reel/DfZ10GtgmnY/",
    fb="https://www.facebook.com/reel/2175302393110926/",
)

add_nc_story(
    "cave-dwelling",
    "4ac1TuQpnd8",
    "n17_cave_dwelling",
    [
        ("I", "Sandstone ceiling, a fire, and the valley through the glass", True),
        ("A", "Home built into a cliff overhang above olive terraces", False),
        ("K", "Stone carport by the terrace — one track up", False),
        ("F", "Stone-walled olive terraces", False),
        ("U", "Rock-cut cellar and cistern", False),
        ("X", "X-ray view — Faraday-lined glass front", False),
    ],
    [
        ("Wool throw blanket", "Soft evenings under the rock lip."),
        ("Clay olive oil cruet", "A table piece for the cave kitchen."),
        ("Stone fire tools", "Quiet heat for sandstone nights."),
        ("Lantern set", "Warm light on the terrace."),
    ],
    ig="https://www.instagram.com/reel/Dfa4hpqAL47/",
    fb="https://www.facebook.com/reel/1157798226999996/",
)

add_nc_story(
    "black-aframe",
    "xspsklEvR3g",
    "n05_aframe",
    [
        ("I", "Wood stove, loft, and the whole lake through the glass", True),
        ("A", "Black timber A-frame on the lake — no road in", False),
        ("K", "Floatplane dock — the only way in", False),
        ("F", "Wood-fired barrel sauna by the water", False),
        ("U", "Ice house dug into the bank", False),
        ("X", "X-ray view — Faraday-lined walls", False),
    ],
    [
        ("Wool throw blanket", "Soft evenings after a cold lake landing."),
        ("Cast-iron stove set", "Warmth for the black A-frame loft."),
        ("Dock lantern", "Motion-soft light as the plane comes in."),
        ("Sauna bucket & ladle", "Steam before a lake dip."),
    ],
    ig="https://www.instagram.com/reel/DfctzBcgSBo/",
    fb="https://www.facebook.com/reel/1022186017584693",
    home_num=14,
)

add_nc_story(
    "bunker-lodge",
    "IUQ4ARm-J_A",
    "n04_bunker_lodge",
    [
        ("I", "Stone fire, sheepskins, and the peaks in every window", True),
        ("A", "Stone-and-timber lodge half into the alpine slope", False),
        ("K", "Vault door set into the mountain", False),
        ("F", "Ski-in deck above the snow", False),
        ("U", "Spring-fed cistern under the lodge", False),
        ("X", "X-ray view — Faraday-lined walls", False),
    ],
    [
        ("Sheepskin throw", "Soft texture for the stone lounge."),
        ("Wood stove accessories", "Evenings under the sod roof."),
        ("Wool lounge chair", "Quiet seating with the peaks outside."),
        ("Ski-boot tray", "A practical piece for the lodge entry."),
    ],
    ig="https://www.instagram.com/reel/DfddhiPAQCj/",
    fb="https://www.facebook.com/reel/1117580981198029",
    home_num=15,
)

add_nc_story(
    "marsh-stilt",
    "qm2R-Sq3SmA",
    "n10_marsh_stilt",
    [
        ("I", "Ceiling fans, cypress walls, and the marsh through the screens", True),
        ("A", "Cypress stilt house two meters above the tide", False),
        ("K", "Boardwalk from a crushed-shell pad", False),
        ("F", "Raised garden deck over the marsh", False),
        ("N", "Night — lights wake along the boardwalk", False),
        ("X", "X-ray view — Faraday-lined walls", False),
    ],
    [
        ("Ceiling fan, warm wood", "Quiet air for screened porches."),
        ("Raised garden bed kit", "Greens kept high above the tide."),
        ("Screened porch swing", "Soft evenings over the salt marsh."),
        ("Storm lantern lamp", "Warm light along the boardwalk."),
    ],
    ig="https://www.instagram.com/lockandlinen/reel/Dfh25CLg-vi/",
    fb="https://www.facebook.com/reel/1503395011935195",
    home_num=16,
)

add_nc_story(
    "glacier-cabin",
    "umFSpe-IdC0",
    "n13_glacier_cabin",
    [
        ("I", "Wood stove, sheepskins, and the ice through the glass", True),
        ("A", "Black timber cabin on a rock shelf above the glacier", False),
        ("K", "Garage cut into the rock — one moraine road in", False),
        ("F", "Sheltered glass greenhouse", False),
        ("U", "Rock-cut cold cellar", False),
        ("X", "X-ray view — Faraday-lined walls", False),
    ],
    [
        ("Sheepskin throw", "Soft evenings facing the ice."),
        ("Wood stove accessories", "Warmth under the solar steel roof."),
        ("Wool lounge chair", "Quiet seating at the glass corner."),
        ("Greenhouse grow lights", "Greens through the glacier winter."),
    ],
    ig="https://www.instagram.com/reel/DfimwmUgbr8/",
    fb="https://www.facebook.com/reel/1149125324236323",
    home_num=17,
)



def add_formula_story(slug, yt, title, tagline, h2, body, aside, shop, card, img_root, still_map, hero_file):
    STORIES.append(
        {
            "slug": slug,
            "yt": yt,
            "title": title,
            "eyebrow": "Concept home · Stories",
            "tagline": tagline,
            "h2": h2,
            "body": body,
            "aside": aside,
            "gallery": [(f"gallery-{i+1}.jpg", cap, "wide" if wide else "") for i, (_, cap, wide) in enumerate(still_map)],
            "hero_alt": f"{title} — AI-generated concept render",
            "shop": shop,
            "ai_note": f"Visuals on this page are AI-generated concept renders (same materials as the Lock & Linen {title} reel). This is an illustrative concept home, not a real listing or buildable plan.",
            "card_blurb": card,
            "source": "formula",
            "img_root": str(img_root),
            "still_map": still_map,
            "hero_file": hero_file,
        }
    )


f01 = json.loads((FORMULA01 / "script.json").read_text())
add_formula_story(
    slug="canyon-homestead",
    yt="jsMsVDwY_N0",
    title="The Canyon Homestead",
    tagline=f01["hook"],
    h2=f01["hook"],
    body=[
        f01["vo"].split(" Desert willow")[0] + ".",
        "Desert willow softens it. A spring keeps the garden green: potatoes, corn, eggs and goat milk. Every roof makes power and catches rain.",
        "The root cellar holds the harvest, and the garage keeps two rides ready. Could your family call this home?",
    ],
    aside=[
        "Cliffs on three sides — one way in",
        "One fence, softened by desert willow",
        "Spring-fed garden: potatoes, corn, eggs, goat milk",
        "Rooftop solar and rain catch",
        "Root cellar holds the harvest",
    ],
    shop=[
        ("Raised garden bed kit", "Potatoes and greens in the canyon floor."),
        ("Rain barrel", "Catch what the roofs already gather."),
        ("Chicken coop starter", "Eggs a few steps from the door."),
        ("Solar string lights", "Warm evenings under desert walls."),
    ],
    card="One road, one gate, canyon walls on every side — crops, goats, solar, and a root cellar.",
    img_root=FORMULA01 / "stills",
    still_map=[
        ("H.raw.png", "Cozy home under canyon walls", True),
        ("C.raw.png", "Root cellar and stone cistern", False),
        ("F.raw.png", "Potato rows, corn, coop and goat pen", False),
        ("G.raw.png", "Garage and fueled rides", False),
        ("S2.raw.png", "One fence — one way in", False),
        ("N.raw.png", "Night — lights wake on motion", False),
    ],
    hero_file="H.raw.png",
)

f03s = json.loads((BATCH2 / "scripts.json").read_text())["f03"]
f03r = json.loads((BATCH2 / "reels.json").read_text())["f03"]
add_formula_story(
    slug="sea-cliff-homestead",
    yt="bVx0Dp1YlHw",
    title="The Sea-Cliff Homestead",
    tagline=f03s["parts"][0],
    h2=f03s["parts"][0],
    body=[
        " ".join(f03s["parts"][0:3]),
        " ".join(f03s["parts"][3:6]),
        " ".join(f03s["parts"][6:]),
    ],
    aside=f03s["lines"][:5],
    shop=[
        ("Raised garden bed kit", "Potatoes and greens on the headland."),
        ("Wool throw blanket", "Soft evenings after the surf wind."),
        ("Chicken coop starter", "Eggs a few steps from the porch."),
        ("Storm lantern lamp", "Warm light for cliff-side nights."),
    ],
    card="Sea cliffs on three sides — one lane, one gate, raised beds, and a Faraday cage inside.",
    img_root=BATCH2 / "f03" / "stills",
    still_map=[
        ("H.raw.png", "Shingle-and-stone cottage on the headland", True),
        ("C.raw.png", "Turf-roofed root cellar", False),
        ("F.raw.png", "Raised beds, potatoes, coop and sheep shelter", False),
        ("G.raw.png", "Garage and fueled rides", False),
        ("S2.raw.png", "One lane — one gate", False),
        ("N.raw.png", "Night — lights wake on the headland", False),
    ],
    hero_file="H.raw.png",
)

f04s = json.loads((BATCH2 / "scripts.json").read_text())["f04"]
add_formula_story(
    slug="mountain-homestead",
    yt="7C93FPhHNe8",
    title="The Mountain Homestead",
    tagline=f04s["parts"][0],
    h2=f04s["parts"][0],
    body=[
        " ".join(f04s["parts"][0:3]),
        " ".join(f04s["parts"][3:6]),
        " ".join(f04s["parts"][6:]),
    ],
    aside=f04s["lines"][:5],
    shop=[
        ("Wool throw blanket", "Quiet evenings under granite peaks."),
        ("Raised garden bed kit", "Potatoes and cabbage on the alpine bench."),
        ("Goat-milk cheese board", "A table piece for the mountain kitchen."),
        ("Cast-iron skillet", "Hearty meals after a cold climb."),
    ],
    card="Granite behind, steep drops in front — one switchback road, spring water, solar roofs.",
    img_root=BATCH2 / "f04" / "stills",
    still_map=[
        ("H.raw.png", "Stone-and-timber chalet on the alpine bench", True),
        ("C.raw.png", "Cellar door and water cistern", False),
        ("F.raw.png", "Potatoes, cabbage, coop and goat pen", False),
        ("G.raw.png", "Garage and fueled rides", False),
        ("S1.raw.png", "One road in — the only approach", False),
        ("N.raw.png", "Night — lights wake on the bench", False),
    ],
    hero_file="H.raw.png",
)


def compress_image(src: Path, dest: Path, max_w=MAX_W, max_bytes=MAX_BYTES) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if w > max_w:
        nh = int(h * (max_w / w))
        im = im.resize((max_w, nh), Image.Resampling.LANCZOS)
    # Prefer JPEG for broad support; keep under max_bytes
    q = JPEG_Q_START
    while q >= 55:
        im.save(dest, "JPEG", quality=q, optimize=True, progressive=True)
        if dest.stat().st_size <= max_bytes:
            return
        q -= 5
    # last resort: shrink further
    w, h = im.size
    im = im.resize((int(w * 0.85), int(h * 0.85)), Image.Resampling.LANCZOS)
    im.save(dest, "JPEG", quality=70, optimize=True, progressive=True)


def prepare_images():
    # Island: reuse mockup images (compress into public)
    island_dir = PUBLIC / "stories" / "island-home" / "images"
    for name in [
        "hero.jpg",
        "gallery-living.jpg",
        "gallery-living-close.jpg",
        "gallery-food-forest.jpg",
        "gallery-dock.jpg",
        "gallery-cistern.jpg",
        "gallery-faraday.jpg",
    ]:
        compress_image(MOCKUP_IMG / name, island_dir / name)

    # Index hero: island hero copy
    compress_image(Path(__file__).parent / "home-hero-cliff-src.jpg", PUBLIC / "images" / "home-hero-cliff.jpg", max_w=1920, max_bytes=600_000)

    for s in STORIES:
        out = PUBLIC / "stories" / s["slug"] / "images"
        compress_image(Path(__file__).parent / "banners" / f"{s['slug']}.jpg", out / "banner.jpg", max_w=1920, max_bytes=600_000)
        if s["source"] == "mockup":
            continue
        if s["source"] == "nc":
            stills = NC / s["concept_key"] / "stills"
            hero_src = stills / f"{s['hero_letter']}.raw.png"
            compress_image(hero_src, out / "hero.jpg")
            for i, (letter, _cap, _wide) in enumerate(s["still_map"]):
                compress_image(stills / f"{letter}.raw.png", out / f"gallery-{i+1}.jpg")
        else:
            root = Path(s["img_root"])
            compress_image(root / s["hero_file"], out / "hero.jpg")
            for i, (fname, _cap, _wide) in enumerate(s["still_map"]):
                compress_image(root / fname, out / f"gallery-{i+1}.jpg")


CSS = r"""
:root {
  --ink: #1c1a17;
  --muted: #6b655c;
  --sand: #f6f1e8;
  --cream: #fbf8f3;
  --linen: #ebe4d6;
  --teak: #8b5e3c;
  --lagoon: #2a7a7b;
  --lagoon-deep: #1d5a5b;
  --card: #ffffff;
  --line: #e2d9c8;
  --placeholder: #d4cdc0;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
  color: var(--ink);
  background: var(--cream);
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
a { color: inherit; text-decoration: none; }
img { display: block; max-width: 100%; height: auto; }

.site-header {
  position: sticky; top: 0; z-index: 40;
  background: rgba(251,248,243,0.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--line);
}
.header-inner {
  max-width: 1100px; margin: 0 auto;
  padding: 0.9rem 1.25rem;
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
}
.wordmark {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase;
  font-size: 0.82rem;
}
.wordmark span { color: var(--lagoon); }
nav {
  display: flex; gap: 1.4rem;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--muted);
}
nav a:hover { color: var(--ink); }

.hero {
  position: relative;
  padding: 0;
  background: #1c2320;
  overflow: hidden;
}
.hero img {
  display: block;
  width: 100%; height: auto;
  aspect-ratio: 16 / 9;
  object-fit: contain;
}
.hero-scrim {
  position: absolute; inset: 0;
  background: linear-gradient(to top, rgba(16,22,20,0.72) 0%, rgba(16,22,20,0.12) 40%, rgba(16,22,20,0) 100%);
  pointer-events: none;
}
.hero-copy {
  position: absolute; left: 0; right: 0; bottom: 0; z-index: 1;
  max-width: 1100px; width: 100%; margin: 0 auto;
  padding: 2.5rem 1.25rem 2.75rem;
  color: #fff;
}
@media (max-width: 720px) {
  .hero-scrim { display: none; }
  .hero-copy { position: static; padding: 1.25rem 1.25rem 1.5rem; }
}
.eyebrow {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.72rem; letter-spacing: 0.18em; text-transform: uppercase;
  opacity: 0.85; margin-bottom: 0.65rem;
}
.hero h1 {
  font-size: clamp(2.1rem, 5vw, 3.4rem);
  font-weight: 500; line-height: 1.08;
  letter-spacing: -0.02em;
  max-width: 16ch;
}
.hero .tagline {
  margin-top: 0.75rem;
  font-size: clamp(1rem, 2.2vw, 1.25rem);
  font-style: italic;
  opacity: 0.92;
  max-width: 32ch;
}

.wrap { max-width: 1100px; margin: 0 auto; padding: 0 1.25rem; }
section { padding: 3.5rem 0; }
section.hero { padding: 0; }
.section-label {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.7rem; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--lagoon); margin-bottom: 0.85rem;
}
h2 {
  font-size: clamp(1.55rem, 3vw, 2rem);
  font-weight: 500; letter-spacing: -0.015em;
  margin-bottom: 1.25rem;
}

.story-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 2.5rem; align-items: start;
}
.story-body p {
  font-size: 1.08rem; color: #2a2621;
  margin-bottom: 1.1rem; max-width: 58ch;
}
.story-body p:last-child { margin-bottom: 0; }
.story-aside {
  background: var(--sand);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 1.4rem 1.35rem;
}
.story-aside h3 {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.72rem; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--muted); margin-bottom: 0.9rem;
}
.story-aside ul { list-style: none; }
.story-aside li {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.9rem;
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--line);
  display: flex; gap: 0.65rem; align-items: baseline;
}
.story-aside li:last-child { border-bottom: 0; }
.story-aside .dot {
  width: 0.45rem; height: 0.45rem; border-radius: 50%;
  background: var(--lagoon); flex: 0 0 auto; margin-top: 0.35rem;
}

.gallery { background: var(--sand); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}
.g-card {
  background: var(--card);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--line);
  box-shadow: 0 1px 0 rgba(28,26,23,0.03);
}
.g-card.wide { grid-column: span 2; }
.g-card .frame {
  aspect-ratio: 4 / 5;
  background: var(--linen);
  overflow: hidden;
}
.g-card.wide .frame { aspect-ratio: 16 / 10; }
.g-card img {
  width: 100%; height: 100%;
  object-fit: cover; object-position: center;
}
.g-card figcaption {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.78rem; color: var(--muted);
  padding: 0.75rem 0.9rem 0.95rem;
  letter-spacing: 0.02em;
}

.embed-wrap {
  position: relative;
  width: 100%;
  max-width: 420px;
  margin: 1.4rem auto 0;
  aspect-ratio: 9 / 16;
  background: #111;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--line);
}
.embed-wrap iframe {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  border: 0;
}

.shop-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}
.product {
  background: var(--card);
  border: 1px dashed #b9b0a0;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}
.product .ph-badge {
  position: absolute; top: 0.55rem; left: 0.55rem; z-index: 1;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase;
  background: rgba(28,26,23,0.78); color: #fff;
  padding: 0.28rem 0.45rem; border-radius: 4px;
}
.product .ph-img {
  aspect-ratio: 1 / 1;
  background: var(--sand);
  display: flex; align-items: center; justify-content: center;
  color: var(--muted);
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
  padding: 1rem;
  overflow: hidden;
}
.product .ph-img img {
  width: 100%; height: 100%;
  object-fit: contain; object-position: center;
}
.product .ph-body { padding: 0.9rem 0.95rem 1.05rem; }
.product h3 {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.92rem; font-weight: 600; margin-bottom: 0.25rem;
}
.product p {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.78rem; color: var(--muted); margin-bottom: 0.85rem;
}
.btn-soon {
  display: inline-block; width: 100%; text-align: center;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
  padding: 0.7rem 0.6rem;
  background: var(--linen); color: var(--muted);
  border-radius: 8px; border: 1px solid var(--line);
  cursor: default;
}

.stories-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.15rem;
  margin-top: 1.4rem;
}
.story-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  display: flex; flex-direction: column;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.story-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(28,26,23,0.08);
}
.story-card .thumb {
  aspect-ratio: 4 / 5;
  background: var(--linen);
  overflow: hidden;
}
.story-card .thumb img {
  width: 100%; height: 100%;
  object-fit: cover; object-position: center;
}
.story-card .body { padding: 1rem 1.05rem 1.15rem; }
.story-card .body .eyebrow {
  opacity: 1; color: var(--lagoon); margin-bottom: 0.35rem;
}
.story-card h3 {
  font-size: 1.2rem; font-weight: 500; letter-spacing: -0.01em;
  margin-bottom: 0.45rem;
}
.story-card p {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.84rem; color: var(--muted);
  margin-bottom: 0.85rem;
}
.story-card .more {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.72rem; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--lagoon);
}

.prose {
  max-width: 62ch;
  font-size: 1.08rem;
  color: #2a2621;
}
.prose p { margin-bottom: 1.1rem; }

footer {
  background: var(--ink); color: #d9d2c6;
  padding: 2.4rem 0 2.6rem;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
}
.footer-inner {
  max-width: 1100px; margin: 0 auto; padding: 0 1.25rem;
  display: grid; gap: 1.1rem;
}
.footer-brand {
  letter-spacing: 0.14em; text-transform: uppercase;
  font-size: 0.78rem; font-weight: 600; color: #fff;
}
.footer-brand span { color: #7ec8c9; }
.disclosures {
  font-size: 0.78rem; line-height: 1.55; color: #a89f90;
  max-width: 70ch;
}
.disclosures strong { color: #d9d2c6; font-weight: 600; }
.footer-nav {
  display: flex; gap: 1.2rem; flex-wrap: wrap;
  font-size: 0.72rem; letter-spacing: 0.1em; text-transform: uppercase;
  color: #a89f90;
}
.footer-nav a:hover { color: #fff; }

@media (max-width: 900px) {
  .story-grid { grid-template-columns: 1fr; gap: 1.5rem; }
  .gallery-grid { grid-template-columns: 1fr 1fr; }
  .g-card.wide { grid-column: span 2; }
  .shop-grid { grid-template-columns: 1fr 1fr; }
  .stories-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 560px) {
  nav { gap: 0.85rem; font-size: 0.7rem; }
  section { padding: 2.6rem 0; }
  .gallery-grid { grid-template-columns: 1fr; }
  .g-card.wide { grid-column: span 1; }
  .g-card.wide .frame { aspect-ratio: 4 / 5; }
  .shop-grid { grid-template-columns: 1fr; }
  .stories-grid { grid-template-columns: 1fr; }
}
.page-hero {
  padding: 2.8rem 0 0.4rem;
}
.page-hero h1 {
  font-size: clamp(1.8rem, 3.5vw, 2.4rem);
  font-weight: 500; letter-spacing: -0.02em;
  margin: 0.35rem 0 0.6rem;
}
.fr-summary {
  margin: 1.6rem 0 0;
  padding: 1.1rem 1.15rem;
  background: var(--sand);
  border: 1px solid var(--line);
  border-radius: 10px;
  max-width: 70ch;
}
.fr-summary h3 {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--lagoon); font-weight: 600; margin-bottom: 0.55rem;
}
.fr-summary p {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.9rem; color: #3a342c; margin-bottom: 0.55rem;
}
.fr-summary p:last-child { margin-bottom: 0; }
.ideas-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1.4rem;
}
.idea-card {
  display: grid; grid-template-columns: 110px 1fr; gap: 0.9rem;
  background: var(--card); border: 1px solid var(--line); border-radius: 12px;
  overflow: hidden; text-decoration: none; color: inherit;
}
.idea-card:hover { border-color: #cbbda6; }
.idea-card .thumb {
  aspect-ratio: 1; background: var(--linen); overflow: hidden;
}
.idea-card .thumb img { width: 100%; height: 100%; object-fit: cover; }
.idea-card .body { padding: 0.85rem 0.9rem 0.95rem 0; }
.idea-card .body .eyebrow {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.68rem; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--lagoon); margin-bottom: 0.25rem;
}
.idea-card h3 {
  font-size: 1.05rem; font-weight: 500; margin-bottom: 0.3rem;
}
.idea-card p {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.82rem; color: var(--muted);
}
.guide-intro { max-width: 62ch; margin-top: 0.4rem; }
.contact-list {
  list-style: none; margin: 1rem 0 0; padding: 0;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
}
.contact-list li { margin-bottom: 0.7rem; }
.contact-list a { color: var(--lagoon-deep); text-decoration: underline; text-underline-offset: 2px; }
.gear-cta {
  background: var(--sand);
  border-top: 1px solid var(--line);
  padding: 2.6rem 0 2.8rem;
}
.gear-cta-inner { max-width: 720px; }
.gear-cta h2 {
  font-size: clamp(1.55rem, 2.4vw, 1.95rem);
  font-weight: 500;
  letter-spacing: -0.01em;
  margin: 0.2rem 0 0.65rem;
}
.gear-cta-copy {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.95rem;
  color: var(--muted);
  max-width: 54ch;
  margin: 0 0 1rem;
}
.gear-picks-label {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.72rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 0.4rem 0 0.45rem;
}
.gear-picks {
  list-style: none;
  margin: 0 0 1.15rem;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.gear-picks a {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.95rem;
  color: var(--lagoon-deep);
  text-decoration: underline;
  text-underline-offset: 3px;
}
.gear-picks a:hover { color: var(--ink); }
.gear-cta-btn {
  display: inline-block;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.78rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  background: var(--ink);
  color: #fff !important;
  padding: 0.75rem 1.15rem;
  border-radius: 999px;
}
.gear-cta-btn:hover { background: var(--lagoon-deep); }
.amazon-line {
  font-size: 0.86rem !important; line-height: 1.5; color: #d9d2c6 !important;
  max-width: 70ch;
}
.amazon-line strong { color: #fff; font-weight: 600; }
.shop-note {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.88rem; color: var(--muted); margin: -0.2rem 0 0.35rem; max-width: 52ch;
}
.shop-fr {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.8rem; color: var(--muted); margin: 0 0 1.2rem; max-width: 56ch;
}
@media (max-width: 700px) {
  .ideas-grid { grid-template-columns: 1fr; }
  .idea-card { grid-template-columns: 88px 1fr; }
}

"""


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def head_meta(title: str, description: str, canonical_path: str, og_image: str | None = None) -> str:
    """canonical_path is site-absolute path like / or /privacy/ or /stories/cliffside/."""
    canon = SITE_URL.rstrip("/") + (canonical_path if canonical_path.startswith("/") else "/" + canonical_path)
    if not canon.endswith("/") and not canon.rsplit("/", 1)[-1].endswith((".html", ".xml", ".txt", ".ico", ".svg", ".png", ".jpg")):
        # keep as-is for .html pages; directories should end with /
        pass
    og = og_image or (SITE_URL + "/images/home-hero-cliff.jpg")
    if og.startswith("/"):
        og = SITE_URL.rstrip("/") + og
    return f"""<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}" />
<link rel="canonical" href="{esc(canon)}" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Lock &amp; Linen" />
<meta property="og:title" content="{esc(title)}" />
<meta property="og:description" content="{esc(description)}" />
<meta property="og:url" content="{esc(canon)}" />
<meta property="og:image" content="{esc(og)}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{esc(title)}" />
<meta name="twitter:description" content="{esc(description)}" />
<meta name="twitter:image" content="{esc(og)}" />
<meta name="p:domain_verify" content="d8eba614593c879141a48e3784ac2664" />
<meta name="google-site-verification" content="epKejJR5K_EWgKNm6s708GhHztnLz79qfR9GjJEubyo" />
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-CK8VTP8KF1"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-CK8VTP8KF1');
</script>
"""


def header(prefix: str) -> str:
    return f"""  <header class="site-header">
    <div class="header-inner">
      <a class="wordmark" href="{prefix}index.html">Lock <span>&amp;</span> Linen</a>
      <nav aria-label="Primary">
        <a href="{prefix}index.html#homes">Homes</a>
        <a href="{prefix}index.html#stories">Stories</a>
        <a href="{prefix}guides/quiet-security-ideas/index.html">Guide</a>
        <a href="{prefix}guides/gear-wed-put-in-these-homes/index.html">Gear</a>
        <a href="{prefix}about.html">About</a>
        <a href="{prefix}contact/index.html">Contact</a>
      </nav>
    </div>
  </header>"""


def footer(ai_note: str, prefix: str) -> str:
    return f"""  <footer id="about">
    <div class="footer-inner">
      <div class="footer-brand">Lock <span>&amp;</span> Linen</div>
      <div class="footer-nav">
        <a href="{prefix}index.html">Homes</a>
        <a href="{prefix}index.html#stories">Stories</a>
        <a href="{prefix}guides/quiet-security-ideas/index.html">Guide</a>
        <a href="{prefix}guides/gear-wed-put-in-these-homes/index.html">Gear</a>
        <a href="{prefix}about.html">About</a>
        <a href="{prefix}privacy/index.html">Privacy</a>
        <a href="{prefix}contact/index.html">Contact</a>
      </div>
      <div class="disclosures">
        <p class="amazon-line">{esc(AMAZON_DISCLOSURE_EN)}</p>
        <p style="margin-top:0.85rem;"><strong>AI disclosure:</strong> {esc(ai_note)}</p>
      </div>
    </div>
  </footer>"""


def write_story(s: dict):
    slug = s["slug"]
    out_dir = PUBLIC / "stories" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = "../../"
    img = "images"
    gallery_html = []
    for fname, cap, wide in s["gallery"]:
        cls = "g-card wide" if wide else "g-card"
        gallery_html.append(
            f"""        <figure class="{cls}">
          <div class="frame"><img src="{img}/{esc(fname)}" alt="{esc(cap)}" /></div>
          <figcaption>{esc(cap)}</figcaption>
        </figure>"""
        )
    aside_html = "\n".join(
        f'          <li><span class="dot" aria-hidden="true"></span> {esc(x)}</li>' for x in s["aside"]
    )
    body_html = "\n".join(f"          <p>{esc(p)}</p>" for p in s["body"])
    shop_html = []
    for name, desc in s["shop"]:
        # No prices, ratings, availability, or product images until Amazon tools supply them.
        shop_html.append(
            f"""        <article class="product">
          <span class="ph-badge">Coming soon</span>
          <div class="ph-img">Image via Amazon</div>
          <div class="ph-body">
            <h3>{esc(name)}</h3>
            <p>{esc(desc)}</p>
            <span class="btn-soon">{esc(SHOP_COPY["en"]["btn"])}</span>
          </div>
        </article>"""
        )
    en, fr = SHOP_COPY["en"], SHOP_COPY["fr"]
    shop_section = ""
    if SHOP_MODULE_ENABLED:
        shop_section = f"""
  <section aria-label="{esc(en['heading'])}">
    <div class="wrap">
      <p class="section-label">{esc(en['label'])}</p>
      <h2>{esc(en['heading'])}</h2>
      <p class="shop-note">{esc(en['subline'])}</p>
      <p class="shop-note">{esc(en['commission'])}</p>
      <p class="shop-fr"><strong>FR — {esc(fr['heading'])}.</strong> {esc(fr['subline'])} {esc(fr['commission'])}</p>
      <div class="shop-grid">
{chr(10).join(shop_html)}
      </div>
    </div>
  </section>
"""

    platform_bits = [
        f'<a href="https://www.youtube.com/shorts/{esc(s["yt"])}" rel="noopener noreferrer">YouTube</a>'
    ]
    if s.get("ig"):
        platform_bits.append(f'<a href="{esc(s["ig"])}" rel="noopener noreferrer">Instagram</a>')
    if s.get("fb"):
        platform_bits.append(f'<a href="{esc(s["fb"])}" rel="noopener noreferrer">Facebook</a>')
    home_bit = f' · Home #{s["home_num"]}' if s.get("home_num") else ""
    platform_links = (
        '      <p class="reel-links" style="font-family:\'Helvetica Neue\',Helvetica,Arial,sans-serif;font-size:0.88rem;color:var(--muted);margin:0.85rem 0 0;">'
        + f"Watch the reel{home_bit}: "
        + " · ".join(platform_bits)
        + "</p>"
    )

    desc = (s.get("card_blurb") or s["tagline"] or s["title"])[:160]
    og_img = f"{SITE_URL}/stories/{slug}/images/banner.jpg"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_meta(f"{s['title']} — Lock & Linen", desc, f"/stories/{slug}/", og_img)}
{FAVICON.format(p=prefix)}<link rel="stylesheet" href="{prefix}css/site.css" />
</head>
<body>
{header(prefix)}

  <section class="hero" id="homes" aria-label="{esc(s['title'])} hero">
    <img src="{img}/banner.jpg" width="1920" height="1080" alt="{esc(s['hero_alt'])}" />
    <div class="hero-scrim" aria-hidden="true"></div>
    <div class="hero-copy">
      <p class="eyebrow">{esc(s['eyebrow'])}</p>
      <h1>{esc(s['title'])}</h1>
      <p class="tagline">{esc(s['tagline'])}</p>
    </div>
  </section>

  <section id="story">
    <div class="wrap story-grid">
      <div>
        <p class="section-label">The story</p>
        <h2>{esc(s['h2'])}</h2>
        <div class="story-body">
{body_html}
        </div>
      </div>
      <aside class="story-aside" aria-label="Key features">
        <h3>On this concept</h3>
        <ul>
{aside_html}
        </ul>
      </aside>
    </div>
  </section>

  <section class="gallery" aria-label="Gallery">
    <div class="wrap">
      <p class="section-label">Inside the concept</p>
      <h2>Rooms &amp; angles</h2>
      <div class="gallery-grid" style="margin-top: 1.4rem;">
{chr(10).join(gallery_html)}
      </div>
    </div>
  </section>

  <section aria-label="Watch the reel">
    <div class="wrap">
      <p class="section-label">Watch</p>
      <h2>The reel</h2>
      <p style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:0.88rem;color:var(--muted);margin:-0.4rem 0 0;max-width:52ch;">Privacy-friendly YouTube embed of the published Lock &amp; Linen Short.</p>
      <div class="embed-wrap">
        <iframe
          src="https://www.youtube-nocookie.com/embed/{esc(s['yt'])}"
          title="{esc(s['title'])} — YouTube Short"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          referrerpolicy="strict-origin-when-cross-origin"
          allowfullscreen
          loading="lazy"></iframe>
      </div>
{platform_links}
    </div>
  </section>

{shop_section}
{gear_section_html(slug, prefix)}
{footer(s['ai_note'], prefix)}
</body>
</html>
"""
    (out_dir / "index.html").write_text(html)


CARD_BLURBS = {
    "cliffside": "Cantilevered glass house above the surf, reached only by funicular, with a rock-cut cellar below.",
    "canyon": "Earth-walled house cut into a canyon wall, with one trail, one hidden gate and a fig courtyard.",
    "lighthouse": "Restored stone lighthouse and keeper's house on a rocky headland, reached by one gravel causeway.",
    "missile-silo": "A converted missile silo under the open prairie, with only a modest farmhouse and a flush hatch on top.",
    "fjord-boathouse": "Dark timber boathouse on dry-stone piers at the foot of a Nordic fjord, with a boat bay under the house.",
}

FAVICON = '<link rel="icon" href="{p}favicon.ico" sizes="any" />\n<link rel="icon" href="{p}favicon.svg" type="image/svg+xml" />\n<link rel="apple-touch-icon" href="{p}apple-touch-icon.png" />\n'


GUIDE_IDEAS = [
    {
        "slug": "island-home",
        "title": "One dock as the only way in",
        "blurb": "A single teak dock and boat lift set the perimeter without looking like a fortress — quiet access control rendered as coastal living.",
        "thumb": "stories/island-home/images/gallery-dock.jpg",
    },
    {
        "slug": "cliffside",
        "title": "A funicular instead of a driveway",
        "blurb": "The Cliffside Glass House uses one clifftop car as the only land entry. Soft oak and linen wait inside the cantilever.",
        "thumb": "stories/cliffside/images/gallery-3.jpg",
    },
    {
        "slug": "canyon",
        "title": "Earth walls that disappear into rock",
        "blurb": "Rammed earth flush with red canyon stone, a planted roof, and a fig courtyard — privacy by terrain, softness by material.",
        "thumb": "stories/canyon/images/gallery-1.jpg",
    },
    {
        "slug": "lighthouse",
        "title": "One gravel causeway to the keeper's house",
        "blurb": "A restored headland light with wool throws and a stove. The causeway is the filter; the interior is the refuge.",
        "thumb": "stories/lighthouse/images/gallery-1.jpg",
    },
    {
        "slug": "missile-silo",
        "title": "A flush hatch under a prairie farmhouse",
        "blurb": "Ordinary above, cylindrical oak living rooms below. Security as a quiet layer, not a showpiece.",
        "thumb": "stories/missile-silo/images/gallery-1.jpg",
    },
    {
        "slug": "fjord-boathouse",
        "title": "Boat bay under the living room",
        "blurb": "Dark timber, sheepskins, and a glass floor over the boat. Arrival by water feels intentional, not theatrical.",
        "thumb": "stories/fjord-boathouse/images/gallery-1.jpg",
    },
    {
        "slug": "canyon-homestead",
        "title": "Canyon walls as the compound edge",
        "blurb": "One road, one gate, cliffs on three sides. Raised beds and a root cellar keep the mood domestic.",
        "thumb": "stories/canyon-homestead/images/gallery-1.jpg",
    },
    {
        "slug": "sea-cliff-homestead",
        "title": "Headland compound above the surf",
        "blurb": "Sea cliffs on three sides, one lane in, wool throws after the wind. Fortification read as geography.",
        "thumb": "stories/sea-cliff-homestead/images/gallery-1.jpg",
    },
    {
        "slug": "mountain-homestead",
        "title": "Granite behind, one switchback road",
        "blurb": "Stone-and-timber under the peaks. Soft evenings, solar roofs, and a single approach that keeps the bench quiet.",
        "thumb": "stories/mountain-homestead/images/gallery-1.jpg",
    },
]


def write_index():
    cards = []
    for s in STORIES:
        thumb = f"stories/{s['slug']}/images/hero.jpg"
        cards.append(
            f"""        <a class="story-card" href="stories/{s['slug']}/index.html">
          <div class="thumb"><img src="{thumb}" alt="{esc(s['title'])}" /></div>
          <div class="body">
            <p class="eyebrow">Concept home</p>
            <h3>{esc(s['title'])}</h3>
            <p>{esc(CARD_BLURBS.get(s['slug'], s['card_blurb']))}</p>
            <span class="more">Read the story</span>
          </div>
        </a>"""
        )
    guide_card = """        <a class="story-card" href="guides/quiet-security-ideas/index.html">
          <div class="thumb"><img src="stories/cliffside/images/hero.jpg" alt="Guide: Quiet security, softly furnished" /></div>
          <div class="body">
            <p class="eyebrow">Guide</p>
            <h3>Quiet security, softly furnished</h3>
            <p>Nine ideas from our AI concept homes — privacy by design, comfort by material.</p>
            <span class="more">Read the guide</span>
          </div>
        </a>"""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_meta("Lock & Linen — Concept Homes", "AI-rendered concept homes: quietly fortified and softly furnished. Room-by-room stories from Lock & Linen.", "/", f"{SITE_URL}/images/home-hero-cliff.jpg")}
{FAVICON.format(p="")}<link rel="stylesheet" href="css/site.css" />
</head>
<body>
{header('')}

  <section class="hero" id="homes" aria-label="Lock and Linen hero">
    <img src="images/home-hero-cliff.jpg" width="1920" height="1080" alt="Glass, stone and timber cliffside home above the sea at golden hour — Lock and Linen concept home (AI-generated)" />
    <div class="hero-scrim" aria-hidden="true"></div>
    <div class="hero-copy">
      <p class="eyebrow">Concept homes · Stories</p>
      <h1>Quiet fortification, softly furnished</h1>
      <p class="tagline">AI-rendered hideaways — private, self-sufficient, and quietly fortified.</p>
    </div>
  </section>

  <section id="stories">
    <div class="wrap">
      <p class="section-label">Stories</p>
      <h2>Published concept homes</h2>
      <p style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:0.92rem;color:var(--muted);margin:-0.35rem 0 0;max-width:58ch;">Each story pairs stills from a Lock &amp; Linen reel with the caption and voiceover already published — no invented facts.</p>
      <div class="stories-grid">
{chr(10).join(cards)}
{guide_card}
      </div>
    </div>
  </section>

{footer(DEFAULT_AI_NOTE, '')}
</body>
</html>
"""
    (PUBLIC / "index.html").write_text(html)


def write_about():
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_meta("About — Lock & Linen", "Lock & Linen tells short stories about AI-rendered concept homes — private, self-sufficient places, quietly fortified and softly furnished.", "/about.html")}
{FAVICON.format(p="")}<link rel="stylesheet" href="css/site.css" />
</head>
<body>
{header('')}

  <section>
    <div class="wrap">
      <p class="section-label">About</p>
      <h2>Lock &amp; Linen</h2>
      <div class="prose">
        <p>Lock &amp; Linen tells short stories about concept homes — private, self-sufficient places rendered as quiet fortification, then softly furnished.</p>
        <p>Every home on this site comes from a published Lock &amp; Linen reel. The copy is taken from that reel’s caption and voiceover. The images are frames from the same render set. Nothing here is a real listing or a buildable plan.</p>
        <p>We participate in the Amazon Services LLC Associates Program. Product links are inspired by the look, not the exact items in the AI render.</p>
      </div>
    </div>
  </section>

{footer(DEFAULT_AI_NOTE, '')}
</body>
</html>
"""
    (PUBLIC / "about.html").write_text(html)


def write_privacy():
    out = PUBLIC / "privacy"
    out.mkdir(parents=True, exist_ok=True)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_meta("Privacy Policy — Lock & Linen", "How Lock & Linen handles information, cookies, Amazon Associates referrals, and hosting logs. Effective November 5, 2026.", "/privacy/")}
{FAVICON.format(p="../")}<link rel="stylesheet" href="../css/site.css" />
</head>
<body>
{header('../')}

  <section class="page-hero">
    <div class="wrap">
      <p class="section-label">Legal</p>
      <h1>Privacy policy</h1>
      <p style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:var(--muted);font-size:0.9rem;">Effective date: November 5, 2026 · Contact: <a href="mailto:hello@lockandlinen.com" style="color:var(--lagoon-deep);text-decoration:underline;">hello@lockandlinen.com</a></p>
      <div class="prose" style="margin-top:1.4rem;">
        <p>Lock &amp; Linen (“we”, “us”) runs this website to share AI-rendered concept-home stories. This policy explains what information is involved when you visit lockandlinen.com, in plain language. It is meant to be readable under Québec’s Law 25 as well as for visitors elsewhere.</p>

        <p><strong>Amazon Associates.</strong> We participate in the Amazon Services LLC Associates Program, an affiliate advertising program designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.com and related sites. {esc(AMAZON_DISCLOSURE_EN)}</p>

        <p><strong>Affiliate cookies.</strong> When you click an Amazon (or other affiliate) link on this site, Amazon and other third parties may place and read cookies or similar technologies on your device to track that you came from Lock &amp; Linen and to attribute a later purchase. We do not control those cookies. Their use is governed by Amazon’s and those parties’ own privacy policies. No affiliate links are live on the site until we enable them.</p>

        <p><strong>Analytics.</strong> We use Google Analytics 4 (GA4), Measurement ID <code>G-CK8VTP8KF1</code>, to understand how people use this site — for example which pages are viewed, approximate location, and device type. Google may set cookies or similar technologies and process usage data under <a href="https://policies.google.com/privacy" rel="noopener noreferrer">Google’s privacy policy</a>. We do not sell personal information. We do not use a Meta Pixel or similar advertising pixels. Story pages may also embed a privacy-enhanced YouTube player (<code>youtube-nocookie.com</code>); YouTube / Google may set or read cookies if you play a video, under Google’s policies.</p>

        <p><strong>Hosting logs.</strong> The site is hosted on Render. Like most hosts, Render may keep standard server logs (for example IP address, user agent, requested URL, and time) for security, debugging, and reliable delivery. We do not use those logs to build marketing profiles, and we do not sell personal information.</p>

        <p><strong>Accounts and forms.</strong> We do not offer user accounts on this site. There is no login and no on-site contact form — only a mailto link to hello@lockandlinen.com. If you email us, we use your message only to reply.</p>

        <p><strong>No sale of data.</strong> We do not sell your personal information.</p>

        <p><strong>Children.</strong> This site is not directed at children under 14.</p>

        <p><strong>Changes.</strong> If this policy changes, we will update the effective date on this page.</p>

        <p><strong>Contact.</strong> Questions: <a href="mailto:hello@lockandlinen.com">hello@lockandlinen.com</a>.</p>
      </div>

      <div class="fr-summary" lang="fr">
        <h3>Résumé (français)</h3>
        <p>Lock &amp; Linen présente des maisons conceptuelles générées par IA. Nous participons au programme Partenaires Amazon Services LLC. {esc(AMAZON_DISCLOSURE_FR)}</p>
        <p>Si vous cliquez un lien d’affiliation, Amazon et d’autres tiers peuvent placer et lire des témoins (cookies) pour attribuer une éventuelle vente. Nous utilisons Google Analytics 4 (GA4), identifiant de mesure <code>G-CK8VTP8KF1</code>, pour comprendre le trafic (pages consultées, localisation approximative, appareil). Google peut placer des témoins et traiter des données d’usage selon sa politique de confidentialité. Nous ne vendons pas de renseignements personnels. Pas de Meta Pixel. L’hébergeur (Render) peut conserver des journaux techniques habituels. Aucun compte utilisateur. Contact : hello@lockandlinen.com. Entrée en vigueur : 5 novembre 2026.</p>
      </div>
    </div>
  </section>

{footer(DEFAULT_AI_NOTE, '../')}
</body>
</html>
"""
    (out / "index.html").write_text(html)


def write_contact():
    out = PUBLIC / "contact"
    out.mkdir(parents=True, exist_ok=True)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_meta("Contact — Lock & Linen", "Email Lock & Linen at hello@lockandlinen.com. Questions about concept homes, press, or the site.", "/contact/")}
{FAVICON.format(p="../")}<link rel="stylesheet" href="../css/site.css" />
</head>
<body>
{header('../')}

  <section class="page-hero">
    <div class="wrap">
      <p class="section-label">Contact</p>
      <h1>Say hello</h1>
      <div class="prose" style="margin-top:1.1rem;">
        <p>For questions about a concept home, a correction on the site, press, or partnership notes — email us. We read every message; replies may take a few days.</p>
        <ul class="contact-list">
          <li><strong>Email:</strong> <a href="mailto:hello@lockandlinen.com">hello@lockandlinen.com</a></li>
          <li><strong>Pinterest:</strong> <a href="https://www.pinterest.com/lockandlinen/" rel="noopener noreferrer">pinterest.com/lockandlinen</a></li>
          <li><strong>Instagram:</strong> <a href="https://www.instagram.com/lockandlinen/" rel="noopener noreferrer">@lockandlinen</a></li>
          <li><strong>YouTube:</strong> <a href="https://www.youtube.com/@LockandLinen" rel="noopener noreferrer">@LockandLinen</a></li>
        </ul>
        <p style="margin-top:1.2rem;">We do not publish a phone number or street address. Visuals on this site are AI-generated concepts, not real listings.</p>
      </div>

      <div class="fr-summary" lang="fr">
        <h3>Résumé (français)</h3>
        <p>Écrivez-nous à <a href="mailto:hello@lockandlinen.com">hello@lockandlinen.com</a> pour toute question sur les maisons conceptuelles, le site ou la presse. Retrouvez-nous aussi sur Pinterest, Instagram et YouTube (@lockandlinen / @LockandLinen). Pas de téléphone ni d’adresse postale publiés.</p>
      </div>
    </div>
  </section>

{footer(DEFAULT_AI_NOTE, '../')}
</body>
</html>
"""
    (out / "index.html").write_text(html)


def write_guide():
    out = PUBLIC / "guides" / "quiet-security-ideas"
    out.mkdir(parents=True, exist_ok=True)
    cards = []
    for i, idea in enumerate(GUIDE_IDEAS, 1):
        cards.append(
            f"""        <a class="idea-card" href="../../stories/{idea['slug']}/index.html">
          <div class="thumb"><img src="../../{esc(idea['thumb'])}" alt="{esc(idea['title'])} — AI concept" /></div>
          <div class="body">
            <p class="eyebrow">Idea {i} · AI concept</p>
            <h3>{esc(idea['title'])}</h3>
            <p>{esc(idea['blurb'])}</p>
          </div>
        </a>"""
        )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_meta("Quiet security, softly furnished: 9 ideas — Lock & Linen", "Nine privacy-and-comfort ideas drawn from Lock & Linen AI concept homes — each linked to its full story.", "/guides/quiet-security-ideas/", f"{SITE_URL}/stories/cliffside/images/banner.jpg")}
{FAVICON.format(p="../../")}<link rel="stylesheet" href="../../css/site.css" />
</head>
<body>
{header('../../')}

  <section class="page-hero">
    <div class="wrap">
      <p class="section-label">Guide</p>
      <h1>Quiet security, softly furnished: 9 ideas from our concept homes</h1>
      <div class="prose guide-intro">
        <p>Lock &amp; Linen homes are AI-rendered concepts, not real listings. What they share is a mood: privacy handled by landform and a single clear entry, then interiors finished in linen, timber, wool, and soft light. Here are nine ideas you can steal for a mood board — each one links to the full story.</p>
        <p>Nothing on this page is a product claim or a security-performance guarantee. It is design inspiration from fictional places.</p>
      </div>
      <div class="ideas-grid">
{chr(10).join(cards)}
      </div>
    </div>
  </section>

{footer(DEFAULT_AI_NOTE, '../../')}
</body>
</html>
"""
    (out / "index.html").write_text(html)


def write_robots_and_sitemap():
    (PUBLIC / "robots.txt").write_text(
        f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    )
    paths = ["/", "/about.html", "/privacy/", "/contact/", "/guides/quiet-security-ideas/", "/guides/gear-wed-put-in-these-homes/", "/gear/"]
    for s in STORIES:
        paths.append(f"/stories/{s['slug']}/")
    urls = []
    for p in paths:
        loc = SITE_URL.rstrip("/") + p
        urls.append(f"""  <url>
    <loc>{loc}</loc>
    <changefreq>weekly</changefreq>
  </url>""")
    (PUBLIC / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def write_gear_shortlink():
    """Static /gear/ fallback that sends visitors to the showcase (Render 301 via Dashboard preferred)."""
    dest = f"{SITE_URL}/guides/gear-wed-put-in-these-homes/"
    out = PUBLIC / "gear"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta http-equiv="refresh" content="0;url={dest}" />
<link rel="canonical" href="{dest}" />
<meta name="robots" content="noindex" />
<title>Gear — Lock &amp; Linen</title>
<script>location.replace({dest!r});</script>
</head>
<body>
  <p>Moved to <a href="{dest}">Gear we'd put in these homes</a>.</p>
</body>
</html>
""")



def main():
    # Preserve hand-authored draft guides (e.g. showcase-draft gear page) across rebuilds.
    preserve_dirs = ["guides/gear-wed-put-in-these-homes"]
    preserved = {}
    for rel in preserve_dirs:
        src = PUBLIC / rel
        if src.exists():
            preserved[rel] = {p.relative_to(src): p.read_bytes() for p in src.rglob("*") if p.is_file()}
    if PUBLIC.exists():
        for child in PUBLIC.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "css").mkdir(parents=True, exist_ok=True)
    (PUBLIC / "css" / "site.css").write_text(CSS)
    for rel, files in preserved.items():
        dest = PUBLIC / rel
        dest.mkdir(parents=True, exist_ok=True)
        for sub, data in files.items():
            out = dest / sub
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
    for f in (Path(__file__).parent / "static").iterdir():
        shutil.copy2(f, PUBLIC / f.name)
    print("Compressing images…")
    prepare_images()
    print("Writing pages…")
    for s in STORIES:
        write_story(s)
        print(" ", s["slug"], s["yt"])
    write_index()
    write_about()
    write_privacy()
    write_contact()
    write_guide()
    write_gear_shortlink()
    write_robots_and_sitemap()
    manifest = [{"slug": s["slug"], "yt": s["yt"], "title": s["title"]} for s in STORIES]
    (ROOT / "site" / "_build" / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("Done.", len(STORIES), "stories + privacy/contact/guide")


if __name__ == "__main__":
    main()
