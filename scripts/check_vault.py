#!/usr/bin/env python3
"""Verifica a integridade de um vault SecondBrain (somente leitura, sem modelo).

Confere: manifesto x pastas reais, [[links]], frontmatter, INDEX.md, ESTADO.md,
e os caminhos citados no CLAUDE.md do projeto e no MEMORY.md da memória.
Uso: check_vault.py <vault> [--json]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _vault import SKIP_DIRS, md_files, read_manifest  # noqa: E402

LINK = re.compile(r"!?\[\[([^\]\n]+?)\]\]")
FENCE = re.compile(r"```.*?```|`[^`\n]+`", re.S)


def mem_dir(project):
    return os.path.expanduser("~/.claude/projects/" + re.sub(r"[^A-Za-z0-9]", "-", project) + "/memory")


def all_notes(vault):
    out = []
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        out += [os.path.join(root, f) for f in files if f.endswith(".md")]
    return out


def build_index(vault):
    """Conjuntos para resolver wikilinks no estilo do Obsidian."""
    rels, base = set(), {}
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), vault)
            rels.add(rel.lower())
            stem = f[:-3] if f.endswith(".md") else f
            base.setdefault(stem.lower(), set()).add(rel.lower())
            base.setdefault(f.lower(), set()).add(rel.lower())
    return rels, base


def resolves(target, rels, base):
    t = target.split("|")[0].split("#")[0].strip().replace("\\", "")
    if not t:
        return True  # [[#cabeçalho]] ou vazio
    t = t.lower()
    cands = [t, t + ".md"]
    if any(c in rels for c in cands):
        return True
    stem = os.path.basename(t)
    stem = stem[:-3] if stem.endswith(".md") else stem
    hits = base.get(stem, set()) | base.get(os.path.basename(t), set())
    if "/" in t:
        suffix = t if t.endswith(".md") else t + ".md"
        return any(h.endswith("/" + suffix) or h == suffix for h in hits)
    return bool(hits)


def broken_links(vault):
    rels, base = build_index(vault)
    bad = []
    for p in all_notes(vault):
        try:
            text = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        body = FENCE.sub("", text)
        for m in LINK.finditer(body):
            if not resolves(m.group(1), rels, base):
                bad.append((os.path.relpath(p, vault), m.group(1)))
    return bad


def bad_frontmatter(vault):
    bad = []
    for p in all_notes(vault):
        try:
            head = open(p, encoding="utf-8", errors="ignore").read(6000)
        except OSError:
            continue
        if head.startswith("---") and not re.match(r"---\r?\n.*?\r?\n---", head, re.S):
            bad.append(os.path.relpath(p, vault))
    return bad


PATH_TOKEN = re.compile(r"(?:(?<=`)|(?<=\s)|^)((?:/home/user|~)/[^\s`'\")\]]+)")


def claude_md_paths(project, claude_files):
    missing = []
    for cf in claude_files:
        text = open(cf, encoding="utf-8", errors="ignore").read()
        for raw in set(PATH_TOKEN.findall(text)):
            p = raw.rstrip(".,;:)")
            if any(c in p for c in "*{}<>$|") or "…" in p or "..." in p:
                continue
            full = os.path.expanduser(p.replace("/home/user", "~", 1))
            if not os.path.exists(full):
                missing.append((os.path.relpath(cf, os.path.dirname(project)) if cf.startswith(project) else cf, raw))
    return missing


def memory_issues(project):
    md = mem_dir(project)
    idx = os.path.join(md, "MEMORY.md")
    if not os.path.isdir(md):
        return {"sem_memoria": True}
    out = {"links_quebrados": [], "orfas": [], "linhas": 0, "bytes": 0}
    if not os.path.isfile(idx):
        out["sem_indice"] = True
        return out
    text = open(idx, encoding="utf-8", errors="ignore").read()
    out["linhas"], out["bytes"] = text.count("\n") + 1, len(text.encode())
    linked = set(re.findall(r"\]\(([^)]+\.md)\)", text))
    for f in linked:
        if not os.path.isfile(os.path.join(md, f)):
            out["links_quebrados"].append(f)
    files = {f for f in os.listdir(md) if f.endswith(".md") and f != "MEMORY.md"}
    out["orfas"] = sorted(files - linked)
    return out


def check(vault):
    vault = vault.rstrip("/")
    project = os.path.dirname(vault)
    res = {"vault": os.path.basename(vault), "projeto": project}
    mf = os.path.join(vault, "_secondbrain.md")
    res["manifesto"] = os.path.isfile(mf)
    res["papeis_ausentes"], res["extras_ausentes"] = [], []
    if res["manifesto"]:
        papeis, extras = read_manifest(vault)
        for role, path in papeis.items():
            if not os.path.exists(os.path.join(vault, path)):
                res["papeis_ausentes"].append(f"{role}: {path}")
        for path, _ in extras:
            if not os.path.exists(os.path.join(vault, path)):
                res["extras_ausentes"].append(path)
    res["links_quebrados"] = broken_links(vault)
    res["frontmatter_quebrado"] = bad_frontmatter(vault)
    claudes = []
    for root, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS | {"build", "dist", ".dart_tool", "Pods"}
                   and not d.startswith(".") and not d.endswith("SecondBrain")]
        if root.count(os.sep) - project.count(os.sep) > 2:
            dirs[:] = []
        if "CLAUDE.md" in files:
            claudes.append(os.path.join(root, "CLAUDE.md"))
    res["claude_md"] = [os.path.relpath(c, project) for c in claudes]
    res["claude_md_caminhos_ausentes"] = claude_md_paths(project, claudes)
    res["memoria"] = memory_issues(project)
    return res


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or not os.path.isdir(args[0]):
        sys.exit("uso: check_vault.py <vault> [--json]")
    r = check(args[0])
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return
    print(f"== {r['vault']}")
    print(f"  manifesto: {'ok' if r['manifesto'] else 'AUSENTE'}; papéis ausentes: {r['papeis_ausentes'] or 'nenhum'}; extras ausentes: {r['extras_ausentes'] or 'nenhum'}")
    print(f"  links quebrados: {len(r['links_quebrados'])}; frontmatter quebrado: {len(r['frontmatter_quebrado'])}")
    print(f"  CLAUDE.md: {r['claude_md'] or 'nenhum'}; caminhos inexistentes citados: {len(r['claude_md_caminhos_ausentes'])}")
    m = r["memoria"]
    print(f"  memória: {m if m.get('sem_memoria') or m.get('sem_indice') else str(m['linhas']) + ' linhas, ' + str(m['bytes']) + ' B, links quebrados ' + str(len(m['links_quebrados'])) + ', órfãs ' + str(len(m['orfas']))}")


if __name__ == "__main__":
    main()
