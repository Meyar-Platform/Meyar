# -*- coding: utf-8 -*-
"""build_bizenv.py, the "بيئة الأعمال" subject.

Reads  : inputs/bizenv-structure.json            (structure, the only reference)
         inputs/bizenv-financial-management.json (bank, 18 topics, 462 questions)
         inputs/bizenv-past-exams.json           (past exams, v2, 185 questions)
         summaries defined below (S-FA-FORMULAS empty, S-MF-C13 page)
         templates/business-environment.template.html
Writes : publish_paused/business-environment.html
         publish_paused/access.js
         publish_paused/data/bizenv-outline.json    (structure and counters, read without the gate)
         publish_paused/data/bizenv-questions.json  (questions, after the gate)
         publish_paused/data/bizenv-summaries.json  (summaries, after the gate)
Returns a report dict used by build_all_fellowship.py.
"""
import html
import os
import shutil
from collections import Counter, OrderedDict

from common import (DATA_OUT, INPUTS, OUT, SRC, SW_REGISTER, TEMPLATES, brand_bar, dump_json, footer, head,
                    load_json, platform_tokens, read, write)

# Question fields that may reach the browser. Everything else (file, source_note,
# fix_note, owner_question, dup_with, note, fixed, axis, kind, ...) stays internal.
PUBLIC_EXAM_FIELDS = ("q", "o", "a", "e", "why")

# Owner decision (28 Sep 2026): drop every item whose explanation says the option or
# data "ورد / غير وارد في المصدر". Removed from the build only; the input file is untouched.
OWNER_EXCLUDED = ["P1-14", "P1-42", "P1-44", "P1-45", "P2-28", "P2-51"]

SUMMARIES = [
    # S-FA-FORMULAS removed by owner decision (28 Sep 2026): no formulas summary.
    OrderedDict([("id", "S-MF-C13"), ("chapter", "MF.C13"), ("title", "هيكل رأس المال"),
                 ("kind", "page"), ("href", "capital-structure.html")]),
]

# §6 of the fellowship prompt: MF.C8 points to tab 1 of the capital structure page.
PAGE_REFS = {
    "MF.C8": [
        {"section": "هيكل التمويل وهيكل رأس المال", "href": "capital-structure.html#determinants",
         "text": "انظر صفحة هيكل رأس المال، التبويب الأول"},
        {"section": "تقييم الهيكل التمويلي", "href": "capital-structure.html#determinants",
         "text": "انظر صفحة هيكل رأس المال، التبويب الأول"},
    ]
}

EXTRA_CSS = """
.b-panel,.b-card{background:var(--card);border:1.5px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.b-panel h3{margin:0 0 4px;font-size:17px}
.b-meta{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;font-size:13.5px;color:var(--muted)}
.b-tag{font-size:12px;font-weight:700;color:var(--primary);background:var(--primary-soft);padding:2px 9px;border-radius:6px;white-space:nowrap}
.b-bar{height:6px;background:var(--line);border-radius:4px;overflow:hidden;margin:6px 0 14px}
.b-bar i{display:block;height:100%;background:var(--primary);width:0;transition:width .25s}
.b-nums{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:10px 0 4px}
.b-nums>div{background:var(--paper);border-radius:10px;padding:8px 6px;text-align:center}
.b-nums .k{font-size:12px;color:var(--muted);font-weight:700}
.b-nums .v{font-size:20px;font-weight:700}
.b-row{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}
.b-row .m-btn{flex:1 1 0;min-width:0}
.b-msg{font-size:13px;color:var(--muted);margin-top:8px;line-height:1.7}
#xfer textarea{width:100%;min-height:78px;font:inherit;font-size:12.5px;border:1.5px solid var(--line);border-radius:10px;padding:8px;background:var(--paper);color:var(--ink);direction:ltr;margin-top:10px}
.b-part{margin-top:22px}
.b-part>h2{font-size:21px;margin:0 0 2px;color:var(--heading)}
.b-part>.b-meta{margin-bottom:10px}
.b-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:10px}
.m-card{display:block;width:100%;text-align:right;font:inherit;color:inherit;background:var(--card);border:1.5px solid var(--line);border-radius:14px;padding:14px 16px}
button.m-card{cursor:pointer}
button.m-card:hover{border-color:var(--primary)}
.b-ch h3{margin:2px 0 4px;font-size:17px;line-height:1.5}
.b-chn{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--muted);font-weight:700}
.b-ch .b-st{margin-inline-start:auto}
.b-secs{font-size:13px;color:var(--muted);line-height:1.7;margin-top:6px}
.b-ch.off{opacity:.55;background:transparent;border-style:dashed;cursor:default}
.b-ch.off .b-ref{opacity:1}
.b-soon{font-size:14px;color:var(--muted);margin-bottom:2px}
.b-ref{font-size:13.5px;margin-top:6px;color:var(--ink)}
.b-back{background:none;border:none;color:var(--primary);font:inherit;font-weight:700;font-size:15px;padding:6px 0;cursor:pointer;min-height:44px}
.b-eyebrow{font-size:13px;color:var(--muted);font-weight:700}
.b-chtitle{font-size:clamp(21px,4.6vw,26px);margin:2px 0 14px;line-height:1.4;color:var(--heading)}
.b-block{margin-top:14px;padding-top:14px;border-top:1.5px solid var(--line)}
.b-block h3{margin:0 0 8px;font-size:17px}
.b-bh{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}
.b-bh h3{margin:0}
.b-seclist{margin:0;padding-inline-start:22px;font-size:15px}
.b-seclist li{margin-bottom:6px}
.b-seclist .b-n{font-size:12px;color:var(--muted);margin-inline-start:8px;font-weight:700}
.b-unit{margin-bottom:10px}
.b-unit h4{margin:0 0 4px;font-size:16.5px;display:flex;align-items:center;gap:8px}
.b-unit .b-row{margin-top:10px}
.b-unit.isdone{border-color:var(--ok);background:var(--ok-soft)}
.b-st{font-size:12px;font-weight:700;padding:2px 9px;border-radius:999px;white-space:nowrap;margin-inline-start:auto;background:var(--line);color:var(--muted)}
.b-st.mid{background:var(--gold);color:#1C2733}
.b-st.done{background:var(--ok);color:#fff}
.b-badge{display:inline-block;font-size:12px;font-weight:700;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:1px 10px;margin-bottom:6px}
.b-q{font-size:18px;margin:4px 0 14px;line-height:1.8;white-space:pre-line}
.b-opts{display:flex;flex-direction:column;gap:9px}
.b-opt{text-align:right;border:1.5px solid var(--line);background:var(--card);color:var(--ink);border-radius:10px;padding:11px 14px;font:inherit;font-weight:500;cursor:pointer;line-height:1.6;display:flex;gap:10px;align-items:flex-start;min-height:44px}
.b-opt .k{flex:0 0 24px;height:24px;border-radius:50%;border:1.5px solid var(--line);font-size:13px;display:inline-flex;align-items:center;justify-content:center;margin-top:2px;font-weight:700}
.b-opt .t{flex:1;min-width:0}
.b-opt .why{display:block;font-size:13.5px;color:var(--muted);margin-top:4px;line-height:1.65}
.b-opt:not([disabled]):hover{border-color:var(--primary)}
.b-opt:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.b-opt.ok{border-color:var(--ok);background:var(--ok-soft)}
.b-opt.ok .k{background:var(--ok);color:#fff;border-color:var(--ok)}
.b-opt.bad{border-color:var(--bad);background:var(--bad-soft)}
.b-opt.bad .k{background:var(--bad);color:#fff;border-color:var(--bad)}
.b-opt[disabled]{cursor:default}
.b-exp{margin-top:14px;padding:12px 14px;border-radius:10px;background:var(--paper);border-right:4px solid var(--ok);font-size:15.5px;line-height:1.8;display:none;white-space:pre-line}
.b-exp.show{display:block}
.b-exp.wrong{border-right-color:var(--bad)}
.b-score{font-size:40px;line-height:1.2;color:var(--primary);margin:4px 0;font-weight:700}
.b-sub{color:var(--muted)}
.b-restitle{margin:0;font-size:19px}
.b-yours{color:var(--bad)}
.b-right{color:var(--ok)}
.b-cards{display:flex;flex-direction:column;gap:10px;margin-top:12px}
.b-flash{display:block;width:100%;text-align:right;font:inherit;color:var(--ink);background:var(--card);border:1.5px solid var(--line);border-radius:14px;padding:14px 16px;cursor:pointer}
.b-flash .fq{font-weight:700;white-space:pre-line}
.b-flash .fa{margin-top:10px;padding-top:10px;border-top:1px dashed var(--line);font-size:15.5px;white-space:pre-line;line-height:1.8}
.b-flash .fh{font-size:12.5px;color:var(--muted);margin-top:8px}
.b-flash[aria-expanded="true"]{border-color:var(--primary)}
.frac{display:inline-flex;flex-direction:column;text-align:center;vertical-align:-0.45em;margin:0 .25em;line-height:1.35}
.frac .num{padding:0 .45em .12em}
.frac .den{padding:.12em .45em 0;border-top:1.5px solid currentColor}
@media (prefers-reduced-motion: reduce){.b-bar i{transition:none}}
"""


def esc_text(s):
    """Past-exam texts are plain text; escape them so the page can render every
    field with innerHTML (bank fields already carry <span class="frac"> markup)."""
    return html.escape(s, quote=False)


def build():
    S = load_json(os.path.join(INPUTS, "bizenv-structure.json"))
    B = load_json(os.path.join(INPUTS, "bizenv-financial-management.json"))
    E = load_json(os.path.join(INPUTS, "bizenv-past-exams.json"))
    bank, exams = B["questions"], E["questions"]
    topics = {t["id"]: t for t in S["topics"]}
    bank_topics = {t["id"]: t for t in B["topics"]}
    report = {"loaded_bank": len(bank), "loaded_exam": len(exams), "loaded_total": len(bank) + len(exams)}

    # ---- sanity: structure topics agree with the bank file ----
    assert [t["id"] for t in sorted(S["topics"], key=lambda t: t["order"])] == [t["id"] for t in B["topics"]], "topic order differs"
    for tid, t in bank_topics.items():
        assert topics[tid]["chapter"] == t["chapter"] and topics[tid]["section"] == t["section"], tid

    chapters = {c["id"]: c for p in S["parts"] for c in p["chapters"]}
    chapter_part = {c["id"]: p["id"] for p in S["parts"] for c in p["chapters"]}

    # ---- questions ----
    out_q = []
    excluded = []
    owner_dropped = []
    for q in bank:
        t = topics[q["t"]]
        assert len(q["o"]) == 4 and 0 <= q["a"] < 4
        out_q.append(OrderedDict([("id", q["id"]), ("src", "bank"), ("ch", t["chapter"]), ("sec", t["section"]),
                                  ("t", q["t"]), ("q", q["q"]), ("o", q["o"]), ("a", q["a"]), ("e", q["e"])]))
    for q in exams:
        if q.get("needs_owner") is True:
            excluded.append(q["id"])
            continue
        if q["id"] in OWNER_EXCLUDED:
            owner_dropped.append(q["id"])
            continue
        assert q["chapter"] in chapters and q["section"] in chapters[q["chapter"]]["sections"], q["id"]
        rec = OrderedDict([("id", q["id"]), ("src", "exam"), ("ch", q["chapter"]), ("sec", q["section"]), ("t", None)])
        rec["q"] = esc_text(q["q"])
        rec["o"] = [esc_text(x) for x in q["o"]]
        rec["a"] = q["a"]
        rec["e"] = esc_text(q["e"])
        if q.get("why"):
            rec["why"] = [esc_text(x) for x in q["why"]]
        if q.get("card_only"):
            rec["card"] = True
        else:
            assert len(q["o"]) == 4 and 0 <= q["a"] < 4, q["id"]
        if q.get("duplicate_of"):
            rec["dup"] = q["duplicate_of"]
        out_q.append(rec)
    report["excluded_needs_owner"] = excluded
    report["excluded_by_owner"] = owner_dropped
    assert sorted(owner_dropped) == sorted(OWNER_EXCLUDED), owner_dropped

    # ---- outline with derived counters ----
    vis_by_ch = Counter(q["ch"] for q in out_q)
    quiz_by_ch = Counter(q["ch"] for q in out_q if not q.get("card"))
    cards_by_ch = Counter(q["ch"] for q in out_q if q.get("card"))
    bank_by_ch = Counter(q["ch"] for q in out_q if q["src"] == "bank")
    exam_by_ch = Counter(q["ch"] for q in out_q if q["src"] == "exam")
    by_sec = Counter((q["ch"], q["sec"]) for q in out_q)
    loaded_by_ch = Counter([topics[q["t"]]["chapter"] for q in bank] + [q["chapter"] for q in exams])
    by_topic = Counter(q["t"] for q in bank)
    summary_by_ch = {s["chapter"]: s for s in SUMMARIES if s["chapter"] and s["kind"] == "page"}

    parts = []
    for p in S["parts"]:
        pch = []
        for c in p["chapters"]:
            refs = []
            for t in S["topics"]:
                if c["id"] in t.get("also_chapters", []):
                    refs.append({"kind": "topic", "topic": t["id"], "title": t["title"], "chapter": t["chapter"]})
            for r in PAGE_REFS.get(c["id"], []):
                assert r["section"] in c["sections"], r
                refs.append(dict(r, kind="page"))
            sm = summary_by_ch.get(c["id"])
            pch.append(OrderedDict([
                ("id", c["id"]), ("n", c["n"]), ("title", c["title"]),
                ("sections", [{"title": s, "q": by_sec.get((c["id"], s), 0)} for s in c["sections"]]),
                ("topics", [{"id": tid, "title": topics[tid]["title"], "n": by_topic[tid], "section": topics[tid]["section"],
                             "order": topics[tid]["order"]} for tid in sorted(c["topics"], key=lambda x: topics[x]["order"])]),
                ("refs", refs),
                ("summary", {"id": sm["id"], "title": sm["title"], "href": sm["href"]} if sm else None),
                ("empty", c["empty"]),
                # a chapter the structure lists as having content, but whose content is all
                # excluded (e.g. pending items) is hidden until something visible is added
                ("hidden", (not c["empty"]) and vis_by_ch[c["id"]] == 0),
                ("counts", OrderedDict([("loaded", loaded_by_ch[c["id"]]), ("visible", vis_by_ch[c["id"]]),
                                        ("quiz", quiz_by_ch[c["id"]]), ("cards", cards_by_ch[c["id"]]),
                                        ("bank", bank_by_ch[c["id"]]), ("exam", exam_by_ch[c["id"]])])),
            ]))
        pc = OrderedDict((k, sum(ch["counts"][k] for ch in pch)) for k in ("loaded", "visible", "quiz", "cards", "bank", "exam"))
        parts.append(OrderedDict([("id", p["id"]), ("order", p["order"]), ("title", p["title"]), ("chapters", pch), ("counts", pc)]))

    totals = OrderedDict([
        ("parts", len(parts)),
        ("chapters", sum(len(p["chapters"]) for p in parts)),
        ("chapters_shown", sum(1 for p in parts for c in p["chapters"] if not c["hidden"])),
        ("sections", sum(len(c["sections"]) for p in parts for c in p["chapters"])),
        ("topics", len(S["topics"])),
        ("loaded", report["loaded_total"]),
        ("visible", len(out_q)),
        ("quiz", sum(1 for q in out_q if not q.get("card"))),
        ("cards", sum(1 for q in out_q if q.get("card"))),
        ("bank", sum(1 for q in out_q if q["src"] == "bank")),
        ("exam", sum(1 for q in out_q if q["src"] == "exam")),
        ("excluded", len(excluded)),
        ("excluded_by_owner", len(owner_dropped)),
    ])
    outline = OrderedDict([("section", "business-environment"), ("title", S["title"]), ("parts", parts), ("totals", totals)])

    dump_json(os.path.join(DATA_OUT, "bizenv-outline.json"), outline)
    dump_json(os.path.join(DATA_OUT, "bizenv-questions.json"), {"questions": out_q})
    dump_json(os.path.join(DATA_OUT, "bizenv-summaries.json"), {"summaries": SUMMARIES})

    # ---- page ----
    t = platform_tokens()
    page = read(os.path.join(TEMPLATES, "business-environment.template.html"))
    page = (page.replace("%%HEAD%%", head("بيئة الأعمال | منصة معيار", t, EXTRA_CSS))
                .replace("%%BRAND%%", brand_bar("fellowship.html", "التحضير لزمالة SOCPA"))
                .replace("%%FOOTER%%", footer())
                .replace("%%SW%%", SW_REGISTER))
    assert "%%" not in page
    write(os.path.join(OUT, "business-environment.html"), page)
    shutil.copyfile(os.path.join(SRC, "access.js"), os.path.join(OUT, "access.js"))

    # ---- report numbers ----
    report.update({
        "totals": dict(totals),
        "loaded_by_part": {p["id"]: p["counts"]["loaded"] for p in parts},
        "visible_by_part": {p["id"]: p["counts"]["visible"] for p in parts},
        "loaded_mcq": sum(1 for q in bank) + sum(1 for q in exams if not q.get("card_only")),
        "loaded_cards": sum(1 for q in exams if q.get("card_only")),
        "mf_c14": {"topics": [x["id"] for x in parts[2]["chapters"][13]["topics"]],
                   "loaded": loaded_by_ch["MF.C14"], "bank": bank_by_ch["MF.C14"]},
        "zero_visible_nonempty": [c["id"] for p in parts for c in p["chapters"] if not c["empty"] and c["counts"]["visible"] == 0],
        "structure_counter_mismatch": [c["id"] for p in S["parts"] for c in p["chapters"] if c["q_total"] != loaded_by_ch[c["id"]]],
        "tokens": t,
    })
    return report


if __name__ == "__main__":
    import json
    r = build()
    r.pop("tokens", None)
    print(json.dumps(r, ensure_ascii=False, indent=1))
