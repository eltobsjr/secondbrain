"""Tokens visuais do SecondBrain, compartilhados pela interface GTK, pelo leitor e pelo grafo.

Uma só fonte de cor, tipografia e espaço (Catppuccin Macchiato no escuro, Latte no claro), para que as
três superfícies (GTK, leitor em WebKit, grafo em WebKit) não divirjam. Regras de leitura do redesign:
texto de apoio nunca abaixo de 12 px, interface em 14 px, leitura em 16 px com linha de até 68 caracteres,
contraste do texto secundário acima de 4,5:1, e a cor nunca é a única pista (status e tipo têm texto).
"""

DARK = {
    "crust": "#181926", "mantle": "#1e2030", "base": "#24273a", "s0": "#363a4f", "s1": "#494d64",
    "text": "#cad3f5", "sub1": "#b8c0e0", "sub0": "#a5adcb",
    "blue": "#8aadf4", "lav": "#b7bdf8", "green": "#a6da95", "peach": "#f5a97f",
    "red": "#ed8796", "mauve": "#c6a0f6", "teal": "#8bd5ca", "yellow": "#eed49f",
    "on_accent": "#181926", "warn_s": "#f5a97f", "ok_s": "#a6da95",
}
LIGHT = {
    "crust": "#dce0e8", "mantle": "#e6e9ef", "base": "#eff1f5", "s0": "#ccd0da", "s1": "#bcc0cc",
    "text": "#4c4f69", "sub1": "#5c5f77", "sub0": "#656880",
    "blue": "#1e66f5", "lav": "#7287fd", "green": "#40a02b", "peach": "#c4500a",
    "red": "#d20f39", "mauve": "#8839ef", "teal": "#137a80", "yellow": "#a8650c",
    "on_accent": "#eff1f5", "warn_s": "#8f3800", "ok_s": "#2b7a1c",      # versões fortes: texto claro ou texto sobre cinza com 4,5:1 ou mais
}

# cores de projeto (ordem estável): as mesmas do logo e do app
PALETTE = ["#8aadf4", "#a6da95", "#f5a97f", "#c6a0f6", "#eed49f", "#8bd5ca", "#ed8796", "#f5bde6", "#91d7e3",
           "#b7bdf8", "#f0c6c6", "#7dc4e4", "#e8c07a", "#8fc4a0", "#c99ad9", "#7fb3d5", "#d99a9a", "#a8c98a"]

FONT_UI = 'Inter, "Cantarell", system-ui, sans-serif'
FONT_MONO = '"JetBrains Mono", "Source Code Pro", ui-monospace, monospace'


def tokens(dark):
    return DARK if dark else LIGHT


def css_vars(dark, selector=":root"):
    """Variáveis CSS para as páginas em WebKit (leitor, grafo, quadro)."""
    t = tokens(dark)
    body = ";".join(f"--{k.replace('_', '-')}:{v}" for k, v in t.items())
    return f"{selector}{{{body}}}"


def gtk_css(dark):
    """Folha de estilo da parte nativa. Classes `sb-*` são aplicadas pelos widgets de gui/secondbrain_gui.py."""
    t = tokens(dark)
    return f"""
window.sb-win {{ background-color: {t['base']}; color: {t['text']}; }}
window.sb-win headerbar {{ background-color: {t['base']}; box-shadow: none; border-bottom: 1px solid {t['s0']}; }}

.sb-side {{ background-color: {t['mantle']}; }}
.sb-brand {{ font-size: 16px; font-weight: 700; color: {t['text']}; }}
.sb-section {{ font-size: 12px; font-weight: 600; color: {t['sub0']}; }}
.sb-foot {{ font-size: 12px; color: {t['sub0']}; }}

.sb-list {{ background: transparent; }}
.sb-list > row {{ background: transparent; color: {t['sub1']}; border-radius: 10px; margin: 1px 0; padding: 0 12px; min-height: 38px; font-size: 14px; }}
.sb-list > row:hover {{ background-color: alpha({t['s0']}, 0.55); }}
.sb-list > row:selected {{ background-color: {t['s0']}; color: {t['text']}; }}
.sb-list .sb-count {{ font-size: 12px; color: {t['sub0']}; }}
.sb-list .sb-warn {{ font-size: 12px; font-weight: 600; color: {t['peach']}; }}
.sb-list .sb-badge {{ font-size: 11px; font-weight: 600; color: {t['sub0']}; border: 1px solid {t['s1']}; border-radius: 6px; padding: 0 5px; min-height: 0; }}

.sb-column {{ background-color: {t['base']}; border-right: 1px solid {t['s0']}; }}
entry.sb-search, searchentry.sb-search {{ min-height: 44px; border-radius: 12px; background-color: {t['mantle']}; border: 1px solid {t['s0']}; padding: 0 12px; font-size: 14px; box-shadow: none; color: {t['text']}; }}
entry.sb-search:focus-within, searchentry.sb-search:focus-within {{ border-color: {t['blue']}; }}

.sb-seg {{ background-color: {t['mantle']}; border-radius: 10px; padding: 3px; }}
.sb-seg button {{ border: none; box-shadow: none; background: transparent; min-height: 30px; padding: 0 10px; border-radius: 8px; color: {t['sub0']}; font-size: 13px; font-weight: 500; }}
.sb-seg button:checked {{ background-color: {t['s0']}; color: {t['text']}; }}
.sb-seg button:hover:not(:checked) {{ color: {t['text']}; }}

.sb-filter {{ background: transparent; border: none; box-shadow: none; padding: 0; }}
.sb-filter > button {{ border: none; box-shadow: none; background-color: {t['s0']}; border-radius: 999px; min-height: 28px; padding: 0 12px; font-size: 13px; color: {t['sub1']}; }}
.sb-filter > button:hover {{ background-color: {t['s1']}; }}
.sb-count-line {{ font-size: 12px; color: {t['sub0']}; }}

.sb-cards {{ background: transparent; }}
.sb-cards > row {{ background: transparent; border-radius: 12px; margin: 2px 8px; padding: 0; border: 1px solid transparent; }}
.sb-cards > row:hover {{ background-color: alpha({t['s0']}, 0.45); }}
.sb-cards > row:selected {{ background-color: {t['s0']}; border-color: {t['s1']}; }}
.sb-title {{ font-size: 15px; font-weight: 600; color: {t['text']}; }}
.sb-meta {{ font-size: 12px; color: {t['sub0']}; }}
.sb-snip {{ font-size: 13px; color: {t['sub1']}; }}
.sb-sens {{ font-size: 11px; font-weight: 600; color: {t['peach']}; border: 1px solid {t['peach']}; border-radius: 6px; padding: 0 5px; min-height: 0; }}

.sb-page-title {{ font-size: 24px; font-weight: 700; color: {t['text']}; }}
.sb-empty {{ font-size: 14px; color: {t['sub0']}; }}
"""


def reader_css(dark):
    """Leitor de notas: 16 px / 1,7, linha de até 68 caracteres, sem rótulos pálidos em maiúsculas."""
    return css_vars(dark) + f"""
*{{box-sizing:border-box}}
html{{background:var(--base)}}
body{{font:16px/1.7 {FONT_UI};color:var(--text);background:var(--base);margin:0;padding:36px 48px 64px}}
.page{{max-width:680px;margin:0 auto}}
.crumb{{font-size:13px;color:var(--sub0);margin-bottom:10px}}
h1{{font-size:28px;line-height:1.25;font-weight:700;letter-spacing:-.015em;margin:0 0 14px}}
h2{{font-size:20px;line-height:1.3;font-weight:600;margin:1.8em 0 .5em}}
h3{{font-size:17px;font-weight:600;margin:1.4em 0 .4em}}
p,li{{margin:.55em 0}}ul,ol{{padding-left:1.4em}}
a{{color:var(--blue);text-decoration:none}}a:hover{{text-decoration:underline}}
code{{font-family:{FONT_MONO};font-size:.88em;background:var(--mantle);color:var(--teal);padding:.12em .4em;border-radius:6px}}
pre{{background:var(--mantle);padding:14px 16px;border-radius:12px;overflow:auto;line-height:1.5}}pre code{{background:none;padding:0;color:var(--text)}}
table{{border-collapse:collapse;width:100%;margin:1em 0;font-size:14px}}td,th{{border:1px solid var(--s0);padding:7px 11px;text-align:left}}th{{background:var(--mantle);font-weight:600}}
blockquote{{margin:1em 0;padding:12px 18px;background:var(--mantle);border-radius:12px;color:var(--sub1)}}blockquote p{{margin:.3em 0}}
hr{{border:0;border-top:1px solid var(--s0);margin:2em 0}}
.chips{{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 28px}}
.chip{{display:inline-flex;align-items:center;height:24px;padding:0 10px;border-radius:999px;background:var(--s0);color:var(--sub1);font-size:12px;font-weight:500}}
.chip.warn{{color:var(--peach)}}.chip.ok{{color:var(--green)}}.chip.kind{{color:var(--mauve)}}
.layout{{display:grid;grid-template-columns:minmax(0,680px) 272px;gap:56px;justify-content:center}}
.ctx{{font-size:14px}}
.ctx h3{{font-size:12px;font-weight:600;color:var(--sub0);margin:0 0 10px;letter-spacing:.02em}}
.ctx .blk{{margin:0 0 30px}}
.ctx ul{{list-style:none;padding:0;margin:0}}.ctx li{{margin:0 0 12px;line-height:1.4}}
.ctx .toc a{{color:var(--sub1)}}.ctx .toc li.l3{{padding-left:14px}}.ctx .toc a:hover{{color:var(--blue)}}
.ctx .todo{{display:flex;gap:10px;align-items:flex-start}}.ctx .todo i{{width:8px;height:8px;border-radius:50%;background:var(--peach);margin-top:7px;flex:none}}
.ctx .todo.done i{{background:var(--green)}}.ctx .todo.done span{{color:var(--sub0);text-decoration:line-through}}
.toc-narrow{{display:none}}
@media (max-width:1060px){{
  .layout{{display:block}}.page{{max-width:680px}}
  .ctx{{margin-top:48px;border-top:1px solid var(--s0);padding-top:24px}}
  .toc-wide{{display:none}}.toc-narrow{{display:block;margin:0 0 28px;padding:14px 18px;background:var(--mantle);border-radius:12px}}
  .toc-narrow h3{{font-size:12px;font-weight:600;color:var(--sub0);margin:0 0 8px}}.toc-narrow ul{{list-style:none;padding:0;margin:0}}.toc-narrow li{{margin:4px 0;font-size:14px}}
}}
.inact{{opacity:.6;text-decoration:line-through}}.tag{{display:block;font-size:12px;color:var(--sub0)}}
.path{{font-size:12px;color:var(--sub0);word-break:break-all;margin-top:28px;font-family:{FONT_MONO}}}
"""
