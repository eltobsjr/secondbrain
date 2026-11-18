"""Testes da guarda de publicação (scripts/guard_publico.py): nada dos seus projetos vai para o GitHub.

Tudo em HOME, banco e repositório git temporários. Os nomes de projeto usados aqui são inventados.
"""
import importlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")


def git(repo, *args, ok=True):
    r = subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@users.noreply.github.com", *args],
                       capture_output=True, text=True)
    if ok and r.returncode != 0:
        raise AssertionError(r.stderr + r.stdout)
    return r


class GuardaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="guard-home-")
        cls.salvo = {k: os.environ.get(k) for k in ("HOME", "SECONDBRAIN_XMEM_DB")}
        os.environ["HOME"] = cls.home
        os.environ["SECONDBRAIN_XMEM_DB"] = os.path.join(cls.home, "x.db")
        con = sqlite3.connect(os.environ["SECONDBRAIN_XMEM_DB"])
        con.execute("create table notes(project text)")
        for p in ("projeto-ficticio-alfa", "meu_app_beta", "zela", "secondbrain", "global", "abc"):
            con.execute("insert into notes values(?)", (p,))
        con.commit()
        con.close()
        os.makedirs(os.path.join(cls.home, ".local/share/secondbrain"))
        with open(os.path.join(cls.home, ".local/share/secondbrain/denylist.txt"), "w", encoding="utf-8") as fh:
            fh.write("# pessoas e empresas\nPessoa Ficticia\nempresa-x  # comentário\n")
        sys.path.insert(0, SCRIPTS)
        sys.modules.pop("guard_publico", None)
        cls.g = importlib.import_module("guard_publico")
        cls.termos = cls.g.termos_locais()
        cls.rx = cls.g.regex_termos(cls.termos)
        cls.gen = cls.g.padroes_genericos()

    @classmethod
    def tearDownClass(cls):
        for k, v in cls.salvo.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(cls.home, ignore_errors=True)

    def acha(self, texto):
        return self.g.achados_em_texto(texto, self.rx, self.gen)

    def test_termos_vem_do_indice_e_do_arquivo_local_e_nao_incluem_o_proprio_plugin(self):
        for t in ("projeto-ficticio-alfa", "projeto ficticio alfa", "meu_app_beta", "meu app beta", "meuappbeta", "pessoa ficticia", "empresa-x", "zela"):
            self.assertIn(t, self.termos, t)
        self.assertNotIn("secondbrain", self.termos, "o nome do próprio plugin pode aparecer")
        self.assertNotIn("global", self.termos)
        self.assertNotIn("abc", self.termos, "termo curto demais gera falso positivo")

    def test_acha_nome_de_projeto_e_de_pessoa_sem_devolver_a_linha(self):
        a = self.acha("Exemplo: o Projeto-Ficticio-Alfa usa cache e a Pessoa Ficticia revisou.")
        self.assertEqual({v for _n, _c, v in a}, {"projeto-ficticio-alfa", "pessoa ficticia"})
        self.assertTrue(all(len(v) < 40 for _n, _c, v in a), "só o termo, nunca a linha inteira")

    def test_limite_de_palavra_evita_falso_positivo(self):
        self.assertEqual(self.acha("o zelador e a zelada do prédio"), [], "'zela' dentro de outra palavra não conta")
        self.assertTrue(self.acha("o app Zela lista os pedidos"), "mas a palavra sozinha conta")

    def test_permitidos_tiram_falso_positivo(self):
        with open(os.path.join(self.home, ".local/share/secondbrain/denylist-permitidos.txt"), "w", encoding="utf-8") as fh:
            fh.write("zela\n")
        try:
            self.assertNotIn("zela", self.g.termos_locais())
        finally:
            os.remove(os.path.join(self.home, ".local/share/secondbrain/denylist-permitidos.txt"))

    def test_padroes_genericos_valem_sem_lista_local(self):
        gen = self.g.padroes_genericos()
        casos = {"pasta pessoal": f"veja {self.home}/dev/coisa", "outra pasta pessoal": "veja /home/" + "joaquim" + "/dev/x", "e-mail": "fale com alguem" + "@exemplo.com",
                 "token": "ghp_" + "a" * 36, "chave privada": "-----BEGIN " + "RSA PRIVATE KEY-----"}
        for nome, txt in casos.items():
            self.assertTrue(self.g.achados_em_texto(txt, None, gen), nome)
        self.assertEqual(self.g.achados_em_texto("use 12345+nome" + "@users.noreply.github.com", None, gen), [], "e-mail noreply do GitHub é permitido")
        self.assertEqual(self.g.achados_em_texto("texto comum sobre cache e quadro", None, gen), [])
        for exemplo in ("/home/user/dev/projeto", "/home/usuario/dev/x", "/Users/nome/dev/x"):
            self.assertEqual(self.g.achados_em_texto("Exemplo: " + exemplo, None, gen), [], f"marcador de exemplo: {exemplo}")

    # ---------------------------------------------------------------- git de verdade
    def repo(self):
        d = tempfile.mkdtemp(prefix="guard-repo-", dir=self.home)
        git(d, "init", "-q")
        return d

    def test_hook_barra_commit_com_projeto_e_deixa_passar_o_limpo(self):
        d = self.repo()
        self.g.instalar_hooks(d)
        for nome in ("pre-commit", "pre-push"):
            self.assertTrue(os.access(os.path.join(d, ".git/hooks", nome), os.X_OK), nome)
        with open(os.path.join(d, "ok.md"), "w", encoding="utf-8") as fh:
            fh.write("# Exemplo\n\nUm app de loja com cache e fila.\n")
        git(d, "add", "ok.md")
        self.assertEqual(git(d, "commit", "-q", "-m", "limpo", ok=False).returncode, 0)
        with open(os.path.join(d, "ruim.md"), "w", encoding="utf-8") as fh:
            fh.write("# Notas\n\nIsso veio do projeto-ficticio-alfa.\n")
        git(d, "add", "ruim.md")
        r = git(d, "commit", "-q", "-m", "ruim", ok=False)
        self.assertNotEqual(r.returncode, 0, "o hook deve barrar")
        self.assertIn("BLOQUEADO", r.stdout + r.stderr)
        self.assertIn("ruim.md:3", r.stdout + r.stderr, "diz arquivo e linha")
        self.assertNotIn("Isso veio do", r.stdout + r.stderr, "e nunca a linha inteira")

    def test_so_linhas_adicionadas_contam(self):
        d = self.repo()
        with open(os.path.join(d, "a.md"), "w", encoding="utf-8") as fh:
            fh.write("linha com projeto-ficticio-alfa\nlinha boa\n")
        git(d, "add", "a.md")
        git(d, "commit", "-q", "-m", "antigo")
        with open(os.path.join(d, "a.md"), "w", encoding="utf-8") as fh:
            fh.write("linha com projeto-ficticio-alfa\nlinha boa\noutra linha boa\n")
        git(d, "add", "a.md")
        self.assertEqual(self.g.varrer_staged(d, self.rx, self.gen), [], "o que já estava no histórico não é reprovado de novo")

    def test_range_e_arvore_e_historico(self):
        d = self.repo()
        with open(os.path.join(d, "a.md"), "w", encoding="utf-8") as fh:
            fh.write("limpo\n")
        git(d, "add", "a.md")
        git(d, "commit", "-q", "-m", "um")
        with open(os.path.join(d, "b.md"), "w", encoding="utf-8") as fh:
            fh.write("do meu_app_beta\n")
        git(d, "add", "b.md")
        git(d, "commit", "-q", "-m", "dois")
        self.assertTrue(self.g.varrer_range(d, "HEAD~1..HEAD", self.rx, self.gen))
        arv = self.g.varrer_arvore(d, self.rx, self.gen)
        self.assertEqual([(a, n) for a, n, _c, _v in arv], [("b.md", 1)])
        hist = self.g.varrer_historico(d, self.rx, self.gen)
        self.assertEqual(len(hist), 1, "só o segundo commit tem achado")

    def test_nao_sobrescreve_hook_alheio_sem_forcar(self):
        d = self.repo()
        alheio = os.path.join(d, ".git/hooks/pre-commit")
        with open(alheio, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\necho outro hook\n")
        self.g.instalar_hooks(d)
        self.assertIn("outro hook", open(alheio, encoding="utf-8").read(), "hook de outra ferramenta fica intacto")
        self.g.instalar_hooks(d, forcar=True)
        self.assertIn("guard_publico", open(alheio, encoding="utf-8").read())
        self.assertTrue(os.path.exists(alheio + ".bak"), "e o antigo vira .bak")

    def test_sem_indice_local_a_guarda_ainda_aplica_os_padroes_genericos(self):
        g = self.g
        self.assertEqual(g.termos_locais(db=os.path.join(self.home, "nao-existe.db"), deny=os.path.join(self.home, "nada"), allow=os.path.join(self.home, "nada")), set())
        self.assertIsNone(g.regex_termos(set()))


if __name__ == "__main__":
    unittest.main()
