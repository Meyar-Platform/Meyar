# -*- coding: utf-8 -*-
"""build_paused.py, phase A: pause the two sectors and prepare publish_paused/.

prepare()  : copies the currently published site (repo root, i.e. the locked
             "restricted" state) into a clean publish_paused/, then writes the
             new home page and the two paused-sector pages.
finalize() : writes sw.js (CACHE +1, new assets) and sitemap.xml once every
             page and data file exists.
"""
import os
import re
import shutil

from common import (live_sw, OUT, ROOT, SW_REGISTER, base_files, brand_bar, footer, head, platform_tokens, read, write)

TODAY = "2026-09-28"
SITE = "https://meyarplatform.com/"

HOME_CSS = """
.h-hero{display:flex;flex-direction:column;align-items:center;text-align:center;gap:6px;padding:28px 0 18px}
.h-hero img{width:64px;height:64px}
.h-hero .ar{font-size:30px;font-weight:700;color:var(--primary);line-height:1.3}
.h-hero .en{font-size:15px;color:var(--muted);direction:ltr}
.h-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr));gap:12px;margin-top:8px}
.h-card{position:relative;display:flex;flex-direction:column;gap:4px;background:var(--card);border:1.5px solid var(--line);border-radius:16px;padding:18px 18px 16px;text-decoration:none;color:var(--ink);min-height:132px}
a.h-card:hover{border-color:var(--primary)}
a.h-card{border-color:var(--primary)}
.h-card .t{font-size:19px;font-weight:700;color:var(--heading);line-height:1.45}
.h-card .e{font-size:13.5px;color:var(--muted);direction:ltr;text-align:right}
.h-card .c{margin-top:auto;padding-top:10px;font-size:14px;color:var(--primary);font-weight:700}
.h-card.paused{opacity:.55;border-style:dashed;cursor:default}
.h-card.paused .stats{display:none}
.h-badge{align-self:flex-start;display:inline-flex;gap:6px;flex-wrap:wrap;font-size:12px;font-weight:700;color:var(--muted);background:var(--line);border-radius:999px;padding:2px 10px;margin-bottom:6px}
.h-badge .en{direction:ltr}
"""

PAUSED_CSS = """
.p-box{background:var(--card);border:1.5px solid var(--primary);border-radius:16px;max-width:520px;margin:40px auto 0;padding:36px 26px;text-align:center}
.p-box h1{margin:0 0 10px;font-size:25px;color:var(--heading)}
.p-box p{margin:0 0 20px;color:var(--muted);line-height:1.9}
"""


def home_html(t):
    return head("منصة معيار", t, HOME_CSS) + """<body>
<div class="m-wrap">
<header class="h-hero">
  <picture><source srcset="assets/logo-white.svg" media="(prefers-color-scheme: dark)"><img src="assets/logo.svg" alt="" width="64" height="64"></picture>
  <div class="ar">منصة معيار</div>
  <div class="en" lang="en">Meyar Platform</div>
</header>
<main class="h-grid">
  <div class="h-card paused" role="link" aria-disabled="true">
    <span class="h-badge"><span>متوقفة مؤقتاً</span><span class="en" lang="en">Temporarily paused</span></span>
    <span class="t">القطاع الخاص</span>
    <span class="e" lang="en">Private sector</span>
  </div>
  <div class="h-card paused" role="link" aria-disabled="true">
    <span class="h-badge"><span>متوقفة مؤقتاً</span><span class="en" lang="en">Temporarily paused</span></span>
    <span class="t">القطاع العام</span>
    <span class="e" lang="en">Public sector</span>
  </div>
  <a class="h-card" href="fellowship.html" id="doorFellowship">
    <span class="t">التحضير لزمالة SOCPA</span>
    <span class="e" lang="en">SOCPA fellowship preparation</span>
    <span class="c" id="fellowshipCounters"><!--FELLOWSHIP_COUNTERS--></span>
  </a>
</main>
""" + footer() + """
</div>
""" + SW_REGISTER + """
</body>
</html>
"""


def paused_html(t, title):
    return head(title + " | منصة معيار", t, PAUSED_CSS, noindex=True) + """<body>
<div class="m-wrap">
""" + brand_bar() + """
<main class="p-box">
  <h1>هذا القسم متوقف مؤقتاً</h1>
  <p>نعمل على تحديثه، وسيعود للعمل قريباً.</p>
  <a class="m-btn" href="index.html">العودة إلى الصفحة الرئيسية</a>
</main>
""" + footer() + """
</div>
""" + SW_REGISTER + """
</body>
</html>
"""


def notfound_html(t):
    return head("الصفحة غير موجودة | منصة معيار", t, PAUSED_CSS, noindex=True) + """<body>
<div class="m-wrap">
""" + brand_bar() + """
<main class="p-box">
  <h1>الصفحة غير موجودة</h1>
  <p>الرابط الذي فتحته غير موجود في المنصة.</p>
  <a class="m-btn" href="/index.html">العودة إلى الصفحة الرئيسية</a>
</main>
""" + footer() + """
</div>
</body>
</html>
"""


def prepare():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    copied = []
    for rel in base_files():
        dst = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(ROOT, rel), dst)
        copied.append(rel)
    t = platform_tokens()
    write(os.path.join(OUT, "index.html"), home_html(t))
    write(os.path.join(OUT, "private-sector.html"), paused_html(t, "القطاع الخاص"))
    write(os.path.join(OUT, "public-sector.html"), paused_html(t, "القطاع العام"))
    # 404 is served for any path, so its asset links must be absolute
    nf = notfound_html(t).replace('url("fonts/', 'url("/fonts/').replace('"assets/', '"/assets/').replace('"icons/', '"/icons/').replace('href="index.html"', 'href="/index.html"').replace('"manifest.webmanifest"', '"/manifest.webmanifest"')
    write(os.path.join(OUT, "404.html"), nf)
    # installed app opens on the new home instead of the paused private-sector page (owner decision)
    mpath = os.path.join(OUT, "manifest.webmanifest")
    man = read(mpath)
    assert '"start_url": "./private-sector.html?source=pwa"' in man
    write(mpath, man.replace('"start_url": "./private-sector.html?source=pwa"', '"start_url": "./index.html?source=pwa"'))
    return {"base_files": copied}


NEW_ASSETS = [
    "./public-sector.html",
    "./fellowship.html",
    "./business-environment.html",
    "./capital-structure.html",
    "./access.js",
    "./data/fellowship-subjects.json",
    "./data/bizenv-outline.json",
    "./data/bizenv-questions.json",
    "./data/bizenv-summaries.json",
    "./assets/logo-white.svg",
]


def finalize():
    sw, sw_src = live_sw()  # the live file, not memory
    m = re.search(r"const CACHE = '([\w-]*?)(\d+)';", sw)
    old = m.group(1) + m.group(2)
    new = m.group(1) + str(int(m.group(2)) + 1)
    sw = sw.replace(m.group(0), "const CACHE = '%s';" % new)
    am = re.search(r"const ASSETS = \[(.*?)\];", sw, re.S)
    existing = re.findall(r"'([^']+)'", am.group(1))
    assets = existing + [a for a in NEW_ASSETS if a not in existing]
    for a in assets:
        p = a[2:] or "index.html"
        assert os.path.exists(os.path.join(OUT, p)), a
    block = "const ASSETS = [\n" + ",\n".join("  '%s'" % a for a in assets) + "\n];"
    sw = sw.replace(am.group(0), block)
    write(os.path.join(OUT, "sw.js"), sw)

    urls = ["", "fellowship.html", "business-environment.html", "capital-structure.html"]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm += ["  <url>", "    <loc>%s%s</loc>" % (SITE, u), "    <lastmod>%s</lastmod>" % TODAY, "  </url>"]
    sm.append("</urlset>")
    write(os.path.join(OUT, "sitemap.xml"), "\n".join(sm) + "\n")
    return {"cache_src": sw_src, "cache_old": old, "cache_new": new, "assets": assets, "sitemap": [SITE + u for u in urls]}


if __name__ == "__main__":
    print(prepare())
