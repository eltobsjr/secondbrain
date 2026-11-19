"""Integridade do quadro.md (P1-1): gravações concorrentes, conteúdo desconhecido, backup e modo do arquivo."""
import importlib
import os
import shutil
import stat
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def manual(i, col="a-fazer"):
    return {"id": f"m{i:06d}", "titulo": f"Decisão manual número {i}", "col": col, "prioridade": None, "etiquetas": [], "campos": {}}


class QuadroIntegridadeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="quadro-home-")
        os.environ["HOME"] = cls.home
        os.environ["SECONDBRAIN_XMEM_DB"] = os.path.join(cls.home, "xmem.db")
        sys.path.insert(0, SCRIPTS)
        for m in ("xmem", "_vault", "board"):
            sys.modules.pop(m, None)
        cls.xmem = importlib.import_module("xmem")
        cls.board = importlib.import_module("board")
        cls.vault = os.path.join(cls.home, "dev/proj_q/ProjQSecondBrain")
        write(cls.vault + "/_secondbrain.md", "---\nschema: 2\nsensibilidade: normal\nbackup: true\nmodulos: [devtrack]\npapeis:\n  devtrack: devtrack/\n---\n\n# m\n")
        write(cls.vault + "/devtrack/2026-11-01 - S.md", "---\ntipo: devtrack\ndata: 2026-11-01\n---\n\n# S\n\n- [ ] Tarefa de exemplo para o quadro\n")
        cls.c = cls.xmem.index(quiet=True)
        cls.q = cls.vault + "/quadro.md"

    @classmethod
    def tearDownClass(cls):
        cls.c.close()
        shutil.rmtree(cls.home, ignore_errors=True)

    def setUp(self):
        if os.path.exists(self.q):
            os.remove(self.q)

    def ids(self):
        return {k["id"] for k in self.board.load_overrides(self.vault)}

    def test_duas_gravacoes_ao_mesmo_tempo_nao_perdem_decisao(self):
        erros = []

        def gravar(i):
            try:
                c = self.xmem.connect()
                self.board.apply_changes(c, "proj_q", [manual(i)], propagar_notas=False)
                c.close()
            except BaseException as e:      # noqa: BLE001
                erros.append(e)

        ts = [threading.Thread(target=gravar, args=(i,)) for i in range(1, 9)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        self.assertEqual(erros, [])
        self.assertEqual(self.ids(), {f"m{i:06d}" for i in range(1, 9)}, "as 8 decisões sobrevivem")

    def test_secao_e_texto_desconhecidos_sobrevivem_a_reescrita(self):
        write(self.q, "---\nkanban-plugin: board\nschema: 1\nminha-chave: valor meu\n---\n\n> Quadro de proj_q. Guarda só decisões.\n\n"
                      "Texto antes das colunas\n\n## A fazer\n\n- [ ] Já existia ^mabc123\n\nNota solta dentro da coluna\n\n"
                      "## Minhas ideias\n\n- ideia um\n- ideia dois\n")
        self.board.apply_changes(self.c, "proj_q", [manual(9)], propagar_notas=False)
        txt = open(self.q, encoding="utf-8").read()
        for trecho in ("minha-chave: valor meu", "Texto antes das colunas", "Nota solta dentro da coluna", "## Minhas ideias", "- ideia um", "- ideia dois"):
            self.assertIn(trecho, txt, trecho)
        self.assertIn("mabc123", self.ids())
        self.board.apply_changes(self.c, "proj_q", [manual(10)], propagar_notas=False)
        self.assertEqual(open(self.q, encoding="utf-8").read().count("## Minhas ideias"), 1, "não duplica a cada gravação")

    def test_backup_no_mesmo_segundo_nao_sobrescreve_e_rotaciona(self):
        self.board.apply_changes(self.c, "proj_q", [manual(1)], propagar_notas=False)
        bdir = os.path.join(self.board.BACKUP_DIR, "proj_q")
        antes = len([f for f in os.listdir(bdir) if f.startswith("quadro-")])
        for i in range(2, 7):
            self.board.apply_changes(self.c, "proj_q", [manual(i)], propagar_notas=False)
        nomes = [f for f in os.listdir(bdir) if f.startswith("quadro-")]
        self.assertEqual(len(nomes), antes + 5, "cada gravação deixa a sua cópia, mesmo dentro do mesmo segundo")
        self.assertEqual(stat.S_IMODE(os.stat(os.path.join(bdir, nomes[0])).st_mode), 0o600)
        old = self.board.BACKUP_MANTER
        try:
            self.board.BACKUP_MANTER = 3
            self.board.apply_changes(self.c, "proj_q", [manual(7)], propagar_notas=False)
            self.assertEqual(len([f for f in os.listdir(bdir) if f.startswith("quadro-")]), 3, "rotação mantém só as mais novas")
        finally:
            self.board.BACKUP_MANTER = old

    def test_modo_do_arquivo_e_preservado(self):
        write(self.q, "---\nkanban-plugin: board\n---\n\n## A fazer\n\n")
        os.chmod(self.q, 0o644)
        self.board.apply_changes(self.c, "proj_q", [manual(1)], propagar_notas=False)
        self.assertEqual(stat.S_IMODE(os.stat(self.q).st_mode), 0o644)

    def test_arquivo_que_muda_durante_a_leitura_nao_e_sobrescrito(self):
        write(self.q, "---\nkanban-plugin: board\n---\n\n## A fazer\n\n- [ ] Original ^mabc123\n")
        real = self.board.parse_quadro

        def intruso(texto):
            r = real(texto)
            write(self.q, "---\nkanban-plugin: board\n---\n\n## A fazer\n\n- [ ] Original ^mabc123\n- [ ] Escrito por outro programa ^mzzz999\n")
            return r

        self.board.parse_quadro = intruso
        try:
            with self.assertRaises(SystemExit):
                self.board.apply_changes(self.c, "proj_q", [manual(1)], propagar_notas=False)
        finally:
            self.board.parse_quadro = real
        self.assertIn("mzzz999", open(self.q, encoding="utf-8").read(), "o que o outro programa escreveu continua lá")


if __name__ == "__main__":
    unittest.main()
