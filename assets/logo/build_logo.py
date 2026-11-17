#!/usr/bin/env python3
"""Gera os SVGs do logo do SecondBrain (reprodutível). Uso: python3 build_logo.py

Conceito: um S traçado por três nós ligados (letra e grafo ao mesmo tempo). Dois arcos de mesmo raio,
junção no centro (128,128), simetria de 180°. Os vãos entre arcos e nós descontam a ponta arredondada
do traço. Paleta Catppuccin Macchiato (a mesma da família Eltob Indicator).
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BLUE, MAUVE, BASE = "#8aadf4", "#c6a0f6", "#24273a"

NORMAL = dict(R=50.0, SW=18.0, RN_END=17.0, RN_MID=12.0, GAP=9.0, ANG=28.0)
SMALL = dict(R=50.0, SW=26.0, RN_END=22.0, RN_MID=15.0, GAP=10.0, ANG=28.0)  # corte para 16–32 px


def mark(p, arc, node):
    R, SW = p["R"], p["SW"]
    cap = SW / 2
    cy1 = 128 - R
    pt = lambda ang: (128 + R * math.cos(math.radians(ang)), cy1 - R * math.sin(math.radians(ang)))
    a0 = p["ANG"] + math.degrees((p["RN_END"] + p["GAP"] + cap) / R)
    a1 = 270 - math.degrees((p["RN_MID"] + p["GAP"] + cap) / R)
    s1, e1, n1 = pt(a0), pt(a1), pt(p["ANG"])
    mir = lambda q: (256 - q[0], 256 - q[1])
    s2, e2, n3 = mir(e1), mir(s1), mir(n1)
    large = 1 if a1 - a0 > 180 else 0
    f = lambda v: f"{v:.1f}"
    return (f'<g fill="none" stroke="{arc}" stroke-width="{SW:g}" stroke-linecap="round">'
            f'<path d="M{f(s1[0])} {f(s1[1])}A{R:g} {R:g} 0 {large} 0 {f(e1[0])} {f(e1[1])}"/>'
            f'<path d="M{f(s2[0])} {f(s2[1])}A{R:g} {R:g} 0 {large} 1 {f(e2[0])} {f(e2[1])}"/></g>'
            f'<g fill="{node}"><circle cx="{f(n1[0])}" cy="{f(n1[1])}" r="{p["RN_END"]:g}"/>'
            f'<circle cx="128" cy="128" r="{p["RN_MID"]:g}"/>'
            f'<circle cx="{f(n3[0])}" cy="{f(n3[1])}" r="{p["RN_END"]:g}"/></g>')


def svg(inner, title, tile=False, scale=0.76):
    body = inner
    if tile:
        body = (f'<rect width="256" height="256" rx="56" fill="{BASE}"/>'
                f'<g transform="translate(128 128) scale({scale}) translate(-128 -128)">{inner}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img"><title>{title}</title>{body}</svg>\n')


def write(name, content):
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
        fh.write(content)
    print("escrito", name)


write("secondbrain-mark.svg", svg(mark(NORMAL, "#000000", "#000000"), "SecondBrain"))
write("secondbrain-mark-color.svg", svg(mark(NORMAL, BLUE, MAUVE), "SecondBrain (para fundo escuro)"))
write("secondbrain-icon.svg", svg(mark(NORMAL, BLUE, MAUVE), "SecondBrain", tile=True))
write("secondbrain-icon-small.svg", svg(mark(SMALL, BLUE, MAUVE), "SecondBrain (corte pequeno)", tile=True, scale=0.82))
