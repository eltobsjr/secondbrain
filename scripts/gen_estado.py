#!/usr/bin/env python3
"""Cria um RASCUNHO de ESTADO.md a partir do devtrack mais recente (só se ainda não existir).

Determinístico (sem modelo): extrai título, resumo curto e pendências do último devtrack e
marca o arquivo como rascunho; o próximo /devtrack o reescreve com o estado real.
Uso: gen_estado.py <vault> [--write]
"""
import os
import re
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _vault import first_h1, read_manifest, split_frontmatter  # noqa: E402


def latest_devtrack(vault, papeis):
    d = os.path.join(vault, papeis.get("devtrack", "devtrack/"))
    if not os.path.isdir(d):
        return None
    cand = [f for f in os.listdir(d) if f.endswith(".md") and re.match(r"\d{4}-\d{2}-\d{2}", f)]
    return os.path.join(d, sorted(cand)[-1]) if cand else None


def section(body, pattern):
    m = re.search(rf"^##+\s+(?:{pattern})[^\n]*\n(.*?)(?=^##+\s|\Z)", body, re.S | re.M | re.I)
    return m.group(1).strip() if m else ""


def clean(s, n):
    s = re.sub(r"\s+", " ", re.sub(r"[`*_>#]", "", s)).strip()
    return (s[: n - 1] + "…") if len(s) > n else s


def build(vault):
    papeis, _ = read_manifest(vault)
    last = latest_devtrack(vault, papeis)
    nome = os.path.basename(os.path.abspath(vault)).replace("SecondBrain", "") or "projeto"
    hoje = date.today().isoformat()
    if not last:
        return None
    stem = os.path.basename(last)[:-3]
    dt = datetime.strptime(stem[:10], "%Y-%m-%d").date()
    dias = (date.today() - dt).days
    text = open(last, encoding="utf-8", errors="ignore").read()
    fm, body = split_frontmatter(text)
    titulo = first_h1(body) or stem
    feito = section(body, r"o que foi feito|resumo|contexto|visão geral")
    if not feito:
        paras = [p for p in re.split(r"\n\s*\n", re.sub(r"^#.*$", "", body, flags=re.M)) if p.strip()]
        feito = paras[0] if paras else ""
    pend = re.findall(r"^\s*[-*]\s*\[ \]\s*(.+)$", body, re.M)
    prox = section(body, r"pr[óo]ximos? passos?|pr[óo]xima a[çc][ãa]o|pend[êe]ncias")
    prox_items = [clean(re.sub(r"^\s*(\d+[.)]|[-*])\s*(\[ \])?\s*", "", ln), 160)
                  for ln in prox.splitlines() if re.match(r"^\s*(\d+[.)]|[-*])\s+", ln)]
    proximo = (prox_items or [clean(p, 160) for p in pend] or ["(definir no próximo /devtrack)"])[0]
    out = ["---", "tipo: estado", f"atualizado: {hoje}", f'ultimo-devtrack: "{stem}"',
           "origem: rascunho gerado na migração a partir do último devtrack (o /devtrack reescreve)", "---", "",
           f"# Estado — {nome}", "", "## Agora",
           f"Último trabalho registrado: **{clean(titulo, 120)}** ({dt.isoformat()}).",
           (clean(feito, 320) if feito else "")]
    if dias > 30:
        out += ["", f"Atenção: sem devtrack há {dias} dias (em {hoje}); confirme se o estado ainda vale."]
    out += ["", "## Próximo passo", proximo, "", "## Bloqueios e dependências",
            "- (não inferido; revise)", "", "## Pendências abertas no último devtrack"]
    out += [f"- {clean(p, 160)}" for p in pend[:7]] or ["- nenhuma registrada"]
    if len(pend) > 7:
        out.append(f"- … e mais {len(pend) - 7} em `{papeis.get('devtrack', 'devtrack/')}{stem}.md`")
    out += ["", "## Fatos voláteis",
            f"- Este estado reflete o devtrack de {dt.isoformat()} (em {hoje[:7]}) — fonte: "
            f"`{papeis.get('devtrack', 'devtrack/')}{stem}.md`"]
    return "\n".join(x for x in out if x is not None).replace("\n\n\n", "\n\n") + "\n"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or not os.path.isfile(os.path.join(args[0], "_secondbrain.md")):
        sys.exit("uso: gen_estado.py <vault com _secondbrain.md> [--write]")
    vault = args[0].rstrip("/")
    papeis, _ = read_manifest(vault)
    target = os.path.join(vault, papeis.get("estado", "ESTADO.md"))
    name = os.path.basename(vault)
    if os.path.exists(target):
        print(f"{name}: ESTADO.md já existe; mantido.")
        return
    text = build(vault)
    if text is None:
        print(f"{name}: sem devtrack; ESTADO.md não gerado.")
        return
    if "--write" in sys.argv:
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"{name}: ESTADO.md criado (rascunho).")
    else:
        print(f"=== {name}\n{text}")


if __name__ == "__main__":
    main()
