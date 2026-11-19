#!/usr/bin/env python3
"""Regras de pendência (decisão 011): o que é tarefa, o que é ruído e o que ficou sem-sinal.

Devtrack é um retrato de fim de sessão: toda caixa `- [ ]` escrita nele vive para sempre, a menos que uma sessão
posterior a reescreva. Em projetos reais, a grande maioria dos itens abertos nunca reaparece numa sessão seguinte. Este
módulo separa o que ainda é pendência do que só ficou no retrato. Só stdlib, determinístico, sem modelo.

- ruído:     não é tarefa (pergunta de checklist, frase de estado como "nenhum commit feito").
- repetido:  a mesma tarefa foi reescrita depois, em aberto; o cartão novo é o vivo.
- feito:     uma sessão posterior marcou `[x]` um item parecido (outra redação).
- sem-sinal:  o projeto seguiu trabalhando (há devtrack 14+ dias depois) e o item nunca mais apareceu, e o estado vivo
             do projeto (ESTADO.md, prioridade/atual.md) também não o cita.

"Sem sinal" (antes "superado") NÃO prova que o item acabou: só diz que o projeto seguiu e o item nunca mais apareceu. Uma conferência no código mostrou itens vivos nessa faixa, por isso o nome e as travas de risco e roadmap.

Nada aqui apaga ou reescreve nota. O resultado só decide o que o quadro mostra por padrão.
"""
import bisect
import math
import re
import unicodedata
from collections import Counter
from datetime import date

SUPERADO_DIAS = 14      # o projeto precisa ter seguido (devtrack) pelo menos isso depois do item
SIM_FECHA = 0.50        # semelhança que basta para tratar "outra redação" como a mesma tarefa
SIM_PROPOSTA = 0.35     # abaixo de SIM_FECHA: só vira proposta na conciliação, nunca ação automática
CITADO = 0.60           # fração do item (por peso) que o documento vivo precisa conter para o item contar como vivo
OCULTOS = ("pergunta", "narrativo", "repetido", "sem-sinal")

STOP = frozenset("""para como mais sobre antes depois ainda esta este esse essa isso aqui sera serem fazer feito feita nesta nesse
desta deste usuario sessao itens item commit commits push fix feat merge branch main codigo arquivo arquivos pelo pela pelos pelas
entre quando onde pode podem deve devem tambem apenas somente depende dependem todos todas cada outro outra outros outras campo campos""".split())

# frase de estado: ancorada no começo e curta. "Não foi testado em Windows o instalador" e "Nada a ver: corrigir o login" são tarefas.
_NARRATIVO = re.compile(
    r"^(nenhum|nenhuma|nada(?! a ver)|ainda nao|nao foi|nao foram|segue sem|continua sem|frontend nao|backend nao|/code-review nao"
    r"|sem mudanca|nao rodado)\b")
NARRATIVO_MAX_PALAVRAS = 6
# item que fala de risco aberto nunca vira "sem-sinal" sozinho: sumir de um devtrack não resolve segredo exposto nem bloqueio
_RISCO = re.compile(r"\b(pendentes?|pendencias?|bloquead[oa]s?|bloqueios?|expost[oa]s?|segredos?|secrets?|chaves?|tokens?|senhas?|credenciais|"
                    r"api.?key|service.?role|rotacion\w*|vazad[oa]s?|vazamentos?|ainda nao|"
                    r"futuro|roadmap|rfc|fase \d+)\b")      # roadmap não "supera" por silêncio: o item é plano, não tarefa esquecida
# primeira palavra de uma pergunta que ainda é tarefa ("Migrar o banco para o PG 16?"): infinitivo, não interrogativo
_NAO_INFINITIVO = frozenset("qualquer colher mulher poder dever prazer taxer".split())


def _infinitivo(t):
    w = re.match(r"[a-z]+", t)
    w = w.group(0) if w else ""
    return len(w) >= 5 and w.endswith(("ar", "er", "ir", "or")) and w not in _NAO_INFINITIVO


def risco(text):
    return bool(_RISCO.search(strip_acc(text.lower())))


def strip_acc(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def tokens(text):
    t = strip_acc(text.lower()).replace("`", "")
    ws = (w.strip(".-") for w in re.findall(r"[a-z0-9_\-\.]{4,}", t))      # "login." == "login"; o ponto de "app.ts" fica
    return frozenset(w for w in ws if len(w) >= 4 and w not in STOP and not w.isdigit())


def ruido(text, kind="devtrack"):
    """'pergunta' (item de checklist em forma de pergunta), 'narrativo' (frase de estado) ou '' (é tarefa).

    Só vale para devtrack, que é retrato de sessão. Em CHECKLIST, feature ou prioridade, uma pergunta ("o serviço volta
    sozinho?") é uma verificação real e uma caixa aberta é trabalho aberto."""
    if kind != "devtrack":
        return ""
    t = strip_acc(text.lower()).strip(" *_`>-")
    if t.endswith("?") and not _infinitivo(t):
        return "pergunta"
    if _NARRATIVO.search(t) and len(t.split()) <= NARRATIVO_MAX_PALAVRAS:
        return "narrativo"
    return ""


class Corpus:
    """IDF sobre um conjunto de textos (cartões, assuntos de commit) para comparar redações diferentes do mesmo assunto."""

    def __init__(self, textos):
        toks = [tokens(t) for t in textos]
        df = Counter(w for t in toks for w in t)
        n = len(toks) + 1
        self._idf = {w: math.log((n + 1) / (v + 0.5)) for w, v in df.items()}

    def peso(self, ws):
        return sum(self._idf.get(w, 0.0) for w in ws)

    def sim(self, a, b):
        """(semelhança 0..1, tokens em comum). Exige 2+ tokens em comum, senão 0."""
        sh = a & b
        if len(sh) < 2:
            return 0.0, sh
        return self.peso(sh) / math.sqrt(self.peso(a) * self.peso(b) + 1e-9), sh


def _dia(s):
    try:
        return date.fromisoformat((s or "")[:10])
    except ValueError:
        return None


class Projeto:
    """Visão de um projeto: as caixas dos devtracks em ordem cronológica e o IDF para comparar redações."""

    def __init__(self, todos, ultimo_devtrack, vivos=()):
        # todos: linhas (dict-like) com text, checked, data, rel, kind, line de TODAS as caixas do projeto
        # vivos: linhas de texto do estado vivo (ESTADO.md, prioridade/atual.md), que podem citar pendências em prosa
        self.dev = sorted((r for r in todos if r["kind"] == "devtrack" and r["data"]), key=lambda r: (r["data"], r["rel"], r["line"]))
        self.tok = [tokens(r["text"]) for r in self.dev]
        self.vivos = [t for t in (tokens(v) for v in vivos) if len(t) >= 2]
        df = Counter(w for t in self.tok + self.vivos for w in t)
        n = len(self.tok) + len(self.vivos) + 1
        self._idf = {w: math.log((n + 1) / (v + 0.5)) for w, v in df.items()}
        self.chaves = [(r["data"], r["rel"]) for r in self.dev]
        self.ultimo = _dia(ultimo_devtrack)

    def _w(self, ws):
        return sum(self._idf.get(w, 0.0) for w in ws)

    def sim(self, a, b):
        sh = a & b
        if len(sh) < 2:
            return 0.0
        return self._w(sh) / math.sqrt(self._w(a) * self._w(b) + 1e-9)

    def citado(self, a):
        """O estado vivo contém (quase) todo o peso do item? Contenção, não semelhança: o item é curto e a linha viva é prosa."""
        if len(a) < 2:
            return False
        total = self._w(a) or 1e-9
        return any(len(a & v) >= 2 and self._w(a & v) / total >= CITADO for v in self.vivos)

    def depois(self, data, rel):
        """Índice do primeiro item de uma nota posterior à (data, rel)."""
        return bisect.bisect_right(self.chaves, (data, rel, ))  # as chaves são (data, rel): tudo > (data, rel) fica à direita

    def classificar(self, text, data, rel):
        """-> (estado, evidencia, semelhança). estado: 'feito' | 'repetido' | 'sem-sinal' | ''."""
        a = tokens(text)
        if len(a) < 2:
            return "", "", 0.0
        ini = self.depois(data, rel + "￿")      # pula as demais caixas da própria nota
        best_chk = best_unc = (0.0, None)
        for i in range(ini, len(self.dev)):
            s = self.sim(a, self.tok[i])
            if self.dev[i]["checked"]:
                if s > best_chk[0]:
                    best_chk = (s, self.dev[i])
            elif s > best_unc[0]:
                best_unc = (s, self.dev[i])
        if best_chk[0] >= SIM_FECHA:
            r = best_chk[1]
            return "feito", f"marcado como feito em {r['data'][:10]}: {r['text'][:80]}", best_chk[0]
        if best_unc[0] >= SIM_FECHA:
            return "repetido", f"reescrito em {best_unc[1]['data'][:10]}", best_unc[0]
        d0 = _dia(data)
        if d0 and self.ultimo and (self.ultimo - d0).days >= SUPERADO_DIAS:
            if risco(text):
                return "", "cita risco aberto (pendente, bloqueado, exposto, segredo): não vira sem-sinal sozinho", max(best_chk[0], best_unc[0])
            if self.citado(a):
                return "", "citado no estado vivo do projeto", max(best_chk[0], best_unc[0])
            return "sem-sinal", f"o projeto seguiu até {self.ultimo.isoformat()} e o item não reapareceu", 0.0
        return "", "", max(best_chk[0], best_unc[0])
