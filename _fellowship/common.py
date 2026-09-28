# -*- coding: utf-8 -*-
"""Shared paths, platform tokens and page chrome for the SOCPA fellowship build.

Every build script imports from here so the header, footer, fonts and colour
tokens stay identical across fellowship.html, business-environment.html,
capital-structure.html and the two paused pages.
"""
import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root = published site
HERE = os.path.dirname(os.path.abspath(__file__))
INPUTS = os.path.join(HERE, "inputs")
TEMPLATES = os.path.join(HERE, "templates")
SRC = os.path.join(HERE, "src")
OUT = os.path.join(ROOT, "publish_paused")
DATA_OUT = os.path.join(OUT, "data")

# Files in the repo root that form the currently published site (the base we copy).
BASE_EXCLUDE_DIRS = {".git", "_fellowship", "publish_paused", "node_modules"}


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, obj, pretty=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        if pretty:
            json.dump(obj, f, ensure_ascii=False, indent=1)
        else:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Platform tokens, read from the published files rather than hard-coded.
# ---------------------------------------------------------------------------
def platform_tokens():
    """Return the platform colours, each read from the file that defines it.

    The prompt names private-sector.html as the source, but in this repository
    that file is the locked "restricted" page. The same values live in:
      --primary, --heading, --line : index.html :root block
      --gold                       : assets/logo.svg (the brand accent)
      --paper                      : manifest.webmanifest background_color
    """
    idx = read(os.path.join(ROOT, "index.html"))
    root_block = re.search(r":root\{([^}]*)\}", idx).group(1)
    vars_ = dict(re.findall(r"--([\w-]+)\s*:\s*([^;]+);?", root_block))
    logo = read(os.path.join(ROOT, "assets", "logo.svg"))
    gold = re.search(r'<rect[^>]*fill="(#[0-9A-Fa-f]{6})"', logo).group(1)
    manifest = load_json(os.path.join(ROOT, "manifest.webmanifest"))
    tokens = {
        "primary": vars_["primary"].strip(),
        "heading": vars_["heading"].strip(),
        "line": vars_["line"].strip(),
        "gold": gold.upper(),
        "paper": manifest["background_color"].upper(),
        "theme": manifest["theme_color"].upper(),
    }
    tokens["_sources"] = {
        "primary": "index.html :root --primary",
        "heading": "index.html :root --heading",
        "line": "index.html :root --line",
        "gold": "assets/logo.svg rect fill",
        "paper": "manifest.webmanifest background_color",
    }
    return tokens


FONT_FACES = """
@font-face{font-family:"Tajawal Latin";font-style:normal;font-weight:400;font-display:swap;src:url("fonts/tajawal-latin-400-normal.woff2") format("woff2")}
@font-face{font-family:"Tajawal Latin";font-style:normal;font-weight:500;font-display:swap;src:url("fonts/tajawal-latin-500-normal.woff2") format("woff2")}
@font-face{font-family:"Tajawal Latin";font-style:normal;font-weight:700;font-display:swap;src:url("fonts/tajawal-latin-700-normal.woff2") format("woff2")}
@font-face{font-family:"Tajawal Arabic";font-style:normal;font-weight:400;font-display:swap;src:url("fonts/tajawal-arabic-400-normal.woff2") format("woff2")}
@font-face{font-family:"Tajawal Arabic";font-style:normal;font-weight:500;font-display:swap;src:url("fonts/tajawal-arabic-500-normal.woff2") format("woff2")}
@font-face{font-family:"Tajawal Arabic";font-style:normal;font-weight:700;font-display:swap;src:url("fonts/tajawal-arabic-700-normal.woff2") format("woff2")}
""".strip()

# Latin subset first so digits and Latin letters come from it; Arabic glyphs fall
# through to the Arabic subset per character.
FONT_STACK = '"Tajawal Latin","Tajawal Arabic","Segoe UI",Tahoma,Arial,sans-serif'


def base_css(t):
    """Platform chrome CSS. Every class is prefixed m- so it never leaks into
    the lesson roots on capital-structure.html."""
    return FONT_FACES + """
:root{
  --primary:%(primary)s; --gold:%(gold)s; --paper:%(paper)s;
  --heading:%(heading)s; --line:%(line)s;
  --card:#FFFFFF; --ink:%(heading)s; --muted:#56636F; --on-primary:#FFFFFF;
  --primary-soft:#E4EAF1; --gold-soft:#FDF1D2;
  --ok:#2F7D5B; --ok-soft:#DDEFE5; --bad:#B4433A; --bad-soft:#F8E6E3;
  --m-font:%(stack)s;
  color-scheme:light;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --primary:#A9C0D8; --paper:#12181F; --heading:#E8EDF2; --line:#2C3744;
    --card:#1A222C; --ink:#E8EDF2; --muted:#9AA7B4; --on-primary:#12181F;
    --primary-soft:#22303F; --gold-soft:#3A3121;
    --ok:#6FC29A; --ok-soft:#1F3A2E; --bad:#E58A8A; --bad-soft:#442222;
    color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --primary:#A9C0D8; --paper:#12181F; --heading:#E8EDF2; --line:#2C3744;
  --card:#1A222C; --ink:#E8EDF2; --muted:#9AA7B4; --on-primary:#12181F;
  --primary-soft:#22303F; --gold-soft:#3A3121;
  --ok:#6FC29A; --ok-soft:#1F3A2E; --bad:#E58A8A; --bad-soft:#442222;
  color-scheme:dark;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%%;scroll-padding-top:env(safe-area-inset-top,0px)}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--m-font);font-weight:500;font-size:17px;line-height:1.75;
  padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);overflow-x:hidden}
h1,h2,h3,h4,strong,b,button{font-weight:700}
a{color:var(--primary)}
[hidden]{display:none!important}
.m-wrap{max-width:760px;margin:0 auto;padding:0 16px 40px}
.m-top{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 0 10px}
.m-brand{display:inline-flex;align-items:center;gap:8px;text-decoration:none;color:var(--primary);font-weight:700;font-size:19px}
.m-brand img{width:30px;height:30px;display:block}
.m-crumb{font-size:14px;color:var(--muted);text-decoration:none}
.m-crumb:hover{color:var(--primary)}
.m-title{font-size:clamp(24px,5vw,32px);line-height:1.35;margin:8px 0 18px;color:var(--heading)}
.m-foot{margin-top:32px;padding:14px 16px;border:1.5px solid var(--line);border-radius:12px;font-size:13px;line-height:1.85;color:var(--muted);background:var(--card)}
.m-foot strong{display:block;margin-top:6px;color:var(--ink);font-weight:500}
.m-btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;border:none;border-radius:10px;padding:11px 16px;font:inherit;font-weight:700;font-size:16px;cursor:pointer;background:var(--primary);color:var(--on-primary);text-decoration:none;min-height:44px}
.m-btn.m-ghost{background:transparent;border:1.5px solid var(--line);color:var(--ink)}
.m-btn:disabled{opacity:.45;cursor:default}
.m-btn:focus-visible,.m-card:focus-visible,a:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
/* gate */
.m-gate{position:fixed;inset:0;z-index:100;background:rgba(18,24,31,.55);display:flex;align-items:center;justify-content:center;padding:16px}
.m-gate-box{background:var(--card);color:var(--ink);border:1.5px solid var(--primary);border-radius:16px;max-width:440px;width:100%%;padding:24px 20px;box-shadow:0 10px 30px rgba(0,0,0,.2)}
.m-gate-box h2{margin:0 0 8px;font-size:20px;color:var(--heading)}
.m-gate-box p{margin:0 0 14px;font-size:15px;color:var(--muted);line-height:1.8}
.m-gate-row{display:flex;gap:8px;flex-wrap:wrap}
.m-gate-row input{flex:1 1 200px;min-width:0;font:inherit;font-size:16px;padding:10px 12px;border:1.5px solid var(--line);border-radius:10px;background:var(--paper);color:var(--ink);direction:ltr;text-align:left;min-height:44px}
.m-gate-row input:focus-visible{outline:2px solid var(--gold);outline-offset:1px}
.m-gate-err{color:var(--bad);font-size:14px;min-height:1.6em;margin-top:6px}
.m-gate-free{font-size:14px;margin-top:10px;color:var(--muted)}
@media (prefers-reduced-motion: reduce){*{scroll-behavior:auto!important}}
""" % dict(t, stack=FONT_STACK)


def head(title, t, extra_css="", noindex=False, description=None):
    robots = '<meta name="robots" content="noindex">\n' if noindex else ""
    desc = '<meta name="description" content="%s">\n' % description if description else ""
    return """<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
%s%s<meta name="theme-color" content="%s">
<title>%s</title>
<link rel="icon" href="assets/logo.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="manifest" href="manifest.webmanifest">
<style>
%s
%s
</style>
</head>
""" % (robots, desc, t["theme"], title, base_css(t), extra_css)


def brand_bar(crumb_href=None, crumb_text=None):
    crumb = ""
    if crumb_href:
        crumb = '<a class="m-crumb" href="%s">%s</a>' % (crumb_href, crumb_text)
    return """<header class="m-top">
  <a class="m-brand" href="index.html"><picture><source srcset="assets/logo-white.svg" media="(prefers-color-scheme: dark)"><img src="assets/logo.svg" alt="" width="30" height="30"></picture><span>منصة معيار</span></a>
  %s
</header>""" % crumb


FOOTER_TEXT = ("هذه المنصة عمل شخصي مستقل لا يمثل اي جهة رسمية او تعليمية، والمحتوى فيها اعد لأغراض "
               "التحضير الذاتي وقد يتضمن اخطاء او تبسيطا في الصياغة، فلا يعتمد عليه كمرجع نهائي ويرجع "
               "دائما الى المصادر المعتمدة.")
FOOTER_RIGHTS = "جميع الحقوق محفوظة لمنصة معيار"


def footer():
    return '<footer class="m-foot">%s<strong>%s</strong></footer>' % (FOOTER_TEXT, FOOTER_RIGHTS)


SW_REGISTER = """<script>
if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js').catch(function(){});});}
</script>"""


def live_sw():
    """sw.js as currently published on origin/main (falls back to the repo root copy).
    CACHE must be bumped from the live value, not from this branch's copy."""
    import subprocess
    try:
        subprocess.run(["git", "-C", ROOT, "fetch", "-q", "origin", "main"], check=False, timeout=60,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        out = subprocess.run(["git", "-C", ROOT, "show", "origin/main:sw.js"], capture_output=True, timeout=30)
        if out.returncode == 0:
            return out.stdout.decode("utf-8"), "origin/main:sw.js"
    except Exception:
        pass
    return read(os.path.join(ROOT, "sw.js")), "sw.js (repo root)"


def base_files():
    """All files of the currently published site (repo root minus build dirs)."""
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel = os.path.relpath(dirpath, ROOT)
        top = rel.split(os.sep)[0]
        if top in BASE_EXCLUDE_DIRS:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in BASE_EXCLUDE_DIRS]
        for fn in filenames:
            p = os.path.normpath(os.path.join(rel, fn))
            out.append(p)
    return sorted(out)
