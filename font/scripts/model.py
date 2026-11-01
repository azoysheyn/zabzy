"""Zabzy script (bold), as data.

An abugida.  Each drawing is one of:

  C        bare consonant ("B.svg")
  C + V    consonant with a vowel mark on top ("B + A.svg")
  + V      vowel on the default carrier ("+ A.svg")
  Default  the carrier alone

Typing: b = bz, p = ps (both spellings give the same sign).  "ng" is one
sign; "n'g" is n followed by g -- the apostrophe ends a sign and is consumed.
"""

# unit -> (glyph-name token, typed spellings)
CONSONANTS = {
    "B":  ("b",  ["b", "bz"]),
    "D":  ("d",  ["d"]),
    "F":  ("f",  ["f"]),
    "G":  ("g",  ["g"]),
    "K":  ("k",  ["k"]),
    "M":  ("m",  ["m"]),
    "N":  ("n",  ["n"]),
    "Ng": ("ng", ["ng"]),
    "P":  ("p",  ["p", "ps"]),
    "R":  ("r",  ["r"]),
    "S":  ("s",  ["s"]),
    "T":  ("t",  ["t"]),
    "V":  ("v",  ["v"]),
    "Z":  ("z",  ["z"]),
}
VOWELS = {v: (v.lower(), [v.lower()]) for v in "AIOUY"}


class Sign:
    def __init__(self, stem, kind, cons, vowel):
        self.stem, self.kind, self.cons, self.vowel = stem, kind, cons, vowel
        c = CONSONANTS[cons][0] if cons else ""
        v = VOWELS[vowel][0] if vowel else ""
        if kind == "default":
            self.name = "zb_default"
        elif kind == "vowel":
            self.name = "zb_" + v
        else:
            self.name = "zb_" + c + v
        self.join = ()

    @property
    def has_mark(self):
        """Drawings with a vowel mark are 15 svg units taller on top."""
        return self.vowel is not None

    def spellings(self):
        cs = CONSONANTS[self.cons][1] if self.cons else [""]
        vs = VOWELS[self.vowel][1] if self.vowel else [""]
        return [list(c + v) for c in cs for v in vs if c + v]


def parse_stem(stem):
    s = " ".join(stem.split())          # "M +  A" has a double space
    if s == "Default":
        return Sign(stem, "default", None, None)
    if s.startswith("+ "):
        v = s[2:]
        if v not in VOWELS:
            raise ValueError(f"{stem}: unknown vowel {v!r}")
        return Sign(stem, "vowel", None, v)
    if " + " in s:
        c, v = s.split(" + ")
        if c not in CONSONANTS or v not in VOWELS:
            raise ValueError(f"{stem}: cannot parse")
        return Sign(stem, "syllable", c, v)
    if s in CONSONANTS:
        return Sign(stem, "consonant", s, None)
    raise ValueError(f"{stem}: cannot parse")


def missing(signs):
    have = {(s.cons, s.vowel) for s in signs}
    want = {(c, v) for c in [None, *CONSONANTS] for v in [None, *VOWELS]}
    return sorted(want - have, key=str)
