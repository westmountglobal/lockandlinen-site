#!/usr/bin/env python3
"""Generate the French (/fr/) twin of every English page in site/public/.

Runs after build_site.py. Translations live in site/_i18n/fr.json (EN key -> FR value).
Keys are "translation units": the inline content of a block element, with inline tags
replaced by placeholders {0} ... {/0} so links/markup (incl. Amazon affiliate hrefs)
are carried over byte-for-byte from the English page.

Usage:
  python3 i18n_fr.py            # build /fr/ pages + inject toggle/hreflang into EN pages
  python3 i18n_fr.py --extract  # write site/_i18n/missing.json with untranslated units
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, NavigableString, Tag, Comment, Doctype

ROOT = Path("/workspace/lockandlinen-site")
PUBLIC = ROOT / "site" / "public"
I18N = ROOT / "site" / "_i18n"
SITE_URL = "https://lockandlinen.com"
FR_LANG = "fr-CA"

BLOCK = {
    "address", "article", "aside", "blockquote", "body", "button", "dd", "details", "dialog", "div",
    "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6",
    "head", "header", "hr", "html", "label", "legend", "li", "main", "nav", "ol", "p", "section",
    "summary", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "ul", "option", "select",
}
SKIP = {"script", "style", "noscript", "svg", "iframe", "code", "template", "title", "textarea", "input"}
VOID = {"br", "img", "input", "wbr", "hr", "source", "meta", "link"}
TRANSLATABLE_ATTRS = ("alt", "title", "aria-label", "placeholder", "data-label")
META_KEYS = {"description", "og:title", "og:description", "twitter:title", "twitter:description", "og:image:alt"}
NOINDEX_REDIRECTS = {"gear/index.html"}


def en_pages() -> list[Path]:
    out = []
    for p in sorted(PUBLIC.rglob("*.html")):
        rel = p.relative_to(PUBLIC).as_posix()
        if rel.startswith("fr/") or re.match(r"google[0-9a-f]+\.html$", rel):
            continue
        out.append(p)
    return out


def clean_path(rel: str) -> str:
    """'stories/x/index.html' -> '/stories/x/' ; 'about.html' -> '/about.html' ; 'index.html' -> '/'."""
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def fr_path(en_clean: str) -> str:
    return "/fr" + en_clean


# ---------------------------------------------------------------- units
def is_block(node) -> bool:
    if not isinstance(node, Tag):
        return False
    if node.name in BLOCK:
        return True
    return any(isinstance(d, Tag) and d.name in BLOCK for d in node.descendants)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def run_key(nodes, tags: list) -> str:
    parts = []
    for n in nodes:
        if isinstance(n, Comment):
            continue
        if isinstance(n, NavigableString):
            parts.append(str(n))
        elif isinstance(n, Tag):
            i = len(tags)
            tags.append(n)
            if n.name in VOID:
                parts.append("{%d}" % i)
            elif n.name in SKIP:
                parts.append("{%d}{/%d}" % (i, i))  # opaque (e.g. <code>) – kept verbatim
            else:
                parts.append("{%d}" % i)
                parts.append(run_key(list(n.children), tags))
                parts.append("{/%d}" % i)
    return "".join(parts)


def has_text(key: str) -> bool:
    return bool(re.sub(r"\{/?\d+\}", "", key).strip())


def iter_runs(el: Tag):
    """Yield lists of consecutive inline children (text + inline tags) of el, recursively."""
    run = []
    for child in list(el.children):
        if isinstance(child, (Comment, Doctype)):
            continue
        if isinstance(child, Tag) and (child.name in SKIP and child.name != "code" or is_block(child)):
            if run:
                yield run
                run = []
            if child.name not in SKIP:
                yield from iter_runs(child)
        else:
            run.append(child)
    if run:
        yield run


def open_tag(t: Tag) -> str:
    attrs = []
    for k, v in t.attrs.items():
        if isinstance(v, list):
            v = " ".join(v)
        if v is None:
            attrs.append(k)
        else:
            attrs.append('%s="%s"' % (k, str(v).replace("&", "&amp;").replace('"', "&quot;")))
    return "<%s%s>" % (t.name, (" " + " ".join(attrs)) if attrs else "")


def esc_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_translation(fr: str, tags: list) -> str:
    out = []
    pos = 0
    for m in re.finditer(r"\{(/?)(\d+)\}", fr):
        out.append(esc_text(fr[pos:m.start()]))
        close, idx = m.group(1), int(m.group(2))
        t = tags[idx]
        if close:
            out.append("</%s>" % t.name)
        elif t.name in SKIP:
            out.append(str(t))  # verbatim opaque element; its {/n} is swallowed below
        else:
            out.append(open_tag(t))
        pos = m.end()
    out.append(esc_text(fr[pos:]))
    html = "".join(out)
    # opaque elements were emitted whole: drop their stray closing tags
    for i, t in enumerate(tags):
        if t.name in SKIP:
            html = html.replace(str(t) + "</%s>" % t.name, str(t), 1)
    return html


def placeholders(s: str) -> list[str]:
    return sorted(re.findall(r"\{/?\d+\}", s))


# ---------------------------------------------------------------- page processing
def collect_units(soup: BeautifulSoup) -> list[str]:
    keys = []
    body = soup.body or soup
    for run in iter_runs(body):
        tags = []
        k = norm(run_key(run, tags))
        if has_text(k):
            keys.append(k)
    for t in soup.find_all(True):
        for a in TRANSLATABLE_ATTRS:
            if t.has_attr(a) and norm(t[a]):
                keys.append(norm(t[a]))
    for m in soup.find_all("meta"):
        k = m.get("name") or m.get("property")
        if k in META_KEYS and m.get("content"):
            keys.append(norm(m["content"]))
    if soup.title and soup.title.string:
        keys.append(norm(soup.title.string))
    return keys


class Missing(Exception):
    pass


def translate_soup(soup: BeautifulSoup, fr: dict, missing: set) -> None:
    body = soup.body or soup
    runs = list(iter_runs(body))
    for run in runs:
        tags = []
        raw = run_key(run, tags)
        k = norm(raw)
        if not has_text(k):
            continue
        if k not in fr:
            missing.add(k)
            continue
        val = fr[k]
        if placeholders(val) != placeholders(k):
            raise Missing(f"placeholder mismatch for {k!r} -> {val!r}")
        lead = re.match(r"^\s*", raw).group(0)
        trail = re.search(r"\s*$", raw).group(0)
        html = (" " if lead else "") + render_translation(val, tags) + (" " if trail and raw.strip() else "")
        frag = BeautifulSoup(html, "html.parser")
        first = run[0]
        anchor = soup.new_string("")
        first.insert_before(anchor)
        for n in run:
            n.extract()
        for n in reversed(list(frag.contents)):
            anchor.insert_after(n)
        anchor.extract()
    for t in soup.find_all(True):
        for a in TRANSLATABLE_ATTRS:
            if t.has_attr(a) and norm(t[a]):
                k = norm(t[a])
                if k in fr:
                    t[a] = fr[k]
                else:
                    missing.add(k)
    for m in soup.find_all("meta"):
        k = m.get("name") or m.get("property")
        if k in META_KEYS and m.get("content"):
            c = norm(m["content"])
            if c in fr:
                m["content"] = fr[c]
            else:
                missing.add(c)
    if soup.title and soup.title.string:
        k = norm(soup.title.string)
        if k in fr:
            soup.title.string = fr[k]
        else:
            missing.add(k)


def rewrite_urls(soup: BeautifulSoup, en_rel: str, page_map: dict) -> None:
    base = SITE_URL + clean_path(en_rel) if not en_rel.endswith("index.html") else SITE_URL + "/" + en_rel
    base = SITE_URL + "/" + en_rel

    def fix(url: str, page_ok=True) -> str:
        if not url or url.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            return url
        absu = urljoin(base, url)
        sp = urlsplit(absu)
        if sp.netloc and sp.netloc not in ("lockandlinen.com", "www.lockandlinen.com"):
            return url  # external (Amazon etc.) untouched
        path = sp.path or "/"
        rel = path.lstrip("/")
        if rel == "" or rel.endswith("/"):
            rel = rel + "index.html"
        keep_abs = url.startswith("http")
        suffix = ("?" + sp.query if sp.query else "") + ("#" + sp.fragment if sp.fragment else "")
        if page_ok and rel in page_map:
            newp = fr_path(clean_path(rel))
        else:
            newp = path
        return (SITE_URL + newp if keep_abs else newp) + suffix

    for t in soup.find_all(True):
        for attr in ("href", "src", "action", "poster"):
            if t.has_attr(attr):
                is_page = not (t.name == "link" and "icon" in " ".join(t.get("rel", []))) and t.name in ("a", "link", "form", "area")
                if t.name == "link" and "stylesheet" in t.get("rel", []):
                    is_page = False
                t[attr] = fix(t[attr], page_ok=is_page)
        if t.has_attr("srcset"):
            t["srcset"] = ", ".join(
                " ".join([fix(p.split()[0], False)] + p.split()[1:]) for p in t["srcset"].split(",") if p.strip()
            )
        if t.has_attr("style") and "url(" in t["style"]:
            t["style"] = re.sub(r"url\((['\"]?)([^)'\"]+)\1\)", lambda m: "url(%s%s%s)" % (m.group(1), fix(m.group(2), False), m.group(1)), t["style"])
    for m in soup.find_all("meta", attrs={"property": "og:url"}):
        m["content"] = fix(m["content"])


def lang_switch_html(en_url: str, fr_url: str, current: str) -> str:
    en_cur = ' aria-current="true"' if current == "en" else ""
    fr_cur = ' aria-current="true"' if current == "fr" else ""
    label = "Choisir la langue" if current == "fr" else "Choose language"
    return (
        f'<div class="lang-switch" role="group" aria-label="{label}">'
        f'<a href="{en_url}" hreflang="en" lang="en" data-ll-lang="en"{en_cur}>EN</a>'
        f'<span class="lang-sep" aria-hidden="true">|</span>'
        f'<a href="{fr_url}" hreflang="fr" lang="fr" data-ll-lang="fr"{fr_cur}>FR</a>'
        f"</div>"
    )


def hreflang_html(en_clean: str) -> str:
    en = SITE_URL + en_clean
    fr = SITE_URL + fr_path(en_clean)
    return (
        f'<link rel="alternate" hreflang="en" href="{en}" />\n'
        f'<link rel="alternate" hreflang="fr" href="{fr}" />\n'
        f'<link rel="alternate" hreflang="x-default" href="{en}" />\n'
    )


LANG_SCRIPT = '<script src="/js/lang.js"></script>\n'

LANG_JS = r"""(function () {
  "use strict";
  // Lock & Linen language routing. No IP lookup, no server redirect.
  // 1) A manual EN|FR choice (localStorage "ll_lang") always wins.
  // 2) Otherwise, once per browser (first visit), a visitor whose top browser
  //    language starts with "fr" is sent from an English page to its /fr/ twin.
  var PREF = "ll_lang", SEEN = "ll_lang_auto_done";
  var html = document.documentElement;
  var pageLang = (html.getAttribute("lang") || "en").slice(0, 2).toLowerCase();
  function get(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { window.localStorage.setItem(k, v); } catch (e) {} }
  function twin(lang) {
    var el = document.querySelector('link[rel="alternate"][hreflang="' + lang + '"]');
    if (!el) return null;
    var u = el.getAttribute("href").replace(/^https?:\/\/[^\/]+/, "");
    return u + (location.hash || "");
  }
  function go(lang) {
    var t = twin(lang);
    if (t && t.split("#")[0] !== location.pathname) location.replace(t);
  }
  var isBot = /bot|crawl|spider|slurp|lighthouse/i.test(navigator.userAgent || "");
  var pref = get(PREF);
  if (!isBot) {
    if (pref === "en" || pref === "fr") {
      if (pref !== pageLang) go(pref);
    } else if (!get(SEEN)) {
      set(SEEN, "1");
      var langs = (navigator.languages && navigator.languages.length) ? navigator.languages : [navigator.language || navigator.userLanguage || ""];
      var first = String(langs[0] || "").toLowerCase();
      if (pageLang === "en" && first.indexOf("fr") === 0) go("fr");
    }
  }
  // Remember a manual toggle click.
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("[data-ll-lang]");
    if (!a) return;
    set(PREF, a.getAttribute("data-ll-lang"));
    set(SEEN, "1");
  });
})();
"""

LANG_CSS = """
/* EN | FR language switch */
.lang-switch {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  flex: 0 0 auto;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  white-space: nowrap;
  color: var(--muted);
  order: 10;
  margin-left: 1.2rem;
}
.site-header .primary-nav { margin-left: auto; }
.lang-switch a {
  color: inherit;
  text-decoration: none;
  padding: 0.35rem 0.15rem;
}
.lang-switch a:hover, .lang-switch a:focus-visible { color: var(--ink); text-decoration: underline; }
.lang-switch a[aria-current="true"] { color: var(--ink); font-weight: 600; }
.lang-switch .lang-sep { opacity: 0.45; }
@media (max-width: 860px) {
  .lang-switch { order: 0; margin-left: 0; font-size: 0.74rem; }
  .site-header .wordmark { white-space: nowrap; }
}
@media (max-width: 430px) {
  .site-header .header-inner { gap: 0.5rem; padding-left: 0.9rem; padding-right: 0.9rem; }
  .site-header .wordmark { letter-spacing: 0.1em; font-size: 0.78rem; }
  .site-header .nav-priority { letter-spacing: 0.04em; font-size: 0.72rem; }
  .lang-switch { gap: 0.15rem; font-size: 0.72rem; letter-spacing: 0.04em; }
  .site-header .nav-toggle-btn { padding: 0.35rem 0.55rem; }
}
@media (max-width: 350px) {
  .site-header .header-inner { gap: 0.4rem; padding-left: 0.75rem; padding-right: 0.75rem; }
  .lang-switch .lang-sep { display: none; }
  .site-header .nav-priority { font-size: 0.66rem; letter-spacing: 0.02em; }
}
"""


def strip_i18n(html: str) -> str:
    """Remove a previous injection so re-running the build is idempotent."""
    html = re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*" />\n?', "", html)
    html = html.replace(LANG_SCRIPT, "")
    html = re.sub(r'\s*<div class="lang-switch"[^>]*>.*?</a></div>', "", html, flags=re.S)
    return html


def inject_head(html: str, extra: str) -> str:
    """Insert extra right after the canonical link (or before </head>)."""
    m = re.search(r'<link rel="canonical"[^>]*>\n?', html)
    if m:
        return html[: m.end()] + extra + html[m.end():]
    return html.replace("</head>", extra + "</head>", 1)


def inject_switch(html: str, switch: str) -> str:
    # Desktop + mobile: the switch sits in the header bar, outside the collapsible nav,
    # so it is visible on phones without opening the menu.
    m = re.search(r'(\s*)<input[^>]*id="nav-toggle"', html)
    if m:
        return html[: m.start()] + m.group(1) + switch + html[m.start():]
    m = re.search(r'(<div class="header-inner">)', html)
    if m:
        return html[: m.end()] + switch + html[m.end():]
    return html


# Hand-written FR pages that do not go through the translator.
def fr_gear_redirect() -> str:
    dest = f"{SITE_URL}/fr/guides/gear-wed-put-in-these-homes/"
    return f"""<!DOCTYPE html>
<html lang="{FR_LANG}">
<head>
<meta charset="utf-8" />
<link rel="canonical" href="{dest}" />
<meta name="robots" content="noindex" />
<title>Équipement — Lock &amp; Linen</title>
<script>location.replace({dest!r} + (location.hash || ""));</script>
</head>
<body>
  <p>Page déplacée : <a href="{dest}">L’équipement qu’on mettrait dans ces maisons</a>.</p>
</body>
</html>
"""


def write_sitemap(page_map: dict) -> None:
    urls = []
    for rel in page_map:
        if rel in NOINDEX_REDIRECTS:
            continue
        en_clean = clean_path(rel)
        en = SITE_URL + en_clean
        fr = SITE_URL + fr_path(en_clean)
        alts = (
            f'    <xhtml:link rel="alternate" hreflang="en" href="{en}" />\n'
            f'    <xhtml:link rel="alternate" hreflang="fr" href="{fr}" />\n'
            f'    <xhtml:link rel="alternate" hreflang="x-default" href="{en}" />\n'
        )
        for loc in (en, fr):
            urls.append(f"  <url>\n    <loc>{loc}</loc>\n{alts}    <changefreq>weekly</changefreq>\n  </url>")
    (PUBLIC / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def main(extract: bool = False):
    fr_file = I18N / "fr.json"
    fr = json.loads(fr_file.read_text()) if fr_file.exists() else {}
    pages = en_pages()
    page_map = {p.relative_to(PUBLIC).as_posix(): p for p in pages}
    missing: set = set()
    all_keys: dict = {}

    if extract:
        for rel, p in page_map.items():
            if rel in NOINDEX_REDIRECTS:
                continue
            soup = BeautifulSoup(strip_i18n(p.read_text()), "html.parser")
            for div in soup.select('.fr-summary[lang="fr"]'):
                div.decompose()
            for k in collect_units(soup):
                all_keys.setdefault(k, rel)
        miss = {k: v for k, v in all_keys.items() if k not in fr}
        (I18N / "missing.json").write_text(json.dumps(miss, ensure_ascii=False, indent=1))
        print(f"{len(all_keys)} units, {len(miss)} missing -> {I18N/'missing.json'}")
        unused = [k for k in fr if k not in all_keys]
        if unused:
            print(f"{len(unused)} unused keys in fr.json")
        return

    # JS + CSS
    (PUBLIC / "js" / "lang.js").write_text(LANG_JS)
    css = PUBLIC / "css" / "site.css"
    if ".lang-switch" not in css.read_text():
        css.write_text(css.read_text() + LANG_CSS)

    count = 0
    for rel, p in page_map.items():
        en_clean = clean_path(rel)
        out = PUBLIC / "fr" / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if rel in NOINDEX_REDIRECTS:
            out.write_text(fr_gear_redirect())
            count += 1
            continue
        src = strip_i18n(p.read_text())
        # ---- French twin
        soup = BeautifulSoup(src, "html.parser")
        for div in soup.select('.fr-summary[lang="fr"]'):
            div.decompose()  # the whole FR page is French; the short EN-page summary is redundant
        translate_soup(soup, fr, missing)
        rewrite_urls(soup, rel, page_map)
        soup.html["lang"] = FR_LANG
        canon = soup.find("link", rel="canonical")
        if canon:
            canon["href"] = SITE_URL + fr_path(en_clean)
        fr_html = str(soup)
        fr_html = fr_html.replace('<html lang="%s">' % FR_LANG, '<html lang="%s">' % FR_LANG)
        fr_html = inject_head(fr_html, hreflang_html(en_clean) + '<meta property="og:locale" content="fr_CA" />\n<meta property="og:locale:alternate" content="en_US" />\n' + LANG_SCRIPT)
        fr_html = inject_switch(fr_html, lang_switch_html(en_clean, fr_path(en_clean), "fr"))
        out.write_text(fr_html)
        # ---- English page: add hreflang + switch + lang router
        en_html = inject_head(src, hreflang_html(en_clean) + LANG_SCRIPT)
        en_html = inject_switch(en_html, lang_switch_html(en_clean, fr_path(en_clean), "en"))
        p.write_text(en_html)
        count += 1
    write_sitemap(page_map)
    if missing:
        (I18N / "missing.json").write_text(json.dumps(sorted(missing), ensure_ascii=False, indent=1))
        print(f"WARNING: {len(missing)} untranslated units (left in English) -> {I18N/'missing.json'}")
    print(f"FR twins written: {count}")


if __name__ == "__main__":
    main(extract="--extract" in sys.argv)
