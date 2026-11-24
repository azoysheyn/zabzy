"""Zabzy Hand — the handwriting of Zabzy 1, as data.

Figma: file ZbrErOiS4kRIlQkP7S6ete, components "Handwriting Letters" (3057:6127)
and "Vowel mark" (3057:6192).

The script:
  - a consonant alone is the bare letter ("z");
  - a consonant with a or o carries the vowel mark on top ("za", "zo");
  - u, i, y are letters of their own: "zu" is Z + U;
  - a or o with no consonant sits on the "zero" letter ("a", "o").

Typing is Latin, as in Zabzy Bold: b = bz, p = ps, v = f; "ng" is one letter,
"n'g" is n then g (the apostrophe ends a sign and is not printed).
"""

# Each letter's component frame (Figma units). The letter box is 26 high at
# y 23..49 (49 = baseline); the vowel-mark slot is 16 x 15 at y 0..15.
#   width   frame width
#   img     where the letter's svg sits in the frame: (x, y, w, h)
#   mark_x  left edge of the mark slot (centred, except G: left, as in Figma)
#   rotate  the zero letter is drawn rotated by 180 degrees in its box
SHORT = (-1.5, 21.5, 61, 29)        # 26 high, in the letter box
DOWN = (-1.5, 21.5, 61, 63)         # 60 high, hangs below the box
LETTERS = {
    # name: (glyph token, typed spellings, width, img, mark_x)
    "M":  ("m",  ["m"],        58, SHORT, 21),
    "F":  ("f",  ["f", "v"],   58, SHORT, 21),
    "BZ": ("bz", ["bz", "b"],  58, DOWN, 21),
    "PS": ("ps", ["ps", "p"],  58, SHORT, 21),
    "Z":  ("z",  ["z"],        58, SHORT, 21),
    "S":  ("s",  ["s"],        58, DOWN, 21),
    "R":  ("r",  ["r"],        58, DOWN, 21),
    "D":  ("d",  ["d"],        58, SHORT, 21),
    "T":  ("t",  ["t"],        58, SHORT, 21),
    "N":  ("n",  ["n"],        58, DOWN, 21),
    "G":  ("g",  ["g"],        46, (-1.5, -12.5, 61, 63), 0),
    "K":  ("k",  ["k"],        58, DOWN, 21),
    "NG": ("ng", ["ng"],       58, SHORT, 21),
    "U":  ("u",  ["u"],        22, (-1.5, -12.5, 25, 63), None),
    "I":  ("i",  ["i"],        16, (-1.5, 21.5, 19, 63), None),
    "Y":  ("y",  ["y"],        22, (-1.5, 21.5, 25, 29), None),
    "zero": ("zero", [],       22, (-1.5, 21.5, 25, 29), 3),
}
CONSONANTS = [k for k in LETTERS if k not in ("U", "I", "Y", "zero")]
MARK_VOWELS = ["a", "o"]           # vowels written as a mark on top
LETTER_VOWELS = ["U", "I", "Y"]    # vowels written as a letter
MARK_IMG = (-1.5, -1.5, 19, 18)    # mark svg relative to its slot


class Sign:
    """One glyph: a letter, optionally with a vowel mark."""

    def __init__(self, letter, vowel=None):
        self.letter, self.vowel = letter, vowel
        token = LETTERS[letter][0]
        if letter == "zero":
            self.name = "hz_" + (vowel or "zero")
        else:
            self.name = "hz_" + token + (vowel or "")

    def spellings(self):
        """Typed sequences (lists of characters) that give this sign."""
        if self.letter == "zero":
            return [[self.vowel]] if self.vowel else []
        cs = LETTERS[self.letter][1]
        return [list(c + (self.vowel or "")) for c in cs]


def signs():
    out = [Sign(c) for c in CONSONANTS]
    out += [Sign(c, v) for c in CONSONANTS for v in MARK_VOWELS]
    out += [Sign(v) for v in LETTER_VOWELS]
    out += [Sign("zero"), *(Sign("zero", v) for v in MARK_VOWELS)]
    names = [s.name for s in out]
    assert len(names) == len(set(names)), "glyph names must be unique"
    return out
