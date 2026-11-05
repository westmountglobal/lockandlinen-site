#!/usr/bin/env python3
"""Build Lock & Linen static site into site/public/ from mockup + published reels only."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from PIL import Image

ROOT = Path("/workspace/lockandlinen-site")
PUBLIC = ROOT / "site" / "public"
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


def add_nc_story(slug, yt, concept_key, still_map, shop, hero_letter="A"):
    c = CONCEPTS[concept_key]
    title = {
        "n01_island": "The Island Home",
        "n02_cliffside": "The Cliffside Glass House",
        "n06_canyon": "The Hidden Canyon House",
        "n07_lighthouse": "The Lighthouse Hideout",
        "n08_missile_silo": "The Missile Silo Home",
        "n09_fjord_boathouse": "The Fjord Boathouse",
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
        ("K", "Clifftop herb terrace", False),
        ("F", "Funicular — the only way in", False),
        ("U", "Rock-cut cellar behind the glass", False),
        ("X", "Cantilevered house on the cliff face", False),
    ],
    [
        ("Low oak lounge chair", "Warm wood for the concrete-and-glass living room."),
        ("Minimal fireplace set", "Quiet evenings above the surf."),
        ("Herb planter boxes", "Wind-sheltered terrace greens."),
        ("Wool throw blanket", "Soft texture against board-formed walls."),
    ],
)

add_nc_story(
    "canyon",
    "ZgWRvfa4y6A",
    "n06_canyon",
    [
        ("I", "Cool interior — thick rammed-earth walls, clay and linen", True),
        ("A", "Earth-walled house flush with the canyon rock", False),
        ("K", "Fig-tree courtyard", False),
        ("F", "Hidden rammed-earth gate", False),
        ("U", "Rock-cut water tank & cellar", False),
        ("X", "Planted roof, nearly invisible in the wall", False),
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
        ("K", "Walled kitchen garden", False),
        ("F", "Gravel causeway — one way in", False),
        ("U", "Granite-cut storeroom below", False),
        ("X", "Lantern room and slate-roofed keeper's house", False),
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
        ("K", "Raised-bed prairie garden", False),
        ("F", "Flush concrete silo hatch", False),
        ("U", "Stacked pantry levels below", False),
        ("X", "Cross-section — living floors down the shaft", False),
    ],
    [
        ("Sectional sofa", "Soft seating for the curved living room."),
        ("Oak wall panel sample", "Warmth against concrete curves."),
        ("Raised garden bed kit", "Tomatoes and sunflowers on the prairie."),
        ("Reading floor lamp", "Quiet light from the skylight shaft."),
    ],
)

add_nc_story(
    "fjord-boathouse",
    "HXxaLpD79EM",
    "n09_fjord_boathouse",
    [
        ("I", "Timber living room — wood stove, sheepskins, glass floor to the boat", True),
        ("A", "Dark timber boathouse on dry-stone piers", False),
        ("K", "Fjord-side timber sauna", False),
        ("F", "Cliff stair — one way in by land", False),
        ("U", "Rock-cut store behind the house", False),
        ("X", "Boat bay under the house", False),
    ],
    [
        ("Sheepskin throw", "Soft texture for the timber lounge."),
        ("Wood stove accessories", "Evenings above the boat bay."),
        ("Sauna bucket & ladle", "Steam before a fjord dip."),
        ("Wool lounge chair", "Nordic calm over dark water."),
    ],
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
        ("C.raw.png", "The compound in the box canyon", False),
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
        ("C.raw.png", "Headland compound above the surf", False),
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
        ("C.raw.png", "Mountain compound under the peaks", False),
        ("F.raw.png", "Potatoes, cabbage, coop and goat pen", False),
        ("G.raw.png", "Garage and fueled rides", False),
        ("S1.raw.png", "One switchback road — one gate", False),
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
  background: linear-gradient(135deg, #ddd6c8 0%, #cfc6b6 50%, #e5dece 100%);
  display: flex; align-items: center; justify-content: center;
  color: var(--muted);
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
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
"""


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def header(prefix: str) -> str:
    return f"""  <header class="site-header">
    <div class="header-inner">
      <a class="wordmark" href="{prefix}index.html">Lock <span>&amp;</span> Linen</a>
      <nav aria-label="Primary">
        <a href="{prefix}index.html#homes">Homes</a>
        <a href="{prefix}index.html#stories">Stories</a>
        <a href="{prefix}about.html">About</a>
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
        <a href="{prefix}about.html">About</a>
      </div>
      <div class="disclosures">
        <p><strong>AI disclosure:</strong> {esc(ai_note)}</p>
        <p style="margin-top:0.7rem;"><strong>Affiliate disclosure (placeholder):</strong> Some links on this site may be affiliate links. If you buy through them, Lock &amp; Linen may earn a commission at no extra cost to you. No affiliate links are live on this page.</p>
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
        shop_html.append(
            f"""        <article class="product">
          <span class="ph-badge">Placeholder</span>
          <div class="ph-img">Image soon</div>
          <div class="ph-body">
            <h3>{esc(name)}</h3>
            <p>{esc(desc)}</p>
            <span class="btn-soon">Affiliate link coming soon</span>
          </div>
        </article>"""
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(s['title'])} — Lock &amp; Linen</title>
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
    </div>
  </section>

  <section aria-label="Shop this look placeholders">
    <div class="wrap">
      <p class="section-label">Shop this look</p>
      <h2>Pieces that match the mood</h2>
      <p style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:0.88rem;color:var(--muted);margin:-0.4rem 0 1.4rem;max-width:52ch;">Placeholder affiliate cards only — no live products or links yet.</p>
      <div class="shop-grid">
{chr(10).join(shop_html)}
      </div>
    </div>
  </section>

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
    default_ai = "Visuals on this site are AI-generated concept renders from Lock & Linen reels. These are illustrative concept homes, not real listings or buildable plans."
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Lock &amp; Linen — Concept Homes</title>
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
      </div>
    </div>
  </section>

{footer(default_ai, '')}
</body>
</html>
"""
    (PUBLIC / "index.html").write_text(html)


def write_about():
    default_ai = "Visuals across Lock & Linen are AI-generated concept renders. These are illustrative concept homes, not real listings or buildable plans."
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>About — Lock &amp; Linen</title>
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
        <p>Shop cards are placeholders only. Affiliate links are not live yet.</p>
      </div>
    </div>
  </section>

{footer(default_ai, '')}
</body>
</html>
"""
    (PUBLIC / "about.html").write_text(html)


def main():
    if PUBLIC.exists():
        # wipe previous public contents carefully
        for child in PUBLIC.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "css").mkdir(parents=True, exist_ok=True)
    (PUBLIC / "css" / "site.css").write_text(CSS)
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
    # manifest for report
    manifest = [{"slug": s["slug"], "yt": s["yt"], "title": s["title"]} for s in STORIES]
    (ROOT / "site" / "_build" / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("Done.", len(STORIES), "stories")


if __name__ == "__main__":
    main()
