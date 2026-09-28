# -*- coding: utf-8 -*-
"""build_capital_structure.py, the "هيكل رأس المال" page (summary of MF.C13).

Merges the two interactive journeys, unchanged in content, into one page with
four tabs:
  1 determinants  محددات اختيار هيكل رأس المال   journey 1 (cs-)
  2 theories      نظريات هيكل رأس المال           journey 1 (cs-)
  3 risk-types    أنواع مخاطر الاستثمار           journey 2 (rk-)
  4 leverage      الرافعة التشغيلية والرافعة المالية journey 2 (rk-)

The two source files are read, never modified. Every transformation lives here
so the page can be rebuilt at any time:
  * ids prefixed cs-/rk- in HTML (id, for, href="#..."), CSS (#...) and JS
    (the $ helper now resolves PFX+id inside the journey root, template ids,
    SVG gradient ids);
  * each script wrapped in its own closure with $ bound to root.querySelector;
  * each stylesheet scoped under .lesson-cs / .lesson-rk, :root variables moved
    to that root, keyframes prefixed;
  * Google Fonts removed, local Tajawal used;
  * localStorage keys renamed to bizenv-dock-cs / bizenv-dock-rk.
"""
import os
import re

from common import (FONT_STACK, INPUTS, OUT, SW_REGISTER, brand_bar, footer, head, platform_tokens, read, write)

TABS = [
    ("determinants", "محددات اختيار هيكل رأس المال", "cs"),
    ("theories", "نظريات هيكل رأس المال", "cs"),
    ("risk-types", "أنواع مخاطر الاستثمار", "rk"),
    ("leverage", "الرافعة التشغيلية والرافعة المالية", "rk"),
]

LESSONS = {
    "cs": {
        "file": "lesson-capital-structure.html",
        "old_dock_key": "cs-dock-off", "new_dock_key": "bizenv-dock-cs",
        "tabs": {"determinants": ["s0", "s1", "s7", "@s8-eval"], "theories": ["@crowd", "s3", "s4", "s5", "s6", "s8", "s9", "s10"]},
        "lead_tab": "determinants",
    },
    "rk": {
        "file": "lesson-risk-leverage.html",
        "old_dock_key": "rk-dock-off", "new_dock_key": "bizenv-dock-rk",
        "tabs": {"risk-types": ["@crowd", "s0", "s1", "s3"], "leverage": ["s4", "s5", "s6", "s8", "s9", "s10"]},
        "lead_tab": "risk-types",
    },
}

EVAL_GROUP_RE = re.compile(
    r'<h4[^>]*>تقييم الهيكل التمويلي</h4>\s*<div class="eqlist">(?:\s*<div class="formula[^"]*">.*?</div>)+\s*</div>', re.S)

LOCAL_SVG_FONT = "Tajawal Latin, Tajawal Arabic, sans-serif"


# ---------------------------------------------------------------------------
# CSS scoping
# ---------------------------------------------------------------------------
def _strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _split_blocks(css):
    """Yield (prelude, body) for each top-level block, body without braces."""
    i, n = 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j == -1:
            break
        prelude = css[i:j].strip()
        depth, k = 1, j + 1
        while depth and k < n:
            if css[k] == "{":
                depth += 1
            elif css[k] == "}":
                depth -= 1
            k += 1
        yield prelude, css[j + 1:k - 1]
        i = k


def _scope_selector(sel, root, pfx):
    sel = sel.strip()
    sel = re.sub(r"#([A-Za-z_][\w-]*)", lambda m: "#" + pfx + m.group(1), sel)
    if sel == ":root":
        return root
    if sel.startswith(":root"):
        return sel + " " + root
    if sel in ("html", "body"):
        return root
    if sel.startswith("body ") or sel.startswith("html "):
        return root + sel[4:]
    if sel == "*":
        return root + "," + root + " *"
    return root + " " + sel


def scope_css(css, root, pfx, keyframes):
    out = []
    for prelude, body in _split_blocks(_strip_comments(css)):
        if prelude.startswith("@media") or prelude.startswith("@supports"):
            out.append(prelude + "{" + scope_css(body, root, pfx, keyframes) + "}")
        elif prelude.startswith("@keyframes"):
            name = prelude.split()[1]
            out.append("@keyframes " + pfx + name + "{" + body + "}")
        else:
            sels = ",".join(_scope_selector(s, root, pfx) for s in prelude.split(","))
            body = _rename_animations(body, pfx, keyframes)
            body = body.replace('"Tajawal","Noto Sans Arabic"', FONT_STACK + ',"Noto Sans Arabic"')
            out.append(sels + "{" + body.strip() + "}")
    return "\n".join(out)


def _rename_animations(body, pfx, keyframes):
    def fix(m):
        val = m.group(2)
        for k in keyframes:
            val = re.sub(r"\b%s\b" % k, pfx + k, val)
        return m.group(1) + val
    return re.sub(r"(animation(?:-name)?\s*:)([^;}]*)", fix, body)


# ---------------------------------------------------------------------------
# HTML / JS transforms
# ---------------------------------------------------------------------------
def section_tab_map():
    m = {}
    for key, L in LESSONS.items():
        for tab, items in L["tabs"].items():
            for it in items:
                if not it.startswith("@"):
                    m[(key, it)] = tab
    return m


SEC_TAB = section_tab_map()


def rename_html_ids(frag, key):
    pfx = key + "-"
    frag = re.sub(r'\bid="([^"$]+)"', lambda m: 'id="%s%s"' % (pfx, m.group(1)), frag)
    frag = re.sub(r'\bfor="([^"$]+)"', lambda m: 'for="%s%s"' % (pfx, m.group(1)), frag)

    def href(m):
        target = m.group(1)
        tab = SEC_TAB.get((key, target))
        if tab:
            return 'href="#%s/%s%s"' % (tab, pfx, target)
        return 'href="#%s%s"' % (pfx, target)
    frag = re.sub(r'href="#([^"$]+)"', href, frag)
    return frag


def transform_js(js, key, L):
    pfx = key + "-"
    root_sel = ".lesson-" + key

    def must(old, new, count=None):
        nonlocal js
        c = js.count(old)
        assert c and (count is None or c == count), (key, old, c)
        js = js.replace(old, new)

    must("const $=id=>document.getElementById(id);", "const $=id=>root.querySelector('#'+PFX+id);", 1)
    must("getComputedStyle(document.documentElement)", "getComputedStyle(root)", 1)
    must("document.querySelectorAll(", "root.querySelectorAll(")
    must("'g'+(++gid)", "PFX+'g'+(++gid)", 1)
    must("showDock(e.target.id)", "showDock(e.target.id.slice(PFX.length))", 1)
    must("'%s'" % L["old_dock_key"], "'%s'" % L["new_dock_key"], 2)
    must('font-family="Tajawal,sans-serif"', 'font-family="%s"' % LOCAL_SVG_FONT)
    # ids written inside template strings
    js = re.sub(r'\bid="([A-Za-z][\w-]*)"', lambda m: 'id="%s%s"' % (pfx, m.group(1)), js)
    # in-page anchors written from JS (e.g. #card-SYS); section anchors become tab routes
    js = re.sub(r'href="#([A-Za-z][\w-]*)"', lambda m: rename_html_ids('href="#%s"' % m.group(1), key), js)
    # redraw hook for hidden tabs, inside the journey closure so it can reach draw/drawMix
    end = js.rstrip()
    assert end.endswith("})();"), key
    hook = ("\n  root.__redraw=function(){try{drawMix();}catch(e){}try{draw();}catch(e){}};\n"
            "  root.__ready=true;\n")
    end = end[: -len("})();")] + hook + "})();"
    return ("(function(){\nconst root=document.querySelector('%s');\nconst PFX='%s';\nif(!root)return;\n%s\n})();"
            % (root_sel, pfx, end))


def parse_lesson(key):
    L = LESSONS[key]
    src = read(os.path.join(INPUTS, L["file"]))
    css = re.findall(r"<style>(.*?)</style>", src, re.S)[-1]
    keyframes = sorted(set(re.findall(r"@keyframes (\w+)", css)))
    js = re.findall(r"<script>(.*?)</script>", src, re.S)[-1]
    header = re.search(r'<header class="header">(.*?)</header>', src, re.S).group(1)
    lead = re.search(r'<p class="lead">.*?</p>', header, re.S).group(0)
    crowd = re.search(r'<div class="crowd" id="crowd"></div>', header).group(0)
    nav = re.search(r'<nav class="nav".*?</nav>', src, re.S).group(0)
    sections = dict(re.findall(r'(?s)<section id="(s\d+)">.*?</section>', src) and
                    [(m.group(1), m.group(0)) for m in re.finditer(r'<section id="(s\d+)">.*?</section>', src, re.S)])
    foot = re.search(r"<footer.*?</footer>", src, re.S).group(0)
    dock = re.search(r'<div id="dock" hidden>.*?</div></div>', src, re.S).group(0)
    return {"src": src, "css": css, "keyframes": keyframes, "js": js, "lead": lead, "crowd": crowd, "nav": nav,
            "sections": sections, "footer": foot, "dock": dock}


PAGE_CSS = """
.m-wrap.cs-page{max-width:1400px}
.cs-tabs{position:sticky;top:0;z-index:20;background:var(--paper);display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;
  padding:8px 0;border-bottom:1.5px solid var(--line);margin-bottom:6px}
.cs-tabs::-webkit-scrollbar{display:none}
.cs-tabs [role=tab]{flex:0 0 auto;font:inherit;font-weight:700;font-size:15px;padding:8px 14px;border-radius:999px;border:1.5px solid var(--line);
  background:var(--card);color:var(--ink);cursor:pointer;white-space:nowrap;min-height:44px}
.cs-tabs [role=tab][aria-selected=true]{background:var(--primary);border-color:var(--primary);color:var(--on-primary)}
.cs-tabs [role=tab]:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.cs-tabs [role=tab] .n{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--gold);color:#1C2733;font-size:12px;margin-inline-end:6px}
.lesson-cs .nav,.lesson-rk .nav{top:var(--tabs-h,60px)}
.lesson-cs section,.lesson-rk section{scroll-margin-top:calc(var(--tabs-h,60px) + 64px)}
.lesson-cs .wrap,.lesson-rk .wrap{padding-inline:0;padding-block:0 120px}
.lesson-cs .cs-lead,.lesson-rk .cs-lead{padding-block:18px 4px}
.lesson-cs .cs-crowd,.lesson-rk .cs-crowd{padding-block:18px 0}
.lesson-cs .cs-crowd .crowd,.lesson-rk .cs-crowd .crowd{display:flex;flex-wrap:wrap;gap:4px;align-items:flex-end;justify-content:center}
.lesson-cs .cs-crowd .crowd .ch,.lesson-rk .cs-crowd .crowd .ch{width:clamp(34px,9vw,46px)!important}
.cs-evalq{padding-block:32px 8px;scroll-margin-top:calc(var(--tabs-h,60px) + 64px)}
.cs-lessonfoot{margin-top:14px;font-size:13.5px;color:var(--muted);line-height:1.8}
.cs-lessonfoot footer{margin-top:0!important}
"""

ROUTER_JS = r"""
<script>
(function(){
  "use strict";
  var TABS=%(tabs)s;
  var list=document.querySelector('.cs-tabs');
  var btns=[].slice.call(list.querySelectorAll('[role=tab]'));
  var drawn={};
  function setTabsH(){document.documentElement.style.setProperty('--tabs-h',list.offsetHeight+'px');}
  function lessonOf(id){for(var i=0;i<TABS.length;i++)if(TABS[i][0]===id)return TABS[i][1];return null;}
  function redraw(key){var r=document.querySelector('.lesson-'+key);if(r&&r.__redraw)r.__redraw();}
  function activate(id,opt){
    opt=opt||{};
    if(!lessonOf(id))id=TABS[0][0];
    btns.forEach(function(b){var on=b.dataset.tab===id;b.setAttribute('aria-selected',on?'true':'false');b.tabIndex=on?0:-1;
      document.getElementById('panel-'+b.dataset.tab).hidden=!on;});
    ['cs','rk'].forEach(function(k){var r=document.querySelector('.lesson-'+k);r.hidden=lessonOf(id)!==k;});
    if(!drawn[id]){drawn[id]=true;}
    redraw(lessonOf(id));
    setTabsH();
    if(opt.focus){var b=document.getElementById('tab-'+id);if(b)b.focus();}
    var t=opt.target?document.getElementById(opt.target):null;
    if(t&&!document.getElementById('panel-'+id).contains(t))t=null;
    if(t){t.scrollIntoView({block:'start'});}
    else if(opt.scroll){window.scrollTo({top:Math.max(0,list.offsetTop-4)});}
  }
  function parse(h){
    h=(h||'').replace(/^#/,'');
    if(!h)return null;
    var parts=h.split('/');
    if(lessonOf(parts[0]))return {tab:parts[0],target:parts[1]||null};
    var el=document.getElementById(h);
    if(el){var p=el.closest('[role=tabpanel]');if(p)return {tab:p.id.replace('panel-',''),target:h};}
    return null;
  }
  function fromHash(scroll){var r=parse(location.hash);if(r)activate(r.tab,{target:r.target,scroll:scroll&&!r.target});else if(!location.hash)activate(TABS[0][0]);}
  btns.forEach(function(b){b.addEventListener('click',function(){history.pushState(null,'','#'+b.dataset.tab);activate(b.dataset.tab,{scroll:true});});});
  list.addEventListener('keydown',function(e){
    var i=btns.indexOf(document.activeElement);if(i<0)return;var n=null;
    if(e.key==='ArrowLeft')n=(i+1)%%btns.length;else if(e.key==='ArrowRight')n=(i-1+btns.length)%%btns.length;
    else if(e.key==='Home')n=0;else if(e.key==='End')n=btns.length-1;
    if(n===null)return;e.preventDefault();var id=btns[n].dataset.tab;history.replaceState(null,'','#'+id);activate(id,{focus:true});
  });
  document.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('a[href^="#"]');if(!a)return;
    var r=parse(a.getAttribute('href'));if(!r)return;
    e.preventDefault();history.pushState(null,'',a.getAttribute('href'));activate(r.tab,{target:r.target,scroll:!r.target});
  });
  window.addEventListener('popstate',function(){fromHash(false);});
  window.addEventListener('hashchange',function(){fromHash(false);});
  var rt=null;window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(function(){setTabsH();var s=btns.filter(function(b){return b.getAttribute('aria-selected')==='true';})[0];if(s)redraw(lessonOf(s.dataset.tab));},150);});
  window.ensureAccess('capital-structure').then(function(ok){
    if(!ok)return;
    document.getElementById('csMain').hidden=false;
    setTabsH();
    fromHash(false);
  });
})();
</script>
"""


def build():
    t = platform_tokens()
    parsed = {k: parse_lesson(k) for k in LESSONS}
    report = {"sections": {}, "eval_group_moved": False}

    # journey 1: split the "تقييم الهيكل التمويلي" group out of s8
    cs = parsed["cs"]
    m = EVAL_GROUP_RE.search(cs["sections"]["s8"])
    assert m, "evaluation group not found in s8"
    group = m.group(0)
    cs["sections"]["s8"] = cs["sections"]["s8"].replace(group, "", 1)
    report["eval_group_moved"] = True
    eval_block = ('<div class="cs-evalq" id="s8-eval"><div class="card">%s</div></div>' % group)

    panels_html = {}
    styles, scripts, lesson_blocks = [], [], []
    for key, L in LESSONS.items():
        P = parsed[key]
        root = ".lesson-" + key
        styles.append(scope_css(P["css"], root, key + "-", P["keyframes"]))
        scripts.append(transform_js(P["js"], key, L))
        for tab, items in L["tabs"].items():
            parts = []
            if tab == L["lead_tab"]:
                parts.append('<div class="cs-lead">%s</div>' % P["lead"])
            for it in items:
                if it == "@crowd":
                    parts.append('<div class="cs-crowd">%s</div>' % P["crowd"])
                elif it == "@s8-eval":
                    parts.append(eval_block)
                else:
                    parts.append(P["sections"][it])
            panels_html[tab] = rename_html_ids("\n".join(parts), key)
        used = [it for items in L["tabs"].values() for it in items if not it.startswith("@")]
        assert sorted(used) == sorted(P["sections"]), (key, used, list(P["sections"]))
        report["sections"][key] = used

    tablist = '<div class="cs-tabs" role="tablist" aria-label="هيكل رأس المال">%s</div>' % "".join(
        '<button type="button" role="tab" id="tab-%s" data-tab="%s" aria-controls="panel-%s" aria-selected="%s" tabindex="%d"><span class="n">%d</span>%s</button>'
        % (tid, tid, tid, "true" if i == 0 else "false", 0 if i == 0 else -1, i + 1, label)
        for i, (tid, label, _) in enumerate(TABS))

    for key, L in LESSONS.items():
        P = parsed[key]
        tabs_of = [tid for tid, _, k in TABS if k == key]
        panels = "".join('<div role="tabpanel" id="panel-%s" aria-labelledby="tab-%s" tabindex="0"%s>%s</div>'
                         % (tid, tid, "" if tid == TABS[0][0] else " hidden", panels_html[tid]) for tid in tabs_of)
        nav = rename_html_ids(P["nav"], key)
        dock = rename_html_ids(P["dock"], key)
        lesson_blocks.append('<div class="lesson-%s"%s><div class="wrap">%s%s</div>%s</div>'
                             % (key, "" if key == "cs" else " hidden", nav, panels, dock))

    lesson_footer = parsed["cs"]["footer"]
    assert lesson_footer == parsed["rk"]["footer"]

    body = """<body>
<div class="m-wrap cs-page">
%(brand)s
<h1 class="m-title">هيكل رأس المال</h1>
<main id="csMain" hidden>
%(tablist)s
%(lessons)s
</main>
%(footer)s
<div class="cs-lessonfoot">%(lessonfoot)s</div>
</div>
<script src="access.js"></script>
%(scripts)s
%(router)s
%(sw)s
</body>
</html>
""" % {
        "brand": brand_bar("business-environment.html#/c/MF.C13", "بيئة الأعمال"),
        "tablist": tablist,
        "lessons": "\n".join(lesson_blocks),
        "footer": footer(),
        "lessonfoot": lesson_footer,
        "scripts": "\n".join("<script>\n%s\n</script>" % s for s in scripts),
        "router": ROUTER_JS % {"tabs": "[%s]" % ",".join('["%s","%s"]' % (tid, k) for tid, _, k in TABS)},
        "sw": SW_REGISTER,
    }
    extra = "\n".join(styles) + "\n" + PAGE_CSS  # page rules last so they win ties
    page = head("هيكل رأس المال | منصة معيار", t, extra) + body
    for bad in ("fonts.googleapis.com", "fonts.gstatic.com"):
        assert bad not in page, bad
    write(os.path.join(OUT, "capital-structure.html"), page)
    report["bytes"] = len(page.encode("utf-8"))
    return report


if __name__ == "__main__":
    import json
    print(json.dumps(build(), ensure_ascii=False, indent=1))
