# -*- coding: utf-8 -*-
"""One command, inputs to publish_paused/:

    python3 build_all_fellowship.py

Order: base copy and phase A pages, then the subject, the capital structure page,
the container page (which fills the home door counters), then sw.js and
sitemap.xml once every file exists. Writes _build_state.json for the report.
"""
import json
import os

import build_bizenv
import build_capital_structure
import build_fellowship
import build_paused
from common import HERE


def main():
    state = {}
    state["paused"] = build_paused.prepare()
    state["bizenv"] = build_bizenv.build()
    state["capital"] = build_capital_structure.build()
    state["fellowship"] = build_fellowship.build()
    state["finalize"] = build_paused.finalize()
    tokens = state["bizenv"].pop("tokens")
    state["tokens"] = tokens
    with open(os.path.join(HERE, "_build_state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    b = state["bizenv"]
    print("loaded %d (bank %d + exam %d), visible %d, excluded needs_owner %d"
          % (b["loaded_total"], b["loaded_bank"], b["loaded_exam"], b["totals"]["visible"], len(b["excluded_needs_owner"])))
    print("CACHE %s -> %s" % (state["finalize"]["cache_old"], state["finalize"]["cache_new"]))
    print("home door:", state["fellowship"]["door_counters"])


if __name__ == "__main__":
    main()
