#!/usr/bin/env python3
"""Avaliação de qualidade da busca do xmem contra respostas conhecidas (golden set).

Cada caso: pergunta + trecho do caminho da nota que DEVE aparecer + projeto de origem da consulta
(para recall, que exclui o projeto atual). As respostas foram verificadas à mão nos vaults reais.
Métrica: posição da nota esperada (hit@3 / hit@5) e MRR. Uso: eval_xmem.py [--verbose]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import xmem  # noqa: E402

# (consulta, trecho do rel esperado, projeto "atual" simulado ou None, descrição)
GOLDEN = []
# Conjunto SEPARADO, escrito depois do ajuste do motor: não foi usado para calibrar nada.
HELDOUT = []

def main():
    verbose = "--verbose" in sys.argv
    c = xmem.index(quiet=True)
    for label, cases in (("CONJUNTO DE AJUSTE", GOLDEN), ("CONJUNTO RESERVADO (não usado para ajustar)", HELDOUT)):
        run(c, label, cases, verbose)


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
