#!/usr/bin/env python3
"""Conciliação (decisão 011): confronta as pendências abertas de um projeto com o git e propõe o que fechar.

Três níveis de evidência, do mais forte ao mais fraco. Só o A fecha, e só com `--aplicar A --sim`:
  A  o cartão cita um hash que existe no git, ou um commit posterior descreve o mesmo assunto (semelhança alta, 3+ termos)
  B  um commit posterior parece tratar do assunto (semelhança média, 2+ termos). Só proposta.
  C  um arquivo citado no cartão foi alterado depois da data dele. Só proposta.

Medido num projeto real: o texto do commit pega pouco e o arquivo citado menos ainda. Por isso a conciliação
propõe, e quem decide é você. Também lista os hashes citados nas notas que não existem em nenhum repositório do projeto.

Uso (via xmem): xmem.py reconcile <projeto> [--json] [--incluir-referencias] [--aplicar A [--sim|--dry-run] [--confirmo]]
"""
import json
import os
import re
import subprocess
import sys

xm = sys.modules.get("xmem") or sys.modules.get("__main__")
if not hasattr(xm, "strip_acc"):
    import xmem as xm  # noqa: E402
import _vault  # noqa: E402
import board  # noqa: E402
import pend  # noqa: E402

HASH = re.compile(r"(?<![0-9A-Za-z/_\-\.])([0-9a-f]{7,12})(?![0-9A-Za-z_\-])")
ARQUIVO = re.compile(r"`([\w.\-/\[\]]+\.(?:java|ts|tsx|js|py|scss|css|html|xml|cfg|json5?|sql|ya?ml|md|png|sh|dart|kt))`")
MAX_ARQUIVOS = 150      # commit que mexe em mais arquivos que isso (port, reformatação) não prova nada sobre um arquivo
NOTAS_COM_HASH = ("devtrack", "estado", "prioridade", "feature", "decisao", "rfc", "postmortem", "analise", "release", "nota")


def _git(repo, *args, entrada=None):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, errors="replace", input=entrada)


def hash_plausivel(h):
    return bool(re.search(r"\d", h) and re.search(r"[a-f]", h) and not re.fullmatch(r"\d{7,8}", h))


def existe(repos, hashes):
    """{hash: repo onde existe} para os que existem em algum repositório (git cat-file --batch-check, aceita abreviação)."""
    achados, faltam = {}, list(hashes)
    for r in repos:
        if not faltam:
            break
        out = _git(r["caminho"], "cat-file", "--batch-check", entrada="\n".join(f"{h}^{{commit}}" for h in faltam) + "\n").stdout.splitlines()
        resto = []
        for h, ln in zip(faltam, out):
            if ln.endswith(" commit") or " commit " in ln:
                achados[h] = r["caminho"]
            else:
                resto.append(h)
        faltam = resto
    return achados


def ref_padrao(repo):
    """Branch padrão (origin/HEAD) ou, sem remoto, o HEAD atual. `--all` contava commit de branch largado como evidência."""
    r = _git(repo, "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD").stdout.strip()
    return r or "HEAD"


def listar_commits(repo, desde):
    out = _git(repo, "log", ref_padrao(repo), "--no-merges", f"--since={desde}", "--name-only", "--format=@@%h|%ad|%an|%s", "--date=short").stdout
    cs, cur = [], None
    for ln in out.splitlines():
        if ln.startswith("@@"):
            h, d, an, s = (ln[2:].split("|", 3) + ["", "", ""])[:4]
            cur = {"hash": h, "data": d, "autor": an, "assunto": s, "arquivos": set(), "caminhos": set(), "repo": os.path.basename(repo)}
            cs.append(cur)
        elif ln.strip() and cur is not None:
            cur["arquivos"].add(os.path.basename(ln.strip()))
            cur["caminhos"].add(ln.strip())
    return cs


def hashes_inexistentes(c, project, todos_repos):
    """Hashes citados nas notas do projeto que não existem em nenhum repositório (inclui os de referência)."""
    achados = {}
    for n in c.execute("select path, rel from notes where project=? and kind in (%s)" % ",".join("?" * len(NOTAS_COM_HASH)), (project, *NOTAS_COM_HASH)):
        try:
            texto = open(n["path"], encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for h in HASH.findall(texto):
            if hash_plausivel(h):
                achados.setdefault(h, n["rel"])
    ok = existe(todos_repos, achados)
    return sorted(((h, rel) for h, rel in achados.items() if h not in ok), key=lambda x: x[1])


def propor(c, project, repos, desde=None):
    """-> (propostas, avisos). Cada proposta: {id, titulo, nivel, evidencias[], oculto, data}."""
    cards = [k for k in board.build(c, project, ocultos=True)
             if k["status"] not in ("feito", "descartado") and k.get("oculto") not in ("pergunta", "narrativo")]
    if not cards:
        return [], []
    desde = desde or min((k["origem"].get("data") or "9999")[:10] for k in cards)
    commits = [cm for r in repos for cm in listar_commits(r["caminho"], desde)]
    corpus = pend.Corpus([k["titulo"] for k in cards] + [cm["assunto"] for cm in commits])
    toq = {k["id"]: pend.tokens(k["titulo"]) for k in cards}
    toc = [pend.tokens(cm["assunto"]) for cm in commits]
    por_arquivo = {}
    for cm in commits:
        if len(cm["arquivos"]) > MAX_ARQUIVOS:
            continue
        for f in cm["arquivos"]:
            por_arquivo.setdefault(f, []).append(cm)
    citados = {}
    for k in cards:
        for h in HASH.findall(k["titulo"]):
            if hash_plausivel(h):
                citados.setdefault(h, []).append(k["id"])
    existentes = existe(repos, citados) if citados else {}
    props = []
    for k in cards:
        data = (k["origem"].get("data") or "")[:10]
        ev, nivel = [], ""
        for h in HASH.findall(k["titulo"]):
            if h in existentes:
                ev.append({"nivel": "A", "tipo": "hash citado existe", "hash": h, "repo": os.path.basename(existentes[h])})
        for cm, t in zip(commits, toc):
            if cm["data"] < data:
                continue
            s, comum = corpus.sim(toq[k["id"]], t)
            if s >= pend.SIM_FECHA and len(comum) >= 3:
                ev.append({"nivel": "A", "tipo": "commit descreve o mesmo assunto", "hash": cm["hash"], "data": cm["data"], "assunto": cm["assunto"][:90], "repo": cm["repo"], "semelhanca": round(s, 2)})
            elif s >= pend.SIM_PROPOSTA:
                ev.append({"nivel": "B", "tipo": "commit parece tratar do assunto", "hash": cm["hash"], "data": cm["data"], "assunto": cm["assunto"][:90], "repo": cm["repo"], "semelhanca": round(s, 2)})
        for f in ARQUIVO.findall(k["titulo"]):
            # com diretório na citação (`src/a/lib.ts`) o caminho tem de bater; só o nome do arquivo vale por basename
            depois = [cm for cm in por_arquivo.get(os.path.basename(f), [])
                      if cm["data"] >= data and ("/" not in f or any(c == f or c.endswith("/" + f.lstrip("./")) for c in cm["caminhos"]))]
            if depois:
                cm = min(depois, key=lambda x: x["data"])
                ev.append({"nivel": "C", "tipo": "arquivo citado foi alterado", "arquivo": os.path.basename(f), "hash": cm["hash"], "data": cm["data"], "assunto": cm["assunto"][:90], "repo": cm["repo"]})
        if ev:
            nivel = min(e["nivel"] for e in ev)
            props.append({"id": k["id"], "titulo": k["titulo"], "nivel": nivel, "evidencias": sorted(ev, key=lambda e: (e["nivel"], -e.get("semelhanca", 0)))[:3],
                          "oculto": k.get("oculto", ""), "data": data})
    props.sort(key=lambda p: (p["nivel"], p["data"]))
    return props, []


def cmd(a, c):
    proj = a.project
    row = c.execute("select min(vault) v from notes where project=?", (proj,)).fetchone()
    if not row or not row["v"]:
        raise SystemExit(f"reconcile: projeto desconhecido: {proj}")
    repos_all = _vault.read_repos(row["v"])
    quebrados = [r for r in repos_all if not r["valido"]]
    validos = [r for r in repos_all if r["valido"]]
    usar = [r for r in validos if r["papel"] == "ativo" or a.incluir_referencias]
    avisos = [f"repositório inválido ({r['aviso']})" if r.get("aviso") else f"repositório inválido (o git não o reconhece): {r['caminho']}" for r in quebrados]
    if not usar:
        msg = "nenhum repositório ativo e válido encontrado; declare `repos:` no manifesto do vault (ver references/vault-resolve.md)."
        if a.json:
            print(json.dumps({"projeto": proj, "erro": msg, "avisos": avisos}, ensure_ascii=False, indent=1))
        else:
            print(f"{proj}: {msg}\n" + "\n".join("  ! " + x for x in avisos))
        return
    props, _ = propor(c, proj, usar, a.desde)
    inexist = hashes_inexistentes(c, proj, validos)
    por = {n: [p for p in props if p["nivel"] == n] for n in "ABC"}
    if a.aplicar:
        if a.aplicar != "A":
            raise SystemExit("reconcile: só o nível A pode ser aplicado (B e C são propostas para você decidir).")
        sel = por["A"]
        if not sel:
            print("nada no nível A para aplicar")
            return
        if not a.sim and not a.dry_run:
            raise SystemExit(f"reconcile: {len(sel)} cartões iriam para Feito em {proj}. Confirme com --sim (ou veja antes com --dry-run). Nada foi gravado.")
        cards = {k["id"]: k for k in board.build(c, proj, ocultos=True)}
        # a data da evidência (commit) vira `feito-em`: é ela que põe o cartão na semana certa do calendário
        ch = [board.change_from_card(cards[p["id"]], "feito", etiquetas=["ja-feito", "reconciliado"],
                                     campos={"feito-em": next((e["data"] for e in p["evidencias"] if e.get("data")), "")}) for p in sel]
        efs = []
        path, _ = board.apply_changes(c, proj, ch, confirmo=a.confirmo, dry_run=a.dry_run, efeitos=efs)
        print(("[simulação] " if a.dry_run else "") + f"{len(ch)} cartão(ões) -> Feito em {path}")
        for e in efs[:15]:
            print("  " + e)
        if len(efs) > 15:
            print(f"  … e mais {len(efs) - 15}")
        return
    if a.json:
        print(json.dumps({"projeto": proj, "repos": [{"caminho": r["caminho"], "papel": r["papel"]} for r in usar], "avisos": avisos,
                          "propostas": props, "hashes_inexistentes": [{"hash": h, "nota": rel} for h, rel in inexist]}, ensure_ascii=False, indent=1))
        return
    print(f"# Conciliação de {proj}\n")
    print("Repositórios usados: " + ", ".join(f"{os.path.basename(r['caminho'])} ({r['papel']})" for r in usar))
    for x in avisos:
        print("  ! " + x)
    print(f"\nPropostas: A {len(por['A'])} (podem fechar com `--aplicar A --sim`), B {len(por['B'])}, C {len(por['C'])}. Nada foi gravado.")
    for n, rot in (("A", "Evidência forte"), ("B", "Parece tratar do assunto (você decide)"), ("C", "Arquivo citado foi alterado (você decide)")):
        if por[n]:
            print(f"\n## {n}: {rot}")
            for p in por[n][: (60 if a.todas else 12)]:
                e = p["evidencias"][0]
                det = e.get("assunto") or e["tipo"]
                print(f"- {p['id']} {p['data']} {p['titulo'][:70]}\n    ← {e['tipo']}: {e.get('hash', '')} {e.get('data', '')} {det}".rstrip())
    if inexist:
        print(f"\n## Hashes citados nas notas que não existem em nenhum repositório do disco: {len(inexist)}")
        print("(hash de repositório que saiu do disco, como um clone apagado ou um repo antigo, aparece aqui sem que a nota esteja errada)")
        for h, rel in inexist[:10]:
            print(f"- {h}  em {rel}")
        if len(inexist) > 10:
            print(f"- … e mais {len(inexist) - 10}")
    print("\nCartões em `board show --ocultos` (superados, repetidos) entram na conciliação; os que o git não confirma ficam para você decidir.")


def add_parser(sp):
    s = sp.add_parser("reconcile", help="confronta pendências abertas com o git e propõe o que fechar")
    s.add_argument("project")
    s.add_argument("--json", action="store_true")
    s.add_argument("--desde", help="só commits a partir desta data (padrão: o cartão mais antigo)")
    s.add_argument("--todas", action="store_true", help="lista mais propostas por nível")
    s.add_argument("--incluir-referencias", action="store_true", help="inclui repositórios marcados como `referencia` (só sob pedido)")
    s.add_argument("--aplicar", help="aplica um nível; só `A` é permitido")
    s.add_argument("--sim", action="store_true", help="confirma a gravação em lote")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--confirmo", action="store_true", help="vault sensível ou versionado")
    return s
