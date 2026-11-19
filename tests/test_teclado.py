"""Interface do quadro sem mouse e sem falha silenciosa (P1-4): contraste, esquema da mensagem e pontos do JS.

O que depende de janela GTK ou de navegador fica fora; aqui entra o que dá para provar sem eles.
"""
import importlib
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gui"))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))


def _lum(h):
    h = h.lstrip("#")
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4   # noqa: E731
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contraste(a, b):
    x, y = sorted((_lum(a), _lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


class ContrasteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.pop("theme", None)
        cls.theme = importlib.import_module("theme")

    def test_selos_do_quadro_tem_4_5_para_1_nos_dois_temas(self):
        for nome, t in (("claro", self.theme.LIGHT), ("escuro", self.theme.DARK)):
            pares = {
                "atrasado (texto sobre erro)": (t["on_accent"], t["red"]),
                "hoje, chegando, P1 e semana cheia (texto sobre aviso forte)": (t["on_accent"], t["warn_s"]),
                "no prazo (texto sobre ok forte)": (t["on_accent"], t["ok_s"]),
                "aviso em cartão (texto sobre o cinza do cartão)": (t["warn_s"], t["s0"]),
                "metadados do cartão (texto sobre o cinza do cartão)": (t["text"], t["s0"]),
                "selo comum (texto de apoio sobre o painel)": (t["sub1"], t["mantle"]),
            }
            for rotulo, (fg, bg) in pares.items():
                self.assertGreaterEqual(contraste(fg, bg), 4.5, f"tema {nome}: {rotulo} = {contraste(fg, bg):.2f}")


class MensagemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for m in ("xmem", "_vault", "board"):
            sys.modules.pop(m, None)
        os.environ["HOME"] = tempfile.mkdtemp(prefix="teclado-")
        os.environ["SECONDBRAIN_XMEM_DB"] = os.path.join(os.environ["HOME"], "x.db")
        cls.board = importlib.import_module("board")

    def test_mensagens_certas_passam(self):
        v = self.board.validar_msg
        self.assertIsNone(v({"op": "move", "project": "p", "id": "cabc", "col": "fazendo"}))
        self.assertIsNone(v({"op": "move", "project": "p", "id": "cabc", "col": "feito", "order": ["a", "b"]}))
        self.assertIsNone(v({"op": "prazo", "project": "p", "id": "cabc", "prazo": ""}), "prazo vazio limpa o prazo")
        self.assertIsNone(v({"op": "add", "project": "p", "titulo": "Fazer algo", "col": "a-fazer", "prioridade": None}))
        self.assertIsNone(v({"op": "project", "name": "p"}))
        self.assertIsNone(v({"op": "discard-old", "project": "p", "days": 60, "n": 3}))

    def test_mensagem_malformada_vira_texto_e_nao_excecao(self):
        v = self.board.validar_msg
        for ruim, trecho in (([], "objeto"), ({"op": "apagar-tudo"}, "desconhecida"), ({"op": "move", "project": "p", "id": "x"}, "'col'"),
                             ({"op": "move", "project": "p", "id": "x", "col": "nao-existe"}, "coluna"), ({"op": "move", "id": "x", "col": "feito"}, "'project'"),
                             ({"op": "move", "project": "p", "id": "x", "col": "feito", "order": "abc"}, "ordem"),
                             ({"op": "add", "project": "p", "titulo": "  ", "col": "a-fazer"}, "'titulo'"),
                             ({"op": "discard-old", "project": "p", "days": "muitos"}, "número")):
            msg = v(ruim)
            self.assertIsInstance(msg, str, ruim)
            self.assertIn(trecho, msg)


class PaginaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.pop("board_page", None)
        cls.html = importlib.import_module("board_page").BOARD_HTML

    def test_cartao_operavel_por_teclado(self):
        for trecho in ("c.tabIndex=0", "role','button'", "ev.key==='Enter'", ":focus-visible", "function openCard"):
            self.assertIn(trecho, self.html)

    def test_erro_nao_some_sozinho_e_esc_fecha(self):
        self.assertIn("if(!erro)toast.h=setTimeout", self.html, "só o aviso comum tem prazo para sumir")
        self.assertIn("if(hideToast())return", self.html)

    def test_esc_dentro_de_campo_nao_descarta_o_formulario(self):
        self.assertIn("if(typing){ev.target.blur();return}", self.html)
        self.assertIn("state.draft", self.html, "o que foi digitado sobrevive ao render")

    def test_render_guarda_foco_e_rolagem(self):
        self.assertIn("function render(){const s=snap();render0();restore(s)}", self.html)


if __name__ == "__main__":
    unittest.main()
