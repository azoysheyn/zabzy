#!/usr/bin/env python3
"""Zabzy Hand: Figma components -> dist/{otf,ttf,woff2}.

    ./scripts/build.sh            (makes .venv on the first run)

1. compose  each sign is assembled from its letter and, for a and o, the vowel
            mark, in the geometry of its Figma component frame -> build/composed/
2. outline  the drawings are strokes (3px, round caps); picosvg expands them into
            filled outlines -> build/svg/
3. build    the svg-font-builder pipeline makes the font.

Figma units map 1:10 onto font units: the letter box is 26 high (x-height 260),
the baseline is the bottom of the letter box (Figma y = 49).
"""

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser("~/.claude/skills/svg-font-builder/scripts"))

from fontTools.ttLib import TTFont                      # noqa: E402
from svgfont import build, feature, measure, verify     # noqa: E402
from svgfont.spec import FontSpec, Glyph, Grid, Vertical  # noqa: E402
import model                                            # noqa: E402

SOURCE = os.path.join(ROOT, "source")
BUILD = os.path.join(ROOT, "build")
COMPOSED = os.path.join(BUILD, "composed")
FLAT = os.path.join(BUILD, "svg")
DIST = os.path.join(ROOT, "dist")

GRID = Grid(size=100, cap=23, baseline=49, upm=1000)
SIDE = 40                     # side bearing on each side, font units, measured from the ink
# Optical spacing: every pair is kerned so that its narrowest gap is GAP. The rule comes
# from Mitia's hand-kerning in Figma (23 Nov 2026, see FIGMA_KERN): his corrected pairs
# end at a narrowest gap of 38 units, give or take two tracking steps.
GAP = 38
# Letters that need more air after them. U is one tall stroke: at GAP, "ut" and "ur" look
# tight (Mitia, 23 Nov 2026).
GAP_AFTER = {"hz_u": 60}
MAX_KERN = 200                # the rule only; a manual kern may go further
MIN_GAP = 20                  # no vowel mark comes closer than this
# Pairs with their own narrowest gap, set by eye after test prints (24 Nov 2026).
PAIR_GAP = {
    ("hz_u", "hz_t"): 85,         # 60 was still too close
    ("hz_n", "hz_r"): 70,         # 97 from Figma was too far, 38 too close
    ("hz_z", "hz_ng"): 50,        # 22 from Figma was too close
}
# Pairs set by hand in Figma, total kern in font units. Text "mazmazang kifuranrug /
# ma daz kir kutnu zabzy" at 12 px; 1 px of tracking = 1000 / 12 units. These win over GAP.
# Keys are bare letters: the pair holds for every vowel variant (main: kerning by letter).
FIGMA_KERN = {
    ("hz_m", "hz_z"): -72,
    ("hz_z", "hz_m"): -52,
    ("hz_k", "hz_i"): -38,        # -0.96 px in one line, -1.44 px in the other: the mean
    ("hz_i", "hz_f"): -24,
    ("hz_f", "hz_u"): -47,
    ("hz_r", "hz_u"): -64,
    ("hz_k", "hz_u"): -185,
    ("hz_bz", "hz_y"): -41,
}
# Second pass, 24 Nov 2026: Mitia went through the kerning table (specimen/kerning.html)
# and set 147 pairs by hand -> source/kerning-manual.tsv. Those win over everything.
# He opened almost every pair, by about 50 units. The pairs he did not reach get the same
# shift, predicted as LOOSEN + LOOSEN_LEFT[left] + LOOSEN_RIGHT[right] on top of the rule
# above. The three numbers are a least-squares fit to his 147 shifts; left out one at a
# time, the fit misses a pair by 10 units at the median (one step in the table).
MANUAL = os.path.join(ROOT, "source", "kerning-manual.tsv")
LOOSEN = 53
LOOSEN_LEFT = {
    "hz_m": 3,
    "hz_f": 6,
    "hz_bz": -3,
    "hz_ps": 12,
    "hz_z": -11,
    "hz_s": 17,
    "hz_r": 0,
    "hz_d": -2,
    "hz_t": 12,
    "hz_n": -2,
    "hz_g": -38,
    "hz_k": 5,
    "hz_ng": -2,
    "hz_u": -5,
    "hz_i": 5,
    "hz_y": 2,
    "hz_zero": -1,
}
LOOSEN_RIGHT = {
    "hz_m": 1,
    "hz_f": 6,
    "hz_bz": -21,
    "hz_ps": 2,
    "hz_z": 3,
    "hz_s": 7,
    "hz_r": 11,
    "hz_d": -2,
    "hz_t": -17,
    "hz_n": -9,
    "hz_g": -1,
    "hz_k": 2,
    "hz_ng": 6,
    "hz_u": 2,
    "hz_i": 17,
    "hz_y": 8,
    "hz_zero": -11,
}
BOUNDARY = "quotesingle"      # n'g -> n, g
CHARS = "abdfgikmnoprstuvyz"

_INNER = re.compile(r"<svg[^>]*>(.*)</svg>", re.S)


def inner(path):
    """The drawing inside an exported svg, without its root element."""
    return _INNER.search(open(path, encoding="utf-8").read()).group(1).strip()


def place(path, box):
    """The drawing moved to its box. The exported svgs are 1:1 (viewBox = size), so a
    translate is enough; picosvg does not read nested <svg> elements."""
    x, y, _w, _h = box
    return f'<g transform="translate({x} {y})">{inner(path)}</g>'


def compose(sign):
    """One sign in its component frame, as a stroked svg."""
    width, img, mark_x = model.LETTERS[sign.letter][2:]
    letter = place(os.path.join(SOURCE, "letters", sign.letter + ".svg"), img)
    if sign.letter == "zero":     # drawn rotated by 180 degrees in its 22 x 26 box
        letter = f'<g transform="rotate(180 11 36)">{letter}</g>'
    parts = [letter]
    if sign.vowel:
        mx, my, mw, mh = model.MARK_IMG
        parts.append(place(os.path.join(SOURCE, "marks", sign.vowel + ".svg"), (mark_x + mx, my, mw, mh)))
    # fill="none" sits on the root of every exported svg: keep it, or each stroke is also filled
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-20 -20 {width + 40} 120" '
           f'width="{width + 40}" height="120" fill="none">' + "".join(parts) + "</svg>\n")
    os.makedirs(COMPOSED, exist_ok=True)
    out = os.path.join(COMPOSED, sign.name + ".svg")
    open(out, "w", encoding="utf-8").write(svg)
    return out


def outline(src):
    """Expand strokes into filled outlines with picosvg."""
    os.makedirs(FLAT, exist_ok=True)
    out = subprocess.run([os.path.join(os.path.dirname(sys.executable), "picosvg"), src],
                         check=True, capture_output=True, text=True).stdout
    dst = os.path.join(FLAT, os.path.basename(src))
    open(dst, "w", encoding="utf-8").write(out)
    return dst


def main():
    signs = model.signs()
    glyphs = [Glyph("space", advance=round(GRID.upm * 0.3))]
    glyphs.append(Glyph(BOUNDARY))
    cmap = {0x20: "space", 0x27: BOUNDARY, 0x2019: BOUNDARY}

    # every typed letter is itself a sign; longer spellings are ligatures of signs
    char_glyph = {}
    for s in signs:
        for sp in s.spellings():
            if len(sp) == 1:
                char_glyph[sp[0]] = s.name
    assert set(char_glyph) == set(CHARS), set(CHARS) ^ set(char_glyph)
    for c, g in char_glyph.items():
        cmap[ord(c)] = g
        cmap[ord(c.upper())] = g

    for s in signs:
        svg = outline(compose(s))
        x0, _y0, x1, _y1 = measure.ink_bounds(svg)
        typed = [[char_glyph[c] for c in sp] for sp in s.spellings()]
        seqs = [q for q in typed if len(q) > 1]
        seqs += [q + [BOUNDARY] for q in typed]   # the apostrophe ends any sign, single letters too
        glyphs.append(Glyph(name=s.name, svg=svg,
                            advance=round((x1 - x0) * GRID.scale) + 2 * SIDE,
                            shift_x=SIDE - x0 * GRID.scale, inputs=seqs))
    cmap[0xE000] = "hz_zero"      # the bare zero letter has no Latin spelling

    spec = FontSpec(
        family="Zabzy Hand", style="Regular",
        designer="Mitia Morovov-Sheiner",
        description="Zabzy 1 handwriting. Type Latin: za, zo, zu = Z+U; b=bz, p=ps, v=f, ng; n'g = n + g.",
        grid=GRID,
        vertical=Vertical(ascender=700, descender=-400, typo_ascender=700, typo_descender=-400,
                          typo_line_gap=200, win_ascent=720, win_descent=420),
        glyphs=glyphs, cmap=cmap,
        latin_fallback=os.path.expanduser("~/Library/Fonts/NotoSans-VariableFont_wdth,wght.ttf"),
        latin_extra={BOUNDARY: 0x27},
    )
    problems = spec.validate()
    assert not problems, problems
    written, _ = build.build(spec, DIST)          # pass 1: spacing only, to measure
    # Kerning by letter: a vowel mark only sits on top, so da = do = d. Every pair is
    # measured on the bare letters and holds for all their vowel variants.
    family = {}
    for sg in signs:
        family.setdefault(model.Sign(sg.letter).name, []).append(sg.name)
    spec.kern_left, spec.kern_right, spec.kern = kern_classes(optical_kerning(written["otf"], family), family)
    problems = spec.validate()
    assert not problems, problems
    written, fea = build.build(spec, DIST)        # pass 2: with kerning
    open(os.path.join(BUILD, spec.ps_name + ".fea"), "w").write(fea)
    print(f"{len(signs)} signs, {feature.rule_count(spec)} substitutions, {len(spec.kern)} kern pairs")
    for p in written.values():
        print("  ->", os.path.relpath(p, ROOT))
    print(verify.describe(written["otf"]))


def optical_kerning(otf, family):
    """Kern every pair of letters to the same narrowest gap; Figma pairs as set.

    family maps a bare letter to all its vowel variants. The gap is measured on the bare
    letters, and the kern holds for every variant. A vowel mark can still meet the
    neighbour (G carries its mark on the left, next to the loop of the letter before);
    then the whole pair opens until no variant comes closer than MIN_GAP.
    Returns {(left, right): kern}."""
    font = TTFont(otf)
    gs, hmtx = font.getGlyphSet(), font["hmtx"]
    rows = list(range(-400, 701, 10))
    glyphs = [g for vs in family.values() for g in vs]
    prof = {n: measure.profile(gs[n], rows) for n in glyphs}

    def narrowest(a, b):
        adv = hmtx[a][0]
        gaps = [(adv + prof[b][y][0]) - prof[a][y][1] for y in prof[a] if y in prof[b]]
        return min(gaps) if gaps else None

    manual = read_manual()
    kerns, opened, table = {}, [], []          # kerns: glyph pair -> kern
    for a in family:
        for b in family:
            n = narrowest(a, b)
            if (a, b) in manual:
                k, source = manual[(a, b)], "manual"
            elif n is None and (a, b) not in FIGMA_KERN:
                continue
            else:
                if (a, b) in FIGMA_KERN:
                    k = FIGMA_KERN[(a, b)]
                else:
                    k = max(-MAX_KERN, min(MAX_KERN, round(PAIR_GAP.get((a, b), GAP_AFTER.get(a, GAP)) - n)))
                k += LOOSEN + LOOSEN_LEFT[a] + LOOSEN_RIGHT[b]
                source = "predicted"
            k = int(round(k)) if abs(k) >= 5 or source == "manual" else 0
            # the letter kern holds for every variant, unless a vowel mark comes too
            # close: then only that variant pair opens (G + Ga, not G + G)
            opened_here = 0
            for va in family[a]:
                for vb in family[b]:
                    w = narrowest(va, vb)
                    if w is not None and w + k < MIN_GAP:
                        kerns[(va, vb)] = round(MIN_GAP - w)
                        opened.append((va, vb, MIN_GAP - w - k))
                        opened_here += 1
                    elif k:
                        kerns[(va, vb)] = k
            table.append({"left": a, "right": b, "kern": k, "source": source, "opened": opened_here,
                          "gap": None if n is None else round(n + k)})
    with open(os.path.join(BUILD, "kerning.json"), "w") as f:
        json.dump(table, f, indent=0)
    print(f"{len(family) ** 2} letter pairs: {len(manual)} by hand, the rest by rule + predicted shift")
    for a, b, d in opened:
        print(f"  opened {a} {b} by {d:.0f}: a vowel mark comes too close")
    return kerns


def kern_classes(kerns, family):
    """Glyph-pair kerns -> (left classes, right classes, class pairs). Variants of a
    letter share a class while they kern alike, so the table stays one row per letter
    except where a vowel mark split it."""
    glyphs = [g for vs in family.values() for g in vs]
    K = lambda a, b: kerns.get((a, b), 0)                        # noqa: E731
    left, right = {}, {}
    for letter, vs in family.items():
        for g in vs:
            left.setdefault((letter, tuple(K(g, r) for r in glyphs)), []).append(g)
            right.setdefault((letter, tuple(K(l, g) for l in glyphs)), []).append(g)
    left = {f"L_{vs[0]}": vs for vs in left.values()}
    right = {f"R_{vs[0]}": vs for vs in right.values()}
    pairs = [(ln, rn, K(lv[0], rv[0])) for ln, lv in left.items() for rn, rv in right.items()
             if K(lv[0], rv[0])]
    return left, right, pairs


def read_manual():
    """source/kerning-manual.tsv -> {(left glyph, right glyph): kern}."""
    out = {}
    for line in open(MANUAL, encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            a, b, k = line.split("\t")
            out[(model.Sign(_letter(a)).name, model.Sign(_letter(b)).name)] = int(k)
    return out


def _letter(token):
    """Typed label in the tsv ("bz", "zero") -> letter name in model.LETTERS."""
    return next(name for name, spec in model.LETTERS.items() if spec[0] == token)


if __name__ == "__main__":
    main()
