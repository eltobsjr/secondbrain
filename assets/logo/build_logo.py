#!/usr/bin/env python3
"""Gera os SVGs do logo do SecondBrain (reprodutível). Uso: python3 build_logo.py

Conceito: um cérebro de perfil cuja rede neural é o S do nome, um S traçado por três nós ligados.
As dobras só partem da borda (fissura lateral, sulco do topo, dobra occipital): nada de rabiscos
internos, que formam rosto. Paleta Catppuccin Macchiato (a mesma da família Eltob Indicator).

Saídas:
  secondbrain-icon.svg        ícone com fundo (principal)
  secondbrain-icon-small.svg  corte para 16-48 px (traço e nós mais grossos, só duas dobras)
  secondbrain-mark.svg        marca em linha, um só tom (preto), fundo transparente
  secondbrain-mark-color.svg  marca em linha colorida, para fundo escuro
  s-mark*.svg                 monograma antigo (só o S), uso alternativo
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BLUE, MAUVE, BASE = "#8aadf4", "#c6a0f6", "#24273a"

BRAIN = ("M48 120C44 88 66 60 100 54C122 36 164 36 184 52C214 56 232 84 226 114"
         "C224 128 214 140 200 142C186 144 176 140 168 146C166 166 148 178 126 176"
         "C112 190 84 192 70 178C56 166 62 152 70 148C52 146 46 134 48 120Z")
SULCUS_TOP, SYLVIAN, OCCIPITAL = "M172 41C168 52 176 58 170 68", "M215 136C198 130 188 130 176 122", "M50 112C62 108 68 112 76 106"
STEM = '<rect x="121" y="178" width="14" height="30" rx="7"{fill}/>'
STEM_SMALL = '<rect x="117" y="176" width="22" height="34" rx="11"{fill}/>'

S_NORMAL = dict(R=50.0, SW=18.0, CAP=9.0, RN_E=17.0, RN_M=12.0, GAP=9.0, ANG=28.0)
S_SMALL = dict(R=50.0, SW=24.0, CAP=12.0, RN_E=21.0, RN_M=15.0, GAP=9.0, ANG=28.0)


def smark(cx, cy, k, p, col, node_col, accent=True):
    """S de três nós (dois arcos de mesmo raio, junção no centro), escalado por k e centrado em (cx, cy)."""
    R = p["R"]
    c1 = 128 - R
    pt = lambda a: (128 + R * math.cos(math.radians(a)), c1 - R * math.sin(math.radians(a)))
    a0 = p["ANG"] + math.degrees((p["RN_E"] + p["GAP"] + p["CAP"]) / R)
    a1 = 270 - math.degrees((p["RN_M"] + p["GAP"] + p["CAP"]) / R)
    s1, e1, n1 = pt(a0), pt(a1), pt(p["ANG"])
    mir = lambda q: (256 - q[0], 256 - q[1])
    s2, e2, n3 = mir(e1), mir(s1), mir(n1)
    T = lambda q: (cx + (q[0] - 128) * k, cy + (q[1] - 128) * k)
    S1, E1, S2, E2, N1, N3 = [T(q) for q in (s1, e1, s2, e2, n1, n3)]
    r = R * k
    large = 1 if a1 - a0 > 180 else 0
    f = lambda v: f"{v:.1f}"
    out = (f'<g fill="none" stroke="{col}" stroke-width="{p["SW"] * k:.1f}" stroke-linecap="round">'
           f'<path d="M{f(S1[0])} {f(S1[1])}A{r:.1f} {r:.1f} 0 {large} 0 {f(E1[0])} {f(E1[1])}"/>'
           f'<path d="M{f(S2[0])} {f(S2[1])}A{r:.1f} {r:.1f} 0 {large} 1 {f(E2[0])} {f(E2[1])}"/></g>'
           f'<g fill="{col}"><circle cx="{f(N1[0])}" cy="{f(N1[1])}" r="{p["RN_E"] * k:.1f}"/>'
           f'<circle cx="{cx}" cy="{cy}" r="{p["RN_M"] * k:.1f}"/>'
           f'<circle cx="{f(N3[0])}" cy="{f(N3[1])}" r="{p["RN_E"] * k:.1f}"/></g>')
    if accent:
        out += f'<circle cx="{f(N1[0])}" cy="{f(N1[1])}" r="{p["RN_E"] * k * 0.45:.1f}" fill="{node_col}"/>'
    return out


def svg(body, title):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img"><title>{title}</title>{body}</svg>\n'


def tile(body):
    return f'<rect width="256" height="256" rx="56" fill="{BASE}"/>{body}'


def folds(width, which):
    paths = {"top": SULCUS_TOP, "syl": SYLVIAN, "occ": OCCIPITAL}
    return (f'<g fill="none" stroke="{BASE}" stroke-width="{width}" stroke-linecap="round">'
            + "".join(f'<path d="{paths[w]}"/>' for w in which) + "</g>")


def write(name, content):
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
        fh.write(content)
    print("escrito", name)


# --- ícone com fundo (cérebro cheio; dobras e S em negativo, na cor do fundo) ---
icon = (f'<path d="{BRAIN}" fill="{BLUE}"/>' + STEM.format(fill=f' fill="{BLUE}"')
        + folds(5, ("top", "syl", "occ")) + smark(128, 104, 0.47, S_NORMAL, BASE, MAUVE))
write("secondbrain-icon.svg", svg(tile(icon), "SecondBrain"))

# --- corte pequeno (16-48 px): sem a dobra occipital, S e nós mais grossos ---
small = (f'<path d="{BRAIN}" fill="{BLUE}"/>' + STEM_SMALL.format(fill=f' fill="{BLUE}"')
         + folds(8, ("top", "syl")) + smark(128, 104, 0.55, S_SMALL, BASE, MAUVE))
write("secondbrain-icon-small.svg", svg(tile(small), "SecondBrain (corte pequeno)"))


# --- marca em linha: sem negativo, funciona em qualquer fundo ---
def line_mark(col, node_col, accent):
    return (f'<path d="{BRAIN}" fill="none" stroke="{col}" stroke-width="8" stroke-linejoin="round"/>'
            + STEM.format(fill=f' fill="{col}"')
            + f'<g fill="none" stroke="{col}" stroke-width="5.5" stroke-linecap="round">'
              f'<path d="{SULCUS_TOP}"/><path d="{SYLVIAN}"/><path d="{OCCIPITAL}"/></g>'
            + smark(128, 104, 0.47, S_NORMAL, col, node_col, accent))


write("secondbrain-mark.svg", svg(line_mark("#000000", "#000000", False), "SecondBrain"))
write("secondbrain-mark-color.svg", svg(line_mark(BLUE, MAUVE, True), "SecondBrain (para fundo escuro)"))

# --- monograma antigo (só o S), uso alternativo ---
write("s-mark.svg", svg(smark(128, 128, 1.0, dict(S_NORMAL), "#000000", "#000000", False), "SecondBrain S"))
write("s-icon.svg", svg(tile(smark(128, 128, 0.78, dict(S_NORMAL), BLUE, MAUVE)), "SecondBrain S"))
