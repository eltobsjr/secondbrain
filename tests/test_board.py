"""Testes do quadro kanban (scripts/board.py) com mini-vaults de fixture: HOME e banco isolados, nada dos seus vaults é tocado."""
import importlib
import os
import shutil
import sys
import tempfile
import unittest
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def manifest(sens="normal", extra=""):
    return (f"---\nschema: 2\nsensibilidade: {sens}\n{extra}backup: true\nmodulos: [devtrack]\npapeis:\n  devtrack: devtrack/\n---\n\n# m\n")


class BoardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="board-home-")
        os.environ["HOME"] = cls.home
        os.environ["SECONDBRAIN_XMEM_DB"] = os.path.join(cls.home, "xmem.db")
        sys.path.insert(0, SCRIPTS)
        for m in ("xmem", "_vault", "board"):
            sys.modules.pop(m, None)
        cls.xmem = importlib.import_module("xmem")
        cls.board = importlib.import_module("board")
        cls.a = os.path.join(cls.home, "dev/proj_a/ProjASecondBrain")
        cls.b = os.path.join(cls.home, "dev/proj_b/ProjBSecondBrain")
        cls.s = os.path.join(cls.home, "dev/proj_s/ProjSSecondBrain")
        write(cls.a + "/_secondbrain.md", manifest())
        write(cls.b + "/_secondbrain.md", manifest(extra="quadro: false\n"))
        write(cls.s + "/_secondbrain.md", manifest(sens="alta"))
        cls.old = (date.today() - timedelta(days=120)).isoformat()
        cls.new = (date.today() - timedelta(days=3)).isoformat()
        for root in (cls.a, cls.b, cls.s):
            write(root + f"/devtrack/{cls.old} - Antigo.md",
                  f"---\ntipo: devtrack\ndata: {cls.old}\n---\n\n# Antigo\n\n- [ ] Configurar rotação de logs\n- [ ] Revisar permissões do bucket\n- [ ] Item que será concluído\n")
            write(root + f"/devtrack/{cls.new} - Novo.md",
                  f"---\ntipo: devtrack\ndata: {cls.new}\n---\n\n# Novo\n\n- [ ] Publicar versão nova do serviço\n- [x] Item que será concluído\n")
        cls.c = cls.xmem.index(quiet=True)

    @classmethod
    def tearDownClass(cls):
        cls.c.close()
        shutil.rmtree(cls.home, ignore_errors=True)

    def cards(self, project="proj_a"):
        # ocultos=True: estes testes verificam a mecânica das colunas, não a visibilidade (ver test_pendencias_ocultas_*)
        return {k["titulo"]: k for k in self.board.build(self.c, project, ocultos=True)}

    def test_colunas_iniciais_por_idade_e_checkbox(self):
        k = self.cards()
        self.assertEqual(k["Configurar rotação de logs"]["status"], "triagem", "aberto há mais de 60 dias nasce em Triagem")
        self.assertEqual(k["Publicar versão nova do serviço"]["status"], "a-fazer")
        self.assertEqual(k["Item que será concluído"]["status"], "feito", "a ocorrência mais recente está marcada")
        self.assertEqual(k["Configurar rotação de logs"]["modo"], "derivado")
        self.assertTrue(k["Configurar rotação de logs"]["parado"])

    def test_id_estavel_entre_execucoes(self):
        a = self.cards()["Configurar rotação de logs"]["id"]
        b = self.cards()["Configurar rotação de logs"]["id"]
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("c") and len(a) == 7)

    def test_mover_grava_quadro_md_com_backup_e_nao_toca_a_origem(self):
        orig = os.path.join(self.a, f"devtrack/{self.old} - Antigo.md")
        antes = open(orig, encoding="utf-8").read()
        k = self.cards()["Revisar permissões do bucket"]
        ch = [self.board.change_from_card(k, "fazendo", "P1", ["seguranca"])]
        path, text = self.board.apply_changes(self.c, "proj_a", ch)
        self.assertTrue(path.endswith("quadro.md"))
        self.assertIn("## Fazendo", text)
        self.assertIn(f"^{k['id']}", text)
        self.assertIn("#P1", text)
        self.assertIn("origem:: [[devtrack/", text)
        self.assertEqual(open(orig, encoding="utf-8").read(), antes, "a nota de origem nunca é reescrita")
        # segunda gravação: cria backup do arquivo anterior, fora do vault
        self.board.apply_changes(self.c, "proj_a", [self.board.change_from_card(k, "revisao")])
        bdir = os.path.join(self.board.BACKUP_DIR, "proj_a")
        self.assertTrue(os.path.isdir(bdir) and os.listdir(bdir), "backup fora do vault")
        self.c = self.xmem.index(quiet=True)
        novo = self.cards()["Revisar permissões do bucket"]
        self.assertEqual(novo["status"], "revisao")
        self.assertEqual(novo["prioridade"], "P1")
        self.assertEqual(novo["etiquetas"], ["seguranca"])
        self.assertEqual(novo["status_origem"], "quadro")

    def test_quadro_md_nao_vira_fonte_de_pendencias(self):
        self.c = self.xmem.index(quiet=True)
        kinds = {r["kind"] for r in self.c.execute("select kind from notes where project='proj_a' and rel='quadro.md'")}
        self.assertEqual(kinds, {"quadro"})
        n = self.c.execute("select count(*) from todos t join notes n on n.id=t.note_id where n.rel='quadro.md'").fetchone()[0]
        self.assertEqual(n, 0)

    def test_concluir_na_origem_vence_o_quadro(self):
        k = self.cards()["Item que será concluído"]
        self.board.apply_changes(self.c, "proj_a", [self.board.change_from_card(k, "fazendo")])
        self.assertEqual(self.cards()["Item que será concluído"]["status"], "feito")

    def test_descartar_vira_coluna_e_nao_apaga_nada(self):
        k = self.cards()["Configurar rotação de logs"]
        self.board.apply_changes(self.c, "proj_a", [self.board.change_from_card(k, "descartado")])
        self.assertEqual(self.cards()["Configurar rotação de logs"]["status"], "descartado")
        self.assertTrue(os.path.isfile(os.path.join(self.a, f"devtrack/{self.old} - Antigo.md")))

    def test_cartao_manual_e_orfao(self):
        ch = [{"id": "m123456", "titulo": "Decidir política de backup", "col": "a-fazer", "prioridade": "P2", "etiquetas": [], "campos": {}}]
        self.board.apply_changes(self.c, "proj_a", ch)
        m = self.cards()["Decidir política de backup"]
        self.assertEqual(m["modo"], "manual")
        self.assertFalse(m["orfao"])
        o = [{"id": "cffffff", "titulo": "Texto que sumiu da origem", "col": "fazendo", "prioridade": None, "etiquetas": [],
              "campos": {"origem": "[[devtrack/nao-existe]]"}}]
        self.board.apply_changes(self.c, "proj_a", o)
        self.assertTrue(self.cards()["Texto que sumiu da origem"]["orfao"], "origem não encontrada vira órfão, nunca é apagado")

    def test_parse_e_render_ida_e_volta(self):
        txt = ("---\nkanban-plugin: board\n---\n\n## Fazendo\n\n- [ ] Tarefa com tags #P0 #grafo ^cabc123\n  origem:: [[devtrack/x]]\n  prazo:: 2026-12-01\n\n## Feito\n\n- [x] Pronto ^cdef456\n")
        cards = self.board.parse_quadro(txt)
        self.assertEqual([c["id"] for c in cards], ["cabc123", "cdef456"])
        self.assertEqual(cards[0]["prioridade"], "P0")
        self.assertEqual(cards[0]["etiquetas"], ["grafo"])
        self.assertEqual(cards[0]["campos"]["prazo"], "2026-12-01")
        self.assertEqual(cards[1]["col"], "feito")
        out = self.board.render("p", {"fazendo": [cards[0]], "feito": [cards[1]]})
        again = self.board.parse_quadro(out)
        self.assertEqual([c["id"] for c in again], ["cabc123", "cdef456"])
        self.assertEqual(again[0]["campos"]["origem"], "[[devtrack/x]]")

    def test_manifesto_quadro_false_bloqueia(self):
        k = self.cards("proj_b")["Configurar rotação de logs"]
        with self.assertRaises(SystemExit):
            self.board.apply_changes(self.c, "proj_b", [self.board.change_from_card(k, "fazendo")])
        self.assertFalse(os.path.exists(os.path.join(self.b, "quadro.md")))

    def test_vault_sensivel_exige_confirmacao(self):
        k = self.cards("proj_s")["Configurar rotação de logs"]
        with self.assertRaises(SystemExit):
            self.board.apply_changes(self.c, "proj_s", [self.board.change_from_card(k, "fazendo")])
        self.assertFalse(os.path.exists(os.path.join(self.s, "quadro.md")))
        self.board.apply_changes(self.c, "proj_s", [self.board.change_from_card(k, "fazendo")], confirmo=True)
        self.assertTrue(os.path.exists(os.path.join(self.s, "quadro.md")))

    def test_dry_run_nao_grava(self):
        k = self.cards("proj_a")["Publicar versão nova do serviço"]
        path, text = self.board.apply_changes(self.c, "proj_a", [self.board.change_from_card(k, "fazendo")], dry_run=True)
        self.assertIn("## Fazendo", text)
        antes = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        self.assertNotIn(f"^{k['id']}", antes)

    def test_privacidade_titulos_remove_origem(self):
        cards = self.board.build(self.c, None, current_project="proj_a")
        s = [k for k in cards if k["projeto"] == "proj_s"]
        self.assertTrue(s)
        self.assertTrue(all(k["origem"] == {} for k in s), "vault sensível vira só título para outro projeto")

    def test_reordenar_dentro_da_coluna_preserva_a_ordem(self):
        cs = self.cards()
        a, b = cs["Revisar permissões do bucket"], cs["Publicar versão nova do serviço"]
        ch = [self.board.change_from_card(b, "fazendo"), self.board.change_from_card(a, "fazendo")]
        self.board.apply_changes(self.c, "proj_a", ch, order={"fazendo": [b["id"], a["id"]]})
        ordem = [k["titulo"] for k in self.board.build(self.c, "proj_a") if k["status"] == "fazendo"]
        self.assertEqual(ordem[:2], ["Publicar versão nova do serviço", "Revisar permissões do bucket"])
        self.board.apply_changes(self.c, "proj_a", ch, order={"fazendo": [a["id"], b["id"]]})
        ordem = [k["titulo"] for k in self.board.build(self.c, "proj_a") if k["status"] == "fazendo"]
        self.assertEqual(ordem[:2], ["Revisar permissões do bucket", "Publicar versão nova do serviço"])

    def test_hook_de_sessao_mostra_o_que_esta_em_andamento(self):
        import io
        from contextlib import redirect_stdout
        from types import SimpleNamespace
        k = self.cards()["Publicar versão nova do serviço"]
        self.board.apply_changes(self.c, "proj_a", [self.board.change_from_card(k, "fazendo")])
        self.board.apply_changes(self.c, "proj_a", [self.board.change_from_card(self.cards()["Revisar permissões do bucket"], "bloqueado", None, None, {"bloqueado-por": "aprovação"})])
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.xmem.cmd_hook_context(SimpleNamespace(cwd=os.path.dirname(self.a), max_chars=1500), self.c)
        out = buf.getvalue()
        self.assertIn("Quadro:", out)
        self.assertIn("fazendo", out)
        self.assertIn("bloqueado", out)
        self.assertLessEqual(len(out), 1600, "o hook continua dentro do teto de caracteres")

    def test_insights_inclui_o_quadro_e_e_serializavel(self):
        import json
        d = self.xmem.insights_data(self.c)
        json.dumps(d)
        self.assertEqual(d["schema_version"], 1)
        self.assertIn("orfaos", d["quadro"])

    def test_graph_tarefas_ligam_o_cartao_a_nota_de_origem(self):
        k = self.cards()["Publicar versão nova do serviço"]
        self.board.apply_changes(self.c, "proj_a", [self.board.change_from_card(k, "fazendo")])
        t = [x for x in self.xmem.active_tasks(self.c, "proj_a") if x["id"] == k["id"]]
        self.assertTrue(t and t[0]["nota_id"], "a tarefa aponta para a nota onde nasceu")

    def test_resumo_conta_por_coluna(self):
        s = self.board.summary(self.board.build(self.c, "proj_a"))
        self.assertIn("proj_a", s)
        self.assertGreaterEqual(sum(s["proj_a"].values()), 4)


if __name__ == "__main__":
    unittest.main()
