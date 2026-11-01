#!/usr/bin/env python3
"""Shaping assertions: typed text -> expected glyphs."""
import os, sys
sys.path.insert(0, os.path.expanduser("~/.claude/skills/svg-font-builder/scripts"))
from svgfont import verify

OTF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "dist/otf/Zabzy-Bold.otf")
CASES = [
    ("zabzy",  ["zb_za", "zb_by"]),
    ("zaby",   ["zb_za", "zb_by"]),
    ("ZABZY",  ["zb_za", "zb_by"]),
    ("psa",    ["zb_pa"]),
    ("pa",     ["zb_pa"]),
    ("ps",     ["zb_p"]),
    ("bz",     ["zb_b"]),
    ("nga",    ["zb_nga"]),
    ("ng",     ["zb_ng"]),
    ("n'ga",   ["zb_n", "zb_ga"]),
    ("n'g",    ["zb_n", "zb_g"]),
    ("anga",   ["zb_a", "zb_nga"]),
    ("an'ga",  ["zb_a", "zb_n", "zb_ga"]),
    ("ai",     ["zb_a", "zb_i"]),
    ("kat",    ["zb_ka", "zb_t"]),
    ("ak'a",   ["zb_a", "zb_k", "zb_a"]),
    ("y",      ["zb_y"]),
    ("vu fo",  ["zb_vu", "space", "zb_fo"]),
    ("", ["zb_default"]),
]
sys.exit(1 if verify.run_cases(OTF, CASES) else 0)
