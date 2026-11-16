#!/usr/bin/env python3
"""Fase 2 da migração: acrescenta `tipo` (e `data`, quando o nome do arquivo tem data)
ao frontmatter das notas de um vault que já tem `_secondbrain.md`.

ADITIVO: nunca altera o corpo nem campos existentes, nunca move/renomeia/apaga.
Dry-run por padrão; use --write para gravar. Idempotente.

Uso: add_frontmatter.py <pasta-do-vault> [--write]
"""
import os
import re
import sys

ROLE_TIPO = {"devtrack": "devtrack", "decisoes": "decisao", "features": "feature",
             "rfcs": "rfc", "postmortems": "postmortem", "releases": "release",
             "commits": "commit", "prioridade": "prioridade", "estado": "estado"}
SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules", "imports"}
MAX_BYTES = 1_000_000


def read_manifest(vault):
    text = open(os.path.join(vault, "_secondbrain.md"), encoding="utf-8").read()
    fm = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    if not fm:
        sys.exit("manifesto sem frontmatter")
    papeis, in_p = {}, False
    for ln in fm.group(1).splitlines():
        if re.match(r"^papeis:", ln):
            in_p = True
            continue
        if in_p:
            m = re.match(r"^\s+([a-z]+):\s*([^#\s][^#]*?)\s*(#.*)?$", ln)
            if m:
                papeis[m.group(1)] = m.group(2).strip()
            elif ln and not ln.startswith(" "):
                in_p = False
    return papeis


def classify(rel, papeis):
    best, best_len = None, -1
    for role, path in papeis.items():
        base = path if path.endswith("/") else (path.rsplit("/", 1)[0] + "/" if "/" in path else "")
        if base and rel.startswith(base) and len(base) > best_len:
            best, best_len = role, len(base)
    if best in ROLE_TIPO:
        return ROLE_TIPO[best]
    name = os.path.basename(rel).lower()
    if "visão geral" in name or "visao geral" in name:
        return "visao-geral"
    if name.startswith("checklist"):
        return "checklist"
    return "nota"


def plan(vault, papeis):
    changes = []
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if not f.endswith(".md") or f in ("README.md", "_secondbrain.md"):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, vault)
            if os.path.getsize(path) > MAX_BYTES:
                continue
            try:
                raw = open(path, "rb").read()
                text = raw.decode("utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if text.startswith("﻿"):
                continue
            nl = "\r\n" if "\r\n" in text[:500] else "\n"
            tipo = classify(rel, papeis)
            dm = re.match(r"(\d{4}-\d{2}-\d{2})\b", f)
            data = dm.group(1) if dm else None
            fm = re.match(r"---\r?\n(.*?)\r?\n---(\r?\n|$)", text, re.S)
            if text.startswith("---") and not fm:
                continue  # frontmatter malformado: não mexer
            if fm:
                keys = {ln.split(":", 1)[0].strip() for ln in fm.group(1).splitlines()
                        if ":" in ln and not ln.startswith((" ", "-", "#"))}
                add = []
                if "tipo" not in keys:
                    add.append(f"tipo: {tipo}")
                if data and not keys & {"data", "date", "criado", "created"}:
                    add.append(f"data: {data}")
                if add:
                    new = text[:3] + nl + nl.join(add) + text[3:]
                    changes.append((path, rel, add, new))
            else:
                add = [f"tipo: {tipo}"] + ([f"data: {data}"] if data else [])
                new = "---" + nl + nl.join(add) + nl + "---" + nl + nl + text
                changes.append((path, rel, add, new))
    return changes


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or not os.path.isfile(os.path.join(args[0], "_secondbrain.md")):
        sys.exit("uso: add_frontmatter.py <vault com _secondbrain.md> [--write]")
    vault = args[0].rstrip("/")
    changes = plan(vault, read_manifest(vault))
    by = {}
    for _, rel, add, _ in changes:
        by[add[0]] = by.get(add[0], 0) + 1
    print(f"{os.path.basename(vault)}: {len(changes)} nota(s) a ajustar", dict(sorted(by.items())))
    if "--write" in sys.argv:
        for path, _, _, new in changes:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(new)
        print("  gravado.")
    elif changes:
        print("  exemplo:", changes[0][1], "->", " | ".join(changes[0][2]))


if __name__ == "__main__":
    main()
