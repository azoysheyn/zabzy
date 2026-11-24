#!/usr/bin/env python3
"""Kerning table: build/kerning.json + the font -> specimen/kerning.html.

One cell per pair of letters, drawn in the font, with its kern and where the kern comes
from. Kerning goes by letter: one cell holds for every vowel variant (da = do = d).
The page lets you move a pair closer or further and copy the list of changes.
"""

import base64
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model  # noqa: E402

# glyph name -> (label, typed text). The apostrophe ends a sign, so "b'" + "z" stays
# BZ + Z instead of one BZ. The zero letter has no Latin spelling: U+E000.
LETTERS = {}
for name, (_token, spellings, *_rest) in model.LETTERS.items():
    glyph = model.Sign(name).name
    if name == "zero":
        LETTERS[glyph] = ("zero", "", "")
    else:
        LETTERS[glyph] = (spellings[0], spellings[0] + "'", spellings[0])


def main():
    table = json.load(open(os.path.join(ROOT, "build", "kerning.json")))
    font = base64.b64encode(open(os.path.join(ROOT, "dist", "woff2", "ZabzyHand-Regular.woff2"), "rb").read()).decode()
    letters = [{"glyph": g, "label": lab, "left": left, "right": right}
               for g, (lab, left, right) in LETTERS.items()]
    build_id = hashlib.sha1(json.dumps(table).encode()).hexdigest()[:10]
    html = (PAGE.replace("__FONT__", font).replace("__BUILD__", build_id)
                .replace("__LETTERS__", json.dumps(letters, ensure_ascii=False))
                .replace("__PAIRS__", json.dumps(table)))
    out = os.path.join(ROOT, "specimen", "kerning.html")
    open(out, "w", encoding="utf-8").write(html)
    print("  ->", os.path.relpath(out, ROOT))


PAGE = r"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Zabzy Hand kerning</title>
<style>
@font-face { font-family: "Zabzy Hand Table"; src: url(data:font/woff2;base64,__FONT__) format("woff2"); }
:root {
  --bg: #f4f3ef; --paper: #fffefb; --ink: #1d1c1a; --muted: #8a877f; --line: #e3e0d8;
  --rule: #8a877f; --after: #2f6fb3; --pair: #2e8a4f; --figma: #c46a12; --mark: #c23b3b; --max: #7b4bb3;
  --sel: #1d1c1a; --hover: #f1eee6; --edit: #fff3c4;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #171716; --paper: #1f1f1d; --ink: #ecebe6; --muted: #8f8c84; --line: #2f2e2b;
    --rule: #8f8c84; --after: #6ea6e6; --pair: #5cc07f; --figma: #e59a4a; --mark: #ec6b6b; --max: #b08ae6;
    --sel: #ecebe6; --hover: #282826; --edit: #3b3520;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 14px/1.4 -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif; }
header { padding: 20px 16px 8px; max-width: 1100px; }
h1 { font-size: 20px; margin: 0 0 4px; font-weight: 600; }
p { margin: 4px 0; color: var(--muted); }
.legend { display: flex; flex-wrap: wrap; gap: 6px 16px; padding: 8px 16px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.try { padding: 8px 16px 12px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.try input { font: inherit; padding: 6px 10px; border: 1px solid var(--line); border-radius: 6px;
  background: var(--paper); color: var(--ink); width: min(360px, 100%); }
.try .sample { font-family: "Zabzy Hand Table"; font-size: 40px; line-height: 1.6; }
.wrap { overflow: auto; margin: 0 16px 140px; border: 1px solid var(--line); border-radius: 8px;
  background: var(--paper); max-height: calc(100vh - 230px); }
table { border-collapse: collapse; }
th { position: sticky; background: var(--paper); color: var(--muted); font-weight: 500; z-index: 1; }
thead th { top: 0; padding: 6px 4px; border-bottom: 1px solid var(--line); }
tbody th { left: 0; padding: 0 10px; border-right: 1px solid var(--line); text-align: right; }
thead th:first-child { left: 0; z-index: 2; font-size: 11px; }
td { width: 92px; min-width: 92px; height: 92px; padding: 0; border: 1px solid var(--line);
  text-align: center; vertical-align: top; cursor: pointer; position: relative; }
td:hover { background: var(--hover); }
td.edited { background: var(--edit); }
td.sel { outline: 2px solid var(--sel); outline-offset: -2px; }
td.hl, th.hl { color: var(--ink); }
.pair { font-family: "Zabzy Hand Table"; font-size: 32px; line-height: 1; white-space: nowrap;
  font-kerning: none; padding-top: 18px; height: 64px; }
.pair span { display: inline-block; }
.num { font-size: 11px; font-variant-numeric: tabular-nums; }
.delta { font-weight: 600; color: var(--ink); }
.bar { position: fixed; left: 0; right: 0; bottom: 0; background: var(--paper); border-top: 1px solid var(--line);
  padding: 10px 16px; display: grid; gap: 8px 12px; align-items: center;
  grid-template-columns: 180px 300px auto 1fr auto; }
/* fixed sizes: the buttons must not move while a pair is adjusted */
.bar .big { font-family: "Zabzy Hand Table"; font-size: 44px; line-height: 1; height: 60px; width: 180px;
  overflow: hidden; white-space: nowrap; font-kerning: none; padding-top: 8px; }
.bar .big span { display: inline-block; }
.bar .info { width: 300px; height: 2.8em; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
  font-variant-numeric: tabular-nums; }
.bar .tools, .bar .global { display: flex; gap: 8px; align-items: center; }
.bar .tools button { width: 96px; }
.bar .tools #reset { width: auto; }
.bar .count { min-width: 80px; text-align: right; font-variant-numeric: tabular-nums; }
@media (max-width: 1000px) {
  .bar { grid-template-columns: 140px 1fr; }
  .bar .big { width: 140px; }
  .bar .info { width: auto; }
  .bar .tools, .bar .global { grid-column: 1 / -1; }
  .bar .spacer, .bar .keys { display: none; }
}
button { font: inherit; padding: 6px 12px; border-radius: 6px; border: 1px solid var(--line);
  background: var(--bg); color: var(--ink); cursor: pointer; }
button:hover { border-color: var(--muted); }
button.primary { min-width: 170px;  background: var(--ink); color: var(--paper); border-color: var(--ink); }
.keys { color: var(--muted); font-size: 12px; }
</style>
</head>
<body>
<header>
  <h1>Zabzy Hand — кернинг всех пар</h1>
  <p>Строка — левая буква, столбец — правая. Число — кернинг в единицах шрифта (1000 на кегль). Минус — ближе.</p>
  <p>Кернинг идёт по буквам: одна клетка работает для всех вариантов со знаком гласной (da = do = d).</p>
</header>
<div class="legend" id="legend"></div>
<div class="try">
  <input id="tryText" value="mazmazang kifuranrug ma daz kir kutnu zabzy" aria-label="Пробный текст">
  <div class="sample" id="trySample"></div>
</div>
<div class="wrap"><table id="grid"></table></div>
<div class="bar">
  <div class="big" id="selPair"></div>
  <div class="info" id="selInfo">Выберите пару в таблице.</div>
  <div class="tools">
    <button id="closer">← ближе</button>
    <button id="further">дальше →</button>
    <button id="reset">Сбросить пару</button>
  </div>
  <span class="keys spacer">Стрелки — выбор пары, − и + — сдвиг на 10 единиц</span>
  <div class="global">
    <span class="count" id="count"></span>
    <button id="clear">Сбросить всё</button>
    <button class="primary" id="copy">Скопировать правки</button>
  </div>
</div>
<script>
const LETTERS = __LETTERS__;
const PAIRS = __PAIRS__;
const STEP = 10;
const STORE = "zabzy-hand-kern-edits-__BUILD__";   // edits belong to one build of the font
const SOURCES = {
  manual:    ["твоя правка", "--figma"],
  predicted: ["правило + сдвиг, выведенный из твоих правок", "--rule"],
};
const MARK_NOTE = "* — варианты со знаком гласной раздвинуты, голые буквы — как в клетке";
const byKey = {};
for (const p of PAIRS) byKey[p.left + "|" + p.right] = p;
const index = {};
LETTERS.forEach((l, i) => index[l.glyph] = i);

let edits = {};
try { edits = JSON.parse(localStorage.getItem(STORE) || "{}"); } catch (e) { edits = {}; }
function save() { try { localStorage.setItem(STORE, JSON.stringify(edits)); } catch (e) {} }

const legend = document.getElementById("legend");
for (const [k, [label, color]] of Object.entries(SOURCES)) {
  const s = document.createElement("span");
  s.innerHTML = `<i class="dot" style="background:var(${color})"></i>${label}`;
  legend.appendChild(s);
}
{ const s = document.createElement("span"); s.textContent = MARK_NOTE; legend.appendChild(s); }

function pairHTML(a, b, kern) {
  const em = kern / 1000;
  return `<span>${esc(a.left)}</span><span style="margin-left:${em}em">${esc(b.right)}</span>`;
}
function esc(s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
function fmt(n) { return (n > 0 ? "+" : n < 0 ? "−" : "") + Math.abs(n); }

const grid = document.getElementById("grid");
let html = "<thead><tr><th>лев. \\ пр.</th>";
for (const b of LETTERS) html += `<th data-col="${b.glyph}">${b.label}</th>`;
html += "</tr></thead><tbody>";
for (const a of LETTERS) {
  html += `<tr><th data-row="${a.glyph}">${a.label}</th>`;
  for (const b of LETTERS) html += `<td data-l="${a.glyph}" data-r="${b.glyph}"></td>`;
  html += "</tr>";
}
grid.innerHTML = html + "</tbody>";

function info(l, r) {
  const p = byKey[l + "|" + r] || { kern: 0, source: "predicted", gap: null };
  const d = edits[l + "|" + r] || 0;
  return { p, d, kern: p.kern + d };
}
function draw(td) {
  const l = td.dataset.l, r = td.dataset.r;
  const { p, d, kern } = info(l, r);
  const color = SOURCES[p.source] ? SOURCES[p.source][1] : "--rule";
  td.classList.toggle("edited", d !== 0);
  td.innerHTML = `<div class="pair">${pairHTML(LETTERS[index[l]], LETTERS[index[r]], kern)}</div>` +
    `<div class="num" style="color:var(${color})">${fmt(p.kern)}${p.opened ? "*" : ""}` +
    (d ? ` <span class="delta">${fmt(d)}</span>` : "") + `</div>`;
}
grid.querySelectorAll("td").forEach(draw);

let sel = null;
function select(td) {
  if (sel) sel.classList.remove("sel");
  grid.querySelectorAll(".hl").forEach(e => e.classList.remove("hl"));
  sel = td;
  if (!td) return;
  td.classList.add("sel");
  grid.querySelector(`th[data-row="${td.dataset.l}"]`).classList.add("hl");
  grid.querySelector(`th[data-col="${td.dataset.r}"]`).classList.add("hl");
  td.scrollIntoView({ block: "nearest", inline: "nearest" });
  showSel();
}
function showSel() {
  if (!sel) return;
  const l = sel.dataset.l, r = sel.dataset.r;
  const a = LETTERS[index[l]], b = LETTERS[index[r]];
  const { p, d, kern } = info(l, r);
  document.getElementById("selPair").innerHTML = pairHTML(a, b, kern);
  const src = SOURCES[p.source] ? SOURCES[p.source][0] : p.source;
  const gap = p.gap == null ? "" : ` · зазор ${p.gap + d}`;
  document.getElementById("selInfo").innerHTML =
    `<b>${a.label} → ${b.label}</b> · кернинг ${fmt(kern)}${d ? ` (было ${fmt(p.kern)})` : ""}${gap}<br>` +
    `<span style="color:var(--muted)">${src}${p.opened ? ` · со знаком раздвинуто вариантов: ${p.opened}` : ""}</span>`;
}
function adjust(delta) {
  if (!sel) return;
  const key = sel.dataset.l + "|" + sel.dataset.r;
  const v = (edits[key] || 0) + delta;
  if (v) edits[key] = v; else delete edits[key];
  save(); draw(sel); showSel(); count();
}
function count() {
  const n = Object.keys(edits).length;
  document.getElementById("count").textContent = n ? `Правок: ${n}` : "";
}
count();

grid.addEventListener("click", e => { const td = e.target.closest("td"); if (td) select(td); });
document.getElementById("closer").onclick = () => adjust(-STEP);
document.getElementById("further").onclick = () => adjust(STEP);
document.getElementById("reset").onclick = () => { if (sel) adjust(-(edits[sel.dataset.l + "|" + sel.dataset.r] || 0)); };
document.getElementById("clear").onclick = () => {
  if (!Object.keys(edits).length || !confirm("Сбросить все правки?")) return;
  edits = {}; save(); grid.querySelectorAll("td").forEach(draw); showSel(); count();
};
document.getElementById("copy").onclick = async () => {
  const lines = Object.entries(edits).map(([k, d]) => {
    const [l, r] = k.split("|");
    const p = byKey[k] || { kern: 0 };
    return `${LETTERS[index[l]].label} → ${LETTERS[index[r]].label}: ${fmt(d)} (${d < 0 ? "ближе" : "дальше"}), кернинг ${fmt(p.kern)} → ${fmt(p.kern + d)}`;
  });
  const text = lines.length ? "Zabzy Hand, правки кернинга:\n" + lines.join("\n") : "Правок нет.";
  try { await navigator.clipboard.writeText(text); flash("Скопировано"); }
  catch (e) { prompt("Скопируйте:", text); }
};
function flash(t) {
  const b = document.getElementById("copy"), old = b.textContent;
  b.textContent = t; setTimeout(() => b.textContent = old, 1200);
}
document.addEventListener("keydown", e => {
  if (e.target.tagName === "INPUT") return;
  if (e.key === "-" || e.key === "_") { adjust(-STEP); e.preventDefault(); return; }
  if (e.key === "+" || e.key === "=") { adjust(STEP); e.preventDefault(); return; }
  const mv = { ArrowLeft: [0, -1], ArrowRight: [0, 1], ArrowUp: [-1, 0], ArrowDown: [1, 0] }[e.key];
  if (!mv) return;
  e.preventDefault();
  let i = sel ? index[sel.dataset.l] : 0, j = sel ? index[sel.dataset.r] : 0;
  if (sel) { i = Math.max(0, Math.min(LETTERS.length - 1, i + mv[0])); j = Math.max(0, Math.min(LETTERS.length - 1, j + mv[1])); }
  select(grid.querySelector(`td[data-l="${LETTERS[i].glyph}"][data-r="${LETTERS[j].glyph}"]`));
});

const tryText = document.getElementById("tryText"), trySample = document.getElementById("trySample");
function trySet() { trySample.textContent = tryText.value; }
tryText.addEventListener("input", trySet); trySet();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
