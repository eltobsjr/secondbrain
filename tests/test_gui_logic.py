"""Testes da lógica da interface que não precisam de tela: segurança do leitor e validade do JS do grafo."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gui"))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))


class GuiLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import secondbrain_gui as g
        except Exception as e:  # sem GTK/WebKit neste ambiente
            raise unittest.SkipTest(f"GTK/WebKit indisponível: {e}")
        cls.g = g

    def test_html_cru_da_nota_e_escapado(self):
        evil = "# T\n\n<script>alert(1)</script>\n\n<img src=http://evil/x.png onerror=alert(1)>\n\n[[Outra]]"
        out = self.g.md_to_html(evil, {"outra": 7})
        self.assertNotIn("<script", out)
        self.assertNotIn("<img", out)
        self.assertIn("sb://note/7", out, "wikilink resolvido para o id da nota")

    def test_wikilink_inexistente_nao_vira_link(self):
        out = self.g.md_to_html("ver [[Nao Existe]]", {})
        self.assertNotIn("sb://note/", out)

    def test_reader_html_mostra_sensivel_e_inativa_sem_emoji(self):
        d = {"note": {"title": "<b>x</b>", "project": "p", "tipo": "decisao", "kind": "decisao", "data": "2026-01-01", "status": "substituída",
                      "sens": "alta", "inactive": 1, "path": "/a/b.md"},
             "body": "texto", "out": [], "in": [], "lineage": []}
        h = self.g.reader_html(d, True, {})
        self.assertIn("Sensível", h)
        self.assertIn("Inativa", h)
        self.assertNotIn("🔒", h, "o sinal de sensibilidade é texto, não emoji")
        self.assertNotIn("<b>x</b>", h, "título é escapado")

    def test_reader_nao_repete_o_titulo_do_corpo(self):
        d = {"note": {"title": "Minha nota", "project": "p", "tipo": "nota", "kind": "nota", "data": "", "status": "",
                      "sens": "normal", "inactive": 0, "path": "/a/b.md"},
             "body": "# Minha nota\n\ntexto", "out": [], "in": [], "lineage": []}
        h = self.g.reader_html(d, False, {})
        self.assertEqual(h.count("<h1>"), 1, "o título aparece uma vez só")

    def test_tokens_cobrem_claro_e_escuro(self):
        import theme
        self.assertEqual(set(theme.DARK), set(theme.LIGHT))
        self.assertIn("--base", theme.css_vars(True))
        self.assertIn("sb-win", theme.gtk_css(False))

    def test_datas_e_tempos(self):
        self.assertEqual(self.g.fmt_date("2026-11-17"), "17 nov 2026")
        self.assertEqual(self.g.fmt_date("sem data"), "sem data")
        self.assertEqual(self.g.ago(30), "agora")
        self.assertEqual(self.g.ago(300), "há 5 min")

    def test_js_do_quadro_e_valido(self):
        node = shutil.which("node") or shutil.which("nodejs")
        if not node:
            self.skipTest("node ausente")
        import board
        import board_page
        html_ = (board_page.BOARD_HTML.replace("{{THEME}}", self.g.graph_theme()).replace("{{COLS}}", json.dumps(board.COLUMNS))
                 .replace("{{HINT}}", json.dumps(board_page.HINTS)).replace("{{COLORS}}", "{}")
                 .replace("{{DATA}}", '{"project":null,"resumo":{},"cartoes":[],"triagem_dias":60}'))
        js = html_.split("<script>")[1].split("</script>")[0]
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(js)
        r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
        os.unlink(f.name)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_politica_de_navegacao_libera_as_tres_paginas(self):
        import inspect
        src = inspect.getsource(self.g.Win.on_policy)
        for page in ("sb://reader", "sb://graph", "sb://board"):
            self.assertIn(page, src, f"{page} precisa ser permitido, senão a página fica em branco")

    def test_grafo_tem_foco_em_projeto_e_animacao_continua(self):
        h = self.g.GRAPH_HTML
        for marca in ("function focusProject", "function exitFocus", "function hitProject", "id=\"crumb\"", "if(tween)schedule()"):
            self.assertIn(marca, h, marca)
        self.assertIn("sb.cam3.", h, "chave da câmera nova: não herda a câmera salva do layout antigo")

    def test_js_do_grafo_e_valido(self):
        node = shutil.which("node") or shutil.which("nodejs")
        if not node:
            self.skipTest("node ausente")
        data = {"nodes": [{"id": 1, "project": "a", "title": "t", "tipo": "x", "kind": "x", "data": "", "sens": "normal", "inactive": 0}], "edges": []}
        html_ = (self.g.GRAPH_HTML.replace("{{DATA}}", json.dumps(data))
                 .replace("{{COLORS}}", '{"a":"#fff"}').replace("{{SIG}}", "teste")
                 .replace("{{PROJECT}}", "null").replace("{{THEME}}", self.g.graph_theme()))
        js = html_.split("<script>")[1].split("</script>")[0]
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(js)
        r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
        os.unlink(f.name)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
