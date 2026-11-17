"""Utilitários compartilhados dos scripts do SecondBrain (somente stdlib)."""
import os
import re

SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules", "imports"}


def read_manifest(vault):
    """Retorna (papeis, extras) lidos do frontmatter de _secondbrain.md."""
    text = open(os.path.join(vault, "_secondbrain.md"), encoding="utf-8").read()
    fm = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    if not fm:
        raise SystemExit("manifesto sem frontmatter")
    papeis, extras, sec = {}, [], None
    for ln in fm.group(1).splitlines():
        if re.match(r"^(papeis|extras):", ln):
            sec = ln.split(":")[0]
            continue
        if ln and not ln.startswith((" ", "\t")):
            sec = None
        if sec == "papeis":
            m = re.match(r"^\s+([a-z]+):\s*([^#\s][^#]*?)\s*(#.*)?$", ln)
            if m:
                papeis[m.group(1)] = m.group(2).strip()
        elif sec == "extras":
            m = re.search(r"path:\s*([^,}]+),\s*descricao:\s*\"([^\"]*)\"", ln)
            if m:
                extras.append((m.group(1).strip(), m.group(2)))
    return papeis, extras


def split_frontmatter(text):
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
    if not m:
        return {}, text
    fm = {}
    for ln in m.group(1).splitlines():
        if ":" in ln and not ln.startswith((" ", "-", "#")):
            k, v = ln.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm, text[m.end():]


def first_h1(body):
    for ln in body.splitlines()[:40]:
        if ln.startswith("# "):
            return ln[2:].strip()
    return None


def md_files(path):
    out = []
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for f in sorted(files):
            if f.endswith(".md") and f not in ("README.md", "_secondbrain.md", "INDEX.md"):
                out.append(os.path.join(root, f))
    return out
