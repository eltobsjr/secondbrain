#!/usr/bin/env python3
"""Infere o manifesto `_secondbrain.md` de um vault SecondBrain existente.

Somente leitura por padrão: imprime o manifesto proposto (dry-run).
Com --write, grava APENAS `_secondbrain.md` (e só se ele ainda não existir).
Nunca move, renomeia nem apaga nada.

Uso: infer_manifest.py <pasta-do-vault> [--write]
"""
import os
import re
import subprocess
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _vault import detectar_repos  # noqa: E402

ALIASES = {
    "devtrack": ["devtrack"],
    "decisoes": ["decisions", "decisoes", "decisões", "adr"],
    "features": ["features", "hus", "hu", "docs/hu"],
    "rfcs": ["rfcs", "rfc"],
    "postmortems": ["postmortems", "postmortem"],
    "releases": ["releases"],
    "commits": ["commits"],
    "analise": ["analise", "análise"],
    "prioridade": ["prioridade", "prioridades"],
}
KNOWN_DESC = {
    "telas": "Mapa de telas e rotas",
    "api": "Contrato e notas da API",
    "components": "Notas de componentes",
    "docs": "Documentação de apoio",
    "análise": "Relatórios gerados pelo /analyze",
    "analise": "Relatórios gerados pelo /analyze",
    "auditorias": "Auditorias e revisões",
    "metodos": "Como gerar as notas e os artefatos",
    "arquitetura": "Arquitetura, modelo de dados e diagramas",
    "requisitos": "Requisitos, casos de uso e histórias",
    "entregas": "O que saiu do projeto para terceiros",
    "entrega": "O que saiu do projeto para terceiros",
    "imports": "Dumps e pacotes importados (retratos de data fixa)",
    "diagramas": "Diagramas",
}
SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules"}
BASE_KEYS = {"tipo", "data", "status", "atualizado"}


def notes_in(path):
    out = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.endswith(".md") and f != "README.md":
                out.append(os.path.join(root, f))
    return out


def frontmatter_keys(path):
    try:
        text = open(path, encoding="utf-8").read(4000)
    except OSError:
        return set()
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m:
        return set()
    return {ln.split(":", 1)[0].strip() for ln in m.group(1).splitlines()
            if ":" in ln and not ln.startswith((" ", "-", "#"))}


def detect_name(files):
    names = [os.path.basename(f) for f in files]
    if not names:
        return None
    pats = [(r"^\d{4}-\d{2}-\d{2} - ", "AAAA-MM-DD - Título"),
            (r"^\d{3,4} - ", "NNN - Título"),
            (r"^\d{4}-\d{2}-\d{2}\.md$", "AAAA-MM-DD")]
    for rx, label in pats:
        if sum(bool(re.match(rx, n)) for n in names) >= max(1, len(names) * 0.6):
            return label
    return None


def readme_descriptions(vault):
    """Extrai 'pasta -> descrição' de tabelas/listas de README, Índice ou Convenções."""
    desc = {}
    for cand in ("README.md", "00 - Índice.md", "Convenções.md"):
        p = os.path.join(vault, cand)
        if not os.path.isfile(p):
            continue
        for ln in open(p, encoding="utf-8"):
            m = re.search(r"`([\w\-./áéíóúãõç]+?)/?`\s*[|:\-–]+\s*(.+)", ln)
            if m:
                key = m.group(1).strip("/")
                d = re.sub(r"[|`]", " ", m.group(2)).strip()
                d = re.split(r"\s{2,}|\s\|\s", d)[0].strip()
                if key and d and key not in desc:
                    desc[key] = d[:90]
    return desc


def is_versioned(vault):
    try:
        r = subprocess.run(["git", "-C", os.path.dirname(os.path.abspath(vault)),
                            "check-ignore", "-q", os.path.basename(os.path.abspath(vault))],
                           capture_output=True)
        inside = subprocess.run(["git", "-C", os.path.dirname(os.path.abspath(vault)),
                                 "rev-parse", "--is-inside-work-tree"],
                                capture_output=True)
        if inside.returncode != 0:
            return None
        return r.returncode != 0  # 0 = ignorado
    except OSError:
        return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    write = "--write" in sys.argv
    if not args or not os.path.isdir(args[0]):
        sys.exit("uso: infer_manifest.py <pasta-do-vault> [--write]")
    vault = args[0].rstrip("/")
    name = os.path.basename(os.path.abspath(vault))
    target = os.path.join(vault, "_secondbrain.md")
    if os.path.exists(target):
        sys.exit("_secondbrain.md já existe; nada a inferir.")

    top = sorted(d for d in os.listdir(vault)
                 if os.path.isdir(os.path.join(vault, d)) and d not in SKIP_DIRS
                 and not d.startswith("."))
    papeis, used = {}, set()
    for role, aliases in ALIASES.items():
        for d in top:
            if d.lower() in aliases:
                papeis[role] = d + "/"
                used.add(d)
                break
        else:  # aliases aninhados, ex.: docs/hu
            for a in aliases:
                if "/" in a and os.path.isdir(os.path.join(vault, a)):
                    papeis[role] = a + "/"
                    break
    if "prioridade" in papeis and papeis["prioridade"].endswith("/") and \
            os.path.basename(papeis["prioridade"].rstrip("/")).lower() in ALIASES["prioridade"]:
        # o /board (prioridades) grava sempre em <pasta>/atual.md
        papeis["prioridade"] = papeis["prioridade"] + "atual.md"
    if os.path.isfile(os.path.join(vault, "ESTADO.md")):
        papeis["estado"] = "ESTADO.md"

    descs = readme_descriptions(vault)
    extras = []
    for d in top:
        if d in used or (d == "prioridade"):
            continue
        extras.append((d + "/", descs.get(d) or KNOWN_DESC.get(d.lower()) or "(descrever)"))

    # padrão novo: ESTADO.md faz parte de todo vault (criado no próximo /devtrack se ainda não existir)
    papeis.setdefault("estado", "ESTADO.md")
    papeis.setdefault("indice", "INDEX.md")
    modulos = []
    for role, path in papeis.items():
        full = os.path.join(vault, path)
        if role == "indice":
            continue
        if role == "estado":
            modulos.append(role)
            continue
        if os.path.isdir(full) and not notes_in(full):
            continue
        modulos.append(role)

    nomes, campos = {}, {}
    for role in ("devtrack", "decisoes", "features", "rfcs"):
        if role in papeis and os.path.isdir(os.path.join(vault, papeis[role])):
            files = notes_in(os.path.join(vault, papeis[role]))
            n = detect_name(files)
            if n:
                nomes[role] = n
            if files:
                counts = {}
                for f in files:
                    for k in frontmatter_keys(f):
                        counts[k] = counts.get(k, 0) + 1
                extra = sorted(k for k, c in counts.items()
                               if c >= len(files) * 0.5 and k not in BASE_KEYS)
                if extra:
                    campos[role] = extra

    versioned = is_versioned(vault)
    out = ["---", "schema: 2",
           "versionado: " + ("true" if versioned else "false") +
           ("" if versioned is not None else "   # não é repositório git: confirme"),
           "sensibilidade: normal   # normal | alta (alta = dados de startup/institucional; nunca vai para o git)",
           "backup: true            # false = fora do backup para HD externo",
           "hooks: false", "diataxis: false",
           "modulos: [" + ", ".join(modulos) + "]", "papeis:"]
    out += [f"  {r}: {p}" for r, p in papeis.items()]
    if extras:
        out.append("extras:")
        out += [f'  - {{ path: {p}, descricao: "{d}" }}' for p, d in extras]
    if nomes:
        out.append("nomes:")
        out += [f'  {r}: "{n}"' for r, n in nomes.items()]
    if campos:
        out.append("campos-extra:")
        out += [f"  {r}: [{', '.join(c)}]" for r, c in campos.items()]
    proj_dir = os.path.dirname(os.path.abspath(vault))
    repos = [r for r in detectar_repos(proj_dir, os.path.abspath(vault)) if r["valido"] and not re.search(r"\s", os.path.relpath(r["caminho"], proj_dir))]
    if repos:
        out.append("repos:   # repositórios git do projeto (ativo = conciliação; referencia = só se consulta sob pedido)")
        out += [f"  - {os.path.relpath(r['caminho'], proj_dir)} {r['papel']}" for r in repos]
    out += [f"criado: {date.today().isoformat()}", "migrado-de: legado", "---", "",
            f"# {name.replace('SecondBrain', '')} — Manifesto do vault", "",
            "Mapa humano do vault. Edite livremente; as skills leem o frontmatter acima.", ""]
    text = "\n".join(out)
    if write:
        open(target, "w", encoding="utf-8").write(text)
        print(f"gravado: {target}")
    else:
        print(text)
        print("\n# (dry-run: nada foi gravado; use --write após confirmar)", file=sys.stderr)


if __name__ == "__main__":
    main()
