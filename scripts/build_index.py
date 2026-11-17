#!/usr/bin/env python3
"""Gera o INDEX.md de um vault: mapa de navegação para humanos e para IA.

Sem modelo, sem rede: lê o manifesto e o frontmatter/H1 das notas. Seguro para rodar sempre
(só escreve INDEX.md). Uso: build_index.py <vault> [--stdout]
"""
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _vault import first_h1, md_files, read_manifest, split_frontmatter  # noqa: E402

LIMITS = {"devtrack": 12, "commits": 8}
DEFAULT_LIMIT = 40
ROLE_TITLES = {"devtrack": "Devtracks", "decisoes": "Decisões", "features": "Features",
               "rfcs": "RFCs", "postmortems": "Postmortems", "releases": "Releases",
               "commits": "Commits", "prioridade": "Prioridades", "analise": "Análises"}


def entry(vault, path):
    rel = os.path.relpath(path, vault)
    stem = rel[:-3]
    try:
        text = open(path, encoding="utf-8", errors="ignore").read(6000)
    except OSError:
        return None
    fm, body = split_frontmatter(text)
    title = first_h1(body) or os.path.basename(stem)
    base = os.path.basename(stem)
    meta = [fm.get(k) for k in ("tipo", "data", "status") if fm.get(k)]
    norm = lambda x: re.sub(r"\W+", "", x.lower())
    redundante = norm(title) in norm(base) or norm(title.split(":", 1)[-1]) in norm(base)
    t = "" if redundante else title
    t = (t[:90] + "…") if len(t) > 90 else t
    line = f"- [[{stem}]]" + (f" — {t}" if t else "") + (f" · {' · '.join(meta)}" if meta else "")
    return line.replace("|", "\\|")


def section(vault, title, relpath, role=None):
    full = os.path.join(vault, relpath)
    if os.path.isfile(full):
        files = [full]
    elif os.path.isdir(full):
        files = md_files(full)
    else:
        return []
    if not files:
        return []
    recent_first = role == "devtrack"
    files = sorted(files, key=lambda p: os.path.relpath(p, vault), reverse=recent_first)
    limit = LIMITS.get(role, DEFAULT_LIMIT)
    out = [f"## {title} ({len(files)})", f"`{relpath}`", ""]
    for p in files[:limit]:
        e = entry(vault, p)
        if e:
            out.append(e)
    if len(files) > limit:
        out.append(f"- … mais {len(files) - limit} notas em `{relpath}` "
                   f"({'as mais recentes acima' if recent_first else 'liste a pasta para ver todas'})")
    out.append("")
    return out


def build(vault):
    papeis, extras = read_manifest(vault)
    name = os.path.basename(os.path.abspath(vault)).replace("SecondBrain", "") or "projeto"
    body, total, seen = [], 0, set()
    for role, path in papeis.items():
        if role in ("estado", "indice"):
            continue
        sec = section(vault, ROLE_TITLES.get(role, role.capitalize()), path, role)
        if sec:
            body += sec
        seen.add(path.rstrip("/").split("/")[0])
    for path, desc in extras:
        top = path.rstrip("/")
        if top in seen:
            continue
        sec = section(vault, f"{top} — {desc}" if desc else top, path)
        if sec:
            body += sec
    roots = [f for f in sorted(os.listdir(vault))
             if f.endswith(".md") and f not in ("INDEX.md", "_secondbrain.md", "README.md")]
    head = []
    if roots:
        head = ["## Raiz do vault", ""] + [f"- [[{f[:-3]}]]" for f in roots] + [""]
    total = sum(1 for ln in head + body if ln.startswith("- [["))
    fm = ["---", "tipo: indice", f"gerado: {date.today().isoformat()}", "gerado-por: scripts/build_index.py", "---", ""]
    intro = [f"# Índice — {name}", "",
             "> Gerado automaticamente. **Não edite**; rode `build_index.py` (o `/devtrack` já faz isso).",
             "> Mapa de pastas e regras do vault: [[_secondbrain]]." + (" Retrato atual: [[ESTADO]]." if os.path.isfile(os.path.join(vault, "ESTADO.md")) else ""), ""]
    return "\n".join(fm + intro + head + body).rstrip() + "\n", total


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or not os.path.isfile(os.path.join(args[0], "_secondbrain.md")):
        sys.exit("uso: build_index.py <vault com _secondbrain.md> [--stdout]")
    vault = args[0].rstrip("/")
    text, n = build(vault)
    if "--stdout" in sys.argv:
        print(text)
        return
    target = os.path.join(vault, "INDEX.md")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"{os.path.basename(vault)}: INDEX.md ({n} entradas, {len(text.encode())//1024} KB)")


if __name__ == "__main__":
    main()
