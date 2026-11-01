#!/usr/bin/env python3
"""Zabzy Bold: drawings -> dist/{otf,ttf,woff2}.

    .venv/bin/python scripts/build_font.py

The SVGs sit in the project root, as drawn.  Bare consonants are drawn on a
canvas 15 units shorter at the top than the vowel-marked ones, so before
building each drawing is copied into build/svg/ with its body bottom moved to
y=256 -- the shared baseline.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser("~/.claude/skills/svg-font-builder/scripts"))

from fontTools.ttLib import TTFont                      # noqa: E402
from svgpathtools import parse_path                     # noqa: E402
from svgfont import build, feature, verify              # noqa: E402
from svgfont.spec import FontSpec, Glyph, Grid, Vertical  # noqa: E402
import model                                            # noqa: E402

SOURCE = ROOT
DIST = os.path.join(ROOT, "dist")
BUILD = os.path.join(ROOT, "build")
NORM = os.path.join(BUILD, "svg")

# svg units: vowel mark 0..60, body 70..256, descenders to 329.
# One em = 330 svg units, so vowel-mark top ~ 776, descender ~ -221.
GRID = Grid(size=330, cap=70, baseline=256, upm=1000)
BEARING_SVG = 15          # each side; two neighbours sit one stroke (30) apart
INK_W = 168
BEARING = round(BEARING_SVG * GRID.scale)

CHARS = "abdfgikmnoprstuvyz"
BOUNDARY = "quotesingle"  # n'g -> n, g

_D = re.compile(r'(<path[^>]*\bd=")([^"]*)(")')


def normalise(sign):
    src = open(os.path.join(SOURCE, sign.stem + ".svg"), encoding="utf-8").read()
    dy = 0 if sign.has_mark else 15
    if dy:
        src = _D.sub(lambda m: m.group(1) + parse_path(m.group(2))
                     .translated(complex(0, dy)).d() + m.group(3), src)
    os.makedirs(NORM, exist_ok=True)
    out = os.path.join(NORM, sign.name + ".svg")
    open(out, "w", encoding="utf-8").write(src)
    return out


def inputs_for(sign, char_glyph):
    # every typed letter is itself a sign, so the cmap sends it straight to
    # that sign and longer spellings are ligatures of signs
    seqs = [[char_glyph[c] for c in sp] for sp in sign.spellings()]
    seqs += [s + [BOUNDARY] for s in seqs]
    return seqs


def main():
    stems = sorted(f[:-4] for f in os.listdir(SOURCE) if f.endswith(".svg"))
    signs = [model.parse_stem(s) for s in stems]
    assert not model.missing(signs), model.missing(signs)

    glyphs = [Glyph("space", advance=round(GRID.upm * 0.35))]
    glyphs.append(Glyph(BOUNDARY))
    cmap = {0x20: "space", 0x27: BOUNDARY, 0x2019: BOUNDARY}
    char_glyph = {}
    for sign in signs:
        for sp in sign.spellings():
            if len(sp) == 1:
                char_glyph[sp[0]] = sign.name
    assert set(char_glyph) == set(CHARS), set(CHARS) ^ set(char_glyph)
    for c, g in char_glyph.items():
        cmap[ord(c)] = g
        cmap[ord(c.upper())] = g

    adv = round((INK_W + 2 * BEARING_SVG) * GRID.scale)
    for sign in signs:
        spellings = inputs_for(sign, char_glyph) if sign.kind != "default" else []
        glyphs.append(Glyph(
            name=sign.name, svg=normalise(sign), advance=adv,
            shift_x=BEARING, inputs=spellings))
    # carrier alone has no Latin spelling -- reach it at U+E000
    cmap[0xE000] = "zb_default"

    spec = FontSpec(
        family="Zabzy", style="Bold",
        designer="Mitia Morovov-Sheiner",
        description="Zabzy script. Type Latin (b=bz, p=ps, ng; n'g = n + g).",
        grid=GRID,
        vertical=Vertical(ascender=800, descender=-250,
                          typo_ascender=800, typo_descender=-250,
                          typo_line_gap=200, win_ascent=820, win_descent=260),
        glyphs=glyphs, cmap=cmap,
        latin_fallback=os.path.expanduser(
            "~/Library/Fonts/NotoSans-VariableFont_wdth,wght.ttf"),
        latin_extra={BOUNDARY: 0x27},
    )
    problems = spec.validate()
    assert not problems, problems

    written, fea = build.build(spec, DIST)
    os.makedirs(BUILD, exist_ok=True)
    open(os.path.join(BUILD, spec.ps_name + ".fea"), "w").write(fea)
    for path in written.values():
        mark_bold(path)
    print(f"{len(signs)} drawings, {feature.rule_count(spec)} substitutions")
    for path in written.values():
        print("  ->", os.path.relpath(path, ROOT))
    print(verify.describe(written["otf"]))


def mark_bold(path):
    """Set the Bold flags, and merge overlapping strokes.

    The drawings are built from separate overlapping paths, some wound the
    other way; without a union their overlaps cancel out into holes.
    """
    from fontTools.ttLib.removeOverlaps import removeOverlaps
    f = TTFont(path)
    removeOverlaps(f)
    f["OS/2"].usWeightClass = 700
    f["OS/2"].fsSelection = (f["OS/2"].fsSelection & ~0x40) | 0x20   # BOLD, not REGULAR
    f["head"].macStyle |= 0x01
    f.save(path)


if __name__ == "__main__":
    main()
