#!/usr/bin/env python3
"""Shaping assertions: typed text -> expected glyphs."""
import os
import sys

sys.path.insert(0, os.path.expanduser("~/.claude/skills/svg-font-builder/scripts"))
from svgfont import verify  # noqa: E402

OTF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "dist/otf/ZabzyHand-Regular.otf")
CASES = [
    ("za",      ["hz_za"]),                      # consonant + a: mark on top
    ("zo",      ["hz_zo"]),
    ("zu",      ["hz_z", "hz_u"]),               # u is a letter of its own
    ("zi",      ["hz_z", "hz_i"]),
    ("zy",      ["hz_z", "hz_y"]),
    ("z",       ["hz_z"]),                       # bare consonant
    ("a",       ["hz_a"]),                       # a with no consonant: on zero
    ("o",       ["hz_o"]),
    ("ama",     ["hz_a", "hz_ma"]),
    ("zabzy",   ["hz_za", "hz_bz", "hz_y"]),
    ("ZABZY",   ["hz_za", "hz_bz", "hz_y"]),
    ("zaby",    ["hz_za", "hz_bz", "hz_y"]),     # b = bz
    ("bza",     ["hz_bza"]),
    ("ba",      ["hz_bza"]),
    ("psa",     ["hz_psa"]),
    ("pa",      ["hz_psa"]),                     # p = ps
    ("va",      ["hz_fa"]),                      # v = f
    ("vo",      ["hz_fo"]),
    ("nga",     ["hz_nga"]),
    ("ng",      ["hz_ng"]),
    ("n'ga",    ["hz_n", "hz_ga"]),              # apostrophe splits n'g
    ("n'g",     ["hz_n", "hz_g"]),
    ("anga",    ["hz_a", "hz_nga"]),
    ("kat",     ["hz_ka", "hz_t"]),
    ("ak'a",    ["hz_a", "hz_k", "hz_a"]),
    ("kua",     ["hz_k", "hz_u", "hz_a"]),
    ("mazmazang kifuranrug", ["hz_ma", "hz_z", "hz_ma", "hz_za", "hz_ng", "space",     # ma z ma za ng
                              "hz_k", "hz_i", "hz_f", "hz_u", "hz_ra", "hz_n", "hz_r", "hz_u", "hz_g"]),
    ("",  ["hz_zero"]),
]
sys.exit(1 if verify.run_cases(OTF, CASES) else 0)
