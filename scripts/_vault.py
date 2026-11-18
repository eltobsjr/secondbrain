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


def detectar_repos(proj, vault_abs):
    """Repositórios git até 2 níveis abaixo da pasta do projeto, fora do vault. Os que estão numa pasta `referencias` entram como `referencia`."""
    out = []
    for root, dirs, _ in os.walk(proj):
        depth = root[len(proj):].count(os.sep)
        if os.path.abspath(root) == vault_abs:
            dirs[:] = []
            continue
        if ".git" in dirs or os.path.isfile(os.path.join(root, ".git")):
            ref = any(p in ("referencias", "references", "referencia") for p in os.path.relpath(root, proj).split(os.sep))
            valido = _repo_valido(root)
            out.append({"caminho": root, "papel": "referencia" if ref else "ativo", "declarado": False, "valido": valido})
            if valido:
                dirs[:] = []
                continue
            # `.git` que o git não reconhece: sinaliza e continua descendo, porque os repositórios de dentro podem ser válidos
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "build", "target", ".venv", "venv") and not d.endswith("SecondBrain")] if depth < 2 else []
    return sorted(out, key=lambda r: r["caminho"])


def _repo_valido(path):
    import subprocess
    try:
        return subprocess.run(["git", "-C", path, "rev-parse", "--git-dir"], capture_output=True).returncode == 0
    except OSError:
        return False


def read_repos(vault):
    """[{caminho, papel, declarado, valido}] dos repositórios git do projeto.

    Declarados no manifesto, na chave `repos:` (um por linha, relativo à pasta do projeto, ao lado do vault):
        repos:
          - ds-evidencia ativo
          - referencias/repo-antigo referencia      # só se consulta sob pedido
    `ativo` entra na conciliação; `referencia` só com --incluir-referencias. Sem a chave, detecta repositórios até 2 níveis
    abaixo da pasta do projeto; os que estão numa pasta `referencias`/`references` entram como `referencia`.
    `valido` é falso quando existe `.git` mas o git não o reconhece (repositório quebrado)."""
    proj = os.path.dirname(os.path.abspath(vault))
    text = open(os.path.join(vault, "_secondbrain.md"), encoding="utf-8").read()
    fm = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    decl, sec = [], None
    for ln in (fm.group(1).splitlines() if fm else []):
        if re.match(r"^repos:\s*(#.*)?$", ln):
            sec = "repos"
            continue
        if ln and not ln.startswith((" ", "\t")):
            sec = None
        m = re.match(r"^\s+-\s+(\S+)(?:\s+(ativo|referencia))?\s*(#.*)?$", ln) if sec == "repos" else None
        if m:
            decl.append((os.path.normpath(os.path.join(proj, m.group(1))), m.group(2) or "ativo"))
    out = []
    if decl:
        for path, papel in decl:
            if os.path.exists(os.path.join(path, ".git")):
                out.append({"caminho": path, "papel": papel, "declarado": True, "valido": _repo_valido(path)})
        return out
    return detectar_repos(proj, os.path.abspath(vault))


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
