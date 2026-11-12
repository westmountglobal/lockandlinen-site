#!/usr/bin/env python3
"""Local QA for the EN/FR site: twins, toggle round-trip, hreflang, broken links, affiliate parity."""
import re, sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup

PUBLIC = Path("/workspace/lockandlinen-site/site/public")
SITE = "https://lockandlinen.com"
errors, warns = [], []

def rel_of(p): return p.relative_to(PUBLIC).as_posix()
def url_of(rel):
    if rel == "index.html": return "/"
    if rel.endswith("/index.html"): return "/" + rel[:-10]
    return "/" + rel
def file_for(path):
    rel = path.lstrip("/")
    if rel == "" or rel.endswith("/"): rel += "index.html"
    return PUBLIC / rel

pages = [p for p in PUBLIC.rglob("*.html") if not re.match(r"google[0-9a-f]+\.html$", p.name)]
en = [p for p in pages if not rel_of(p).startswith("fr/")]
fr = [p for p in pages if rel_of(p).startswith("fr/")]
print(f"EN pages: {len(en)}  FR pages: {len(fr)}")
soups = {rel_of(p): BeautifulSoup(p.read_text(), "html.parser") for p in pages}

for p in en:
    r = rel_of(p)
    if not (PUBLIC / "fr" / r).exists():
        errors.append(f"no FR twin for {r}")

ids_cache = {}
def ids(rel):
    if rel not in ids_cache:
        s = soups.get(rel)
        ids_cache[rel] = {t.get("id") for t in s.find_all(id=True)} if s else set()
    return ids_cache[rel]

for r, s in soups.items():
    is_fr = r.startswith("fr/")
    redirect = s.find("meta", attrs={"name": "robots", "content": "noindex"}) is not None
    lang = s.html.get("lang", "")
    if is_fr and not lang.startswith("fr"): errors.append(f"{r}: lang={lang}")
    if not is_fr and lang != "en": errors.append(f"{r}: lang={lang}")
    if not redirect:
        hl = {l["hreflang"]: l["href"] for l in s.find_all("link", rel="alternate") if l.get("hreflang")}
        if set(hl) != {"en", "fr", "x-default"}: errors.append(f"{r}: hreflang {sorted(hl)}")
        sw = s.select(".lang-switch a[data-ll-lang]")
        if len(sw) != 2: errors.append(f"{r}: lang switch missing"); continue
        target = [a for a in sw if a["data-ll-lang"] == ("en" if is_fr else "fr")][0]["href"]
        tf = file_for(target)
        if not tf.exists(): errors.append(f"{r}: toggle -> {target} missing"); continue
        back_s = soups[rel_of(tf)]
        back = [a for a in back_s.select(".lang-switch a[data-ll-lang]") if a["data-ll-lang"] == ("fr" if is_fr else "en")][0]["href"]
        if file_for(back) != PUBLIC / r: errors.append(f"{r}: round-trip {target} -> {back}")
        canon = s.find("link", rel="canonical")["href"]
        if canon != SITE + url_of(r): errors.append(f"{r}: canonical {canon}")
    # links
    base = SITE + "/" + r
    for t in s.find_all(True):
        for a in ("href", "src"):
            v = t.get(a)
            if not v or v.startswith(("mailto:", "tel:", "javascript:", "data:")): continue
            u = urlsplit(urljoin(base, v))
            if u.netloc and u.netloc != "lockandlinen.com": continue
            f = file_for(u.path)
            if not f.exists():
                errors.append(f"{r}: broken {a}={v}")
            elif u.fragment and f.suffix == ".html" and t.name == "a":
                if u.fragment not in ids(rel_of(f)):
                    warns.append(f"{r}: missing #{u.fragment} in {rel_of(f)}")
            if is_fr and t.name == "a" and a == "href" and f.suffix == ".html" and not rel_of(f).startswith("fr/") and not t.get("data-ll-lang"):
                errors.append(f"{r}: FR page links to EN page {v}")

# affiliate parity
def amz(s):
    return sorted((a["href"], " ".join(a.get("rel", []))) for a in s.find_all("a", href=True) if "amazon." in a["href"] and ("/dp/" in a["href"] or "tag=" in a["href"]))
for p in en:
    r = rel_of(p)
    e, f = amz(soups[r]), amz(soups.get("fr/" + r, BeautifulSoup("", "html.parser")))
    if e != f: errors.append(f"{r}: Amazon link mismatch EN {len(e)} vs FR {len(f)}")
    for href, rel in f:
        if "tag=lockandlinen-20" not in href or rel != "nofollow sponsored noopener noreferrer":
            errors.append(f"fr/{r}: bad affiliate link {href} rel={rel}")
print("Amazon links on FR pages:", sum(len(amz(soups[rel_of(p)])) for p in fr))

for w in warns: print("WARN", w)
for e in errors: print("ERR ", e)
print("errors:", len(errors), "warnings:", len(warns))
sys.exit(1 if errors else 0)
