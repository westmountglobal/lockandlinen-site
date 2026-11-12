"""Amazon.ca affiliate settings for French (/fr/) pages only.

English pages stay on amazon.com with the US Associates tags.
Do not put a US tag on amazon.ca — it will not track.

The Canadian Associates tracking ID was not found in the repo or
workspace notes. Replace AMAZON_TAG_CA with the verified Amazon.ca
tag before merging or deploying. Untagged amazon.ca links earn nothing.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

# Placeholder only — not a real Associates ID. Replace before deploy.
AMAZON_TAG_CA = "REPLACE_WITH_AMAZON_CA_ASSOCIATES_TAG"

# No amazon.ca listing and no exact-same-model replacement found.
# Leave these cards on amazon.com / USD.
AMAZON_CA_UNFIXABLE = frozenset({
    "B0GKGFWY69",  # DaranEner 600W / 288Wh — CA has other capacities only
    "B0FK5BJZKM",  # EZVALO cordless wood-grain lamp — no same model on CA
    "B0D46PQT2C",  # Barebones Edison Light Stick, Brass — only string lights
    "B06XVJDYSF",  # Swiss Safe 200-piece first-aid kit — brand not sold on CA
})

# US ASIN -> CA ASIN when the US ASIN is absent or lands on the wrong variant.
AMAZON_CA_ASIN_MAP = {
    # SLNT leather Medium. US ASIN B07GXZM5PM lands on black leather XL (B017VOS1DA).
    "B07GXZM5PM": "B017VOS0FE",
    # rabbitgoo 17.5 × 78.7 in frosted ("Dépoli pur"). US ASIN B00RDVE2L2 lands on 30 × 200 cm matte black.
    "B00RDVE2L2": "B0CT5BXLDS",
}

_DP_RE = re.compile(
    r"https://www\.amazon\.com/(?:[^/]+/)?(?:dp|gp/product)/([A-Z0-9]{10})(?:[/?][^\"\s]*)?"
)
_PRIVACY_RE = re.compile(r"https://www\.amazon\.com/privacy")


def ca_product_url(us_asin: str) -> str | None:
    """Return the amazon.ca product URL, or None if the card must stay unchanged."""
    if us_asin in AMAZON_CA_UNFIXABLE:
        return None
    ca_asin = AMAZON_CA_ASIN_MAP.get(us_asin, us_asin)
    return f"https://www.amazon.ca/dp/{ca_asin}?tag={AMAZON_TAG_CA}"


def rewrite_fr_amazon_links(soup: BeautifulSoup) -> None:
    """Point FR product links at amazon.ca; leave unfixable ASINs on amazon.com."""
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "amazon.com/privacy" in href:
            a["href"] = _PRIVACY_RE.sub("https://www.amazon.ca/privacy", href)
            continue
        m = _DP_RE.match(href)
        if not m:
            continue
        new = ca_product_url(m.group(1))
        if new:
            a["href"] = new


def rewrite_fr_amazon_text(html: str) -> str:
    """Rewrite any amazon.com/privacy URL leftover in visible text."""
    return html.replace("https://www.amazon.com/privacy", "https://www.amazon.ca/privacy")
