#!/usr/bin/env python3
"""Avaliação de qualidade da busca do xmem contra respostas conhecidas (golden set).

Cada caso: pergunta + trecho do caminho da nota que DEVE aparecer + projeto de origem da consulta
(para recall, que exclui o projeto atual). As respostas foram verificadas à mão nos vaults reais.
NENHUM caso fica neste arquivo (o repositório é público e os casos citam assuntos dos seus projetos): todos vivem em
~/.local/share/secondbrain/eval_local.json, que o script carrega sozinho (--local ARQ usa outro arquivo). Formato em
tests/eval_local.example.json.
Métrica: posição da nota esperada (hit@3 / hit@5) e MRR.

Uso: eval_xmem.py [--verbose] [--auto [N]] [--local ARQUIVO.json] [--save]
  --auto [N]   gera até N (padrão 150) consultas a partir do índice real (item conhecido: o `description` de uma memória
               ou a primeira frase do Contexto de uma decisão; esperado = a própria nota). Nada é gravado no git e o
               texto das notas de vault sensível nunca é impresso. Mede regressão de ranking, não a qualidade "humana".
  --local ARQ  casos escritos à mão fora do repositório: JSON [[consulta, trecho_esperado, projeto_atual|null, descrição], ...]
               (padrão: ~/.local/share/secondbrain/eval_local.json, se existir). Lugar certo para casos de vault sensível.
  --save       grava as métricas como linha de base em ~/.local/share/secondbrain/eval_baseline.json; as próximas
               execuções mostram a diferença.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import xmem  # noqa: E402

# (consulta, trecho do rel esperado, projeto "atual" simulado ou None, descrição). O repositório é público e não
# guarda nenhum caso: veja tests/eval_local.example.json para o formato e use ~/.local/share/secondbrain/eval_local.json.
GOLDEN = []   # vazio de propósito: casos de avaliação citam assuntos reais e ficam só em eval_local.json (fora do git)

# Conjunto SEPARADO, escrito depois do ajuste do motor: não foi usado para calibrar nada.
HELDOUT = []   # vazio de propósito: casos de avaliação citam assuntos reais e ficam só em eval_local.json (fora do git)


DATA = os.path.join(os.path.expanduser("~"), ".local", "share", "secondbrain")
BASELINE = os.path.join(DATA, "eval_baseline.json")
LOCAL = os.path.join(DATA, "eval_local.json")
SECTIONS = ("contexto", "problema", "context", "motivacao", "motivação")


def _arg(flag, default):
    """Valor opcional de uma flag: `--auto` -> default; `--auto 80` -> '80'."""
    if flag not in sys.argv:
        return None
    i = sys.argv.index(flag)
    nxt = sys.argv[i + 1] if i + 1 < len(sys.argv) else ""
    return nxt if nxt and not nxt.startswith("--") else default


def first_sentence(body):
    """Primeira linha de texto sob uma seção Contexto/Problema (a pergunta que a nota responde)."""
    lines = body.splitlines()
    for i, ln in enumerate(lines):
        m = re.match(r"#{2,3}\s+(.+)", ln)
        if m and m.group(1).strip().lower() in SECTIONS:
            for nxt in lines[i + 1:]:
                if nxt.startswith("#"):
                    break
                t = re.sub(r"[*_`>\[\]]", "", nxt).strip(" -")
                if len(t.split()) >= 8:
                    return " ".join(t.split()[:14])
    return None


def auto_cases(c, n):
    """Consultas de item conhecido tiradas do índice. Ambíguas (mesma consulta em >1 nota) são descartadas."""
    cand = []
    for r in c.execute("select id,project,kind,title,path,sens from notes where inactive=0 and kind in ('memory','decisao','postmortem','rfc') order by id"):
        try:
            fm, body = xmem.parse_note(open(r["path"], encoding="utf-8").read())
        except OSError:
            continue
        q = str(fm.get("description") or "").strip() if r["kind"] == "memory" else first_sentence(body)
        if q and len(q.split()) >= 5:
            cand.append((" ".join(q.split()), r))
    contagem = {}
    for q, _ in cand:
        contagem[q.lower()] = contagem.get(q.lower(), 0) + 1
    unicas = [(q, r) for q, r in cand if contagem[q.lower()] == 1]
    passo = max(1, len(unicas) // n)
    return unicas[::passo][:n], len(cand) - len(unicas)


def run_auto(c, n, verbose):
    cases, ambiguas = auto_cases(c, n)
    print(f"== AUTO (item conhecido): {len(cases)} consultas; {ambiguas} descartadas por ambiguidade (mesma consulta em várias notas)")
    por_tipo, rr_all, h3_all = {}, 0.0, 0
    falhas = []
    for q, r in cases:
        res = xmem.hybrid(c, q, k=8)
        pos = next((i for i, h in enumerate(res, 1) if h["row"]["id"] == r["id"]), None)
        rr = 1.0 / pos if pos else 0.0
        rr_all += rr
        h3_all += 1 if pos and pos <= 3 else 0
        t = por_tipo.setdefault(r["kind"], [0, 0.0, 0])
        t[0] += 1; t[1] += rr; t[2] += 1 if pos and pos <= 3 else 0
        if not pos or pos > 3:
            falhas.append((pos, r, q))
    for k, (qtd, rr, h3) in sorted(por_tipo.items()):
        print(f"   {k:10} n={qtd:3}  hit@3 {h3}/{qtd}  MRR {rr / qtd:.3f}")
    n = len(cases) or 1
    print(f"   TOTAL      n={len(cases):3}  hit@3 {h3_all}/{len(cases)}  MRR {rr_all / n:.3f}\n")
    if falhas:
        print(f"   {len(falhas)} fora do top 3 (pior primeiro):")
        for pos, r, q in sorted(falhas, key=lambda x: (x[0] is not None, -(x[0] or 0)))[: (30 if verbose else 8)]:
            txt = "(texto omitido: vault sensível)" if r["sens"] == "alta" else q[:70]
            print(f"   {('#%d' % pos) if pos else 'NÃO ACHOU':>10}  {r['project']}:{r['title'][:55]}  — {txt}")
        print()
    return {"auto_mrr": round(rr_all / n, 4), "auto_hit3": round(h3_all / n, 4), "auto_n": len(cases)}


def compare_baseline(m, save):
    old = {}
    try:
        old = json.load(open(BASELINE, encoding="utf-8"))
    except (OSError, ValueError):
        pass
    for k in ("auto_mrr", "auto_hit3"):
        if k in m and k in old:
            d = m[k] - old[k]
            print(f"   {k}: {m[k]:.3f} (linha de base {old[k]:.3f}, {'+' if d >= 0 else ''}{d:.3f}{'  ⚠ piorou' if d < -0.01 else ''})")
    if save:
        os.makedirs(DATA, exist_ok=True)
        json.dump(m, open(BASELINE, "w", encoding="utf-8"), indent=1)
        print(f"   linha de base gravada em {BASELINE}")


def main():
    verbose = "--verbose" in sys.argv
    c = xmem.index(quiet=True)
    for label, cases in (("CONJUNTO DE AJUSTE", GOLDEN), ("CONJUNTO RESERVADO (não usado para ajustar)", HELDOUT)):
        if cases:
            run(c, label, cases, verbose)
    local = _arg("--local", LOCAL) or (LOCAL if os.path.isfile(LOCAL) else None)
    if local and os.path.isfile(local):
        run(c, f"LOCAL ({os.path.basename(local)}; fora do git)", [tuple(x) for x in json.load(open(local, encoding="utf-8"))], verbose)
    auto = _arg("--auto", "150")
    if auto:
        compare_baseline(run_auto(c, int(auto), verbose), "--save" in sys.argv)


def run(c, label, cases, verbose):
    print(f"== {label}")
    hits3 = hits5 = 0
    rr = 0.0
    for q, want, cur, desc in cases:
        res = xmem.hybrid(c, q, k=8, exclude_project=cur)
        pos = next((i for i, h in enumerate(res, 1) if want.lower() in h["row"]["rel"].lower() or want.lower() in h["row"]["project"].lower()), None)
        if pos and pos <= 3:
            hits3 += 1
        if pos and pos <= 5:
            hits5 += 1
        rr += 1.0 / pos if pos else 0.0
        mark = f"#{pos}" if pos else "NÃO ACHOU"
        print(f"{mark:>10}  {desc}")
        if verbose or not pos or pos > 3:
            for i, h in enumerate(res[:4], 1):
                print(f"            {i}. {h['row']['project']}:{h['row']['rel'][:70]}")
    n = len(cases)
    print(f"hit@3 {hits3}/{n}   hit@5 {hits5}/{n}   MRR {rr / n:.3f}\n")


if __name__ == "__main__":
    main()
