# -*- coding: utf-8 -*-
"""build_fellowship.py, the "التحضير لزمالة SOCPA" container page.

Reads  : publish_paused/data/bizenv-outline.json, templates/fellowship.template.html
Writes : publish_paused/data/fellowship-subjects.json (counters re-derived here)
         publish_paused/fellowship.html
         the fellowship door counters inside publish_paused/index.html
Adding a subject later means adding one entry to SUBJECTS and building its page;
the container page itself does not change.
"""
import os
from collections import OrderedDict

from common import (DATA_OUT, OUT, SW_REGISTER, TEMPLATES, brand_bar, dump_json, footer, head, load_json,
                    platform_tokens, read, write)

SUBJECTS = [
    OrderedDict([("id", "business-environment"), ("title", "بيئة الأعمال"), ("status", "active"),
                 ("href", "business-environment.html"), ("gate", True), ("outline", "bizenv-outline.json")]),
]

CSS = """
.f-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,260px),1fr));gap:12px}
.f-card{display:flex;flex-direction:column;gap:6px;background:var(--card);border:1.5px solid var(--primary);border-radius:16px;padding:18px;text-decoration:none;color:var(--ink);min-height:112px}
a.f-card:hover{background:var(--primary-soft)}
.f-card .t{font-size:20px;font-weight:700;color:var(--heading)}
.f-card .c{margin-top:auto;font-size:14.5px;color:var(--primary);font-weight:700}
.f-card.soon{opacity:.55;border-style:dashed;border-color:var(--line);cursor:default}
.f-badge{align-self:flex-start;font-size:12px;font-weight:700;color:var(--muted);background:var(--line);border-radius:999px;padding:2px 10px}
"""


def ar_count(n, w):
    """Arabic counted noun: one, two, 3 to 10, and 11 or more (or zero)."""
    if n == 1:
        return w[0]
    if n == 2:
        return w[1]
    if 3 <= n <= 10:
        return "%d %s" % (n, w[2])
    return "%d %s" % (n, w[3])


def build():
    subjects = []
    total_q = 0
    for s in SUBJECTS:
        rec = OrderedDict((k, v) for k, v in s.items() if k != "outline")
        if s["status"] == "active":
            o = load_json(os.path.join(DATA_OUT, s["outline"]))
            rec["counters"] = OrderedDict([("parts", o["totals"]["parts"]), ("chapters", o["totals"]["chapters"]),
                                           ("questions", o["totals"]["visible"])])
            total_q += o["totals"]["visible"]
        else:
            rec["counters"] = {}
        subjects.append(rec)
    dump_json(os.path.join(DATA_OUT, "fellowship-subjects.json"), subjects, pretty=True)

    t = platform_tokens()
    page = read(os.path.join(TEMPLATES, "fellowship.template.html"))
    page = (page.replace("%%HEAD%%", head("التحضير لزمالة SOCPA | منصة معيار", t, CSS))
                .replace("%%BRAND%%", brand_bar())
                .replace("%%FOOTER%%", footer())
                .replace("%%SW%%", SW_REGISTER))
    assert "%%" not in page
    write(os.path.join(OUT, "fellowship.html"), page)

    # door counters on the home page, derived from the same data
    n_active = sum(1 for s in subjects if s["status"] == "active")
    counter_text = "%s · %s" % (ar_count(n_active, ("مادة واحدة", "مادتان", "مواد", "مادة")),
                                ar_count(total_q, ("سؤال واحد", "سؤالان", "أسئلة", "سؤالاً")))
    idx_path = os.path.join(OUT, "index.html")
    idx = read(idx_path)
    assert "<!--FELLOWSHIP_COUNTERS-->" in idx
    write(idx_path, idx.replace("<!--FELLOWSHIP_COUNTERS-->", counter_text))
    return {"subjects": subjects, "door_counters": counter_text}


if __name__ == "__main__":
    import json
    print(json.dumps(build(), ensure_ascii=False, indent=1))
