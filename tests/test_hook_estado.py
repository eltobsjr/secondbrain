"""Hook de sessão e ESTADO.md (P0-6): rascunho não vira fato, caminho fica dentro do vault, aviso de estado defasado.

Mini-vault e repositório git temporários, HOME e banco isolados.
"""
import importlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")
MANIFESTO = "---\nschema: 2\nsensibilidade: normal\nbackup: true\nmodulos: [devtrack]\npapeis:\n  devtrack: devtrack/\nrepos:\n  - codigo ativo\n---\n\n# m\n"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def dia(n):
    return (date.today() - timedelta(days=n)).isoformat()


def commit(repo, msg, n):
    env = dict(os.environ, GIT_AUTHOR_DATE=f"{dia(n)}T12:00:00", GIT_COMMITTER_DATE=f"{dia(n)}T12:00:00")
    write(os.path.join(repo, f"f{msg}.txt"), msg)
    for args in (["add", "-A"], ["commit", "-q", "-m", msg]):
        subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", *args], check=True, capture_output=True, env=env)


class HookEstadoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="hook-home-")
        os.environ["HOME"] = cls.home
        os.environ["SECONDBRAIN_XMEM_DB"] = os.path.join(cls.home, "xmem.db")
        sys.path.insert(0, SCRIPTS)
        for m in ("xmem", "_vault"):
            sys.modules.pop(m, None)
        cls.xmem = importlib.import_module("xmem")
        cls.proj = os.path.join(cls.home, "dev/proj_h")
        cls.vault = cls.proj + "/ProjHSecondBrain"
        write(cls.vault + "/_secondbrain.md", MANIFESTO)
        write(cls.vault + f"/devtrack/{dia(10)} - Sessao.md", f"---\ntipo: devtrack\ndata: {dia(10)}\n---\n\n# Sessao\n\nTrabalho feito.\n")
        os.makedirs(cls.proj + "/codigo")
        subprocess.run(["git", "-C", cls.proj + "/codigo", "init", "-q"], check=True)
        cls.c = cls.xmem.index(quiet=True)
        cls.estado = cls.vault + "/ESTADO.md"

    @classmethod
    def tearDownClass(cls):
        cls.c.close()
        shutil.rmtree(cls.home, ignore_errors=True)

    def hook(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.xmem.cmd_hook_context(SimpleNamespace(cwd=self.proj, max_chars=3000), self.c)
        return buf.getvalue()

    def escrever_estado(self, fm, corpo="# Estado\n\n## Agora\nFase de testes em andamento.\n"):
        if os.path.lexists(self.estado):
            os.remove(self.estado)
        write(self.estado, f"---\ntipo: estado\n{fm}---\n\n{corpo}")

    def test_estado_normal_entra_no_contexto(self):
        self.escrever_estado(f"atualizado: {dia(1)}\n")
        self.assertIn("Fase de testes em andamento", self.hook())

    def test_rascunho_nao_entra_como_fato(self):
        self.escrever_estado(f'atualizado: {dia(1)}\nultimo-devtrack: "Sessao"\norigem: rascunho gerado na migração a partir do último devtrack (o /devtrack reescreve)\n')
        out = self.hook()
        self.assertNotIn("Fase de testes em andamento", out, "o corpo do rascunho não é injetado")
        self.assertIn("rascunho", out)
        self.assertIn("Sessao", out, "aponta o último devtrack")

    def test_estado_fora_do_vault_nao_e_lido(self):
        fora = os.path.join(self.home, "fora.md")
        write(fora, "---\ntipo: estado\n---\n\nCONTEUDO-DE-FORA\n")
        if os.path.lexists(self.estado):
            os.remove(self.estado)
        os.symlink(fora, self.estado)
        self.assertNotIn("CONTEUDO-DE-FORA", self.hook())
        os.remove(self.estado)

    def test_dentro_do_vault(self):
        self.assertTrue(self.xmem.dentro_do_vault(self.vault, "ESTADO.md").startswith(os.path.realpath(self.vault)))
        self.assertIsNone(self.xmem.dentro_do_vault(self.vault, "../fora.md"))
        self.assertIsNone(self.xmem.dentro_do_vault(self.vault, "/etc/passwd"))

    def test_avisa_commits_depois_do_estado(self):
        repo = self.proj + "/codigo"
        self.escrever_estado(f"atualizado: {dia(6)}\n")
        self.assertNotIn("commits depois do ESTADO", self.hook(), "sem commits novos, sem aviso")
        for i in range(3):
            commit(repo, f"novo{i}", 2)
        commit(repo, "antigo", 8)                      # antes do ESTADO: não conta
        out = self.hook()
        self.assertIn("3 commits depois do ESTADO.md", out)
        self.escrever_estado(f"atualizado: {dia(1)}\n")
        self.assertNotIn("commits depois do ESTADO", self.hook(), "estado mais novo que os commits")

    def test_check_vault_falha_com_rascunho_antigo(self):
        import check_vault
        self.escrever_estado(f"atualizado: {dia(10)}\norigem: rascunho gerado na migração\n")
        self.assertEqual(check_vault.estado_rascunho_antigo(self.vault), 10)
        self.escrever_estado(f"atualizado: {dia(3)}\norigem: rascunho gerado na migração\n")
        self.assertIsNone(check_vault.estado_rascunho_antigo(self.vault), "rascunho novo ainda dentro do prazo")
        self.escrever_estado(f"atualizado: {dia(30)}\n")
        self.assertIsNone(check_vault.estado_rascunho_antigo(self.vault), "estado antigo que não é rascunho não entra aqui")
        self.escrever_estado(f"atualizado: {dia(10)}\norigem: rascunho gerado na migração\n")
        r = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "check_vault.py"), self.vault], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("rascunho de migração há 10 dias", r.stdout)


if __name__ == "__main__":
    unittest.main()
