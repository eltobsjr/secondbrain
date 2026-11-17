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

    def test_reader_html_mostra_cadeado_e_inativa(self):
        d = {"note": {"title": "<b>x</b>", "project": "p", "tipo": "decisao", "kind": "decisao", "data": "2026-01-01", "status": "substituída",
                      "sens": "alta", "inactive": 1, "path": "/a/b.md"},
             "body": "texto", "out": [], "in": [], "lineage": []}
        h = self.g.reader_html(d, True, {})
        self.assertIn("🔒", h)
        self.assertIn("inativa", h)
        self.assertNotIn("<b>x</b>", h, "título é escapado")

    def test_js_do_grafo_e_valido(self):
        node = shutil.which("node") or shutil.which("nodejs")
        if not node:
            self.skipTest("node ausente")
        data = {"nodes": [{"id": 1, "project": "a", "title": "t", "tipo": "x", "kind": "x", "data": "", "sens": "normal", "inactive": 0}], "edges": []}
        html_ = self.g.GRAPH_HTML.replace("{{DATA}}", json.dumps(data)).replace("{{COLORS}}", '{"a":"#fff"}').replace("{{DARK}}", "")
        js = html_.split("<script>")[1].split("</script>")[0]
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(js)
        r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
        os.unlink(f.name)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
