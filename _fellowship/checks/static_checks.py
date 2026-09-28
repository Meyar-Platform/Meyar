# -*- coding: utf-8 -*-
"""Static acceptance checks on the built output. Run after build_all_fellowship.py:
    python3 checks/static_checks.py
Writes checks/static_results.json, exits non-zero on any failure."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import HERE as FH, INPUTS, OUT, ROOT, load_json, md5, read  # noqa: E402

results = []


def rec(id_, name, ok, detail=None):
    results.append({"id": id_, "name": name, "pass": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + id_ + " " + name + (" :: " + json.dumps(detail, ensure_ascii=False)[:600] if detail is not None else ""))


S = load_json(os.path.join(INPUTS, "bizenv-structure.json"))
B = load_json(os.path.join(INPUTS, "bizenv-financial-management.json"))
E = load_json(os.path.join(INPUTS, "bizenv-past-exams.json"))
O = load_json(os.path.join(OUT, "data", "bizenv-outline.json"))
Q = load_json(os.path.join(OUT, "data", "bizenv-questions.json"))["questions"]
SUM = load_json(os.path.join(OUT, "data", "bizenv-summaries.json"))["summaries"]
state = load_json(os.path.join(FH, "_build_state.json"))

# ---- C0 counts (replaces checks 1, 2, 5) ----
bank, ex = B["questions"], E["questions"]
loaded_by_part = {p["id"]: p["counts"]["loaded"] for p in O["parts"]}
mcq_loaded = len(bank) + sum(1 for q in ex if not q.get("card_only"))
cards_loaded = sum(1 for q in ex if q.get("card_only"))
mf14 = [c for p in O["parts"] for c in p["chapters"] if c["id"] == "MF.C14"][0]
rec("C0", "الأعداد: 647 = 462 + 185 · الأجزاء 52 و69 و526 · 624 اختيارياً و23 بطاقة · MF.C14 تسعة مواضيع",
    len(bank) + len(ex) == 647 and len(bank) == 462 and len(ex) == 185 and loaded_by_part == {"IT": 52, "EC": 69, "MF": 526}
    and mcq_loaded == 624 and cards_loaded == 23 and [t["id"] for t in mf14["topics"]] == ["F1", "F2", "F3", "F4", "F5a", "F5b", "F6a", "F6b", "F6c"]
    and mf14["counts"]["loaded"] == 171 and mf14["counts"]["bank"] == 168,
    {"loaded": len(bank) + len(ex), "by_part": loaded_by_part, "mcq": mcq_loaded, "cards": cards_loaded,
     "mf14": {"topics": [t["id"] for t in mf14["topics"]], "loaded": mf14["counts"]["loaded"], "bank": mf14["counts"]["bank"]},
     "displayed_after_exclusion": O["totals"]})

# ---- 3 structure ----
same = True
for ps, po in zip(S["parts"], O["parts"]):
    same &= ps["id"] == po["id"] and ps["title"] == po["title"] and len(ps["chapters"]) == len(po["chapters"])
    for cs, co in zip(ps["chapters"], po["chapters"]):
        same &= cs["id"] == co["id"] and cs["title"] == co["title"] and cs["sections"] == [s["title"] for s in co["sections"]]
rec("3", "البنية 3 أجزاء و32 فصلاً و130 مبحثاً مطابقة لملف البنية", same and len(O["parts"]) == 3 and O["totals"]["chapters"] == 32 and O["totals"]["sections"] == 130,
    {"parts": len(O["parts"]), "chapters": O["totals"]["chapters"], "sections": O["totals"]["sections"]})

# ---- 4 topic order ----
order_struct = [t["id"] for t in sorted(S["topics"], key=lambda t: t["order"])]
order_out = [t["id"] for p in O["parts"] for c in p["chapters"] for t in c["topics"]]
bank_seq = []
for q in bank:
    if not bank_seq or bank_seq[-1] != q["t"]:
        bank_seq.append(q["t"])
rec("4", "ترتيب مواضيع الإدارة المالية مطابق لحقل order", order_out == order_struct == bank_seq, order_out)

# ---- 5 engine vs cards ----
eng = [q for q in Q if not q.get("card")]
rec("5", "لا سؤال بلا أربعة خيارات داخل محرك الاختبار، والبطاقات خارجه",
    all(len(q["o"]) == 4 and 0 <= q["a"] < 4 for q in eng) and all(q.get("card") for q in Q if not q["o"]),
    {"engine": len(eng), "cards": len(Q) - len(eng)})

# ---- 6 needs_owner excluded ----
no_ids = {q["id"] for q in ex if q.get("needs_owner") is True}
shown = {q["id"] for q in Q}
cnt_ok = O["totals"]["visible"] == len(Q) == 647 - len(no_ids)
rec("6", "17 سؤالاً needs_owner خارج الاختبار والبطاقات والعدّادات", len(no_ids) == 17 and not (no_ids & shown) and cnt_ok,
    {"needs_owner": sorted(no_ids), "visible": O["totals"]["visible"]})

# ---- 7 empty chapters in data ----
empty = [c["id"] for p in O["parts"] for c in p["chapters"] if c["empty"]]
rec("7s", "الفصول الفارغة الأربعة في البيانات بعدّاد صفر ولم يُحذف فصل", empty == ["MF.C2", "MF.C3", "MF.C10", "MF.C12"]
    and all(c["counts"]["visible"] == 0 for p in O["parts"] for c in p["chapters"] if c["empty"]), empty)

# ---- D7 MF.C13 counter ----
c13 = [c for p in O["parts"] for c in p["chapters"] if c["id"] == "MF.C13"][0]
rec("D7", "عدّاد MF.C13 من ملفات البيانات وحدها (4 أسئلة دورات، بلا أسئلة الرحلتين وبطاقاتهما)", c13["counts"]["visible"] == 4 and c13["counts"]["exam"] == 4 and c13["summary"]["href"] == "capital-structure.html", c13["counts"])

# ---- summaries ----
rec("S", "الملخصات: S-FA-FORMULAS فارغ من نوع text، و S-MF-C13 صفحة", SUM[0]["id"] == "S-FA-FORMULAS" and SUM[0]["kind"] == "text" and SUM[0]["body"] == ""
    and SUM[1] == {"id": "S-MF-C13", "chapter": "MF.C13", "title": "هيكل رأس المال", "kind": "page", "href": "capital-structure.html"}, SUM)

# ---- A1 isolation: repo-root published files unchanged ----
base = {}
for line in read(os.path.join(FH, "_baseline_md5.txt")).splitlines():
    h, p = line.split(None, 1)
    base[p.strip()] = h
changed = [p for p, h in base.items() if not os.path.exists(os.path.join(ROOT, p)) or md5(os.path.join(ROOT, p)) != h]
rec("A1", "لا ملف من الموقع المنشور (جذر المستودع) تغيّر، مقارنة بـ _baseline_md5.txt", not changed, {"files": len(base), "changed": changed})

# ---- A5 sw.js ----
sw = read(os.path.join(OUT, "sw.js"))
live = re.search(r"const CACHE = '([^']+)'", read(os.path.join(ROOT, "sw.js"))).group(1)
new = re.search(r"const CACHE = '([^']+)'", sw).group(1)
need = ["./fellowship.html", "./business-environment.html", "./capital-structure.html", "./access.js", "./private-sector.html",
        "./public-sector.html", "./data/bizenv-outline.json", "./data/bizenv-questions.json", "./data/bizenv-summaries.json", "./data/fellowship-subjects.json"]
num = lambda s: int(re.search(r"(\d+)$", s).group(1))  # noqa: E731
rec("A5", "CACHE مرفوع إصداراً واحداً، و ASSETS تشمل الصفحات الجديدة وبياناتها وصفحتي الإيقاف",
    num(new) == num(live) + 1 and all("'%s'" % a in sw for a in need), {"live": live, "new": new})

# ---- sitemap ----
sm = read(os.path.join(OUT, "sitemap.xml"))
rec("SM", "الخريطة فيها الصفحات الثلاث الجديدة وليس فيها صفحتا القطاعين",
    all(u in sm for u in ("fellowship.html", "business-environment.html", "capital-structure.html")) and "sector" not in sm)

# ---- 14 no references / internal fields in built pages and displayed data ----
pages = ["index.html", "fellowship.html", "business-environment.html", "capital-structure.html", "private-sector.html", "public-sector.html"]
page_ref = re.compile(r"صفحة\s*[0-9٠-٩]+|ص\s*\.\s*[0-9٠-٩]+|\bp\.\s*\d+|\bpage\s+\d+", re.I)
internal = re.compile(r"fix_note|source_note|owner_question|dup_with|needs_owner|suggest_topic|\"file\"")
hits = {}
for pg in pages + ["data/bizenv-questions.json", "data/bizenv-outline.json", "data/bizenv-summaries.json", "data/fellowship-subjects.json"]:
    txt = read(os.path.join(OUT, pg))
    h = page_ref.findall(txt) + internal.findall(txt)
    if h:
        hits[pg] = h[:5]
allowed_keys = {"id", "src", "ch", "sec", "t", "q", "o", "a", "e", "why", "card", "dup"}
bad_keys = sorted({k for q in Q for k in q} - allowed_keys)
# exam session names and source file names must not reach the browser
sources = [m["source"] for m in E["meta"]] + [m["exam"] for m in E["meta"]]
src_leak = [pg for pg in pages + ["data/bizenv-questions.json"] if any(s in read(os.path.join(OUT, pg)) for s in sources)]
rec("14", "لا رقم صفحة ولا إحالة لملف مصدر ولا حقل داخلي في الصفحات المبنية والبيانات المعروضة", not hits and not bad_keys and not src_leak,
    {"hits": hits, "bad_keys": bad_keys, "source_leak": src_leak})
# informational: the word "المصدر" used in displayed explanations to mean the original exam paper
word_src = sorted({q["id"] for q in Q for f in ("e",) if re.search(r"(ورد|وارد|واردة)\s+في\s+المصدر", q[f])}
                  | {q["id"] for q in Q if any(re.search(r"(ورد|وارد|واردة)\s+في\s+المصدر", w) for w in q.get("why") or [])})
results.append({"id": "14i", "name": "بنود تعليلها يقول \"ورد في المصدر\" بمعنى ورقة الاختبار الأصلية (للقرار)", "pass": True, "detail": word_src, "info": True})
print("INFO 14i", word_src)

# ---- 15 counters derived, no hand-written count in templates ----
tpl = "".join(read(os.path.join(FH, "templates", f)) for f in os.listdir(os.path.join(FH, "templates")))
tpl += read(os.path.join(FH, "build_paused.py"))
nums = ["647", "630", "624", "621", "526", "514", "462", "185", "171", "168", "130", "52", "69", "32"]
found = [n for n in nums if re.search(r"(?<![\d#.\-])%s(?![\d%%px])" % n, tpl)]
idx = read(os.path.join(OUT, "index.html"))
door = re.search(r'id="fellowshipCounters">([^<]*)<', idx).group(1)
rec("15", "كل عدد معروض مشتق من البيانات، ولا رقم عدّاد مكتوب في القوالب", not found and str(O["totals"]["visible"]) in door,
    {"numbers_in_templates": found, "door": door})

# ---- 17 / D6 fonts and tokens ----
font_ok, g_hits = True, []
for pg in ["index.html", "fellowship.html", "business-environment.html", "capital-structure.html", "private-sector.html", "public-sector.html"]:
    t = read(os.path.join(OUT, pg))
    if "fonts.googleapis" in t or "fonts.gstatic" in t:
        g_hits.append(pg)
    font_ok &= 'url("fonts/tajawal-arabic-500-normal.woff2")' in t and 'url("fonts/tajawal-arabic-700-normal.woff2")' in t
tok = state["tokens"]
rec("17", "Tajawal محلي في كل صفحة جديدة، والألوان مقروءة من ملفات المنصة", font_ok and not g_hits and tok["primary"] == "#364C63" and tok["gold"] == "#F0AE14" and tok["paper"] == "#EDF1F5",
    {"google": g_hits, "tokens": {k: tok[k] for k in ("primary", "gold", "paper")}, "sources": tok["_sources"]})

# ---- E2 style in text I wrote ----
authored = [os.path.join(FH, "templates", f) for f in os.listdir(os.path.join(FH, "templates"))] + \
           [os.path.join(FH, f) for f in ("common.py", "build_paused.py", "build_bizenv.py", "build_capital_structure.py", "build_fellowship.py")] + \
           [os.path.join(FH, "src", "access.js")]
style_hits = {}
for f in authored:
    t = read(f)
    h = re.findall(r"[«»]", t) + re.findall(r"[؀-ۿ]\s*[-–—]\s*[؀-ۿ]", t) + \
        re.findall(r"(?i)\b(?:claude|anthropic|chatgpt|openai|generated by|ai[- ]generated)\b|بالذكاء الاصطناعي", t)
    if h:
        style_hits[os.path.basename(f)] = h[:5]
rec("E2", "لا «» ولا شرطة داخل جملة عربية في النص الجديد، ولا ذكر لأداة أو ذكاء اصطناعي", not style_hits, style_hits)

# ---- no console.log in production ----
cl = [pg for pg in pages + ["access.js", "sw.js"] if "console.log" in read(os.path.join(OUT, pg))]
rec("CL", "لا console.log في الإنتاج", not cl, cl)

# ---- E1 static: storage keys referenced in code ----
keys = set()
for pg in pages + ["access.js"]:
    t = read(os.path.join(OUT, pg))
    keys |= set(re.findall(r"localStorage\.(?:get|set|remove)Item\('([^']+)'", t))
    keys |= set(re.findall(r'var K_\w+ = "([^"]+)"', t))
std = [pg for pg in ("private-sector.html", "public-sector.html", "index.html") if "localStorage" in read(os.path.join(OUT, pg))]
rec("E1s", "المفاتيح المكتوبة في الشيفرة من الجدول وحده، ولا تخزين في صفحات القطاعين والرئيسية",
    keys <= {"bizenv-subject-id", "bizenv-access", "bizenv-pending-signups", "bizenv-dock-cs", "bizenv-dock-rk"} and not std, {"keys": sorted(keys), "std": std})

with open(os.path.join(HERE, "static_results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
sys.exit(0 if all(r["pass"] for r in results) else 1)
