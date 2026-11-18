#!/usr/bin/env python3
"""Quadro kanban do SecondBrain (decisão 009): cartões DERIVADOS das caixas `- [ ]` dos vaults + decisões
humanas guardadas em `quadro.md` (formato do plugin Obsidian Kanban), um por projeto, criado só quando alguém mexe.

Princípios: nada é reescrito nas notas de origem (devtrack é histórico); descartar = mover a linha para
`## Descartado` (nunca apaga); escrita sempre com backup fora do vault; vault sensível/versionado exige confirmação.

Uso (via xmem): xmem.py board show|summary|proposals|move|add|discard ...
"""
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections import defaultdict
from datetime import date, datetime

xm = sys.modules.get("xmem") or sys.modules.get("__main__")
if not hasattr(xm, "strip_acc"):  # importado fora do xmem (testes, outras ferramentas)
    import xmem as xm  # noqa: E402

SCHEMA = 1
COLUMNS = [("triagem", "Triagem"), ("a-fazer", "A fazer"), ("fazendo", "Fazendo"), ("bloqueado", "Bloqueado"),
           ("revisao", "Revisão"), ("feito", "Feito"), ("descartado", "Descartado")]
KEYS = [k for k, _ in COLUMNS]
LABEL = dict(COLUMNS)
PRIORITIES = ("P0", "P1", "P2", "P3")
TRIAGE_DAYS = 60            # item aberto há mais que isso nasce em Triagem
BACKUP_DIR = os.path.join(xm.HOME, ".local/share/secondbrain/backups/quadro")


def _norm_col(name):
    n = re.sub(r"[^a-z0-9]+", "-", xm.strip_acc(name.lower())).strip("-")
    return n if n in KEYS else None


def card_id(project, norm):
    return "c" + hashlib.sha1(f"{project}\0{norm}".encode()).hexdigest()[:6]


def _age(data):
    try:
        return (date.today() - date.fromisoformat((data or "")[:10])).days
    except ValueError:
        return 0


# ------------------------------------------------------------------ derivação (índice -> cartões)
def derive(c, project=None):
    """Um cartão por (projeto, texto normalizado); vale a ocorrência mais recente (regra do open_items)."""
    q = ("select t.text,t.norm,t.checked,t.line,n.data,n.project,n.rel,n.kind,n.sens,n.policy "
         "from todos t join notes n on n.id=t.note_id")
    rows = c.execute(q + (" where n.project=?" if project else ""), (project,) if project else ()).fetchall()
    grp = defaultdict(list)
    for r in rows:
        grp[(r["project"], r["norm"])].append(r)
    cards = {}
    for (proj, norm), occ in grp.items():
        occ.sort(key=lambda r: (r["data"] or "", r["rel"], r["line"]))
        last, first = occ[-1], occ[0]
        age = _age(last["data"])
        cid = card_id(proj, norm)
        col = "feito" if last["checked"] else ("triagem" if age > TRIAGE_DAYS else "a-fazer")
        cards[cid] = {
            "id": cid, "titulo": last["text"], "status": col, "prioridade": "", "tipo": "criterio-feature" if last["kind"] == "feature" else "todo",
            "projeto": proj, "origem": {"nota": last["rel"], "linha": last["line"], "data": last["data"]},
            "criado": first["data"], "atualizado": last["data"], "idade_dias": age, "parado": (not last["checked"]) and age > xm.STALE_OPEN_DAYS,
            "bloqueado_por": [], "relacionadas": [], "etiquetas": [], "modo": "derivado", "responsavel": "", "prazo": "",
            "orfao": False, "status_origem": "automatico", "sens": last["sens"], "policy": last["policy"],
        }
    return cards


# ------------------------------------------------------------------ quadro.md (leitura)
CARD_RE = re.compile(r"^-\s*\[( |x|X)\]\s+(.*?)\s*$")
FIELD_RE = re.compile(r"^\s+([a-z][a-z0-9-]*)::\s*(.*)$")


def vault_of(c, project):
    r = c.execute("select min(vault) v from notes where project=?", (project,)).fetchone()
    return r["v"] if r and r["v"] else None


def quadro_path(vault):
    return os.path.join(vault, "quadro.md")


def parse_quadro(text):
    """-> lista de cartões {id,col,feito,titulo,prioridade,etiquetas,campos,extras} na ordem do arquivo."""
    out, col = [], None
    body = re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", text, count=1, flags=re.S)
    for ln in body.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", ln)
        if m:
            col = _norm_col(m.group(1))
            continue
        if col is None:
            continue
        m = CARD_RE.match(ln)
        if m:
            raw = m.group(2)
            mid = re.search(r"\s\^([A-Za-z0-9-]+)\s*$", " " + raw)
            cid = mid.group(1) if mid else ""
            if mid:
                raw = (" " + raw)[:mid.start()].strip()
            tags = re.findall(r"(?<!\S)#([\w-]+)", raw)
            prio = next((t.upper() for t in tags if t.upper() in PRIORITIES), "")
            titulo = re.sub(r"(?<!\S)#[\w-]+", "", raw).strip()
            out.append({"id": cid, "col": col, "feito": m.group(1) != " ", "titulo": titulo, "prioridade": prio,
                        "etiquetas": [t for t in tags if t.upper() not in PRIORITIES], "campos": {}, "extras": []})
            continue
        f = FIELD_RE.match(ln)
        if f and out:
            out[-1]["campos"][f.group(1)] = f.group(2).strip()
        elif ln.strip() and ln.startswith((" ", "\t")) and out:
            out[-1]["extras"].append(ln.rstrip())
    return out


def load_overrides(vault):
    p = quadro_path(vault)
    if not os.path.isfile(p):
        return []
    with open(p, encoding="utf-8", errors="ignore") as fh:
        return parse_quadro(fh.read())


# ------------------------------------------------------------------ quadro (derivado + decisões)
def build(c, project=None, current_project=None):
    """Quadro completo: cartões derivados com as decisões do quadro.md aplicadas por cima."""
    derived = derive(c, project)
    projects = [project] if project else [r["project"] for r in c.execute("select distinct project from notes order by project")]
    for proj in projects:
        vault = vault_of(c, proj)
        if not vault:
            continue
        for ov in load_overrides(vault):
            cid = ov["id"] or card_id(proj, re.sub(r"\W+", " ", xm.strip_acc(ov["titulo"].lower())).strip()[:120])
            d = derived.get(cid)
            if d is None:
                orig = ov["campos"].get("origem", "")
                derived[cid] = {
                    "id": cid, "titulo": ov["titulo"], "status": ov["col"], "prioridade": ov["prioridade"], "tipo": "manual" if not orig else "todo",
                    "projeto": proj, "origem": {"nota": re.sub(r"[\[\]]", "", orig), "linha": 0, "data": ""} if orig else {},
                    "criado": ov["campos"].get("criado", ""), "atualizado": ov["campos"].get("atualizado", ""), "idade_dias": _age(ov["campos"].get("criado", "")),
                    "parado": False, "bloqueado_por": [x for x in [ov["campos"].get("bloqueado-por", "")] if x],
                    "relacionadas": [x.strip() for x in ov["campos"].get("relacionadas", "").split(",") if x.strip()],
                    "etiquetas": ov["etiquetas"], "modo": "derivado" if orig else "manual", "responsavel": ov["campos"].get("responsavel", ""),
                    "prazo": ov["campos"].get("prazo", ""), "orfao": bool(orig), "status_origem": "quadro", "sens": "", "policy": "",
                }
                continue
            if d["status"] == "feito" and ov["col"] != "descartado":
                col = "feito"          # a origem foi concluída: concluir vale mais que o resto
            else:
                col = ov["col"]
            d.update({"status": col, "prioridade": ov["prioridade"] or d["prioridade"], "etiquetas": ov["etiquetas"],
                      "bloqueado_por": [x for x in [ov["campos"].get("bloqueado-por", "")] if x],
                      "relacionadas": [x.strip() for x in ov["campos"].get("relacionadas", "").split(",") if x.strip()],
                      "responsavel": ov["campos"].get("responsavel", ""), "prazo": ov["campos"].get("prazo", ""),
                      "status_origem": "quadro"})
    cards = list(derived.values())
    if current_project:                # privacidade: o mesmo critério do hook (nada de texto de vault 'nenhum'; 'titulos' sem origem)
        keep = []
        for k in cards:
            if k["projeto"] != current_project:
                if k.get("policy") == "nenhum":
                    continue
                if k.get("policy") == "titulos":
                    k = dict(k, origem={}, relacionadas=[], bloqueado_por=[])
            keep.append(k)
        cards = keep
    order = {p: i for i, p in enumerate(PRIORITIES)}
    cards.sort(key=lambda k: (KEYS.index(k["status"]), order.get(k["prioridade"], 9), -k["idade_dias"]))
    return cards


def summary(cards):
    out = defaultdict(lambda: {k: 0 for k in KEYS})
    for k in cards:
        out[k["projeto"]][k["status"]] += 1
    return {p: v for p, v in sorted(out.items())}


# ------------------------------------------------------------------ escrita (sempre aditiva, com backup)
def _render_card(k):
    tags = ([k["prioridade"]] if k.get("prioridade") else []) + list(k.get("etiquetas") or [])
    line = f"- [{'x' if k['col'] == 'feito' else ' '}] {k['titulo']}" + "".join(f" #{t}" for t in tags) + f" ^{k['id']}"
    lines = [line]
    for key in ("origem", "bloqueado-por", "relacionadas", "responsavel", "prazo", "criado", "atualizado"):
        v = k["campos"].get(key, "")
        if v:
            lines.append(f"  {key}:: {v}")
    lines += k.get("extras", [])
    return "\n".join(lines)


def render(project, cards_by_col):
    head = f"---\nkanban-plugin: board\nschema: {SCHEMA}\ntipo: quadro\natualizado: {date.today().isoformat()}\n---\n\n"
    head += f"> Quadro de {project}. Guarda só decisões; o resto vem das caixas `- [ ]` das notas (derivado). Mover um cartão entre colunas é decidir.\n\n"
    parts = []
    for key, label in COLUMNS:
        parts.append(f"## {label}\n\n" + "".join(_render_card(k) + "\n" for k in cards_by_col.get(key, [])))
    return head + "\n".join(parts)


def _policy_gate(c, project, vault, confirmo):
    ms = xm.manifest_scalars(vault) if os.path.isfile(os.path.join(vault, "_secondbrain.md")) else {}
    if ms.get("quadro", "true") == "false":
        raise SystemExit(f"quadro: o manifesto de {project} desliga o quadro (quadro: false). Nada foi gravado.")
    if (ms.get("sens") == "alta" or ms.get("versionado") == "true") and not confirmo:
        raise SystemExit(f"quadro: {project} é sensível ou versionado; gravar `quadro.md` exige confirmação explícita (--confirmo). Nada foi gravado.")


def apply_changes(c, project, changes, confirmo=False, dry_run=False):
    """changes: lista de dicts {id, titulo, col, prioridade, etiquetas, campos}. Mescla no quadro.md do projeto."""
    vault = vault_of(c, project)
    if not vault:
        raise SystemExit(f"quadro: projeto desconhecido: {project}")
    _policy_gate(c, project, vault, confirmo)
    cur = load_overrides(vault)
    by_id = {k["id"]: k for k in cur if k["id"]}
    for ch in changes:
        old = by_id.get(ch["id"])
        if old:
            old["col"] = ch.get("col") or old["col"]
            if ch.get("prioridade") is not None:
                old["prioridade"] = ch["prioridade"]
            if ch.get("etiquetas") is not None:
                old["etiquetas"] = ch["etiquetas"]
            old["campos"].update({k: v for k, v in (ch.get("campos") or {}).items() if v != ""})
            old["feito"] = old["col"] == "feito"
        else:
            nk = {"id": ch["id"], "col": ch["col"], "feito": ch["col"] == "feito", "titulo": ch["titulo"], "prioridade": ch.get("prioridade") or "",
                  "etiquetas": ch.get("etiquetas") or [], "campos": dict(ch.get("campos") or {}), "extras": []}
            nk["campos"].setdefault("criado", date.today().isoformat())
            cur.append(nk)
            by_id[nk["id"]] = nk
    cols = defaultdict(list)
    for k in cur:
        cols[k["col"]].append(k)
    text = render(project, cols)
    path = quadro_path(vault)
    if dry_run:
        return path, text
    if os.path.isfile(path):
        bdir = os.path.join(BACKUP_DIR, project)
        os.makedirs(bdir, exist_ok=True)
        shutil.copy2(path, os.path.join(bdir, f"quadro-{datetime.now():%Y%m%d-%H%M%S}.md"))
    fd, tmp = tempfile.mkstemp(dir=vault, prefix=".quadro-", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)
    return path, text


def _card_for_change(cards, cid):
    for k in cards:
        if k["id"] == cid:
            return k
    raise SystemExit(f"quadro: cartão {cid} não existe neste projeto (use `board show --project ... ` para ver os ids)")


def change_from_card(k, col, prioridade=None, etiquetas=None, campos=None):
    camp = {}
    if k.get("origem", {}).get("nota"):
        camp["origem"] = "[[" + re.sub(r"\.md$", "", k["origem"]["nota"]) + "]]"
    camp.update(campos or {})
    return {"id": k["id"], "titulo": k["titulo"], "col": col, "prioridade": prioridade, "etiquetas": etiquetas, "campos": camp}


# ------------------------------------------------------------------ linha de comando
def fmt_card(k):
    pr = f"[{k['prioridade']}] " if k["prioridade"] else ""
    extra = f" · parado há {k['idade_dias']}d" if k["parado"] else ""
    orf = " (órfão)" if k["orfao"] else ""
    return f"- {k['id']} {pr}{k['titulo'][:110]} · {k['projeto']}{extra}{orf}"


def cmd(a, c):
    cur = getattr(a, "project_atual", None) or None
    sub = a.board_cmd
    if sub in ("show", "summary", "proposals"):
        cards = build(c, a.project, cur)
    if sub == "summary":
        s = summary(cards)
        if a.json:
            print(json.dumps({"schema": SCHEMA, "resumo": s}, ensure_ascii=False, indent=1))
        else:
            for p, v in s.items():
                print(f"{p:24} " + "  ".join(f"{LABEL[k]} {n}" for k, n in v.items() if n))
        return
    if sub == "show":
        want = {x.strip() for x in a.status.split(",")} if a.status else None
        sel = [k for k in cards if (not want or k["status"] in want) and (a.todos or k["status"] not in ("feito", "descartado") or want)]
        if a.limit:
            sel = sel[:a.limit]
        if a.json:
            slim = [{k: v for k, v in x.items() if k not in ("sens", "policy")} for x in sel]
            print(json.dumps({"schema": SCHEMA, "colunas": KEYS, "cartoes": slim}, ensure_ascii=False, indent=1))
            return
        for key in KEYS:
            grp = [k for k in sel if k["status"] == key]
            if grp:
                print(f"\n## {LABEL[key]} ({len(grp)})")
                for k in grp:
                    print(fmt_card(k))
        return
    if sub == "proposals":
        old = [k for k in cards if k["status"] == "triagem" and k["idade_dias"] >= a.older_than]
        by = defaultdict(list)
        for k in old:
            by[k["projeto"]].append(k)
        print(f"{len(old)} cartões em Triagem com {a.older_than}+ dias, em {len(by)} projetos. Nada foi gravado.")
        for p, lst in sorted(by.items(), key=lambda x: -len(x[1])):
            print(f"  {p:24} {len(lst):4}   ex.: {lst[0]['titulo'][:70]}")
        return
    if sub in ("move", "add", "discard"):
        proj = a.project
        cards = build(c, proj)
        if sub == "move":
            if a.coluna not in KEYS:
                raise SystemExit(f"coluna inválida: {a.coluna} (use: {', '.join(KEYS)})")
            k = _card_for_change(cards, a.id)
            campos = {}
            if a.bloqueado_por:
                campos["bloqueado-por"] = a.bloqueado_por
            ch = [change_from_card(k, a.coluna, a.prioridade, a.etiqueta if a.etiqueta is not None else None, campos)]
        elif sub == "add":
            nid = "m" + hashlib.sha1(f"{proj}\0{a.titulo}\0{datetime.now().isoformat()}".encode()).hexdigest()[:6]
            ch = [{"id": nid, "titulo": a.titulo, "col": a.coluna, "prioridade": a.prioridade, "etiquetas": a.etiqueta or [],
                   "campos": {"origem": a.origem} if a.origem else {}}]
        else:
            if a.ids:
                ch = [change_from_card(_card_for_change(cards, i), "descartado") for i in a.ids]
            else:
                ch = [change_from_card(k, "descartado") for k in cards if k["status"] == "triagem" and k["idade_dias"] >= a.older_than]
            if not ch:
                print("nada para descartar")
                return
            if not a.sim and not a.dry_run:
                raise SystemExit(f"quadro: {len(ch)} cartões iriam para Descartado em {proj}. Confirme com --sim (ou veja antes com --dry-run). Nada foi gravado.")
        path, text = apply_changes(c, proj, ch, confirmo=a.confirmo, dry_run=a.dry_run)
        print(("[simulação] " if a.dry_run else "") + f"{len(ch)} cartão(ões) -> {path}")
        if a.dry_run:
            print(text[:1500])
        return


def add_parser(sp):
    s = sp.add_parser("board", help="quadro kanban (cartões derivados + quadro.md por projeto)")
    bs = s.add_subparsers(dest="board_cmd", required=True)
    x = bs.add_parser("show"); x.add_argument("--project"); x.add_argument("--status"); x.add_argument("--limit", type=int, default=0)
    x.add_argument("--todos", action="store_true", help="inclui Feito e Descartado"); x.add_argument("--json", action="store_true"); x.add_argument("--project-atual")
    x = bs.add_parser("summary"); x.add_argument("--project"); x.add_argument("--json", action="store_true"); x.add_argument("--project-atual")
    x = bs.add_parser("proposals"); x.add_argument("--project"); x.add_argument("--older-than", type=int, default=TRIAGE_DAYS); x.add_argument("--project-atual")
    for name in ("move", "add", "discard"):
        x = bs.add_parser(name); x.add_argument("project")
        x.add_argument("--dry-run", action="store_true"); x.add_argument("--confirmo", action="store_true", help="vault sensível ou versionado")
        if name == "move":
            x.add_argument("id"); x.add_argument("coluna"); x.add_argument("--prioridade", choices=PRIORITIES); x.add_argument("--etiqueta", action="append")
            x.add_argument("--bloqueado-por")
        elif name == "add":
            x.add_argument("titulo"); x.add_argument("--coluna", default="a-fazer"); x.add_argument("--prioridade", choices=PRIORITIES)
            x.add_argument("--etiqueta", action="append"); x.add_argument("--origem")
        else:
            x.add_argument("ids", nargs="*"); x.add_argument("--older-than", type=int, default=TRIAGE_DAYS)
            x.add_argument("--sim", action="store_true", help="confirma a gravação em lote")
    return s
