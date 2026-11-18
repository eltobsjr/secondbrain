"""Testes de semana, prazo, flags e janelas (scripts/semana.py) e da integração no quadro. Datas fixas: nada depende do dia da execução."""
import contextlib
import importlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from argparse import Namespace
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")
HOJE = date(2026, 11, 18)            # quarta-feira, semana 2026-W47 (16 a 22/11)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class SemanaPuraTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, SCRIPTS)
        sys.modules.pop("semana", None)
        cls.sm = importlib.import_module("semana")

    def test_semana_iso_e_intervalo(self):
        sm = self.sm
        self.assertEqual(sm.semana_iso(HOJE), "2026-W47")
        self.assertEqual(sm.semana_iso(date(2026, 11, 16)), "2026-W47", "segunda abre a semana")
        self.assertEqual(sm.semana_iso(date(2026, 11, 22)), "2026-W47", "domingo fecha a semana")
        self.assertEqual(sm.rotulo("2026-W47"), "16 a 22/11")
        self.assertEqual(sm.rotulo("2026-W49"), "30/11 a 06/12", "semana que cruza o mês")
        self.assertEqual(sm.deslocar("2027-W01", -1), "2026-W53", "2026 tem 53 semanas ISO: atravessa o ano")
        self.assertEqual(sm.deslocar("2026-W01", -1), "2025-W52")
        self.assertEqual(sm.prazo_padrao("2026-W47"), date(2026, 11, 22), "sem prazo, o padrão é o domingo da semana")

    def test_resolver_semana_e_data(self):
        sm = self.sm
        self.assertEqual(sm.resolver_semana("esta", HOJE), "2026-W47")
        self.assertEqual(sm.resolver_semana("proxima", HOJE), "2026-W48")
        self.assertEqual(sm.resolver_semana("anterior", HOJE), "2026-W46")
        self.assertEqual(sm.resolver_semana("w50", HOJE), "2026-W50")
        self.assertEqual(sm.resolver_semana("backlog", HOJE), "backlog")
        with self.assertRaises(ValueError):
            sm.resolver_semana("2026-W99", HOJE)
        self.assertEqual(sm.resolver_data("+3d", HOJE), date(2026, 11, 21))
        self.assertEqual(sm.resolver_data("amanha", HOJE), date(2026, 11, 19))
        self.assertEqual(sm.resolver_data("fim-da-semana", HOJE), date(2026, 11, 22))
        with self.assertRaises(ValueError):
            sm.resolver_data("semana que vem", HOJE)

    def test_dentro_do_prazo_nunca_e_atrasado(self):
        sm = self.sm
        casos = [("2026-12-30", "no-prazo"), ("2026-11-22", "no-prazo"), ("2026-11-21", "chegando"), ("2026-11-19", "chegando"),
                 ("2026-11-18", "hoje"), ("2026-11-17", "atrasado"), ("", "sem-prazo")]
        for prazo, esperado in casos:
            self.assertEqual(sm.situacao(prazo, HOJE)[0], esperado, prazo)
        self.assertEqual(sm.situacao("2026-11-17", HOJE)[2], "atrasado há 1 dia")
        self.assertEqual(sm.situacao("2026-11-13", HOJE)[2], "atrasado há 5 dias")
        self.assertEqual(sm.situacao("2026-11-19", HOJE)[2], "vence amanhã")
        self.assertEqual(sm.situacao("2026-11-21", HOJE)[2], "vence em 3 dias")
        self.assertEqual(sm.situacao("", HOJE)[0], "sem-prazo", "sem prazo nunca atrasa")

    def test_janela_de_alerta_configuravel(self):
        self.assertEqual(self.sm.situacao("2026-11-23", HOJE, alerta=5)[0], "chegando")
        self.assertEqual(self.sm.situacao("2026-11-23", HOJE, alerta=3)[0], "no-prazo")

    def test_janelas_da_agenda(self):
        sm = self.sm
        casos = [("2026-11-10", "atrasadas"), ("2026-11-18", "hoje"), ("2026-11-20", "esta-semana"), ("2026-11-25", "proxima-semana"),
                 ("2026-12-15", "adiante"), ("", "sem-prazo")]
        for prazo, esperado in casos:
            self.assertEqual(sm.janela(prazo, HOJE), esperado, prazo)

    def _card(self, i, **kw):
        base = {"id": i, "projeto": "p", "titulo": i, "status": "a-fazer", "oculto": "", "backlog": False, "semana_ef": "", "planejado": False,
                "fora_calendario": False, "feito_em": "", "prazo": ""}
        base.update(kw)
        return base

    def test_abre_na_ultima_semana_com_registro(self):
        cards = [self._card("a", semana_ef="2026-W44"), self._card("b", status="feito", feito_em="2026-11-09", semana_ef="2026-W43"),
                 self._card("c", status="feito", feito_em="2026-11-18", fora_calendario=True, semana_ef="2026-W47"),
                 self._card("d", backlog=True, semana_ef="")]
        self.assertEqual(self.sm.ultima_semana(cards), "2026-W46", "feito em 09/11 é registro da 46; limpeza e backlog não contam")
        self.assertEqual(self.sm.ultima_semana([]), None)
        faixa = self.sm.faixa(cards, HOJE, tamanho=4)
        self.assertEqual(faixa[-1], "2026-W48", "a faixa chega até a semana que vem, para poder planejar")
        self.assertEqual(len(faixa), 4)

    def test_feito_fica_na_semana_em_que_foi_feito(self):
        cards = [self._card("a", status="feito", feito_em="2026-11-10", semana_ef="2026-W44"), self._card("b", semana_ef="2026-W44")]
        abertas, feitas = self.sm.da_semana(cards, "2026-W46")
        self.assertEqual([k["id"] for k in feitas], ["a"], "feito em 10/11 pertence à semana 46, mesmo tendo surgido na 44")
        self.assertEqual([k["id"] for k in abertas], [])
        abertas44, feitas44 = self.sm.da_semana(cards, "2026-W44")
        self.assertEqual([k["id"] for k in abertas44], ["b"])
        self.assertEqual(feitas44, [])

    def test_carga_conta_so_planejados(self):
        cards = [self._card("a", semana_ef="2026-W47", planejado=True), self._card("b", semana_ef="2026-W47"),
                 self._card("c", semana_ef="2026-W47", planejado=True, status="feito")]
        self.assertEqual(self.sm.carga(cards, "2026-W47"), 1, "só o planejado e ainda aberto; o que surgiu sem plano não pesa")

    def test_revisao_propoe_por_criterio_e_nunca_move(self):
        cards = [self._card("fut", semana_ef="2026-W44", prazo="2026-12-02"), self._card("and", semana_ef="2026-W44", status="fazendo"),
                 self._card("blq", semana_ef="2026-W44", status="bloqueado"), self._card("ven", semana_ef="2026-W44", prazo="2026-11-05"),
                 self._card("sem", semana_ef="2026-W44"), self._card("atual", semana_ef="2026-W47"),
                 self._card("oculto", semana_ef="2026-W44", oculto="superado"), self._card("feito", semana_ef="2026-W44", status="feito")]
        p = {x["id"]: x for x in self.sm.propostas_revisao(cards, HOJE)}
        self.assertEqual(set(p), {"fut", "and", "blq", "ven", "sem"}, "semana atual, oculto e feito ficam de fora")
        self.assertEqual((p["fut"]["criterio"], p["fut"]["para"], p["fut"]["mecanica"]), ("prazo-futuro", "2026-W49", True))
        self.assertEqual((p["and"]["criterio"], p["and"]["para"]), ("em-andamento", "2026-W47"))
        self.assertFalse(p["blq"]["mecanica"])
        self.assertEqual(p["ven"]["criterio"], "prazo-vencido")
        self.assertEqual(p["sem"]["criterio"], "sem-prazo")
        self.assertFalse(p["sem"]["mecanica"], "sem prazo: quem decide é o usuário")


class QuadroSemanaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="sem-home-")
        os.environ["HOME"] = cls.home
        os.environ["SECONDBRAIN_XMEM_DB"] = os.path.join(cls.home, "xmem.db")
        sys.path.insert(0, SCRIPTS)
        for m in ("xmem", "_vault", "board", "pend", "semana", "reconcile"):
            sys.modules.pop(m, None)
        for m in ("xmem", "pend", "semana", "board"):
            setattr(cls, m, importlib.import_module(m))
        cls.vault = os.path.join(cls.home, "dev/proj_s/ProjSSecondBrain")
        write(cls.vault + "/_secondbrain.md",
              "---\nschema: 2\nsensibilidade: normal\nquadro-alerta: 5\nquadro-capacidade: 2\nbackup: true\nmodulos: [devtrack, prioridade]\npapeis:\n  devtrack: devtrack/\n  prioridade: prioridade/\n---\n\n# m\n")
        write(cls.vault + "/devtrack/2026-11-03 - Semana 45.md",
              "---\ntipo: devtrack\ndata: 2026-11-03\n---\n\n# S45\n\n- [ ] Configurar monitoramento do servidor de relatórios\n- [ ] Revisar contrato com o fornecedor de pagamentos\n")
        write(cls.vault + "/devtrack/2026-11-10 - Semana 46.md",
              "---\ntipo: devtrack\ndata: 2026-11-10\n---\n\n# S46\n\n- [ ] Publicar a nova versão do aplicativo móvel\n- [x] Configurar monitoramento do servidor de relatórios\n")
        write(cls.vault + "/prioridade/atual.md", "---\ntipo: prioridade\ndata: 2026-11-16\n---\n\n# Prioridades\n\n- [ ] Migrar o banco de dados analítico para a nova região\n")
        cls.c = cls.xmem.index(quiet=True)

    @classmethod
    def tearDownClass(cls):
        cls.c.close()
        shutil.rmtree(cls.home, ignore_errors=True)

    def setUp(self):
        self.q = os.path.join(self.vault, "quadro.md")
        if os.path.exists(self.q):
            os.remove(self.q)

    def cards(self, **kw):
        return {k["titulo"]: k for k in self.board.build(self.c, "proj_s", ocultos=True, hoje=HOJE, **kw)}

    def test_surgiu_so_para_devtrack_e_documento_vivo_vai_para_backlog(self):
        k = self.cards()
        self.assertEqual(k["Publicar a nova versão do aplicativo móvel"]["surgiu"], "2026-W46")
        self.assertEqual(k["Publicar a nova versão do aplicativo móvel"]["semana_ef"], "2026-W46")
        doc = k["Migrar o banco de dados analítico para a nova região"]
        self.assertEqual(doc["surgiu"], "", "a data do documento vivo é a da migração, não a do surgimento")
        self.assertTrue(doc["backlog"])
        self.assertEqual(doc["semana_ef"], "")

    def test_linha_do_cartao_e_a_linha_do_arquivo(self):
        """Regressão: a linha vinha do corpo da nota (sem o frontmatter) e não batia com o arquivo que o usuário abre."""
        k = self.cards()["Revisar contrato com o fornecedor de pagamentos"]
        arquivo = os.path.join(self.vault, k["origem"]["nota"])
        linhas = open(arquivo, encoding="utf-8").read().splitlines()
        self.assertIn("Revisar contrato com o fornecedor de pagamentos", linhas[k["origem"]["linha"] - 1])

    def test_feito_pela_origem_leva_a_data_da_sessao_que_marcou(self):
        k = self.cards()["Configurar monitoramento do servidor de relatórios"]
        self.assertEqual(k["status"], "feito")
        self.assertEqual(k["feito_em"], "2026-11-10")
        self.assertEqual(k["surgiu"], "2026-W45", "surgiu na 45, foi feito na 46")

    def test_sem_prazo_nao_atrasa_e_flag_respeita_o_alerta_do_manifesto(self):
        k = self.cards()["Publicar a nova versão do aplicativo móvel"]
        self.assertEqual((k["flag"], k["janela"]), ("sem-prazo", "sem-prazo"))
        p = self.board.planejar(k, "esta", "2026-11-23", HOJE)[1]
        self.board.apply_changes(self.c, "proj_s", [self.board.change_from_card(k, "a-fazer", None, None, p)])
        k2 = self.cards()["Publicar a nova versão do aplicativo móvel"]
        self.assertEqual(k2["flag"], "chegando", "o manifesto abre o alerta para 5 dias: 23/11 está a 5 dias de 18/11")
        self.assertFalse(k2["parado"], "com prazo, quem avisa é a flag")

    def test_planejar_define_prazo_padrao_e_tira_da_triagem(self):
        k = self.cards()["Revisar contrato com o fornecedor de pagamentos"]
        self.assertEqual(k["status"], "triagem" if k["idade_dias"] > 60 else k["status"])
        col, campos = self.board.planejar(dict(k, status="triagem", prazo=""), "proxima", None, HOJE)
        self.assertEqual(col, "a-fazer")
        self.assertEqual(campos, {"semana": "2026-W48", "prazo": "2026-11-29"}, "sem prazo: domingo da semana planejada")
        _, campos2 = self.board.planejar(dict(k, prazo="2026-12-01"), "proxima", None, HOJE)
        self.assertNotIn("prazo", campos2, "prazo que já existe não é sobrescrito")
        self.assertEqual(self.board.planejar(k, "backlog", None, HOJE)[1], {"semana": "backlog"})

    def test_ida_e_volta_no_quadro_md_com_semana_prazo_e_feito_em(self):
        k = self.cards()["Publicar a nova versão do aplicativo móvel"]
        self.board.apply_changes(self.c, "proj_s", [self.board.change_from_card(k, "a-fazer", None, None, {"semana": "2026-W48", "prazo": "2026-11-27", "feito-em": "2026-11-20"})])
        texto = open(self.q, encoding="utf-8").read()
        for linha in ("semana:: 2026-W48", "prazo:: 2026-11-27", "feito-em:: 2026-11-20"):
            self.assertIn(linha, texto)
        k2 = self.cards()["Publicar a nova versão do aplicativo móvel"]
        self.assertEqual((k2["semana"], k2["semana_ef"], k2["prazo"], k2["feito_em"]), ("2026-W48", "2026-W48", "2026-11-27", "2026-11-20"))
        self.assertTrue(k2["planejado"])

    def test_mover_para_feito_carimba_a_data_e_reabrir_limpa(self):
        k = self.cards()["Publicar a nova versão do aplicativo móvel"]
        self.assertEqual(self.board.campos_ao_mover(k, "feito", HOJE), {"feito-em": "2026-11-18"})
        self.assertEqual(self.board.campos_ao_mover(k, "fazendo", HOJE), {})
        self.assertEqual(self.board.campos_ao_mover(dict(k, status="feito"), "a-fazer", HOJE), {"feito-em": ""})

    def test_limpeza_fica_fora_do_calendario(self):
        k = self.cards()["Publicar a nova versão do aplicativo móvel"]
        self.board.apply_changes(self.c, "proj_s", [self.board.change_from_card(k, "feito", None, ["limpeza-2026-11", "ja-feito"], {})])
        k2 = self.cards()["Publicar a nova versão do aplicativo móvel"]
        self.assertTrue(k2["fora_calendario"])
        vis = [x for x in self.board.build(self.c, "proj_s", hoje=HOJE)]
        _, feitas = self.semana.da_semana(vis, "2026-W47")
        self.assertNotIn(k["id"], [x["id"] for x in feitas])

    def test_cli_semana_abre_na_ultima_semana_com_registro(self):
        buf = io.StringIO()
        ns = Namespace(board_cmd="semana", project="proj_s", semana=None, json=True, project_atual=None)
        with contextlib.redirect_stdout(buf):
            self.board.cmd(ns, self.c)
        d = json.loads(buf.getvalue())
        self.assertEqual(d["semana"], d["ultima_semana"])
        self.assertEqual(d["capacidade"], 2, "vem de quadro-capacidade no manifesto")
        self.assertIn("rotulo", d)

    def test_cli_revisao_exige_confirmacao_e_aplica_so_o_mecanico(self):
        k = self.cards()["Publicar a nova versão do aplicativo móvel"]
        # 46 é uma semana passada em relação a hoje real; prazo futuro => proposta mecânica para a semana do prazo
        self.board.apply_changes(self.c, "proj_s", [self.board.change_from_card(k, "a-fazer", None, None, {"semana": "2026-W46", "prazo": "2099-01-05"})])
        base = dict(board_cmd="revisao", project="proj_s", json=False, project_atual=None, aplicar=True, sim=False, dry_run=False, confirmo=False)
        with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
            self.board.cmd(Namespace(**base), self.c)
        with contextlib.redirect_stdout(io.StringIO()):
            self.board.cmd(Namespace(**{**base, "sim": True}), self.c)
        k2 = {x["titulo"]: x for x in self.board.build(self.c, "proj_s", ocultos=True, hoje=HOJE)}["Publicar a nova versão do aplicativo móvel"]
        self.assertEqual(k2["semana"], "2099-W02", "foi para a semana do prazo")

    def test_insights_e_hook_avisam_dos_prazos(self):
        from types import SimpleNamespace
        k = self.cards()["Publicar a nova versão do aplicativo móvel"]
        self.board.apply_changes(self.c, "proj_s", [self.board.change_from_card(k, "a-fazer", None, None, {"prazo": "2020-01-01"})])
        d = self.xmem.insights_data(self.c)
        self.assertGreaterEqual(d["prazos"]["atrasados"], 1)
        self.assertIn("proj_s", d["prazos"]["por_projeto"])
        self.assertTrue(any(r["flag"] == "atrasado" for r in d["prazos"]["lista"]))
        json.dumps(d)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.xmem.cmd_hook_context(SimpleNamespace(cwd=os.path.dirname(self.vault), max_chars=1500), self.c)
        self.assertIn("Prazos:", buf.getvalue())
        self.assertIn("atrasado", buf.getvalue())

    def test_cli_plan_e_prazo(self):
        k = self.cards()["Revisar contrato com o fornecedor de pagamentos"]
        with contextlib.redirect_stdout(io.StringIO()):
            self.board.cmd(Namespace(board_cmd="plan", project="proj_s", id=k["id"], semana="proxima", prazo=None, dry_run=False, confirmo=False), self.c)
        k2 = {x["titulo"]: x for x in self.board.build(self.c, "proj_s", ocultos=True)}["Revisar contrato com o fornecedor de pagamentos"]
        self.assertTrue(k2["planejado"])
        self.assertTrue(k2["prazo"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.board.cmd(Namespace(board_cmd="prazo", project="proj_s", id=k["id"], data=None, limpar=True, dry_run=False, confirmo=False), self.c)
        k3 = {x["titulo"]: x for x in self.board.build(self.c, "proj_s", ocultos=True)}["Revisar contrato com o fornecedor de pagamentos"]
        self.assertEqual(k3["prazo"], "")
        with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
            self.board.cmd(Namespace(board_cmd="plan", project="proj_s", id=k["id"], semana="semana-errada", prazo=None, dry_run=False, confirmo=False), self.c)


class InstaladorTest(unittest.TestCase):
    def test_todo_script_do_repositorio_esta_na_lista_do_instalador(self):
        """Regressão: o instalador esquecia o semana.py e a cópia instalada (a que a interface e o hook usam) quebrava no import."""
        import re
        texto = open(os.path.join(SCRIPTS, "install-tools.sh"), encoding="utf-8").read()
        lista = set(re.search(r"for f in ([^;]+); do", texto).group(1).split())
        esperados = {f for f in os.listdir(SCRIPTS) if f.endswith((".py", ".sh")) and f != "install-tools.sh"}
        self.assertEqual(esperados - lista, set(), "scripts que faltam no instalador")


class PaginasTest(unittest.TestCase):
    """As páginas do quadro e dos insights são HTML+JS autocontidos: sintaxe válida e elementos que a interface usa."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(HERE, "..", "gui"))
        for m in ("board_page", "insights_page"):
            sys.modules.pop(m, None)
        cls.bp = importlib.import_module("board_page")
        cls.ip = importlib.import_module("insights_page")

    def _js(self, html, subs):
        for k, v in subs.items():
            html = html.replace(k, v)
        import re
        return re.search(r"<script>(.*)</script>", html, re.S).group(1)

    def _node_check(self, js):
        import subprocess
        if not shutil.which("node"):
            self.skipTest("node indisponível")
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
            fh.write(js)
        try:
            r = subprocess.run(["node", "--check", fh.name], capture_output=True, text=True)
        finally:
            os.remove(fh.name)
        self.assertEqual(r.returncode, 0, r.stderr[:400])

    def test_pagina_do_quadro(self):
        js = self._js(self.bp.BOARD_HTML, {"{{THEME}}": "", "{{COLS}}": "[]", "{{HINT}}": "{}", "{{COLORS}}": "{}", "{{DATA}}": "{}"})
        self._node_check(js)
        for ident in ('id="vc"', 'id="va"', 'id="weeks"', 'id="sprint"', 'id="cal"', 'id="agenda"', 'id="fs"', 'id="fj"'):
            self.assertIn(ident, self.bp.BOARD_HTML)
        self.assertIn("op:'plan'", self.bp.BOARD_HTML)
        self.assertIn("view:'calendario'", self.bp.BOARD_HTML, "abre no calendário")
        self.assertIn("DATA.ultima_semana", self.bp.BOARD_HTML, "abre na última semana com registro")

    def test_pagina_de_insights(self):
        self._node_check(self._js(self.ip.INSIGHTS_HTML, {"{{THEME}}": "", "{{COLORS}}": "{}", "{{DATA}}": json.dumps(
            {"desde": "x", "dias_parado": 14, "atividade": [], "parados_por_projeto": {}, "total_parados": 0, "projetos_sem_devtrack": [], "contradicoes": [],
             "quadro": {"orfaos": [], "parados": []}, "prazos": {"atrasados": 1, "hoje": 0, "chegando": 0, "sem_prazo": 1, "por_projeto": {}, "lista": []}})}))


if __name__ == "__main__":
    unittest.main()
