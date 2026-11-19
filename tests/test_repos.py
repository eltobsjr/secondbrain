"""`repos:` do manifesto (P2-4): só caminho relativo dentro do projeto, aspas, aviso de ausente; reconcile por caminho completo e branch padrão."""
import importlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def git(repo, *a, env=None):
    return subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True, capture_output=True, text=True, env=env)


class ReposTest(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="repos-")
        os.environ["HOME"] = self.base
        os.environ["SECONDBRAIN_XMEM_DB"] = os.path.join(self.base, "x.db")
        sys.path.insert(0, SCRIPTS)
        for m in ("xmem", "_vault", "board", "pend", "reconcile"):
            sys.modules.pop(m, None)
        self.v = importlib.import_module("_vault")
        self.proj = os.path.join(self.base, "dev/proj")
        self.vault = self.proj + "/ProjSecondBrain"
        os.makedirs(self.proj + "/com espaco/repo")
        git(self.proj + "/com espaco/repo", "init", "-q")

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def manifesto(self, linhas):
        write(self.vault + "/_secondbrain.md", "---\nschema: 2\nrepos:\n" + "".join(f"  - {x}\n" for x in linhas) + "---\n")
        return {os.path.relpath(r["caminho"], self.proj): r for r in self.v.read_repos(self.vault)}

    def test_aspas_com_espaco_e_papel(self):
        r = self.manifesto(['"com espaco/repo" referencia'])
        self.assertTrue(r["com espaco/repo"]["valido"])
        self.assertEqual(r["com espaco/repo"]["papel"], "referencia")

    def test_caminho_que_sai_do_projeto_nao_vale(self):
        r = self.manifesto(["../fora ativo", "/etc ativo"])
        self.assertTrue(r and all(not x["valido"] and "fora da pasta do projeto" in x["aviso"] for x in r.values()), r)

    def test_ausente_vira_aviso_e_nao_some_calado(self):
        r = self.manifesto(["nao-existe ativo"])
        self.assertFalse(r["nao-existe"]["valido"])
        self.assertIn("sem .git", r["nao-existe"]["aviso"])

    def test_reconcile_olha_o_caminho_e_nao_so_o_nome(self):
        import reconcile
        repo = self.proj + "/com espaco/repo"
        for caminho in ("a/lib.ts", "b/lib.ts"):
            write(os.path.join(repo, caminho), "x\n")
        git(repo, "add", "a/lib.ts")
        env = dict(os.environ, GIT_AUTHOR_DATE="2026-11-10T12:00:00", GIT_COMMITTER_DATE="2026-11-10T12:00:00")
        git(repo, "commit", "-q", "-m", "mexe so em a", env=env)
        cs = reconcile.listar_commits(repo, "2026-01-01")
        self.assertEqual(len(cs), 1)
        self.assertIn("a/lib.ts", cs[0]["caminhos"])
        self.assertNotIn("b/lib.ts", cs[0]["caminhos"])
        self.assertEqual(reconcile.ref_padrao(repo), "HEAD")


if __name__ == "__main__":
    unittest.main()
