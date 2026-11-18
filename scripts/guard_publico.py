#!/usr/bin/env python3
"""Guarda de publicação: nada dos seus projetos vai para o GitHub.

O repositório do SecondBrain é público e deve conter só a ferramenta. Nomes de projetos, de pessoas e de empresas com quem
você trabalha ficam só no seu computador. Esta guarda impede o contrário:

- A lista de termos proibidos é montada AQUI, no seu computador, a cada execução: os projetos que o índice local conhece
  (~/.local/share/secondbrain/xmem.db) mais o arquivo ~/.local/share/secondbrain/denylist.txt (um termo por linha, `#`
  comenta) para pessoas e empresas. Ela nunca é gravada no repositório.
- Padrões genéricos valem em qualquer máquina: caminho da sua pasta pessoal, e-mail (exceto @users.noreply.github.com) e
  formatos comuns de chave e token.
- Só linhas ADICIONADAS entram na checagem de commit e de push; o que já está no histórico só se corrige reescrevendo-o.
- A guarda mostra o termo ou a categoria encontrados e o arquivo:linha, nunca a linha inteira.

Uso:
  guard_publico.py --staged             o que está no índice do git (hook de pre-commit)
  guard_publico.py --tree               todos os arquivos versionados hoje (CI e conferência manual)
  guard_publico.py --range A..B         linhas adicionadas entre dois commits
  guard_publico.py --pre-push           lê o que o `git push` vai enviar na entrada padrão (hook de pre-push)
  guard_publico.py --historico          varre todos os commits e só relata (nada é bloqueado)
  guard_publico.py --instalar-hook      instala os hooks de pre-commit e pre-push neste repositório (locais, não versionados)
Termos que dão falso positivo (palavra comum que também é nome de projeto) vão em ~/.local/share/secondbrain/denylist-permitidos.txt.
Saída 0 sem achados, 1 com achados.
"""
import os
import re
import sqlite3
import subprocess
import sys

HOME = os.path.expanduser("~")
DATA = os.path.join(HOME, ".local", "share", "secondbrain")
DB = os.environ.get("SECONDBRAIN_XMEM_DB") or os.path.join(DATA, "xmem.db")
DENY = os.path.join(DATA, "denylist.txt")
ALLOW = os.path.join(DATA, "denylist-permitidos.txt")
PROPRIOS = {"secondbrain", "global"}            # nomes do próprio plugin: podem aparecer
EMAIL_OK = ("@users.noreply.github.com",)
MARCA = "guard_publico"
ARVORE_VAZIA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"   # objeto da árvore vazia do git
BINARIOS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".db", ".gz", ".woff", ".woff2", ".ttf")
SEGREDOS = [(r"AKIA[0-9A-Z]{16}", "chave AWS"), (r"gh[pousr]_[A-Za-z0-9]{30,}", "token do GitHub"),
            (r"sk-[A-Za-z0-9_\-]{32,}", "chave de API"), (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "chave privada")]


def _linhas(caminho):
    try:
        with open(caminho, encoding="utf-8") as fh:
            return [ln.split("#", 1)[0].strip() for ln in fh if ln.split("#", 1)[0].strip()]
    except OSError:
        return []


def termos_locais(db=None, deny=None, allow=None):
    """Termos proibidos, em minúsculas: projetos do índice local + denylist.txt, menos os permitidos."""
    db, deny, allow = db or DB, deny or DENY, allow or ALLOW
    out = set()
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        projetos = [r[0] for r in con.execute("select distinct project from notes") if r[0]]
        con.close()
    except sqlite3.Error:
        projetos = []
    for p in projetos:
        if p.lower() in PROPRIOS:
            continue
        for v in {p, p.replace("-", " "), p.replace("_", " "), p.replace("-", "").replace("_", "")}:
            out.add(v.lower())
    out |= {t.lower() for t in _linhas(deny)}
    out -= {t.lower() for t in _linhas(allow)}
    return {t for t in out if len(t) >= 4}


def regex_termos(termos):
    if not termos:
        return None
    alt = "|".join(re.escape(t) for t in sorted(termos, key=len, reverse=True))
    return re.compile(r"(?<![A-Za-zÀ-ÿ0-9])(" + alt + r")(?![A-Za-zÀ-ÿ0-9])", re.I)


def padroes_genericos():
    pad = [(re.compile(p), r) for p, r in SEGREDOS]
    if HOME and HOME != "/":
        pad.append((re.compile(re.escape(HOME) + r"(?=/|\b)"), "caminho da sua pasta pessoal"))
    # pasta pessoal de outro usuário, exceto marcadores óbvios de exemplo (/home/user/, /home/usuario/, ...)
    pad.append((re.compile(r"/(?:home|Users)/(?!(?:user|usuario|nome|name|username|you|me|seu[-_]usuario)/)[A-Za-z0-9._-]+/", re.I), "caminho de pasta pessoal"))
    return pad


EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")


def achados_em_texto(texto, rx_termos, genericos):
    """[(linha, categoria, valor_curto)] sem devolver a linha inteira."""
    out = []
    for n, ln in enumerate(texto.splitlines(), 1):
        if rx_termos:
            for m in rx_termos.finditer(ln):
                out.append((n, "nome de projeto ou pessoa", m.group(1).lower()))
        for rx, rotulo in genericos:
            if rx.search(ln):
                out.append((n, rotulo, ""))
        for m in EMAIL.finditer(ln):
            if not m.group(0).lower().endswith(EMAIL_OK):
                out.append((n, "e-mail", ""))
    return out


def _git(repo, *args, entrada=None):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, errors="replace", input=entrada).stdout


def _varrer_diff(repo, args, rx, gen):
    """Parseia `git diff -U0`: só linhas adicionadas, com arquivo e número da linha no destino."""
    out, arq, ln = [], None, 0
    for linha in _git(repo, "diff", "--no-color", "--unified=0", "--no-renames", *args).splitlines():
        if linha.startswith("+++ "):
            arq = linha[6:] if linha.startswith("+++ b/") else None
        elif linha.startswith("@@"):
            m = re.search(r"\+(\d+)", linha)
            ln = int(m.group(1)) if m else 0
        elif linha.startswith("+") and arq and not arq.lower().endswith(BINARIOS):
            for _n, cat, val in achados_em_texto(linha[1:], rx, gen):
                out.append((arq, ln, cat, val))
            ln += 1
    return out


def varrer_staged(repo, rx, gen):
    return _varrer_diff(repo, ["--cached"], rx, gen)


def varrer_range(repo, intervalo, rx, gen):
    return _varrer_diff(repo, [intervalo], rx, gen)


def varrer_arvore(repo, rx, gen):
    out = []
    for f in _git(repo, "ls-files").splitlines():
        if not f or f.lower().endswith(BINARIOS):
            continue
        try:
            with open(os.path.join(repo, f), encoding="utf-8") as fh:
                texto = fh.read()
        except (OSError, UnicodeDecodeError):
            continue
        out += [(f, n, cat, val) for n, cat, val in achados_em_texto(texto, rx, gen)]
    return out


def varrer_historico(repo, rx, gen):
    """{sha_curto: [(arquivo, linha, categoria, valor)]} de todos os commits (só relata)."""
    res = {}
    for sha in _git(repo, "rev-list", "--all").split():
        pai = f"{sha}^" if _git(repo, "rev-parse", "-q", "--verify", f"{sha}^").strip() else ARVORE_VAZIA   # commit raiz: contra a árvore vazia
        a = _varrer_diff(repo, [pai, sha], rx, gen)
        if a:
            res[sha[:7]] = a
    return res


def _mostrar(achados):
    for arq, ln, cat, val in achados:
        print(f"  {arq}:{ln}  [{cat}{(': ' + val) if val else ''}]")


def _barrar(achados, onde):
    print(f"BLOQUEADO ({onde}): {len(achados)} achado(s) de dado pessoal ou nome de projeto no que iria para o repositório público.")
    _mostrar(achados[:40])
    if len(achados) > 40:
        print(f"  … e mais {len(achados) - 40}")
    print("Troque por um exemplo fictício. Palavra comum que é falso positivo vai em "
          "~/.local/share/secondbrain/denylist-permitidos.txt.")
    return 1


def instalar_hooks(repo, forcar=False):
    caminho_hooks = _git(repo, "rev-parse", "--git-path", "hooks").strip()
    caminho_hooks = caminho_hooks if os.path.isabs(caminho_hooks) else os.path.join(repo, caminho_hooks)
    os.makedirs(caminho_hooks, exist_ok=True)
    me = os.path.abspath(__file__)
    feitos = []
    for nome, modo in (("pre-commit", "--staged"), ("pre-push", "--pre-push")):
        alvo = os.path.join(caminho_hooks, nome)
        if os.path.exists(alvo) and MARCA not in open(alvo, encoding="utf-8", errors="ignore").read() and not forcar:
            print(f"já existe um hook {nome} que não é desta guarda; nada foi alterado (use --force para substituir, com cópia .bak)")
            continue
        if os.path.exists(alvo) and MARCA not in open(alvo, encoding="utf-8", errors="ignore").read():
            os.replace(alvo, alvo + ".bak")
        with open(alvo, "w", encoding="utf-8") as fh:
            fh.write(f"#!/bin/sh\n# {MARCA}: barra dado pessoal e nome de projeto antes de ir para o repositório público\nexec python3 -I \"{me}\" {modo}\n")
        os.chmod(alvo, 0o755)
        feitos.append(nome)
    if feitos:
        print("hooks instalados (locais, não versionados): " + ", ".join(feitos))
    return 0


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    repo = os.environ.get("GUARD_REPO") or (_git(os.getcwd(), "rev-parse", "--show-toplevel").strip() or os.getcwd())
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--instalar-hook":
        return instalar_hooks(repo, "--force" in a)
    rx, gen = regex_termos(termos_locais()), padroes_genericos()
    if a[0] == "--staged":
        ach = varrer_staged(repo, rx, gen)
        return _barrar(ach, "commit") if ach else 0
    if a[0] == "--tree":
        ach = varrer_arvore(repo, rx, gen)
        if ach:
            return _barrar(ach, "árvore")
        print("árvore limpa" + ("" if rx else " (sem lista local de termos: só padrões genéricos)"))
        return 0
    if a[0] == "--range" and len(a) > 1:
        ach = varrer_range(repo, a[1], rx, gen)
        return _barrar(ach, "intervalo") if ach else 0
    if a[0] == "--pre-push":
        ach = []
        for ln in sys.stdin.read().splitlines():
            p = ln.split()
            if len(p) < 4 or set(p[1]) == {"0"}:
                continue
            base = p[3]
            if set(base) == {"0"}:                      # ramo novo: tudo o que ainda não está em nenhum remoto
                for sha in reversed(_git(repo, "rev-list", p[1], "--not", "--remotes").split()):
                    ach += varrer_range(repo, f"{sha}^!", rx, gen)
            else:
                ach += varrer_range(repo, f"{base}..{p[1]}", rx, gen)
        return _barrar(ach, "push") if ach else 0
    if a[0] == "--historico":
        res = varrer_historico(repo, rx, gen)
        print(f"{len(res)} commit(s) de {len(_git(repo, 'rev-list', '--all').split())} têm achados (só relatório).")
        for sha, ach in res.items():
            print(f"- {sha}: {len(ach)} achado(s) em {len({x[0] for x in ach})} arquivo(s)")
        return 0
    print("opção desconhecida; use --help")
    return 2


if __name__ == "__main__":
    sys.exit(main())
