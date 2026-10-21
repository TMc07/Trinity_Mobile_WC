#!/usr/bin/env python3
"""
Builds the Trinity Care Continuum website.

HOW TO USE
  1. Edit page text in  _source/pages/*.html   (or styles in _source/assets/styles.css)
  2. Run:   python3 _source/build.py
  3. Commit and push. GitHub Pages publishes the generated files in the repo root.

Everything lives in plain files; only Python 3 is needed (no installs).
The build also checks every internal link and #anchor and tells you if any are broken.
"""
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)  # the repo root

# ---------------------------------------------------------------------------
# EDIT HERE: facts that appear on many pages. Change once, rebuild.
# ---------------------------------------------------------------------------
SITE = {
    "NAME": "Trinity Care Continuum",
    "DOMAIN": "https://trinitycarecontinuum.com",
    "PHONE": "(817) 910-6711",
    "PHONE_TEL": "+18179106711",
    "EMAIL": "intake@trinitymwc.com",
    "FAX": "800-915-0474",
    "FAX_TEL": "+18009150474",
    "JOTFORM": "https://form.jotform.com/260365813296058",
}

PROGRAM_NAV = [
    ("Chronic Care Management", "/chronic-care-management/"),
    ("Anxiety and/or Depression", "/anxiety-and-depression/"),
    ("Palliative Care", "/palliative-care/"),
    ("Transitional Care Management", "/transitional-care-management/"),
    ("All programs", "/programs/"),
]

# URLs that used to exist and now just forward somewhere (old URL -> new URL)
REDIRECTS = {
    "privacy.html": "/privacy/",
    "behavioral-health-integration/index.html": "/anxiety-and-depression/",
}

# ---------------------------------------------------------------------------


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def esc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def parse_page(path):
    raw = read(path)
    head, sep, body = raw.partition("\n---\n")
    if not sep:
        sys.exit("Page %s is missing the '---' line after its header." % path)
    meta = {}
    for line in head.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, body


PARTIALS = {}


def load_partials():
    d = os.path.join(HERE, "partials")
    for fn in os.listdir(d):
        if fn.endswith(".html"):
            PARTIALS[fn[:-5].upper()] = read(os.path.join(d, fn)).strip()


def subst(text):
    for _ in range(3):  # partials can contain placeholders too
        for k, v in PARTIALS.items():
            text = text.replace("{{%s}}" % k, v)
        for k, v in SITE.items():
            text = text.replace("{{%s}}" % k, v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", text)
    if left:
        sys.exit("Unknown placeholder(s): %s" % sorted(set(left)))
    return text


def asset_version(*names):
    h = hashlib.md5()
    for n in names:
        h.update(read(os.path.join(HERE, "assets", n)).encode("utf-8"))
    return h.hexdigest()[:8]


def header_html(path):
    def cur(href):
        if href == path:
            return ' aria-current="page"'
        return ""

    parent = ' aria-current="true"' if path.startswith(("/programs/", "/chronic-", "/anxiety-", "/palliative-", "/transitional-")) and path != "/programs/" else ""
    subs = "".join('<a href="%s"%s>%s</a>' % (u, cur(u), n) for n, u in PROGRAM_NAV)
    return (
        '<header><div class="wrap nav">'
        '<a class="brand" href="/" aria-label="Trinity Care Continuum home">'
        '<img src="/logo.png" alt="Trinity Care Continuum" width="760" height="262"></a>'
        '<a class="btn call-mobile" href="tel:{{PHONE_TEL}}">Call</a>'
        '<button class="menu" aria-expanded="false" aria-controls="navigation">Menu ☰</button>'
        '<nav id="navigation" aria-label="Main navigation">'
                '<div class="has-sub"><a href="/programs/"%s%s>Programs</a><div class="sub">%s</div></div>'
        '<a href="/areas-we-serve/"%s>Areas we serve</a>'
        '<a href="/partners/"%s>Partners</a>'
        '<a href="/faq/"%s>FAQ</a>'
        '<a href="/contact/"%s>Contact</a>'
        '<a class="navcall" href="tel:{{PHONE_TEL}}">{{PHONE}}</a>'
        '<a class="btn" href="/partners/#refer">Refer a patient <span aria-hidden="true">↗</span></a>'
        "</nav></div></header>"
    ) % (cur("/programs/"), parent if not cur("/programs/") else "", subs, cur("/areas-we-serve/"), cur("/partners/"), cur("/faq/"), cur("/contact/"))


TOPLINE = '<div class="topline"><div class="wrap"><span>Confidence Through Continuity.</span><a href="/areas-we-serve/">Telehealth across all of Texas</a></div></div>'

FOOTER = (
    '<footer><div class="wrap"><div class="footer-main"><div>'
    '<img src="/logo.png" alt="Trinity Care Continuum" width="760" height="262" loading="lazy">'
    "<p>One Patient. One Team. One Coordinated Plan.<br>Confidence Through Continuity.</p></div>"
    '<div class="footer-cols">'
    '<div><h4>Programs</h4>'
    '<a href="/chronic-care-management/">Chronic Care Management</a>'
    '<a href="/anxiety-and-depression/">Anxiety and/or Depression</a>'
    '<a href="/palliative-care/">Palliative Care</a>'
    '<a href="/transitional-care-management/">Transitional Care</a></div>'
    '<div><h4>Trinity</h4>'
    '<a href="/areas-we-serve/">Areas we serve</a>'
    '<a href="/partners/">For healthcare partners</a>'
    '<a href="/faq/">FAQ</a>'
    '<a href="/contact/">Contact</a>'
    '<a href="/privacy/">Privacy Notice</a></div>'
    '<div><h4>Contact</h4>'
    '<a href="tel:{{PHONE_TEL}}">{{PHONE}}</a>'
    '<a href="mailto:{{EMAIL}}">{{EMAIL}}</a>'
    '<span>Fax {{FAX}}</span></div>'
    "</div></div>"
    '<div class="footer-bottom"><span>© <span id="year">2026</span> Trinity Care Continuum. All rights reserved.</span>'
    "<span>Program availability is based on clinical need and eligibility. For a medical emergency, call 911.</span></div>"
    "</div></footer>"
)


def crumbs_html(meta):
    parts = ['<a href="/">Home</a>']
    items = [c.strip() for c in meta.get("crumbs", "").split(",") if c.strip()]
    for i, item in enumerate(items):
        sep = '<span aria-hidden="true">/</span>'
        if i == len(items) - 1:
            label = item.split("|")[0]
            parts.append(sep + '<span aria-current="page">%s</span>' % label)
        else:
            label, url = item.split("|")
            parts.append(sep + '<a href="%s">%s</a>' % (url, label))
    return '<div class="crumbs" role="navigation" aria-label="Breadcrumb">%s</div>' % "".join(parts)


def hero_html(meta):
    actions = ""
    if meta.get("actions", "default") != "none":
        actions = (
            '<div class="actions"><a class="btn" href="tel:{{PHONE_TEL}}">Call {{PHONE}}</a>'
            '<a class="btn outline" href="/partners/#refer">Refer a patient <span aria-hidden="true">↗</span></a></div>'
        )
    return (
        '<section class="page-hero"><div class="wrap">%s<div class="eyebrow">%s</div><h1>%s</h1><p class="lead">%s</p>%s</div></section>'
        % (crumbs_html(meta), meta.get("eyebrow", ""), meta["h1"], meta.get("lead", ""), actions)
    )


def head_html(meta, css_v):
    url = SITE["DOMAIN"] + meta["path"]
    title = esc(meta["title"])
    desc = esc(subst(meta["description"]))
    robots = '<meta name="robots" content="noindex">' if meta.get("noindex") == "yes" else ""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="theme-color" content="#102f40">'
        "<!-- Generated by _source/build.py. Edit _source/pages, not this file. -->"
        "<title>%s</title>" % title
        + '<meta name="description" content="%s">' % desc
        + robots
        + '<link rel="canonical" href="%s">' % url
        + '<link rel="icon" href="/favicon.ico" sizes="any">'
        '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">'
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">'
        '<meta property="og:type" content="website">'
        '<meta property="og:site_name" content="Trinity Care Continuum">'
        '<meta property="og:title" content="%s">' % title
        + '<meta property="og:description" content="%s">' % desc
        + '<meta property="og:url" content="%s">' % url
        + '<meta property="og:image" content="%s/og-image.png">' % SITE["DOMAIN"]
        + '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
        '<meta property="og:image:alt" content="Trinity Care Continuum logo">'
        '<meta name="twitter:card" content="summary_large_image">'
        '<link rel="stylesheet" href="/styles.css?v=%s"></head>' % css_v
    )


def build_page(meta, body, css_v, js_v):
    path = meta["path"]
    if meta.get("layout") == "home":
        inner = body
    else:
        inner = hero_html(meta) + body
        if meta.get("cta", "yes") != "no":
            inner += "\n{{CTA}}"
    page = (
        head_html(meta, css_v)
        + '<body><a class="skip" href="#main">Skip to content</a>'
        + TOPLINE
        + header_html(path)
        + '<main id="main">'
        + inner
        + "</main>"
        + FOOTER
        + '<script src="/site.js?v=%s"></script></body></html>\n' % js_v
    )
    return subst(page)


def out_file(path):
    rel = path.lstrip("/")
    if rel == "" or path.endswith("/"):
        rel = os.path.join(rel, "index.html")
    return os.path.join(OUT, rel)


def check_links(built):
    """built: list of (url_path, file_path). Verifies every internal href/src and #anchor."""
    problems = 0
    count = 0
    cache = {}
    for url, f in built:
        html = read(f)
        for href in re.findall(r'(?:href|src)="(/[^"]*)"', html):
            if href.startswith("//"):
                continue
            count += 1
            base, _, frag = href.partition("#")
            base = base.split("?")[0]
            target = out_file(base if base else "/")
            if not os.path.isfile(target):
                print("  BROKEN LINK on %s -> %s" % (url, href))
                problems += 1
                continue
            if frag:
                if target not in cache:
                    cache[target] = read(target)
                if ('id="%s"' % frag) not in cache[target]:
                    print("  MISSING ANCHOR on %s -> %s" % (url, href))
                    problems += 1
    return count, problems


def main():
    load_partials()
    css_v = asset_version("styles.css")
    js_v = asset_version("site.js")

    write(os.path.join(OUT, "styles.css"),
          "/* GENERATED by _source/build.py from _source/assets/styles.css. Edit the source, not this file. */\n"
          + read(os.path.join(HERE, "assets", "styles.css")))
    write(os.path.join(OUT, "site.js"), read(os.path.join(HERE, "assets", "site.js")))

    built = []      # (url path, file on disk)
    sitemap = []
    warnings = 0
    for fn in sorted(os.listdir(os.path.join(HERE, "pages"))):
        if not fn.endswith(".html"):
            continue
        meta, body = parse_page(os.path.join(HERE, "pages", fn))
        html = build_page(meta, body, css_v, js_v)
        if html.count("<h1") != 1:
            print("  WARNING %s: expected exactly one <h1>, found %d" % (fn, html.count("<h1")))
            warnings += 1
        if len(meta["title"]) > 70:
            print("  WARNING %s: title is %d characters (aim for 60-70)" % (fn, len(meta["title"])))
            warnings += 1
        desc = subst(meta["description"])
        if len(desc) > 165:
            print("  WARNING %s: description is %d characters (aim for under 160)" % (fn, len(desc)))
            warnings += 1
        target = os.path.join(OUT, meta["output"]) if meta.get("output") else out_file(meta["path"])
        write(target, html)
        built.append((meta["path"], target))
        if meta.get("sitemap", "yes") != "no":
            sitemap.append(meta["path"])

    for old, new in REDIRECTS.items():
        write(os.path.join(OUT, old),
              '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved</title>'
              '<meta name="robots" content="noindex"><link rel="canonical" href="%s%s">'
              '<meta http-equiv="refresh" content="0; url=%s"></head>'
              '<body><p>This page has moved to <a href="%s">%s</a>.</p></body></html>\n'
              % (SITE["DOMAIN"], new, new, new, new))

    urls = "".join("  <url><loc>%s%s</loc></url>\n" % (SITE["DOMAIN"], p) for p in sitemap)
    write(os.path.join(OUT, "sitemap.xml"),
          '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n' % urls)
    write(os.path.join(OUT, "robots.txt"),
          "User-agent: *\nAllow: /\nDisallow: /_source/\n\nSitemap: %s/sitemap.xml\n" % SITE["DOMAIN"])

    n_links, bad = check_links(built)
    print("Built %d pages. Checked %d internal links: %d problem(s). %d warning(s)." % (len(built), n_links, bad, warnings))
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
