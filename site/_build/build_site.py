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
AMAZON_DISCLOSURE_NEAR = AMAZON_DISCLOSURE_EN  # Lex 2026-11-12: official singular wording everywhere
AMAZON_TRADEMARK = "Amazon and the Amazon logo are trademarks of Amazon.com, Inc. or its affiliates."
AMAZON_DISCLOSURE_FR = "En tant que Partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises."
GEAR_PAGE_HREF = "/guides/gear-wed-put-in-these-homes/"
GEAR_PAGE_REL = {  # prefix-relative from a story page
    "../../": "../../guides/gear-wed-put-in-these-homes/index.html",
}
# Optional tasteful picks for story pages that clearly match the showcase (name + ASIN).
GEAR_PICKS = {
    "cliffside": [
        ("SLNT leather phone sleeve", "B07GXZM5PM"),
        ("eufy Video Doorbell E340", "B0CD7NT4Y9"),
        ("Puzipha cordless wood & linen lamp", "B0GFDJ4X22"),
    ],
    "missile-silo": [
        ("Mission Darkness Faraday phone bag", "B09BGTVBKG"),
        ("SentrySafe fireproof document box", "B00KOO599O"),
        ("Swiss Safe first-aid kit", "B06XVJDYSF"),
    ],
    "bunker-lodge": [
        ("Buddybar door security bar", "B002BQ4VBU"),
        ("Mission Darkness Faraday phone bag", "B09BGTVBKG"),
        ("FosPower NOAA weather radio", "B0G53Z8RD1"),
    ],
    "fjord-boathouse": [
        ("Pendleton Eco-Wise wool throw", "B00I3N0M40"),
        ("UCO candle lantern", "B000BS05XS"),
        ("LLB ivory sheepskin", "B09BYXV2FR"),
    ],
    "glacier-cabin": [
        ("Pendleton Eco-Wise wool throw", "B00I3N0M40"),
        ("NICETOWN blackout curtains", "B07R5FC3K1"),
        ("FosPower NOAA weather radio", "B0G53Z8RD1"),
    ],
    "mountain-homestead": [
        ("eufy Video Doorbell E340", "B0CD7NT4Y9"),
        ("Barebones Edison Light Stick", "B0D46PQT2C"),
        ("UCO candle lantern", "B000BS05XS"),
    ],
    "canyon": [
        ("eufy Smart Lock C220", "B0CYYZ6WRW"),
        ("Twelve South PowerCapsule", "B0GMRFYVZ9"),
        ("Barebones Edison Light Stick", "B0D46PQT2C"),
    ],
    "island-home": [
        ("Simple&Opulence linen sheet set", "B08ZBWCTCK"),
        ("LifeStraw personal water filter", "B006QF3TW4"),
        ("Addalock portable door lock", "B00186URTY"),
    ],
    "cave-dwelling": [
        ("SentrySafe fireproof document box", "B00KOO599O"),
        ("Barebones Edison Light Stick", "B0D46PQT2C"),
        ("Luminara flameless pillars", "B09S24TQVP"),
    ],
    "black-aframe": [
        ("Pendleton Eco-Wise wool throw", "B00I3N0M40"),
        ("FosPower NOAA weather radio", "B0G53Z8RD1"),
        ("Twelve South PowerCapsule", "B0GMRFYVZ9"),
    ],
    "treehouse": [
        ("Addalock portable door lock", "B00186URTY"),
        ("Simple&Opulence linen sheet set", "B08ZBWCTCK"),
        ("Goal Zero Crush Light lantern", "B07BMJPH8L"),
    ],
    "marsh-stilt": [
        ("UltraPro window and door alarms", "B00178HMCI"),
        ("LifeStraw personal water filter", "B006QF3TW4"),
        ("Goal Zero Crush Light lantern", "B07BMJPH8L"),
    ],
    "lighthouse": [
        ("UltraPro window and door alarms", "B00178HMCI"),
        ("LifeStraw personal water filter", "B006QF3TW4"),
        ("FosPower NOAA weather radio", "B0G53Z8RD1"),
    ],
    "volcanic-plateau": [
        ("Goal Zero Crush Light lantern", "B07BMJPH8L"),
        ("Mission Darkness Faraday phone bag", "B09BGTVBKG"),
        ("UCO candle lantern", "B000BS05XS"),
    ],
    "cliff-monastery": [
        ("Addalock portable door lock", "B00186URTY"),
        ("Pendleton Eco-Wise wool throw", "B00I3N0M40"),
        ("UCO candle lantern", "B000BS05XS"),
    ],
    "canyon-homestead": [
        ("eufy Smart Lock C220", "B0CYYZ6WRW"),
        ("SentrySafe fireproof document box", "B00KOO599O"),
        ("Swiss Safe first-aid kit", "B06XVJDYSF"),
    ],
    "sea-cliff-homestead": [
        ("eufy Video Doorbell E340", "B0CD7NT4Y9"),
        ("NICETOWN blackout curtains", "B07R5FC3K1"),
        ("LifeStraw personal water filter", "B006QF3TW4"),
    ],
}

def gear_section_html(slug: str, prefix: str) -> str:
    """Tasteful end-of-story CTA linking to the gear showcase."""
    href = f"{prefix}guides/gear-wed-put-in-these-homes/index.html"
    picks = GEAR_PICKS.get(slug) or []
    picks_html = f'<p class="affiliate-near">{esc(AMAZON_DISCLOSURE_NEAR)}</p>\n'
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
            f'<p class="affiliate-near">{esc(AMAZON_DISCLOSURE_NEAR)}</p>\n'
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
.nav-priority,
.nav-toggle,
.nav-toggle-btn { display: none; }

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
.affiliate-near {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.78rem;
  line-height: 1.45;
  color: var(--muted);
  margin: 0.85rem 0 0;
  max-width: 62ch;
}
.gear-cta .affiliate-near {
  margin: -0.25rem 0 1rem;
}
.amazon-line {
  font-size: 0.86rem !important; line-height: 1.5; color: #d9d2c6 !important;
  max-width: 70ch;
}
.amazon-line + .amazon-line { margin-top: 0.4rem; }
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

.footer-nav .cookie-settings-link {
  text-transform: none;
  letter-spacing: 0.02em;
}
.ll-cookie-banner {
  position: fixed;
  left: 0; right: 0; bottom: 0;
  z-index: 80;
  max-height: 45dvh;
  overflow-y: auto;
  padding-bottom: env(safe-area-inset-bottom, 0px);
  -webkit-overflow-scrolling: touch;
  background: var(--cream);
  color: var(--ink);
  border-top: 1px solid var(--line);
  box-shadow: 0 -8px 24px rgba(28, 26, 23, 0.08);
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
}
.ll-cookie-banner[hidden] { display: none !important; }
.ll-cookie-banner:focus { outline: none; }
.ll-cookie-banner:focus-visible {
  outline: 2px solid var(--lagoon);
  outline-offset: -2px;
}
.ll-cookie-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0.9rem 1.25rem 1rem;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.55rem 1.25rem;
  align-items: end;
}
.ll-cookie-title {
  grid-column: 1 / -1;
  font-size: 0.68rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 600;
  color: var(--lagoon-deep);
  margin: 0;
}
.ll-cookie-copy p {
  font-size: 0.82rem;
  line-height: 1.45;
  color: var(--muted);
  margin: 0 0 0.3rem;
}
.ll-cookie-copy p:last-child { margin-bottom: 0; }
.ll-cookie-copy a {
  color: var(--lagoon-deep);
  text-decoration: underline;
  text-underline-offset: 2px;
}
.ll-cookie-actions {
  display: flex;
  gap: 0.55rem;
  flex-shrink: 0;
}
.ll-cookie-btn {
  appearance: none;
  font-family: inherit;
  font-size: 0.78rem;
  letter-spacing: 0.03em;
  line-height: 1.2;
  min-width: 10.5rem;
  padding: 0.65rem 1rem;
  border: 1px solid var(--ink);
  background: var(--cream);
  color: var(--ink);
  border-radius: 999px;
  cursor: pointer;
  text-align: center;
}
.ll-cookie-btn:hover { background: var(--sand); }
.ll-cookie-btn:focus-visible {
  outline: 2px solid var(--lagoon);
  outline-offset: 2px;
}
body.ll-cookie-open { padding-bottom: var(--ll-cookie-banner-h, 9rem); }
.ll-cookie-banner {
  max-height: 45dvh;
  overflow-y: auto;
  padding-bottom: env(safe-area-inset-bottom, 0px);
  -webkit-overflow-scrolling: touch;
}
@media (max-width: 720px) {
  .ll-cookie-inner {
    grid-template-columns: 1fr;
    padding: 0.65rem 0.9rem 0.7rem;
    gap: 0.4rem;
  }
  .ll-cookie-title { font-size: 0.62rem; }
  .ll-cookie-copy p { font-size: 0.75rem; line-height: 1.35; margin-bottom: 0.2rem; }
  .ll-cookie-actions { width: 100%; }
  .ll-cookie-btn { flex: 1 1 0; min-width: 0; padding: 0.58rem 0.7rem; font-size: 0.75rem; }
}

/* Field Notes long-form */
.fn-hero h1 { max-width: 22ch; }
.fn-article { padding: 2.5rem 0 3.75rem; }
.fn-article h2 { max-width: 62ch; }
.fn-copy { max-width: 62ch; }
.fn-copy p { margin-bottom: 1.1rem; font-size: 1.08rem; color: #2a2621; }
.fn-copy a { color: var(--ink); text-decoration: underline; text-decoration-thickness: 1px; text-underline-offset: 0.15em; }
.fn-copy a:hover { color: var(--lagoon); }
.fn-figure { margin: 1.75rem 0 2rem; max-width: 70ch; }
.fn-figure img {
  display: block; width: 100%; height: auto;
  border-radius: 10px;
  background: #1c2320;
}
.fn-figure figcaption {
  padding: 0.7rem 0.1rem 0;
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  font-size: 0.92rem;
  font-style: italic;
  color: var(--muted);
  max-width: 62ch;
}
.fn-table-wrap { overflow-x: auto; margin: 1.35rem 0 2rem; max-width: 70ch; }
.fn-table {
  width: 100%; border-collapse: collapse;
  font-size: 0.92rem; line-height: 1.45;
}
.fn-table th, .fn-table td {
  text-align: left; vertical-align: top;
  padding: 0.65rem 0.8rem 0.65rem 0;
  border-bottom: 1px solid var(--line);
}
.fn-table th {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.68rem; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--muted); font-weight: 600;
}
.fn-credit {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.82rem; color: var(--muted);
  margin: 0.65rem 0 0; max-width: 62ch;
}
.fn-picks { list-style: none; padding: 0; margin: 1.1rem 0 1.8rem; max-width: 62ch; }
.fn-picks li { margin: 0 0 0.95rem; padding: 0 0 0.95rem; border-bottom: 1px solid var(--line); }
.fn-picks li:last-child { border-bottom: 0; }
.fn-picks a { color: var(--ink); }
.fn-article-end { margin-top: 2.2rem; }
.fn-card-meta { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin: 0 0 0.35rem; }
.fn-glance { margin: 0.4rem 0 2.4rem; }
.fn-glance h2 { max-width: none; margin-bottom: 0.7rem; }
.fn-jumps {
  display: flex; flex-wrap: wrap; gap: 0.5rem 1.15rem;
  margin: 0 0 1.15rem;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;
}
.fn-jumps a { color: var(--lagoon); text-decoration: none; }
.fn-jumps a:hover { color: var(--ink); }
.fn-article .product { border-style: solid; border-color: var(--line); }
.fn-section { margin: 0 0 2.35rem; }
.fn-section .shop-grid { margin-top: 1rem; }
/* One-product tiers (Pocket, Camping): a single full card, not 1/4 of a 280px grid */
.shop-grid.shop-grid--single,
.fn-section .shop-grid.shop-grid--single { grid-template-columns: minmax(0, 1fr); max-width: 280px; }
.affiliate-note { margin: 0 0 1.4rem; max-width: 62ch; }
.page-hero .tagline {
  margin: 0 0 0.5rem;
  font-size: clamp(1rem, 2.2vw, 1.25rem);
  font-style: italic;
  color: var(--muted);
  max-width: 40ch;
}
.fn-copy h3 {
  font-size: 1.18rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 1.7rem 0 0.7rem;
  max-width: 62ch;
}
.fn-copy ul {
  margin: 0 0 1.3rem;
  padding-left: 1.25rem;
  max-width: 62ch;
}
.fn-copy li { margin: 0 0 0.55rem; }
.fn-article h2[id] { scroll-margin-top: 5rem; }
.btn-amazon {
  background: var(--lagoon); color: #fff; border-color: var(--lagoon-deep);
  cursor: pointer; text-decoration: none;
}
.btn-amazon:hover { filter: brightness(1.05); color: #fff; }
@media (max-width: 560px) {
  .fn-glance .shop-grid,
  .fn-section .shop-grid { grid-template-columns: 1fr 1fr; }
  .fn-section .shop-grid.shop-grid--single { grid-template-columns: minmax(0, 1fr); max-width: 260px; }
}
@media (max-width: 860px) {
  .header-inner { position: relative; gap: 0.75rem; }
  .nav-priority {
    display: inline-block;
    margin-left: auto;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--lagoon); font-weight: 600;
    white-space: nowrap;
  }
  .nav-priority:hover { color: var(--ink); }
  .nav-toggle {
    position: absolute; width: 1px; height: 1px;
    padding: 0; margin: -1px; overflow: hidden;
    clip: rect(0,0,0,0); border: 0;
  }
  .nav-toggle-btn {
    display: inline-flex; align-items: center; justify-content: center;
    flex: 0 0 auto;
    min-height: 2.2rem; padding: 0.35rem 0.7rem;
    border: 1px solid var(--line); border-radius: 8px;
    background: var(--card); color: var(--ink);
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
    cursor: pointer;
  }
  .nav-toggle-open { display: none; }
  .nav-toggle:checked ~ .nav-toggle-btn .nav-toggle-closed { display: none; }
  .nav-toggle:checked ~ .nav-toggle-btn .nav-toggle-open { display: inline; }
  .site-header .primary-nav {
    display: none;
    position: absolute; left: 0; right: 0; top: 100%;
    z-index: 45;
    flex-direction: column;
    gap: 0;
    background: var(--cream);
    border-bottom: 1px solid var(--line);
    padding: 0.35rem 1.25rem 0.85rem;
    box-shadow: 0 10px 24px rgba(28,26,23,0.08);
  }
  .site-header .primary-nav a {
    display: block;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--line);
    font-size: 0.84rem;
  }
  .site-header .primary-nav a:last-child { border-bottom: 0; }
  .nav-toggle:checked ~ .primary-nav { display: flex; }
}

.home-feature { padding: 1.35rem 0 0; }
.fn-feature {
  display: grid;
  grid-template-columns: 1.15fr 0.9fr;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 14px;
  overflow: hidden;
  color: inherit;
}
.fn-feature:hover { border-color: #cbbda6; }
.fn-feature .thumb {
  aspect-ratio: 16 / 9;
  background: #1c2320;
  overflow: hidden;
  min-height: 0;
}
.fn-feature .thumb img {
  width: 100%; height: 100%;
  object-fit: cover; object-position: center;
}
.fn-feature .body {
  padding: 1.35rem 1.4rem 1.45rem;
  display: flex; flex-direction: column; justify-content: center;
}
.fn-feature .body .eyebrow { opacity: 1; color: var(--lagoon); margin-bottom: 0.4rem; }
.fn-feature h2 {
  font-size: clamp(1.45rem, 2.6vw, 1.9rem);
  font-weight: 500; letter-spacing: -0.02em;
  margin: 0 0 0.5rem;
  max-width: none;
}
.fn-feature p {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.92rem; color: var(--muted);
  margin: 0 0 1rem;
  max-width: 42ch;
}
.btn-feature {
  display: inline-block;
  align-self: flex-start;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
  padding: 0.7rem 1rem;
  background: var(--lagoon); color: #fff;
  border-radius: 8px; border: 1px solid var(--lagoon-deep);
}
.fn-feature:hover .btn-feature { filter: brightness(1.05); }

.fn-banner {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 0;
  margin: 1.25rem 0 0.4rem;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  color: inherit;
  max-width: 52rem;
}
.fn-banner:hover { border-color: #cbbda6; }
.fn-banner img {
  width: 100%; height: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover; object-position: center;
  background: #1c2320;
}
.fn-banner-body {
  padding: 0.9rem 1.05rem 1rem;
  display: flex; flex-direction: column; justify-content: center;
}
.fn-banner-body .eyebrow { opacity: 1; color: var(--lagoon); margin-bottom: 0.25rem; }
.fn-banner-title {
  font-size: 1.15rem; font-weight: 500; letter-spacing: -0.01em;
  margin: 0 0 0.25rem;
}
.fn-banner-copy {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.84rem; color: var(--muted);
  margin: 0 0 0.75rem;
}
.fn-banner .btn-feature { align-self: flex-start; }
.fn-banner:hover .btn-feature { filter: brightness(1.05); }

.home-feature .fn-feature + .fn-feature { margin-top: 1.25rem; }
.fn-banner + .fn-banner { margin-top: 1rem; }
.fn-figure.fn-figure--portrait { max-width: 28rem; }

@media (max-width: 720px) {
  .fn-feature { grid-template-columns: 1fr; }
  .fn-feature .body { padding: 1.1rem 1.05rem 1.2rem; }
  .fn-banner { grid-template-columns: 1fr; }
}

"""



COOKIE_JS = r"""(function () {
  "use strict";
  var KEY = "ll_cookie_consent";
  var GA_ID = "G-CK8VTP8KF1";
  var GTAG_SRC = "https://www.googletagmanager.com/gtag/js?id=" + GA_ID;

  function getChoice() {
    try { return window.localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function setChoice(value) {
    try { window.localStorage.setItem(KEY, value); } catch (e) {}
  }

  function loadAnalytics() {
    if (window.__llGtagLoaded) return;
    window.__llGtagLoaded = true;
    window.dataLayer = window.dataLayer || [];
    function gtag() { window.dataLayer.push(arguments); }
    window.gtag = gtag;
    gtag("consent", "default", {
      analytics_storage: "denied",
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
      wait_for_update: 500
    });
    gtag("consent", "update", {
      analytics_storage: "granted",
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied"
    });
    var s = document.createElement("script");
    s.async = true;
    s.src = GTAG_SRC;
    s.onload = function () {
      gtag("js", new Date());
      gtag("config", GA_ID);
    };
    document.head.appendChild(s);
  }

  function revokeAnalytics() {
    if (typeof window.gtag === "function") {
      window.gtag("consent", "update", {
        analytics_storage: "denied",
        ad_storage: "denied",
        ad_user_data: "denied",
        ad_personalization: "denied"
      });
    }
  }

  function setBannerHeight(el) {
    document.body.style.setProperty("--ll-cookie-banner-h", el.offsetHeight + "px");
  }

  function pinToVisualViewport() {
    var el = document.getElementById("ll-cookie-banner");
    if (!el) return;
    var vv = window.visualViewport;
    var visible = vv ? vv.height : window.innerHeight;
    var offset = 0;
    if (vv) offset = Math.max(0, window.innerHeight - vv.height - (vv.offsetTop || 0));
    el.style.bottom = offset + "px";
    el.style.maxHeight = Math.max(160, Math.floor(visible * 0.45)) + "px";
    if (!el.hidden) setBannerHeight(el);
  }

  function hideBanner() {
    var el = document.getElementById("ll-cookie-banner");
    if (el) {
      el.hidden = true;
      el.setAttribute("hidden", "");
    }
    document.body.classList.remove("ll-cookie-open");
  }

  function showBanner() {
    ensureBanner();
    var el = document.getElementById("ll-cookie-banner");
    el.hidden = false;
    el.removeAttribute("hidden");
    document.body.classList.add("ll-cookie-open");
    pinToVisualViewport();
    if (document.activeElement && document.activeElement.id === "ll-cookie-settings") {
      var first = el.querySelector("button, a");
      if (first) first.focus();
    }
  }

  function accept() {
    setChoice("accepted");
    hideBanner();
    loadAnalytics();
  }
  function refuse() {
    setChoice("refused");
    hideBanner();
    revokeAnalytics();
  }

  function isFrenchPage() {
    return /^fr/i.test(document.documentElement.getAttribute("lang") || "");
  }

  function bannerHtml() {
    if (isFrenchPage()) {
      return '<div class="ll-cookie-inner">' +
        '<p id="ll-cookie-title" class="ll-cookie-title">Témoins et analyse d’audience</p>' +
        '<div id="ll-cookie-desc" class="ll-cookie-copy">' +
          '<p lang="fr">Nous utilisons Google Analytics uniquement pour comprendre le trafic sur ce site. Pas de publicité. Consultez la <a href="/fr/privacy/#consent">politique de confidentialité</a>.</p>' +
        "</div>" +
        '<div class="ll-cookie-actions">' +
          '<button type="button" class="ll-cookie-btn" data-ll-refuse>Refuser</button>' +
          '<button type="button" class="ll-cookie-btn" data-ll-accept>Accepter</button>' +
        "</div>" +
      "</div>";
    }
    return '<div class="ll-cookie-inner">' +
        '<p id="ll-cookie-title" class="ll-cookie-title">Témoins et analyse / Cookies and analytics</p>' +
        '<div id="ll-cookie-desc" class="ll-cookie-copy">' +
          '<p lang="fr">Nous utilisons Google Analytics uniquement pour comprendre le trafic sur ce site. Pas de publicité. Consultez la <a href="/fr/privacy/#consent">politique de confidentialité</a>.</p>' +
          '<p lang="en">We use Google Analytics only to understand how this site is used. No advertising. See the <a href="/privacy/#consent">privacy policy</a>.</p>' +
        "</div>" +
        '<div class="ll-cookie-actions">' +
          '<button type="button" class="ll-cookie-btn" data-ll-refuse>Refuser / Refuse</button>' +
          '<button type="button" class="ll-cookie-btn" data-ll-accept>Accepter / Accept</button>' +
        "</div>" +
      "</div>";
  }

  function ensureBanner() {
    if (document.getElementById("ll-cookie-banner")) return;
    var wrap = document.createElement("div");
    wrap.id = "ll-cookie-banner";
    wrap.className = "ll-cookie-banner";
    wrap.setAttribute("role", "dialog");
    wrap.setAttribute("aria-modal", "false");
    wrap.setAttribute("aria-labelledby", "ll-cookie-title");
    wrap.setAttribute("aria-describedby", "ll-cookie-desc");
    wrap.tabIndex = -1;
    wrap.hidden = true;
    wrap.innerHTML = bannerHtml();
    document.body.appendChild(wrap);
    wrap.querySelector("[data-ll-refuse]").addEventListener("click", refuse);
    wrap.querySelector("[data-ll-accept]").addEventListener("click", accept);
    wrap.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      if (getChoice()) hideBanner();
    });
    window.addEventListener("resize", pinToVisualViewport);
    if (window.visualViewport) {
      window.visualViewport.addEventListener("resize", pinToVisualViewport);
      window.visualViewport.addEventListener("scroll", pinToVisualViewport);
    }
  }

  function bindFooter() {
    document.addEventListener("click", function (e) {
      var t = e.target.closest && e.target.closest("#ll-cookie-settings");
      if (!t) return;
      e.preventDefault();
      showBanner();
    });
  }

  function init() {
    ensureBanner();
    bindFooter();
    var choice = getChoice();
    if (choice === "accepted") loadAnalytics();
    else if (choice !== "refused") showBanner();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
"""


def write_cookie_js() -> None:
    dest = PUBLIC / "js"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "cookie-consent.js").write_text(COOKIE_JS)


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
<script src="/js/cookie-consent.js" defer></script>
"""


def header(prefix: str) -> str:
    return f"""  <header class="site-header">
    <div class="header-inner">
      <a class="wordmark" href="{prefix}index.html">Lock <span>&amp;</span> Linen</a>
      <a class="nav-priority" href="{prefix}field-notes/index.html">Field Notes</a>
      <input type="checkbox" id="nav-toggle" class="nav-toggle" />
      <label for="nav-toggle" class="nav-toggle-btn">
        <span class="nav-toggle-closed">Menu</span>
        <span class="nav-toggle-open">Close</span>
      </label>
      <nav class="primary-nav" aria-label="Primary">
        <a href="{prefix}index.html#homes">Homes</a>
        <a href="{prefix}index.html#stories">Stories</a>
        <a href="{prefix}guides/quiet-security-ideas/index.html">Guide</a>
        <a href="{prefix}field-notes/index.html">Field Notes</a>
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
        <a href="{prefix}field-notes/index.html">Field Notes</a>
        <a href="{prefix}guides/gear-wed-put-in-these-homes/index.html">Gear</a>
        <a href="{prefix}about.html">About</a>
        <a href="{prefix}privacy/index.html">Privacy</a>
        <a href="/privacy/#consent" id="ll-cookie-settings" class="cookie-settings-link">Cookie settings / Paramètres des témoins</a>
        <a href="{prefix}contact/index.html">Contact</a>
      </div>
      <div class="disclosures">
        <p class="amazon-line">{esc(AMAZON_DISCLOSURE_EN)}</p>
        <p class="amazon-line">{esc(AMAZON_TRADEMARK)}</p>
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

  <section class="home-feature" aria-label="Field Notes">
    <div class="wrap">
      <a class="fn-feature" href="field-notes/closed-up-for-the-evening/index.html">
        <div class="thumb">
          <img src="field-notes/closed-up-for-the-evening/hero.jpg" width="1280" height="720" alt="A softly lit entryway at dusk: a closed off-white front door, a brass lamp on an oak console, and linen curtains." />
        </div>
        <div class="body">
          <p class="eyebrow">Field Notes</p>
          <h2>Closed Up for the Evening</h2>
          <p>Quiet layers for the doors, the windows, and the glass of a hidden home.</p>
          <span class="btn-feature">Read the guide</span>
        </div>
      </a>
      <a class="fn-feature" href="field-notes/when-the-grid-goes-dark/index.html">
        <div class="thumb">
          <img src="field-notes/when-the-grid-goes-dark/hero.jpg" width="1280" height="720" alt="A quiet residential street at night during a power outage. One mid-block house is still warmly lit." />
        </div>
        <div class="body">
          <p class="eyebrow">Field Notes</p>
          <h2>When the Grid Goes Dark</h2>
          <p>The power bank guide for your hidden home — from a bank in a jacket pocket to a station that can keep a fridge going through an outage.</p>
          <span class="btn-feature">Read the power guide</span>
        </div>
      </a>
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
{head_meta("Privacy Policy — Lock & Linen", "How Lock & Linen handles information, cookies, Amazon Associates referrals, and hosting logs. Effective November 10, 2026.", "/privacy/")}
{FAVICON.format(p="../")}<link rel="stylesheet" href="../css/site.css" />
</head>
<body>
{header('../')}

  <section class="page-hero">
    <div class="wrap">
      <p class="section-label">Legal</p>
      <h1>Privacy policy</h1>
      <p style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:var(--muted);font-size:0.9rem;">Effective date: November 10, 2026 · Contact: <a href="mailto:hello@lockandlinen.com" style="color:var(--lagoon-deep);text-decoration:underline;">hello@lockandlinen.com</a></p>
      <div class="prose" style="margin-top:1.4rem;">
        <p>Lock &amp; Linen (“we”, “us”) runs this website to share AI-rendered concept-home stories. This policy explains what information is involved when you visit lockandlinen.com, in plain language. It is meant to be readable under Québec’s Law 25 as well as for visitors elsewhere.</p>

        <p><strong>Amazon Associates.</strong> We participate in the Amazon Services LLC Associates Program, an affiliate advertising program designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.com and related sites. {esc(AMAZON_DISCLOSURE_EN)}</p>

        <p><strong>Affiliate links and cookies.</strong> This site contains Amazon affiliate links. If you click one and buy something, we may earn a commission at no extra cost to you. When you click an Amazon (or other affiliate) link on this site, Amazon and other third parties may place and read cookies or similar technologies on your device to track that you came from Lock &amp; Linen and to attribute a later purchase. We do not control those cookies. Their use is governed by <a href="https://www.amazon.com/privacy" rel="noopener noreferrer">Amazon’s privacy notice</a> (https://www.amazon.com/privacy) and by those parties’ own privacy policies.</p>

        <p><strong>Analytics.</strong> We use Google Analytics 4 (GA4), Measurement ID <code>G-CK8VTP8KF1</code>, to understand how people use this site — for example which pages are viewed, approximate location, and device type. Google may set cookies or similar technologies and process usage data under <a href="https://policies.google.com/privacy" rel="noopener noreferrer">Google’s privacy policy</a>. Analytics loads only after you accept the cookie banner described below. We do not sell personal information. We do not use a Meta Pixel or similar advertising pixels. Story pages may also embed a privacy-enhanced YouTube player (<code>youtube-nocookie.com</code>); YouTube / Google may set or read cookies if you play a video, under Google’s policies.</p>

        <p id="consent"><strong>Cookie consent.</strong> The first time you visit, we show a consent banner: French only on French-language pages, and bilingual French and English on English-language pages. Google Analytics is not loaded, and no analytics cookies are set, until you choose Accept. If you choose Refuse, we do not load Google Analytics. We store your choice in your browser’s localStorage (key <code>ll_cookie_consent</code>) so later visits can honour it. You can change your mind at any time with the “Cookie settings / Paramètres des témoins” link in the footer, or by clearing your browser data. Analytics is the only purpose of this banner. We do not use advertising cookies. Clicking an Amazon affiliate link may still allow Amazon to set its own cookies, which we do not control.</p>

        <p id="language">We also store two language-preference keys in your browser’s localStorage: <code>ll_lang</code> (your manual EN or FR choice) and <code>ll_lang_auto_done</code> (a flag that a first-visit language suggestion has already run). These values stay in your browser only; they are not sent to us and are not used for analytics or advertising. You can clear them by clearing your browser data, or the site data, for lockandlinen.com.</p>

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
        <p>Si vous cliquez un lien d’affiliation, Amazon et d’autres tiers peuvent placer et lire des témoins (cookies) pour attribuer une éventuelle vente. Nous utilisons Google Analytics 4 (GA4), identifiant de mesure <code>G-CK8VTP8KF1</code>, pour comprendre le trafic (pages consultées, localisation approximative, appareil), seulement après que vous ayez accepté la bannière de consentement. Google peut alors placer des témoins et traiter des données d’usage selon sa politique de confidentialité. Un refus signifie que GA4 n’est pas chargé. Votre choix est conservé dans le localStorage du navigateur et peut être modifié en tout temps via le lien « Cookie settings / Paramètres des témoins » dans le pied de page. Nous ne vendons pas de renseignements personnels. Pas de Meta Pixel ni de témoins publicitaires de notre part. L’hébergeur (Render) peut conserver des journaux techniques habituels. Aucun compte utilisateur. Contact : hello@lockandlinen.com. Entrée en vigueur : 10 novembre 2026.</p>
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



FIELD_NOTES_CONTENT = ROOT / "site" / "_content" / "field-notes"
AMAZON_REL = 'rel="nofollow sponsored noopener noreferrer"'


def _amazon(asin: str) -> str:
    return f"https://www.amazon.com/dp/{asin}?tag=lockandlinen-20"


def fn_product_card(asin, image, alt, badge, title, blurb):
    """A gear-style product card. Image and button both go to the tagged Amazon URL."""
    url = _amazon(asin)
    return f"""        <article class="product">
          <span class="ph-badge">{badge}</span>
          <a class="ph-img" href="{url}" {AMAZON_REL}>
            <img src="{image}" alt="{alt}" width="600" height="600" loading="lazy" decoding="async" referrerpolicy="no-referrer-when-downgrade" />
          </a>
          <div class="ph-body">
            <h3>{title}</h3>
            <p>{blurb}</p>
            <a class="btn-soon btn-amazon" href="{url}" {AMAZON_REL}>View on Amazon</a>
          </div>
        </article>
"""


def write_field_notes():
    """Index + first long-form article. Images are copied from site/_content."""
    src_root = FIELD_NOTES_CONTENT
    dest_root = PUBLIC / "field-notes"
    dest_root.mkdir(parents=True, exist_ok=True)
    if src_root.exists():
        for src in src_root.rglob("*"):
            if src.is_file():
                dest = dest_root / src.relative_to(src_root)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
    write_field_notes_index()
    write_field_notes_grid_goes_dark()
    write_field_notes_closed_up()
    write_field_notes_water_filtration()


def write_field_notes_index():
    prefix = "../"
    out = PUBLIC / "field-notes"
    out.mkdir(parents=True, exist_ok=True)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_meta("Field Notes — Lock & Linen", "Long-form notes on hidden homes and the quiet gear that belongs in them. From Lock & Linen.", "/field-notes/", f"{SITE_URL}/field-notes/when-the-grid-goes-dark/hero.jpg")}
{FAVICON.format(p=prefix)}<link rel="stylesheet" href="{prefix}css/site.css" />
</head>
<body>
{header(prefix)}

  <section class="page-hero">
    <div class="wrap">
      <p class="section-label">Field Notes</p>
      <h1>Notes from hidden homes</h1>
      <div class="prose guide-intro">
        <p>Longer pieces on comfort that stays on, and the quiet objects that belong in these rooms. Written to be read through, with pictures.</p>
      </div>
      <div class="ideas-grid" style="margin-top:2rem;">
        <a class="idea-card" href="closed-up-for-the-evening/index.html">
          <div class="thumb"><img src="closed-up-for-the-evening/hero.jpg" alt="A softly lit entryway at dusk, with a closed door, a brass lamp, and linen curtains" /></div>
          <div class="body">
            <p class="eyebrow">Field Notes</p>
            <h3>Closed Up for the Evening</h3>
            <p>Quiet layers for the doors, the windows, and the glass of a hidden home.</p>
          </div>
        </a>
        <a class="idea-card" href="when-the-grid-goes-dark/index.html">
          <div class="thumb"><img src="when-the-grid-goes-dark/hero.jpg" alt="A quiet street at night; one house is still lit" /></div>
          <div class="body">
            <p class="eyebrow">Field Notes</p>
            <h3>When the Grid Goes Dark</h3>
            <p>The power bank guide for your hidden home — from a bank in a jacket pocket to a station that can keep a fridge going through an outage.</p>
          </div>
        </a>
      </div>
    </div>
  </section>

{footer(DEFAULT_AI_NOTE, prefix)}
</body>
</html>
"""
    (out / "index.html").write_text(html)


def write_field_notes_grid_goes_dark():
    prefix = "../../"
    slug = "when-the-grid-goes-dark"
    out = PUBLIC / "field-notes" / slug
    out.mkdir(parents=True, exist_ok=True)

    img_twelve = "https://m.media-amazon.com/images/I/61ZZw2GRDVL._AC_SL1500_.jpg"
    img_anker_20 = "https://m.media-amazon.com/images/I/217wCCtq3QL._AC_UL1500_.jpg"
    img_anker_26 = "https://m.media-amazon.com/images/I/31PvsmoVUfL._AC_UL1500_.jpg"
    img_daran = "https://m.media-amazon.com/images/I/81qxI84VesL._AC_SL1500_.jpg"
    img_jackery_1000 = "https://m.media-amazon.com/images/I/31+D1tNXreL._AC_UL1500_.jpg"
    img_jackery_2000 = "https://m.media-amazon.com/images/I/41-aYRSzjEL._AC_UL1500_.jpg"
    img_ecoflow = "https://m.media-amazon.com/images/I/61bW3qrsEbL._AC_SL1500_.jpg"
    img_solix = "https://m.media-amazon.com/images/I/41iJKYxROtL._AC_UL1500_.jpg"

    card_twelve = fn_product_card(
        "B0GMRFYVZ9", img_twelve,
        "Twelve South PowerCapsule 10,000 mAh power bank in Dune, attached to the back of a phone",
        "Pocket", "Twelve South PowerCapsule 10K",
        "10,000 mAh in Dune leather. Usually around $45.",
    )
    card_anker_20 = fn_product_card(
        "B0F66NH2ZX", img_anker_20,
        "Anker Prime Power Bank, 20,100 mAh, 220 W, in silver and black with a digital display",
        "Everyday carry", "Anker Prime 20,100 mAh, 220W",
        "Laptop-ready everyday bank. Usually around $180.",
    )
    card_anker_26 = fn_product_card(
        "B0F66LNB8D", img_anker_26,
        "Anker Prime Power Bank, 26,250 mAh, 300 W, in silver and black with a digital display",
        "Everyday carry", "Anker Prime 26,250 mAh, 300W",
        "More headroom for a weekend. Usually around $230.",
    )
    card_daran = fn_product_card(
        "B0GKGFWY69", img_daran,
        "DaranEner portable power station in a compact grey case with a handle and AC outlets",
        "Camping", "DaranEner 600W / 288Wh",
        "A compact station for a night away. Usually around $175.",
    )
    card_ecoflow = fn_product_card(
        "B0DCC2BVFW", img_ecoflow,
        "EcoFlow DELTA 3 Plus home-backup power station, silver case with a front display and AC outlets",
        "Home backup", "EcoFlow DELTA 3 Plus",
        "1,024 Wh, expandable to about 5 kWh. Usually around $720.",
    )
    card_jackery_1000 = fn_product_card(
        "B0D7PPG25F", img_jackery_1000,
        "Jackery Explorer 1000 v2 portable power station in black and orange with a handle and AC outlets",
        "Home backup", "Jackery Explorer 1000 v2",
        "1,024 Wh, not expandable. Usually around $560.",
    )
    card_jackery_2000 = fn_product_card(
        "B0DFG2WDQH", img_jackery_2000,
        "Jackery Explorer 2000 v2 portable power station in black and orange with a handle and AC outlets",
        "Home backup", "Jackery Explorer 2000 v2",
        "2,042 Wh, not expandable. Usually around $1,000.",
    )
    card_solix = fn_product_card(
        "B0FVFGL38H", img_solix,
        "Anker SOLIX C2000 Gen 2 portable power station in grey and black with a front display and AC outlets",
        "Home backup", "Anker SOLIX C2000 Gen 2",
        "2,048 Wh, expandable to 4 kWh. Usually around $950.",
    )
    a = _amazon

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_meta("When the Grid Goes Dark: The Power Bank Guide for Your Hidden Home — Lock & Linen", "When the block goes dark, one house is still lit. A long guide to the power you can carry, and the kind that can keep a hidden home going through an outage.", "/field-notes/when-the-grid-goes-dark/", f"{SITE_URL}/field-notes/when-the-grid-goes-dark/hero.jpg")}
{FAVICON.format(p=prefix)}<link rel="stylesheet" href="{prefix}css/site.css" />
</head>
<body>
{header(prefix)}

  <section class="hero fn-hero" aria-label="When the Grid Goes Dark">
    <img src="hero.jpg" width="1280" height="720" alt="A quiet residential street at night during a power outage. Almost every house is dark; one mid-block house is still warmly lit, gold lamplight through linen curtains." />
    <div class="hero-scrim" aria-hidden="true"></div>
    <div class="hero-copy">
      <p class="eyebrow">Field Notes</p>
      <h1>When the Grid Goes Dark</h1>
      <p class="tagline">The power bank guide for your hidden home.</p>
    </div>
  </section>

  <article class="fn-article">
    <div class="wrap">
      <div class="prose fn-copy">
        <p>The street has gone quiet in the particular way a block does when the power fails. Porch lights that usually mark the way home are out. Windows that held the evening have gone black. And then, halfway down, one house is still lit — a gold wash on the siding, a lamp behind linen curtains, the kind of light that makes you look twice.</p>
        <p>It is not a louder house. It is not a fortress. Someone in that room simply kept a battery ready for the fridge, the router, and the lamp by the sofa. The hidden-home idea, at its quietest, is comfort that stays on when the rest of the block goes dark.</p>
      </div>

      <p class="affiliate-near affiliate-note">Some links on this page are Amazon affiliate links. We may earn a commission at no extra cost to you.</p>
      <div class="fn-glance">
        <h2>Our picks at a glance</h2>
        <nav class="fn-jumps" aria-label="Jump to a tier">
          <a href="#pocket">Pocket</a>
          <a href="#everyday">Everyday carry</a>
          <a href="#camping">Camping</a>
          <a href="#home-backup">Home backup</a>
        </nav>
        <div class="shop-grid">
{card_twelve}
{card_anker_20}
{card_daran}
{card_ecoflow}
        </div>
      </div>

      <figure class="fn-figure">
        <img src="room-lit-interior.jpg" width="1280" height="720" alt="A warm living room at night: a linen sofa, a lamp, curtains, and a quiet interior while the street outside stays dark." />
        <figcaption>Inside the house that still has light.</figcaption>
      </figure>

      <div class="prose fn-copy">
        <h2>Four sizes of quiet power</h2>
        <p>Power, in a hidden home, comes in four sizes. Three of them you can carry. The fourth stays at the house and can keep a fridge going through an outage.</p>
        <p>A pocket bank, about 5,000 to 10,000 milliamp hours, keeps a phone alive. An everyday-carry bank, about 20,000 to 27,000 milliamp hours, with at least 65 watts of output, can feed a laptop through a work day. A camping-size power station, around 300 watt-hours, has real AC outlets for lights, a fan, and phones for a night away from the wall. Home-backup stations start at about 1,000 watt-hours, and sometimes grow with extra batteries or a solar panel.</p>
        <p>Phone banks are usually listed in milliamp hours. Power stations are listed in watt-hours. They are not the same unit, which is why the table below keeps them on separate rows. These are planning figures, not promises. Real runtimes change with the device, the temperature, and the small losses that happen whenever power is converted.</p>
      </div>

      <div class="fn-table-wrap">
        <table class="fn-table">
          <thead>
            <tr><th>Need</th><th>Rough energy</th><th>What that means in a bank or station</th></tr>
          </thead>
          <tbody>
            <tr><td>One phone charge</td><td>About 4,000–5,000 mAh</td><td>A 10,000 mAh bank is about two phone charges; a 20,000 mAh bank is about four</td></tr>
            <tr><td>A laptop</td><td>A bank of 20,000 mAh or more that can do 65W (140W is more comfortable for a 16-inch machine)</td><td>Everyday-carry territory</td></tr>
            <tr><td>One camping night (lights, a fan, phones)</td><td>About 300 Wh</td><td>A compact power station</td></tr>
            <tr><td>A fridge</td><td>About 1 kWh (1,000 Wh) a day</td><td>Home-backup territory</td></tr>
            <tr><td>Essentials for a day (fridge, router, lights, phones)</td><td>About 1.5 kWh a day</td><td>A 1,000–1,500 Wh station is about one day; 2,000–3,000 Wh is about two or three</td></tr>
          </tbody>
        </table>
      </div>

      <div class="fn-section" id="pocket">
        <div class="prose fn-copy">
          <h2>Pocket</h2>
          <p>For the pocket, we keep coming back to the <a href="{a('B0GMRFYVZ9')}" {AMAZON_REL}>Twelve South PowerCapsule 10K</a>. It is already on our gear page, and it looks like it belongs in a Lock &amp; Linen room: a slim 10,000 milliamp-hour bank wrapped in vegan leather, in a color called Dune, with Qi2 magnetic wireless charging up to 15 watts and a USB-C port besides. It is usually around $45. About two phone charges, quietly, in a jacket pocket.</p>
        </div>
        <div class="shop-grid shop-grid--single">
{card_twelve}
        </div>
      </div>

      <div class="fn-section" id="everyday">
        <div class="prose fn-copy">
          <h2>Everyday carry</h2>
        </div>
        <figure class="fn-figure">
          <img src="room-sidetable.jpg" width="1280" height="720" alt="A quiet sitting-room corner with a wooden side table, a woven basket, and linen curtains. A compact power bank sits on the lower shelf of the table, tucked away beside the basket." />
          <figcaption>An everyday-carry bank, tucked under the side table beside the basket.</figcaption>
        </figure>
        <div class="prose fn-copy">
          <p>When the day includes a laptop, you want more capacity and at least 65 watts — 140 watts if the machine is a larger one. The <a href="{a('B0F66NH2ZX')}" {AMAZON_REL}>Anker Prime Power Bank, 20,100 mAh, 220 W</a> is the everyday-carry we would take first. It holds 20,100 milliamp hours, still light enough for a bag and under the usual carry-on threshold, with 220 watts of total output and up to 140 watts from one USB-C port. It is usually around $180. If you want more headroom for a weekend, the <a href="{a('B0F66LNB8D')}" {AMAZON_REL}>Anker Prime 26,250 mAh, 300 W</a> is the same idea, only larger: 26,250 milliamp hours, 300 watts total, still under 100 watt-hours so it can fly in a carry-on, usually around $230.</p>
        </div>
        <div class="shop-grid">
{card_anker_20}
{card_anker_26}
        </div>
      </div>

      <div class="fn-section" id="camping">
        <div class="prose fn-copy">
          <h2>Camping</h2>
          <p>For a night away from the wall, the step up is a small power station with real AC outlets. The <a href="{a('B0GKGFWY69')}" {AMAZON_REL}>DaranEner 600W / 288Wh</a>, also already on the gear page, is camping-size rather than a home unit: 288 watt-hours, 600 watts rated, two AC outlets, a 100-watt USB-C port, and a weight of about nine pounds. It is usually around $175. Lights, a fan, and phones for a night in a tent or a trunk.</p>
        </div>
        <div class="shop-grid shop-grid--single">
{card_daran}
        </div>
      </div>

      <div class="fn-section" id="home-backup">
        <div class="prose fn-copy">
          <h2>When the house needs to stay on</h2>
        </div>
        <figure class="fn-figure">
          <img src="room-cabinet-nook.jpg" width="1280" height="720" alt="A warm mudroom at night: boots, a linen tote, and a wooden cabinet. A compact power station sits in the open nook beside a woven basket, tucked away rather than on display. The street outside the window is dark." />
          <figcaption>A compact station, left in the cabinet nook.</figcaption>
        </figure>
        <div class="prose fn-copy">
          <p>A home-backup power station is a large battery with AC outlets, charged from the wall or from a solar panel. The simplest path is the one we would start with: when the power goes out, move the fridge plug, the router, and a lamp onto the station’s outlets. No wiring. The box can sit in a mudroom or a closet, quietly, with no fumes and none of the clatter of a generator.</p>
          <p>If you want selected house circuits to switch over without walking plugs around, a licensed electrician can install a transfer switch or an inlet under local permits. That is work for a professional. Never run a cord from a station or a generator into a wall outlet — it can put power on the lines, and it is unsafe for anyone working on them.</p>
          <p>How large a station you want depends on how long you would like the essentials to run. For a fridge, a router, a few lights, and phones, plan on about 1.5 kilowatt-hours a day. A fridge alone is about one kilowatt-hour a day. Runtime is a budget, not a guarantee. A more efficient fridge and LED lamps will stretch it; a space heater or a window air conditioner will spend it quickly.</p>
        </div>

        <div class="fn-table-wrap">
          <table class="fn-table">
            <thead>
              <tr><th>Station size</th><th>About how long it covers that essentials load</th><th>Notes</th></tr>
            </thead>
            <tbody>
              <tr><td>1,000–1,500 Wh</td><td>About 1 day</td><td>The Jackery Explorer 1000 v2 and the base EcoFlow DELTA 3 Plus live here</td></tr>
              <tr><td>2,000–3,000 Wh</td><td>About 2–3 days</td><td>The Jackery Explorer 2000 v2 lives here</td></tr>
              <tr><td>Expandable, plus solar</td><td>Beyond that</td><td>Add a matching expansion battery, and recharge from solar during the day, so the same station covers a longer outage</td></tr>
            </tbody>
          </table>
        </div>

        <div class="prose fn-copy">
          <p>For about a day of those essentials, the <a href="{a('B0D7PPG25F')}" {AMAZON_REL}>Jackery Explorer 1000 v2</a> is the simple start: 1,024 watt-hours, 1,500 watts of AC output, usually around $560. It is not expandable. If two or three days feels more like it, the <a href="{a('B0DFG2WDQH')}" {AMAZON_REL}>Jackery Explorer 2000 v2</a> steps up to 2,042 watt-hours and 2,200 watts, usually around $1,000, still not expandable.</p>
          <p>The expandable pick we would lead with is the <a href="{a('B0DCC2BVFW')}" {AMAZON_REL}>EcoFlow DELTA 3 Plus</a>. It starts at the same 1,024 watt-hours as the smaller Jackery, with 1,800 watts of AC output, and it can grow to about 5 kilowatt-hours with compatible EcoFlow batteries. It is usually around $720. Prices and sellers move — look at the live listing before you buy.</p>
          <p>If that EcoFlow offer looks off, the alternate is the <a href="{a('B0FVFGL38H')}" {AMAZON_REL}>Anker SOLIX C2000 Gen 2</a>. It starts larger, at 2,048 watt-hours and 2,400 watts, and can expand to 4 kilowatt-hours, usually around $950 for the station-only set. Confirm that option, not a solar-panel bundle, before you follow the link, and check the live listing on the day you buy.</p>
        </div>
        <div class="shop-grid">
{card_ecoflow}
{card_jackery_1000}
{card_jackery_2000}
{card_solix}
        </div>
      </div>

      <div class="prose fn-copy fn-article-end">
        <h2>The house that still has light</h2>
        <p>In the end, the picture is simple. The block is dark. One room is not. A lamp is on. The fridge is still holding. The router has not given up. You need a battery the right size for the life you already have, sitting quietly until the evening asks for it.</p>
        <p>The full gear list is at <a href="{prefix}guides/gear-wed-put-in-these-homes/index.html">lockandlinen.com/gear</a>.</p>
      </div>
    </div>
  </article>

{footer(DEFAULT_AI_NOTE, prefix)}
</body>
</html>
"""
    (out / "index.html").write_text(html)


def write_field_notes_closed_up():
    prefix = "../../"
    slug = "closed-up-for-the-evening"
    out = PUBLIC / "field-notes" / slug
    out.mkdir(parents=True, exist_ok=True)

    img_addalock = "https://m.media-amazon.com/images/I/71coaNix4cL._AC_SL1500_.jpg"
    img_buddybar = "https://m.media-amazon.com/images/I/51FWoCaY1HL._AC_SL1500_.jpg"
    img_sabre = "https://m.media-amazon.com/images/I/61HQzV1nC-L._AC_SL1500_.jpg"
    img_prime_slide = "https://m.media-amazon.com/images/I/71bRtrW8lBL._AC_SL1500_.jpg"
    img_prime_flip = "https://m.media-amazon.com/images/I/61BiTnQYnVL._AC_SL1500_.jpg"
    img_ultrapro = "https://m.media-amazon.com/images/I/713mRL8qmxL._AC_SL1500_.jpg"
    img_bdf = "https://m.media-amazon.com/images/I/91ws31QbJFL._AC_SL1500_.jpg"
    img_rabbitgoo = "https://m.media-amazon.com/images/I/81ODG9ldiIL._AC_SL1500_.jpg"

    card_addalock = fn_product_card(
        "B00186URTY", img_addalock,
        "Addalock portable door lock, a small silver lock body with a sliding rod",
        "Portable lock", "Addalock portable door lock",
        "Hooks into the strike plate of an inward-swinging door. $14.95 as of November 12, 2026.",
    )
    card_buddybar = fn_product_card(
        "B002BQ4VBU", img_buddybar,
        "Buddybar door security bar, a powder-coated steel bar with a rubber foot",
        "Security bar", "Buddybar door security bar",
        "Powder-coated steel, 36 to 51 inches. $118.95 as of November 12, 2026.",
    )
    card_sabre = fn_product_card(
        "B00M30SQGA", img_sabre,
        "SABRE wedge door stop alarm, a black floor wedge with a built-in siren",
        "Wedge alarm", "SABRE wedge door stop alarm",
        "A floor wedge with a 120-decibel alarm. $9.79 as of November 12, 2026.",
    )
    card_prime_slide = fn_product_card(
        "B00BAFIQF0", img_prime_slide,
        "Prime-Line sliding window security lock, an aluminum thumb-screw clamp, pack of four",
        "Track lock", "Prime-Line sliding window security lock",
        "A thumb-screw clamp for sliding-window tracks. $5.39 for a pack of four, as of November 12, 2026.",
    )
    card_prime_flip = fn_product_card(
        "B000P0SHTQ", img_prime_flip,
        "Prime-Line U 9929 window flip lock in antique brass, two-pack",
        "Flip lock", "Prime-Line U 9929 window flip lock",
        "A hinged stop for wood double-hung windows. $8.16 for a two-pack, as of November 12, 2026.",
    )
    card_ultrapro = fn_product_card(
        "B00178HMCI", img_ultrapro,
        "UltraPro window and door alarm, two-pack of white magnetic sensors",
        "Contact alarm", "UltraPro window and door alarm, 2-pack",
        "A two-piece magnetic sensor with a chime or siren. $12.88 as of November 12, 2026.",
    )
    card_bdf = fn_product_card(
        "B00CX5Z4B0", img_bdf,
        "BDF S8MC 8 mil clear safety window film, 36-inch by 12-foot roll",
        "Safety film", "BDF S8MC 8 mil clear window film, 36 in × 12 ft",
        "8-mil clear film, 36 in × 12 ft. $69.99 as of November 12, 2026.",
    )
    card_rabbitgoo = fn_product_card(
        "B00RDVE2L2", img_rabbitgoo,
        "rabbitgoo frosted glass privacy film, static-cling roll",
        "Privacy film", "rabbitgoo frosted glass privacy film",
        "Static-cling frosted privacy film, 17.5 × 78.7 in. $5.99 as of November 12, 2026.",
    )
    a = _amazon
    ai_note = (
        "Images in this article are AI-generated illustrations, not product photos or real homes. "
        "Products shown are generic and are not the listed items. For information only; follow your "
        "local building and fire codes, and use a professional for large film installations."
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_meta("Closed Up for the Evening: Quiet Fortification for Your Hidden Home — Lock & Linen", "The street has turned blue, the way it does just after the lamps come on. Quiet layers for the doors, the windows, and the glass of a hidden home.", "/field-notes/closed-up-for-the-evening/", f"{SITE_URL}/field-notes/closed-up-for-the-evening/hero.jpg")}
{FAVICON.format(p=prefix)}<link rel="stylesheet" href="{prefix}css/site.css" />
</head>
<body>
{header(prefix)}

  <section class="hero fn-hero" aria-label="Closed Up for the Evening">
    <img src="hero.jpg" width="1280" height="720" alt="A softly lit entryway at dusk: a closed off-white front door, a brass lamp on an oak console, a wool throw on a bench, linen curtains, and a small plain wedge resting on the floor by the door." />
    <div class="hero-scrim" aria-hidden="true"></div>
    <div class="hero-copy">
      <p class="eyebrow">Field Notes</p>
      <h1>Closed Up for the Evening</h1>
      <p class="tagline">Quiet fortification for your hidden home.</p>
    </div>
  </section>

  <article class="fn-article">
    <div class="wrap">
      <div class="prose fn-copy">
        <p>The street has turned blue, the way it does just after the lamps come on. The kettle clicks off. Someone draws the linen curtains halfway. And then, without anyone quite deciding to, the house is closed up for the evening.</p>
        <p>It is not a fortress. It is not a house that looks like it is waiting for trouble. It is the quiet layer under the comfort: a door that sits the way you want it to, a window that opens only as far as you choose, glass that does a little more than let the light in. Most of it costs less than a good throw blanket. Almost none of it shows.</p>
      </div>

      <p class="affiliate-near affiliate-note">Some links on this page are Amazon affiliate links. We may earn a commission at no extra cost to you.</p>
      <div class="fn-glance">
        <h2>Three quiet layers</h2>
        <nav class="fn-jumps" aria-label="Jump to a layer">
          <a href="#door">At the door</a>
          <a href="#windows">At the windows</a>
          <a href="#glass">On the glass</a>
        </nav>
        <div class="prose fn-copy">
          <p>A hidden home closes up in three places. The doors, where the coming and going happens. The windows, the openings we think about least. And the glass itself, which can be made more private, and a little more resilient, without changing how a room looks.</p>
          <p>None of these are a guarantee. None of them replace a good deadbolt, a solid door, or knowing your neighbors. They are small, practical additions — most of them renter-friendly, most of them gone without a trace when you move.</p>
        </div>
        <div class="fn-table-wrap">
          <table class="fn-table">
            <thead>
              <tr><th>Layer</th><th>What it is</th><th>What it is designed to do</th><th>Install</th></tr>
            </thead>
            <tbody>
              <tr><td>Door: portable lock</td><td>A small lock body with metal claws that hook into the strike plate of an inward-swinging door</td><td>Add a second point of hold from the inside</td><td>No tools; seconds</td></tr>
              <tr><td>Door: security bar</td><td>An adjustable steel bar wedged between the knob and the floor</td><td>Brace a closed door from the inside</td><td>No tools; adjusts to the door</td></tr>
              <tr><td>Door: wedge alarm</td><td>A floor wedge with a built-in siren</td><td>Sound an alarm when the door presses on it</td><td>No tools; one 9V battery</td></tr>
              <tr><td>Window: track lock</td><td>A clamp that screws onto a sliding window's track</td><td>Hold the sash closed, or open only a few inches for air</td><td>No tools</td></tr>
              <tr><td>Window: flip lock</td><td>A small hinged stop for wood double-hung windows</td><td>Block the lower sash from lifting past a set point</td><td>Small screws or nails</td></tr>
              <tr><td>Window: contact alarm</td><td>A two-piece magnetic sensor with a chime or siren</td><td>Let you know when a door or window opens</td><td>Adhesive tape</td></tr>
              <tr><td>Glass: safety film</td><td>A clear, thick film applied to the inside of the glass</td><td>Hold glass together if it breaks, and filter UV</td><td>Squeegee and water solution; afternoon project</td></tr>
              <tr><td>Glass: privacy film</td><td>A frosted static-cling film</td><td>Blur the view in while letting soft light through</td><td>Water only; removable</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="fn-section" id="door">
        <div class="prose fn-copy">
          <h2>At the door</h2>
        </div>
        <figure class="fn-figure">
          <img src="room-bedroom-door.jpg" width="1280" height="720" alt="A calm cabin bedroom at night: a linen bed and wool throw, a ceramic lamp on a walnut nightstand, and a plain charcoal bar resting under the knob of the closed bedroom door." />
          <figcaption>A bar under the bedroom door at night.</figcaption>
        </figure>
        <div class="prose fn-copy">
          <p>The simplest piece we know is the <a href="{a('B00186URTY')}" {AMAZON_REL}>Addalock portable door lock</a>, already on our gear page. Its metal claws hook into the strike plate of an inward-swinging door, the door closes on them, a rod slides in through the lock body, and the door has a second point of hold from the inside. No tools, no screws, nothing left behind on the frame. It travels in a small pouch, so it belongs as much to a rental cabin or a hotel room as to home. As of November 12, 2026, it was $14.95, in stock, sold by Rishon Enterprises Inc. and shipped from Amazon.</p>
          <p>For a front door, or a bedroom door at night, the step up is a bar. The <a href="{a('B002BQ4VBU')}" {AMAZON_REL}>Buddybar door security bar</a>, also on the gear page, is 8.2 pounds of powder-coated steel with no plastic parts, and it extends from 36 to 51 inches to fit most doors. It braces under the knob from the inside, on carpet, tile, wood, or concrete. It is the most expensive thing in this guide — $118.95 on November 12, in stock, sold by MPO Global and shipped from Amazon — and the one we would buy once and keep for years.</p>
          <p>The third door piece does the least and says the most. The <a href="{a('B00M30SQGA')}" {AMAZON_REL}>SABRE wedge door stop alarm</a> slides under the door like any doorstop, on a non-skid pad, and sounds a 120-decibel alarm when the door presses down on it. One 9-volt battery, one low-battery light. SABRE notes it needs about a 7/8-inch gap under the door to trigger, so check yours first. It was $9.79 on November 12, in stock, sold by Amazon.com.</p>
        </div>
        <div class="shop-grid">
{card_addalock}
{card_buddybar}
{card_sabre}
        </div>
      </div>

      <div class="fn-section" id="windows">
        <div class="prose fn-copy">
          <h2>At the windows</h2>
        </div>
        <figure class="fn-figure">
          <img src="room-window-sill.jpg" width="1280" height="720" alt="The inside corner of a sliding window in warm evening light: a small plain aluminum thumb-screw stop on the track, an oatmeal linen curtain, a ceramic vase with a dried grass stem." />
          <figcaption>A small stop on the track, so the window opens only as far as you choose.</figcaption>
        </figure>
        <div class="prose fn-copy">
          <p>Windows are where a house breathes. The best window hardware lets it keep breathing. For sliding windows, the <a href="{a('B00BAFIQF0')}" {AMAZON_REL}>Prime-Line sliding window security lock</a> is a small aluminum clamp with a thumb screw that tightens onto the track. Set it against the sash and the window stays shut. Set it a few inches back and the window opens just that far, for air on a mild night. It fits rails up to 1/8 inch wide — measure before you buy — and needs no tools. It was $5.39 for a pack of four on November 12, in stock, sold by Amazon.com.</p>
          <p>Older wood double-hung windows want something different. The <a href="{a('B000P0SHTQ')}" {AMAZON_REL}>Prime-Line U 9929 window flip lock</a> is a small hinged piece in antique brass that sits on the side of the frame. Flip it out and the lower sash cannot lift past it; flip it back and the window opens fully. It is designed for wood single- and double-hung windows, and Prime-Line notes it is not recommended for dual-pane windows, so check yours. It was $8.16 for a two-pack, in stock, sold by Amazon.com. In antique brass, it looks as if it was always part of the house.</p>
          <p>And then there is simply knowing. The <a href="{a('B00178HMCI')}" {AMAZON_REL}>UltraPro window and door alarm, 2-pack</a>, already on the gear page, is a two-piece magnetic sensor that sticks to the frame with tape. Open the window and it plays a soft chime — or, switched over, a 120-decibel siren. No app, no wifi, no monthly fee; it runs on the included button batteries. It was $12.88 on November 12, down from a typical price of $16.36, in stock, sold by Amazon.com. We like it on the window nobody uses, and as a chime on the back door.</p>
          <p>One thing to keep in mind: a bedroom window is also a way out. Choose locks that open from the inside in a second, and never fix shut a window someone may need in an emergency. Follow your local fire and building codes.</p>
        </div>
        <div class="shop-grid">
{card_prime_slide}
{card_prime_flip}
{card_ultrapro}
        </div>
      </div>

      <div class="fn-section" id="glass">
        <div class="prose fn-copy">
          <h2>On the glass</h2>
        </div>
        <figure class="fn-figure fn-figure--portrait">
          <img src="room-frosted-window.jpg" width="1080" height="1350" alt="A tall wood double-hung window in a reading nook at night, the lower pane softly frosted so the street outside is only a blur, a linen curtain pulled aside, a lamp glowing on a walnut side table, a sheepskin on a wooden chair." />
          <figcaption>From inside, a soft white glow. From outside, a lit window and nothing more.</figcaption>
        </figure>
        <div class="prose fn-copy">
          <p>Window film is the most invisible thing in this guide, and the one people ask us about most.</p>
          <p>The <a href="{a('B00CX5Z4B0')}" {AMAZON_REL}>BDF S8MC security and safety window film, 8 mil clear, 36 in × 12 ft</a> is the same film as the larger roll on our gear page, in a size that suits a door light or a couple of ground-floor windows. It is a crystal-clear, 8-mil film applied to the inside of the glass. BDF says it is designed to absorb impact and hold shattered glass together, and lists it at 99% UV rejection, which also helps slow the fading of rugs and linen near a sunny window. It is not meant for heat control. It is a real afternoon project: a squeegee and knife come in the box, and a professional installer is worth it for large panes. It was $69.99 on November 12, in stock, sold by BuyDecorativeFilm and shipped from Amazon. (The 36 in × 49 ft roll on the gear page was $180.99 with delivery not until December 1–12.)</p>
          <p>For privacy rather than strength, a frosted film does something curtains cannot: it keeps the light and loses the view. The <a href="{a('B00RDVE2L2')}" {AMAZON_REL}>rabbitgoo frosted glass privacy film, 17.5 × 78.7 in</a> is a static-cling film that goes on with water, no glue, and peels off without residue — easy for a rental, easy to trim to a bathroom window or a front-door sidelight. It is a privacy film, not a security film. It was $5.99 on November 12, in stock, sold by Authorized Rabbitgoo Seller Globegou and shipped from Amazon. On a street-facing window, it does exactly what a hidden home wants. From inside, a soft white glow. From outside, a lit window and nothing more.</p>
        </div>
        <div class="shop-grid">
{card_bdf}
{card_rabbitgoo}
        </div>
      </div>

      <div class="prose fn-copy fn-article-end">
        <h2>Closed up for the evening</h2>
        <p>In the end, it is the same small ritual. The kettle, the lamp, the curtains. A bar under the bedroom door. A window open three inches and no further. A pane that glows instead of showing. Nobody walking past would notice any of it, and that is rather the point. The house looks the way it always has — softly furnished, lamplit, a little hidden — and it is closed up for the evening.</p>
        <p>The full gear list is at <a href="{prefix}guides/gear-wed-put-in-these-homes/index.html">lockandlinen.com/gear</a>.</p>
      </div>
    </div>
  </article>

{footer(ai_note, prefix)}
</body>
</html>
"""
    (out / "index.html").write_text(html)


def write_field_notes_water_filtration():
    """Unlisted preview of the water filtration guide. Not in the index, sitemap, or nav cards."""
    prefix = "../../"
    slug = "water-filtration-guide"
    out = PUBLIC / "field-notes" / slug
    out.mkdir(parents=True, exist_ok=True)
    a = _amazon
    ai_note = 'Images are AI-generated, for illustration.'
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_meta("What's in the Glass: A Quiet Guide to Water at Home — Lock & Linen", 'Water is the quietest system in a house. What to test, what each filter is built for, and what it costs by the litre.', "/field-notes/water-filtration-guide/")}
<meta name="robots" content="noindex,nofollow" />
{FAVICON.format(p=prefix)}<link rel="stylesheet" href="{prefix}css/site.css" />
</head>
<body>
{header(prefix)}

  <section class="page-hero">
    <div class="wrap">
      <p class="section-label">Field Notes</p>
      <h1>What's in the Glass</h1>
      <p class="tagline">A Quiet Guide to Water at Home</p>
    </div>
  </section>

  <article class="fn-article">
    <div class="wrap">
      <div class="prose fn-copy">
        <p>Morning, before anyone has said much. The tap runs for a moment, the kettle fills, and someone holds a glass up to the window the way you would check a wine: light through it, nothing to see. Water is the quietest system in a house. It arrives, it leaves, and it keeps going while the rest of the day happens around it.</p>
        <p>Most days it asks nothing of you. But a home that runs on its own deserves one careful look at what comes out of the tap, out of the same care that chose the linen and the lamp. This guide is that look: what to test, what each filter is built for, and what it costs by the litre.</p>
        <h2>Our picks at a glance</h2>
        <p>These are picks for specific problems, not a kit to buy all at once. Test first. The result tells you which row, if any, is yours.</p>
        <p class="affiliate-near affiliate-note">Some links on this page are Amazon affiliate links. We may earn a commission at no extra cost to you.</p>
        <p>Prices are in US dollars as listed on Nov 13, 2026, and may differ in Canada.</p>
      </div>
      <div class="fn-table-wrap">
        <table class="fn-table">
          <thead>
            <tr><th>Problem</th><th>Filter type</th><th>Our pick</th><th>Certification, as the maker lists it</th><th>Price (USD, Nov 13)</th></tr>
          </thead>
          <tbody>
            <tr><td>Not sure yet</td><td>Mail-in lab test</td><td>Tap Score Advanced Home Water Test</td><td>A lab test, not a treatment device</td><td>$299.00</td></tr>
            <tr><td>Chlorine taste; lead at the tap</td><td>Pitcher</td><td>Brita Tahoe Pitcher with Elite Filter</td><td>NSF/ANSI 42, 53 and 401 (Elite performance data sheet)</td><td>$41.99; filters $19.99</td></tr>
            <tr><td>Chlorine, lead, PFOA/PFOS as certified</td><td>Under-sink carbon</td><td>Aquasana Claryum 3-Stage Max Flow (AQ-6300M-BN)</td><td>WQA: NSF/ANSI 42, 53 (includes P473) and 401</td><td>$224.99</td></tr>
            <tr><td>Contaminants listed on its RO performance data sheet</td><td>Under-sink reverse osmosis</td><td>Waterdrop G3P800</td><td>IAPMO R&amp;T: NSF/ANSI 42, 53 and 58, for the claims on the performance data sheet; NSF/ANSI 372 for low lead</td><td>$849</td></tr>
            <tr><td>The same, without plumbing</td><td>Countertop reverse osmosis</td><td>AquaTru Classic</td><td>IAPMO R&amp;T: NSF/ANSI 42, 53, 58, 372, 401 and P473</td><td>$475.00</td></tr>
            <tr><td>Sediment and chlorine taste, whole house</td><td>Whole-house carbon</td><td>3M AP904</td><td>NSF/ANSI 42</td><td>$426.00 (dealer)</td></tr>
            <tr><td>Hardness and scale</td><td>Water softener</td><td>EcoPure EP31</td><td>No certification claimed</td><td>Price varies</td></tr>
            <tr><td>Supplemental UV on water already considered potable</td><td>UV</td><td>Viqua VH200-V</td><td>NSF/ANSI 55 Class B only (supplemental; not for unsafe or untreated water)</td><td>$815.00 (dealer)</td></tr>
          </tbody>
        </table>
      </div>
      <div class="prose fn-copy">
        <h2>Part 1: Test first</h2>
        <p>Every filter answers a question; the test asks it. A pitcher certified for lead does nothing for nitrate, and a softener does nothing for lead.</p>
        <p>This guide is not a substitute for a laboratory test, or for directions from your local public-health authority. Test your water first, and follow any boil-water or do-not-consume advisory from your municipality or health authority. In Québec, that means the MELCCFP, your municipality, or your direction de santé publique. Official well-testing advice: <a href="https://www.environnement.gouv.qc.ca/eau/potable/depliant/" rel="noopener noreferrer">La qualité de l'eau de mon puits</a>. Official boil-water and do-not-consume notices: <a href="https://www.quebec.ca/agriculture-environnement-et-ressources-naturelles/eau/potable-usees-pluviales/eau-potable/qualite-eau-potable/avis-ebullition-avis-non-consommation" rel="noopener noreferrer">Gouvernement du Québec</a>.</p>
        <h3>If your water comes from the city</h3>
        <p>Municipal water is already treated and tested by the utility. In Québec, public systems fall under the <em>Règlement sur la qualité de l'eau potable</em> (Q-2, r. 40), and the annual quality report is public. Montréal's, for example, counts 17,800 bacteriological and 9,440 physico-chemical samples for 2025, and notes that lead was the only physico-chemical parameter that exceeded the standards; the city describes an action plan for lead service lines. In the US, the same yearly document is the Consumer Confidence Report. A filter is not a substitute for a boil-water or do-not-consume advisory. If one is in effect, follow it.</p>
        <p>People still filter city water for two reasons. One is taste: Health Canada sets no maximum for chlorine, given its low toxicity at drinking-water levels (typically 0.04 to 2.0 mg/L in Canadian systems), but you can taste it. Some cities use chloramine instead, and a filter has to list chloramine on its sheet to claim it. The other is the last few metres of pipe. Lead usually comes from plumbing — service lines, solder, brass — so only a sample at your own tap tells you what it delivers.</p>
        <h3>If your water comes from a private well</h3>
        <p>A private well belongs to whoever owns it, and so does the quality of its water. Québec's environment ministry (MELCCFP) puts it plainly: clear, odourless water can still be contaminated. It recommends analysis by an <strong>accredited laboratory</strong>:</p>
        <ul>
          <li><strong>At least twice a year, in spring and autumn,</strong> for microbiological parameters: <em>E. coli</em>, enterococci and total coliforms.</li>
          <li><strong>At least once while you use the well</strong> for physico-chemical parameters tied to the soil, which change little: arsenic, manganese, barium, nitrates-nitrites, chlorides, sodium, iron, sulfates, fluorides and total hardness.</li>
          <li><strong>Again, any time</strong> taste, odour or appearance changes suddenly, or the well or the ground around it is disturbed.</li>
        </ul>
        <p>The labs are on CEAEQ's official list, DR-12-LLA-03 (see Sources). There is no province-wide free well test in the official sources, though some municipalities or CISSS run local campaigns.</p>
        <p>If a test finds <em>E. coli</em> or enterococci, the fecal indicators, it is a public-health moment, not a shopping one. Follow the lab's and public health's advice (in Québec, the direction de santé publique), which can include boiling water as directed and disinfecting the well, then retest. Total coliforms alone are not proof of fecal contamination, but repeat results beyond 10 CFU per 100 mL may call for a shock disinfection.</p>
        <h3>The numbers, in plain words</h3>
        <p>Health Canada's guidelines (summary tables, December 2025) use three terms: a <strong>MAC</strong> is a maximum acceptable concentration, an <strong>AO</strong> is an aesthetic objective (taste, smell, staining), and <strong>ALARA</strong> means "as low as reasonably achievable." These are national guidelines, not a reading of your house.</p>
      </div>
      <div class="fn-table-wrap">
        <table class="fn-table">
          <thead>
            <tr><th>Parameter</th><th>Health Canada value</th><th>Type</th><th>What it usually means</th></tr>
          </thead>
          <tbody>
            <tr><td>Lead</td><td>0.005 mg/L (5 µg/L)</td><td>MAC, ALARA</td><td>Comes from plumbing; sample at the tap</td></tr>
            <tr><td>Arsenic</td><td>0.010 mg/L (10 µg/L)</td><td>MAC, ALARA</td><td>Occurs naturally in some groundwater</td></tr>
            <tr><td>Nitrate</td><td>45 mg/L as nitrate (10 mg/L as nitrate-nitrogen)</td><td>MAC</td><td>Near farms or septic systems; a particular concern for bottle-fed infants</td></tr>
            <tr><td>Manganese</td><td>0.12 mg/L; AO ≤ 0.02 mg/L</td><td>MAC and AO</td><td>Staining and taste at the AO</td></tr>
            <tr><td>Iron</td><td>No MAC; AO ≤ 0.1 mg/L (updated 2024)</td><td>AO</td><td>Staining and taste</td></tr>
            <tr><td>Fluoride</td><td>1.5 mg/L</td><td>MAC</td><td></td></tr>
            <tr><td>Uranium</td><td>0.02 mg/L</td><td>MAC</td><td>Relevant for some private wells</td></tr>
            <tr><td><em>E. coli</em></td><td>None detectable per 100 mL</td><td>MAC</td><td>Indicator of recent fecal contamination</td></tr>
            <tr><td>PFAS</td><td>30 ng/L for the sum of 25 named PFAS</td><td>Objective (2024), ALARA</td><td>Interim, while a guideline is developed</td></tr>
            <tr><td>Hydrogen sulphide</td><td>AO ≤ 0.05 mg/L</td><td>AO</td><td>The "rotten egg" smell</td></tr>
            <tr><td>Hardness</td><td>No guideline value</td><td>—</td><td>Calcium and magnesium; scale on fixtures</td></tr>
          </tbody>
        </table>
      </div>
      <div class="prose fn-copy">
        <p><em>Side note for US readers:</em> the EPA's lead figure is an action level for public systems, 15 µg/L, moving to 10 µg/L on Nov 1, 2027. Its PFOA and PFOS limits are 4.0 ng/L each, for those two compounds, a different measure from Canada's 25-PFAS objective.</p>
        <h3>How to test</h3>
        <p>For a Québec well, start where the ministry does: an accredited lab. As a mail-in option, the <a href="https://mytapscore.com/products/home-water-test-advanced" rel="noopener noreferrer">Tap Score Advanced Home Water Test</a> is the kit we would order: $299.00 on Tap Score's store, shipping included, about five business days at the lab, covering metals, minerals, bacteria, hardness, silica and VOCs, plus a home strip for chlorine and hydrogen sulfide. Its description does not list PFAS, so ask for a dedicated PFAS test if that is your question. For a Québec well it is an alternative, not a substitute for the accredited lab. Home strips are a screen, never a lab result.</p>
        <h2>Part 2: Match the filter to the problem</h2>
        <p>A filter's box says a lot; its certification says less and means more. Look for "certified to NSF/ANSI [standard] for the claims on the performance data sheet," from a named certifier (NSF International, WQA or IAPMO R&amp;T). In short: <strong>42</strong> is taste, odour and particulates; <strong>53</strong> is health claims, only those named on the sheet; <strong>P473</strong> is PFOA/PFOS; <strong>58</strong> is reverse osmosis; <strong>401</strong> is emerging compounds; <strong>372</strong> is the device's own low-lead build; <strong>44</strong> is softeners; <strong>55</strong> is UV, where Class A is for water that may carry pathogens and Class B is supplemental.</p>
        <h3>Chlorine taste and odour</h3>
        <p>The simplest fix is also the quietest. The <a href="https://www.brita.com/products/brita-tahoe-water-pitcher-elite-filter/" rel="noopener noreferrer">Brita Tahoe Water Pitcher with Elite Filter</a> is a 10-cup pitcher, $41.99 on Brita's store. Its official performance data sheet lists the Elite filter as certified to NSF/ANSI 42 for chlorine and Class I particulates, NSF/ANSI 53 for health-effects claims including lead, and NSF/ANSI 401 for the emerging compounds listed on the sheet. <a href="https://www.brita.com/products/brita-elite-replacement-filters/" rel="noopener noreferrer">Elite filters</a> were $19.99, each rated for 120 gallons (454 litres), about six months for the average family. Its sheet does not list PFOA or PFOS, and it is not for bacteria or nitrate.</p>
        <h3>Lead and PFOA/PFOS</h3>
        <p>For a filter that stays plumbed in, the <a href="https://www.aquasana.com/under-sink-water-filters/claryum-3-stage-max-flow/brushed-nickel-100391704.html" rel="noopener noreferrer">Aquasana Claryum 3-Stage Max Flow</a> (AQ-6300M-BN) sits under the sink and feeds its own faucet. Aquasana states it is WQA tested and certified to NSF/ANSI 42, 53 (which includes P473) and 401, for the claims on the performance data sheet. It was $224.99 on Aquasana's store on Nov 13. <a href="https://www.aquasana.com/water-filter-replacements/under-sink-water-filter-replacements/claryum-3-stage-filter-replacements-100236384.html" rel="noopener noreferrer">Replacement filters</a> were $83.99 a set, rated for 800 gallons or up to six months.</p>
        <h3>Beyond what carbon covers: reverse osmosis</h3>
        <p>Reverse osmosis pushes water through a membrane. Which contaminants a system covers depends on its sheet, so read it before counting on nitrate or fluoride.</p>
        <p>Under the sink, the <a href="{a('B0987FCQQW')}" rel="nofollow sponsored noopener noreferrer">Waterdrop G3P800</a> is a tankless system. Waterdrop states it is certified by IAPMO R&amp;T to NSF/ANSI 42, 53 and 58 for the claims on the performance data sheet, and to NSF/ANSI 372 for low lead. <a href="https://www.waterdropfilter.com/products/tankless-reverse-osmosis-system-wd-g3p800-w-fc-1" rel="noopener noreferrer">On Waterdrop's own store</a> it was $849 on Nov 13; the Amazon price varies. Its <a href="https://www.waterdropfilter.com/products/waterdrop-g3p800-ro-system-replacement-filters" rel="noopener noreferrer">replacement filters</a> run in three stages, and the maker's own table puts the average annual cost at $159.97.</p>
        <p>Without plumbing, the <a href="https://aquatru.com/products/countertop-reverse-osmosis-water-purifier" rel="noopener noreferrer">AquaTru Classic</a> sits on the counter. Its performance data sheet says it is certified by IAPMO R&amp;T according to NSF/ANSI 42, 53, 58, 372, 401 and P473, for the claims specified on that sheet. It was $475.00 on AquaTru's store for the Classic with the VOC carbon filter. Its sheet rules out water of unknown microbiological quality without disinfection, and sets inlet limits for hardness and iron.</p>
        <h3>Sediment, and the whole house</h3>
        <p>The <a href="{a('B08PR79GYC')}" rel="nofollow sponsored noopener noreferrer">3M AP904</a> Sanitary Quick Change system is a whole-house carbon filter for chlorine taste and odour and sediment down to 5 microns. 3M's brochure says it is tested and certified to NSF/ANSI 42 for the substances on its performance data sheet. It was $426.00 at <a href="https://www.freshwatersystems.com/products/3m-aqua-pure-whole-house-sanitary-quick-change-water-filter-system-ap904" rel="noopener noreferrer">Fresh Water Systems</a>, with the AP917HD-S cartridge at <a href="https://www.freshwatersystems.com/products/3m-aqua-pure-ap917hd-s-high-flow-sqc-cto-filter-with-scale-inhibitor" rel="noopener noreferrer">$327.04</a>, rated for 100,000 gallons and about a year under most conditions. It is not certified on that brochure for lead or PFAS, and its scale-inhibiting media is not a softener. Installation is usually a plumber's job.</p>
        <h3>Hardness and scale</h3>
        <p>Hardness is calcium and magnesium, with no Health Canada guideline: it is about kettles and fixtures, not health. The <a href="https://ecopure.com/product/31000-grain-water-softener-ep31/" rel="noopener noreferrer">EcoPure EP31</a> is a 31,000-grain softener the maker describes for households of about one to four people, at 3 to 14 grains per gallon. Price varies; we could not verify one. Softened water carries more sodium, so households watching sodium can ask a clinician, or keep a separate unsoftened drinking tap.</p>
        <h3>Iron, manganese and the sulfur smell</h3>
        <p>Orange stains, a metallic taste, a rotten-egg smell. These want a system sized to a lab result, usually by a professional. We have no certified iron filter to recommend today, and would rather say so than guess.</p>
        <h3>Bacteria on a well</h3>
        <p>UV can be a last stage after sediment filtration, because it needs clear water. The <a href="https://viqua.com/product/vh200-v/" rel="noopener noreferrer">Viqua VH200-V</a> is a whole-home UV unit rated up to 7.8 gpm (29.5 L/min). NSF lists it to <strong>NSF/ANSI 55 Class B</strong>. Class B is only for the supplemental bactericidal treatment of drinking water that is already considered microbiologically safe and of known quality, or that has been tested and deemed acceptable for human consumption by the local health agency. It is designed to reduce normally occurring non-pathogenic nuisance microorganisms. It is not a disinfection system for contaminated, untreated, or microbiologically unsafe water, and it must not be used as one. If a well tests positive for <em>E. coli</em>, or if a boil-water advisory is in effect, follow the public-health advice above, repair and retest, and look to a Class A system or a professional design if disinfection of potentially unsafe water is required — not this unit. It was $815.00 at <a href="https://www.freshwatersystems.com/products/viqua-vh200-v-uv-system-nsf-55-class-b-7-8gpm-120-volt" rel="noopener noreferrer">Fresh Water Systems</a>, with a 9,000-hour lamp life stated by the maker.</p>
        <p>Dedicated iron and manganese filters, and UV systems certified to NSF/ANSI 55 Class A, do exist for those specific problems; a lab result and a qualified installer are the way to choose one.</p>
        <h3>Whole house or one tap?</h3>
        <p>Pitchers, under-sink filters and countertop RO treat the water you drink and cook with. Whole-house filters, softeners and UV treat everything, and usually need a plumber. Most city homes need only the first kind.</p>
        <h2>Part 3: Cost vs payoff</h2>
        <p>The fair comparison is cost per litre of rated capacity: cartridge price ÷ the litres the maker rates it for (1 US gallon = 3.785 L). Hard or cloudy water can wear cartridges faster.</p>
      </div>
      <div class="fn-table-wrap">
        <table class="fn-table">
          <thead>
            <tr><th>Filter</th><th>Upfront</th><th>Replacement</th><th>Rated capacity</th><th>Cost per litre (the math)</th></tr>
          </thead>
          <tbody>
            <tr><td>Brita Elite pitcher</td><td>$41.99</td><td>$19.99 per filter; about $39.98 a year at two filters</td><td>454 L</td><td>$19.99 ÷ 454 L ≈ $0.044 / L</td></tr>
            <tr><td>Aquasana Claryum Max Flow</td><td>$224.99</td><td>$83.99 per set; about $167.98 a year at two sets</td><td>800 gal × 3.785 = 3,028 L</td><td>$83.99 ÷ 3,028 L ≈ $0.028 / L</td></tr>
            <tr><td>Waterdrop G3P800</td><td>$849</td><td>Maker's average: $159.97 a year</td><td>550 gal (2,081.75 L), 1,100 gal (4,163.5 L), 2,200 gal (8,327 L)</td><td>$29.99 ÷ 2,081.75 + $29.99 ÷ 4,163.5 + $139.99 ÷ 8,327 ≈ $0.038 / L</td></tr>
            <tr><td>AquaTru Classic</td><td>$475.00</td><td>Price varies</td><td>600 gal pre-filter, 600 gal VOC filter, 1,200 gal membrane</td><td>Price varies: filter price ÷ (gallons × 3.785), per stage</td></tr>
            <tr><td>3M AP904 (whole house)</td><td>$426.00</td><td>$327.04, about once a year</td><td>100,000 gal × 3.785 = 378,500 L</td><td>$327.04 ÷ 378,500 L ≈ $0.0009 / L, for every tap in the house</td></tr>
            <tr><td>EcoPure EP31</td><td>Price varies</td><td>Salt, plus optional cleaner every four months; price varies</td><td>—</td><td>Not a drinking-water filter</td></tr>
            <tr><td>Viqua VH200-V</td><td>$815.00</td><td>$165.00 lamp and sleeve kit (QL-200)</td><td>9,000 lamp hours</td><td>Per hour, not per litre: $165.00 ÷ 9,000 h ≈ $0.018 / h</td></tr>
            <tr><td>Tap Score lab test</td><td>$299.00</td><td>Retest as needed</td><td>—</td><td>A test, not a filter</td></tr>
            <tr><td><strong>Your bottled water</strong></td><td>—</td><td>—</td><td>Litres in the pack: ____</td><td>Pack price ____ ÷ litres ____ = ____ / L</td></tr>
          </tbody>
        </table>
      </div>
      <div class="prose fn-copy">
        <p>For the last row, use the pack you usually buy: a 24 × 500 mL case is 12 litres, so divide its price by 12.</p>
        <p>The payoff is modest and plain: a known yearly filter budget, fewer single-use bottles, and water that tastes the way you like, from your own tap.</p>
        <h2>The glass at the end of the day</h2>
        <p>Evening, and the house is closing up. Curtains drawn, a lamp on in the kitchen, the last glass poured at the counter. Nothing looks different from the morning, and that is the point. A hidden home keeps its quietest systems in order: tested, matched with care, then left to do their work.</p>
        <h2>Sources</h2>
        <ul>
          <li>Health Canada, Guidelines for Canadian Drinking Water Quality – Summary Tables (December 2025): <a href="https://www.canada.ca/en/health-canada/services/environmental-workplace-health/reports-publications/water-quality/guidelines-canadian-drinking-water-quality-summary-table.html" rel="noopener noreferrer">https://www.canada.ca/en/health-canada/services/environmental-workplace-health/reports-publications/water-quality/guidelines-canadian-drinking-water-quality-summary-table.html</a></li>
          <li>Health Canada, Objective for Canadian drinking water quality – PFAS (Aug 9, 2024): <a href="https://www.canada.ca/en/health-canada/services/publications/healthy-living/objective-drinking-water-quality-per-polyfluoroalkyl-substances.html" rel="noopener noreferrer">https://www.canada.ca/en/health-canada/services/publications/healthy-living/objective-drinking-water-quality-per-polyfluoroalkyl-substances.html</a></li>
          <li>MELCCFP, <em>La qualité de l'eau de mon puits</em>: <a href="https://www.environnement.gouv.qc.ca/eau/potable/depliant/" rel="noopener noreferrer">https://www.environnement.gouv.qc.ca/eau/potable/depliant/</a></li>
          <li>CEAEQ, accredited-lab list DR-12-LLA-03: <a href="https://www.ceaeq.gouv.qc.ca/accreditation/pala/lla03.htm" rel="noopener noreferrer">https://www.ceaeq.gouv.qc.ca/accreditation/pala/lla03.htm</a></li>
          <li>Données Québec, same list: <a href="https://www.donneesquebec.ca/recherche/dataset/dr-12-lla-03" rel="noopener noreferrer">https://www.donneesquebec.ca/recherche/dataset/dr-12-lla-03</a></li>
          <li>Ville de Montréal, drinking-water quality reports (updated Mar 31, 2026): <a href="https://montreal.ca/articles/qualite-et-usage-de-leau-potable-rapports-et-bilans-27872" rel="noopener noreferrer">https://montreal.ca/articles/qualite-et-usage-de-leau-potable-rapports-et-bilans-27872</a></li>
          <li>US EPA, National Primary Drinking Water Regulations: <a href="https://www.epa.gov/ground-water-and-drinking-water/national-primary-drinking-water-regulations" rel="noopener noreferrer">https://www.epa.gov/ground-water-and-drinking-water/national-primary-drinking-water-regulations</a></li>
          <li>US EPA, Drinking Water Regulations and Contaminants: <a href="https://www.epa.gov/sdwa/drinking-water-regulations-and-contaminants" rel="noopener noreferrer">https://www.epa.gov/sdwa/drinking-water-regulations-and-contaminants</a></li>
          <li>Brita Elite performance data sheet: <a href="https://www.brita.com/support/performance-data/brita-elite/" rel="noopener noreferrer">https://www.brita.com/support/performance-data/brita-elite/</a></li>
          <li>AquaTru Classic performance data sheet: <a href="https://cdn.shopify.com/s/files/1/0549/6556/7706/files/AquaTru_Classic_Performance_Datasheet.pdf?v=1729179045" rel="noopener noreferrer">https://cdn.shopify.com/s/files/1/0549/6556/7706/files/AquaTru_Classic_Performance_Datasheet.pdf?v=1729179045</a></li>
          <li>3M AP900 Series brochure: <a href="https://multimedia.3m.com/mws/media/517695O/3m-aqua-pure-whole-house-water-filtration-system-ap900-series.pdf" rel="noopener noreferrer">https://multimedia.3m.com/mws/media/517695O/3m-aqua-pure-whole-house-water-filtration-system-ap900-series.pdf</a></li>
          <li>Prices: maker and dealer pages as linked above, loaded Nov 13, 2026.</li>
        </ul>
      </div>
    </div>
  </article>

{footer(ai_note, prefix)}
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
    paths = ["/", "/about.html", "/privacy/", "/contact/", "/guides/quiet-security-ideas/", "/guides/gear-wed-put-in-these-homes/", "/field-notes/", "/field-notes/when-the-grid-goes-dark/", "/field-notes/closed-up-for-the-evening/"]
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
<link rel="canonical" href="{dest}" />
<meta name="robots" content="noindex" />
<title>Gear — Lock &amp; Linen</title>
<script>location.replace({dest!r} + (location.hash || ""));</script>
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
    write_cookie_js()
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
    write_field_notes()
    write_gear_shortlink()
    write_robots_and_sitemap()
    manifest = [{"slug": s["slug"], "yt": s["yt"], "title": s["title"]} for s in STORIES]
    (ROOT / "site" / "_build" / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("Done.", len(STORIES), "stories + privacy/contact/guide + field notes")
    import i18n_fr  # French twins under /fr/, EN|FR switch, hreflang, sitemap alternates
    i18n_fr.main()


if __name__ == "__main__":
    main()
