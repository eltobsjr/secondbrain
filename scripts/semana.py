#!/usr/bin/env python3
"""Semana, prazo e janelas do quadro (decisão 012). Funções puras: `hoje` entra como parâmetro, então os testes usam datas fixas.

- Semana ISO 8601, segunda a domingo (`2026-W47`).
- Prazo é uma data. Dentro do prazo nunca é atrasado: atrasado só existe com prazo vencido. Sem prazo nunca atrasa.
- Flags: sem-prazo, no-prazo, chegando (até N dias, padrão 3), hoje, atrasado.
- Janelas (agenda): atrasadas, hoje, esta semana, próxima semana, mais adiante, sem prazo.
- `backlog` é o lugar de quem não tem semana: item de documento vivo (data da migração, não do surgimento) ou movido para lá.
"""
import re
from datetime import date, timedelta

ALERTA_DIAS = 3
CAPACIDADE = 7                       # aviso, nunca bloqueio; 0 desliga
BACKLOG = "backlog"
JANELAS = (("atrasadas", "Atrasadas"), ("hoje", "Hoje"), ("esta-semana", "Esta semana"),
           ("proxima-semana", "Próxima semana"), ("adiante", "Mais adiante"), ("sem-prazo", "Sem prazo"))
FLAG_LABEL = {"sem-prazo": "sem prazo", "no-prazo": "no prazo", "chegando": "chegando", "hoje": "vence hoje", "atrasado": "atrasado"}
_SEM = re.compile(r"^(\d{4})-W(\d{2})$")


def parse_data(s):
    try:
        return date.fromisoformat((s or "")[:10])
    except ValueError:
        return None


def semana_iso(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def inicio(sem):
    m = _SEM.match(sem or "")
    if not m:
        raise ValueError(f"semana inválida: {sem!r} (use AAAA-Www, esta, proxima, anterior ou backlog)")
    return date.fromisocalendar(int(m.group(1)), int(m.group(2)), 1)


def intervalo(sem):
    i = inicio(sem)
    return i, i + timedelta(days=6)


def rotulo(sem):
    a, b = intervalo(sem)
    return f"{a.day:02d} a {b.day:02d}/{b.month:02d}" if a.month == b.month else f"{a.day:02d}/{a.month:02d} a {b.day:02d}/{b.month:02d}"


def deslocar(sem, n):
    return semana_iso(inicio(sem) + timedelta(weeks=n))


def resolver_semana(txt, hoje):
    """'esta', 'proxima', 'anterior', 'backlog', 'AAAA-Www' ou 'Www' (ano de hoje) -> texto normalizado."""
    t = (txt or "").strip().lower()
    atual = semana_iso(hoje)
    if t in ("esta", "atual"):
        return atual
    if t in ("proxima", "próxima"):
        return deslocar(atual, 1)
    if t == "anterior":
        return deslocar(atual, -1)
    if t == BACKLOG:
        return BACKLOG
    if re.match(r"^w\d{1,2}$", t):
        t = f"{hoje.year}-W{int(t[1:]):02d}"
    inicio(t.upper())
    return t.upper()


def resolver_data(txt, hoje):
    """ISO, 'hoje', 'amanha', '+Nd' ou 'fim-da-semana' -> date."""
    t = (txt or "").strip().lower()
    if t == "hoje":
        return hoje
    if t in ("amanha", "amanhã"):
        return hoje + timedelta(days=1)
    if t == "fim-da-semana":
        return intervalo(semana_iso(hoje))[1]
    m = re.match(r"^\+(\d+)d$", t)
    if m:
        return hoje + timedelta(days=int(m.group(1)))
    d = parse_data(t) if re.match(r"^\d{4}-\d{2}-\d{2}$", t) else None
    if not d:
        raise ValueError(f"data inválida: {txt!r} (use AAAA-MM-DD, hoje, amanha, +3d ou fim-da-semana)")
    return d


def prazo_padrao(sem):
    """Planejar numa semana sem dar prazo: o prazo é o domingo dela."""
    return intervalo(sem)[1]


def situacao(prazo, hoje, alerta=ALERTA_DIAS):
    """-> (flag, dias, texto). `dias` é o que falta (ou há quanto atrasou). Sem prazo nunca atrasa."""
    d = parse_data(prazo)
    if not d:
        return "sem-prazo", None, "sem prazo"
    dias = (d - hoje).days
    if dias < 0:
        n = -dias
        return "atrasado", n, f"atrasado há {n} dia" + ("" if n == 1 else "s")
    if dias == 0:
        return "hoje", 0, "vence hoje"
    if dias <= alerta:
        return "chegando", dias, "vence amanhã" if dias == 1 else f"vence em {dias} dias"
    return "no-prazo", dias, f"no prazo ({dias} dias)"


def janela(prazo, hoje):
    d = parse_data(prazo)
    if not d:
        return "sem-prazo"
    if d < hoje:
        return "atrasadas"
    if d == hoje:
        return "hoje"
    sh, sd = semana_iso(hoje), semana_iso(d)
    if sd == sh:
        return "esta-semana"
    if sd == deslocar(sh, 1):
        return "proxima-semana"
    return "adiante"


def _semana_de(txt):
    d = parse_data(txt)
    return semana_iso(d) if d else ""


def com_registro(cards):
    """Semanas em que há registro: cartão que surgiu, foi planejado ou foi concluído nelas."""
    out = set()
    for k in cards:
        if k.get("fora_calendario"):
            continue
        if k.get("semana_ef"):
            out.add(k["semana_ef"])
        if k.get("status") == "feito":
            s = _semana_de(k.get("feito_em", ""))
            if s:
                out.add(s)
    return out


def ultima_semana(cards):
    """A semana em que o quadro abre: a mais recente que tem registro (None se não há nenhum)."""
    s = com_registro(cards)
    return max(s) if s else None


def faixa(cards, hoje, tamanho=12):
    """Semanas para a faixa do calendário: contíguas, terminando na mais recente entre o último registro, esta e a próxima."""
    ult = ultima_semana(cards)
    fim = max([x for x in (ult, deslocar(semana_iso(hoje), 1)) if x])
    return [deslocar(fim, -i) for i in range(tamanho - 1, -1, -1)]


def semanas_do_calendario(cards, hoje, limite=80):
    """Todas as semanas, da mais antiga com registro até a próxima de hoje (ou do último registro), contíguas."""
    regs = com_registro(cards) | {semana_iso(hoje), deslocar(semana_iso(hoje), 1)}
    ini, fim = min(regs), max(regs)
    out, s = [], fim
    while s >= ini and len(out) < limite:
        out.append(s)
        s = deslocar(s, -1)
    return list(reversed(out))


def da_semana(cards, sem):
    """-> (abertas, feitas) da semana. Aberta: mora na semana. Feita: foi concluída nela (feito-em)."""
    abertas = [k for k in cards if k.get("status") not in ("feito", "descartado") and k.get("semana_ef") == sem and not k.get("oculto")]
    feitas = [k for k in cards if k.get("status") == "feito" and not k.get("fora_calendario") and _semana_de(k.get("feito_em", "")) == sem]
    return abertas, feitas


def carga(cards, sem):
    """Quantos cartões abertos foram planejados (semana explícita) nesta semana."""
    return sum(1 for k in cards if k.get("planejado") and k.get("semana_ef") == sem and k.get("status") not in ("feito", "descartado"))


def propostas_revisao(cards, hoje):
    """Revisão semanal: cartões abertos de semanas passadas. Propõe, nunca move. `mecanica` = pode ser aplicada sem decidir nada."""
    atual = semana_iso(hoje)
    out = []
    for k in cards:
        if k.get("status") in ("feito", "descartado") or k.get("oculto") or k.get("backlog") or not k.get("semana_ef"):
            continue
        if k["semana_ef"] >= atual:
            continue
        d = parse_data(k.get("prazo", ""))
        base = {"id": k["id"], "projeto": k["projeto"], "titulo": k["titulo"], "de": k["semana_ef"]}
        if d and d >= hoje:
            out.append(dict(base, criterio="prazo-futuro", para=semana_iso(d), mecanica=True,
                            texto=f"o prazo ({d.isoformat()}) cai em {semana_iso(d)}"))
        elif k["status"] in ("fazendo", "revisao"):
            out.append(dict(base, criterio="em-andamento", para=atual, mecanica=True, texto="está em andamento: segue na semana atual"))
        elif k["status"] == "bloqueado":
            out.append(dict(base, criterio="bloqueado", para=None, mecanica=False, texto="bloqueado: fica onde está, com a flag"))
        elif d:
            out.append(dict(base, criterio="prazo-vencido", para=atual, mecanica=False,
                            texto=f"prazo venceu em {d.isoformat()}: replanejar com novo prazo, ou descartar"))
        else:
            out.append(dict(base, criterio="sem-prazo", para=None, mecanica=False,
                            texto="sem prazo: escolha entre semana atual, backlog ou descartar"))
    return out
