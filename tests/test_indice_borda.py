"""Bordas do índice e do hook (P1-2): link quebrado, vaults de mesmo nome, migração de esquema, permissões e hook sem espera."""
import importlib
import io
import os
import shutil
import sqlite3
import stat
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")
MANIFESTO = "---\nschema: 2\nsensibilidade: normal\nbackup: true\nmodulos: [devtrack]\npapeis:\n  devtrack: devtrack/\n---\n\n# m\n"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class IndiceBordaTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="borda-home-")
        os.environ["HOME"] = self.home
        os.environ["SECONDBRAIN_XMEM_DB"] = os.path.join(self.home, ".local/share/secondbrain/xmem.db")
        sys.path.insert(0, SCRIPTS)
        for m in ("xmem", "_vault", "board"):
            sys.modules.pop(m, None)
        self.xmem = importlib.import_module("xmem")

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def vault(self, *partes, nota="Tarefa de exemplo para o índice"):
        v = os.path.join(self.home, "dev", *partes)
        write(v + "/_secondbrain.md", MANIFESTO)
        write(v + "/devtrack/2026-11-01 - S.md", f"---\ntipo: devtrack\ndata: 2026-11-01\n---\n\n# S\n\n- [ ] {nota}\n")
        return v

    def test_link_quebrado_e_link_para_fora_nao_derrubam_o_indice(self):
        v = self.vault("proj_a", "ASecondBrain")
        os.symlink(os.path.join(self.home, "nao-existe.md"), v + "/devtrack/quebrado.md")
        write(os.path.join(self.home, "segredo-fora.md"), "# Fora\n\nTEXTO-DE-FORA\n")
        os.symlink(os.path.join(self.home, "segredo-fora.md"), v + "/devtrack/para-fora.md")
        c = self.xmem.index(quiet=True)
        notas = [r["rel"] for r in c.execute("select rel from notes")]
        self.assertEqual(notas, ["devtrack/2026-11-01 - S.md"])
        self.assertEqual(c.execute("select count(*) from chunks where text like '%TEXTO-DE-FORA%'").fetchone()[0], 0)
        c.close()

    def test_arquivo_que_some_durante_a_indexacao_e_pulado(self):
        self.vault("proj_a", "ASecondBrain")
        real = os.stat
        alvo = "2026-11-01 - S.md"

        def falha(p, *a, **k):
            if str(p).endswith(alvo):
                raise PermissionError("sem acesso")
            return real(p, *a, **k)

        os.stat = falha
        try:
            c = self.xmem.index(quiet=True)
        finally:
            os.stat = real
        self.assertEqual(c.execute("select count(*) from notes").fetchone()[0], 0)
        c.close()

    def test_dois_vaults_na_mesma_pasta_mae_viram_dois_projetos(self):
        self.vault("a", "loja", "LojaSecondBrain", nota="Item do primeiro vault")
        self.vault("b", "loja", "LojaSecondBrain", nota="Item do segundo vault")
        c = self.xmem.index(quiet=True)
        projetos = sorted(r[0] for r in c.execute("select distinct project from notes"))
        self.assertEqual(len(projetos), 2, projetos)
        self.assertEqual(projetos[0], "loja")
        self.assertTrue(projetos[1].startswith("loja@"), projetos)
        self.assertEqual(len(self.xmem.COLISOES), 1)
        c.close()

    def test_troca_de_esquema_guarda_o_banco_antigo(self):
        self.vault("proj_a", "ASecondBrain")
        c = self.xmem.index(quiet=True)
        c.execute("update meta set v='0' where k='schema'")
        c.close()
        c = self.xmem.connect()
        self.assertTrue(os.path.isfile(self.xmem.DB_PATH + ".bak"), "o banco antigo ficou de reserva")
        self.assertEqual(c.execute("select count(*) from notes").fetchone()[0], 0, "o novo começa vazio e será reindexado")
        c.close()

    def test_banco_e_pasta_so_para_o_dono(self):
        self.vault("proj_a", "ASecondBrain")
        c = self.xmem.index(quiet=True)
        c.close()
        self.assertEqual(stat.S_IMODE(os.stat(self.xmem.DB_PATH).st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(os.path.dirname(self.xmem.DB_PATH)).st_mode), 0o700)

    def test_hook_nao_espera_por_um_index_em_andamento(self):
        v = self.vault("proj_a", "ASecondBrain")
        c = self.xmem.index(quiet=True)
        c.close()
        trava = sqlite3.connect(self.xmem.DB_PATH, isolation_level=None)
        trava.execute("begin immediate")                       # um index segurando a escrita
        trava.execute("insert or replace into meta values('x','1')")
        buf = io.StringIO()
        t0 = time.monotonic()
        h = self.xmem.connect(readonly=True)
        self.assertIsNotNone(h)
        with redirect_stdout(buf):
            self.xmem.cmd_hook_context(SimpleNamespace(cwd=os.path.dirname(v), max_chars=1500), h)
        espera = time.monotonic() - t0
        trava.execute("rollback")
        trava.close()
        h.close()
        self.assertLess(espera, 1.0, f"o hook levou {espera:.2f}s com o banco ocupado")
        self.assertIn("SecondBrain", buf.getvalue())

    def test_hook_sem_banco_ou_com_esquema_velho_nao_quebra(self):
        self.assertIsNone(self.xmem.connect(readonly=True), "sem banco: nada a mostrar")
        self.vault("proj_a", "ASecondBrain")
        c = self.xmem.index(quiet=True)
        c.execute("update meta set v='0' where k='schema'")
        c.close()
        self.assertIsNone(self.xmem.connect(readonly=True), "esquema de outra versão: o hook não migra")


if __name__ == "__main__":
    unittest.main()


class UsoTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="uso-home-")
        os.environ["HOME"] = self.home
        os.environ["SECONDBRAIN_XMEM_DB"] = os.path.join(self.home, "x.db")
        os.environ["SECONDBRAIN_USO"] = os.path.join(self.home, "uso.jsonl")
        os.environ.pop("SECONDBRAIN_SEM_USO", None)
        sys.path.insert(0, SCRIPTS)
        for m in ("xmem", "_vault"):
            sys.modules.pop(m, None)
        self.xmem = importlib.import_module("xmem")

    def tearDown(self):
        os.environ.pop("SECONDBRAIN_USO", None)
        shutil.rmtree(self.home, ignore_errors=True)

    def test_registra_ids_e_nunca_a_consulta(self):
        import json
        write(os.path.join(self.home, "dev/p/PSecondBrain/_secondbrain.md"), MANIFESTO)
        write(os.path.join(self.home, "dev/p/PSecondBrain/devtrack/2026-11-01 - S.md"), "---\ntipo: devtrack\ndata: 2026-11-01\n---\n\n# S\n\nConfigurar rotação dos logs do servidor\n")
        c = self.xmem.index(quiet=True)
        a = SimpleNamespace(query="CONSULTA-SECRETA rotação logs", limit=5, project=None, project_atual="p", exclude_project=None, kind=None, tipo=None,
                            since=None, all=False, json=True, full=False, todos_projetos=False)
        with redirect_stdout(io.StringIO()):
            self.xmem.cmd_search(a, c)
        txt = open(self.xmem.USO_PATH, encoding="utf-8").read()
        self.assertNotIn("CONSULTA-SECRETA", txt)
        r = json.loads(txt.splitlines()[0])
        self.assertEqual((r["cmd"], r["proj"]), ("search", "p"))
        self.assertTrue(r["ids"] and all(isinstance(i, int) for i in r["ids"]))
        self.assertEqual(oct(os.stat(self.xmem.USO_PATH).st_mode & 0o777), "0o600")
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.xmem.cmd_uso(SimpleNamespace(), c)
        self.assertIn("1 consultas registradas", buf.getvalue())
        c.close()

    def test_pode_ser_desligado(self):
        os.environ["SECONDBRAIN_SEM_USO"] = "1"
        try:
            self.xmem.registrar_uso("search", "p", [1])
        finally:
            os.environ.pop("SECONDBRAIN_SEM_USO")
        self.assertFalse(os.path.exists(self.xmem.USO_PATH))
