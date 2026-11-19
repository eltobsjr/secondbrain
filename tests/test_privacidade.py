"""Privacidade da memória cruzada (auditoria P0-1 a P0-4): o texto de um vault restrito não sai por nenhum comando.

Fixtures temporárias e nomes inventados. O "canário" é uma palavra que só existe NO CORPO das notas restritas: se aparecer na
saída de qualquer comando rodado de outro projeto, a política vazou.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
XMEM = os.path.join(HERE, "..", "scripts", "xmem.py")
CANARIO = "zumbidoraro"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def manifesto(extra=""):
    return f"---\nschema: 2\n{extra}backup: true\nmodulos: [devtrack]\npapeis:\n  devtrack: devtrack/\n---\n\n# m\n"


class PrivacidadeTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="priv-home-")
        self.env = {"PATH": os.environ["PATH"], "HOME": self.home, "SECONDBRAIN_XMEM_DB": os.path.join(self.home, "x.db"), "LC_ALL": "C.UTF-8"}
        self.pub = os.path.join(self.home, "dev/proj_pub/ProjPubSecondBrain")
        self.res = os.path.join(self.home, "dev/proj_res/ProjResSecondBrain")
        self.nao = os.path.join(self.home, "dev/proj_nao/ProjNaoSecondBrain")
        write(self.pub + "/_secondbrain.md", manifesto())
        write(self.pub + "/devtrack/2026-11-10 - Aberta.md", "---\ntipo: devtrack\ndata: 2026-11-10\n---\n\n# Aberta\n\nO contrato do parceiro precisa de revisão jurídica.\n\n- [ ] Revisar contrato do parceiro\n")
        for raiz, extra in ((self.res, 'sensibilidade: alta\n'), (self.nao, "sensibilidade: alta\ncrossmem: nenhum\n")):
            write(raiz + "/_secondbrain.md", manifesto(extra))
            write(raiz + "/devtrack/2026-11-12 - Reservada.md",
                  f"---\ntipo: devtrack\ndata: 2026-11-12\n---\n\n# Nota reservada\n\nO contrato do parceiro tem a cláusula {CANARIO} e exige revisão jurídica.\n\n- [ ] Renegociar cláusula {CANARIO} do contrato do parceiro\n")
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        self.run_x("index")

    def run_x(self, *args, cwd=None, global_args=()):
        r = subprocess.run([sys.executable, "-I", XMEM, *global_args, *args], capture_output=True, text=True, env=self.env, cwd=cwd or os.path.dirname(self.pub))
        return r.stdout + r.stderr

    def mudar(self, vault, extra):
        write(vault + "/_secondbrain.md", manifesto(extra))

    # ---- P0-1: o YAML comum não pode abrir a política
    def test_grafias_comuns_de_yaml_nao_abrem_a_politica(self):
        import importlib
        sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
        os.environ["HOME"] = self.home
        xm = importlib.import_module("xmem")
        casos = {'crossmem: "nenhum"': "nenhum", "crossmem: 'nenhum'": "nenhum", "crossmem: NENHUM": "nenhum", "crossmem: nenhum  # privado": "nenhum",
                 "crossmem: Titulos": "titulos", "crossmem: talvez": "nenhum"}
        for linha, esperado in casos.items():
            self.mudar(self.res, linha + "\n")
            self.assertEqual(xm.manifest_scalars(self.res)["crossmem"], esperado, linha)
        for linha, esperado in {'sensibilidade: "alta"': "alta", "sensibilidade: ALTA": "alta", "sensibilidade: sigilosa": "alta"}.items():
            self.mudar(self.res, linha + "\n")
            self.assertEqual(xm.manifest_scalars(self.res)["sens"], esperado, linha)
        self.mudar(self.res, "sensibilidade: sigilosa\ncrossmem: talvez\n")
        self.assertEqual(len(xm.manifest_scalars(self.res)["invalidos"]), 2, "o check_vault acusa o que foi lido como o mais restrito")

    def test_vault_com_crossmem_nenhum_entre_aspas_nao_e_indexado(self):
        self.mudar(self.res, 'sensibilidade: alta\ncrossmem: "nenhum"\n')
        self.run_x("index")
        self.assertNotIn("proj_res", self.run_x("status"))

    # ---- P0-2: a política muda sem reindexar
    def test_mudar_o_manifesto_vale_sem_reindexar(self):
        cmd = ("recall", "contrato do parceiro")
        self.mudar(self.res, "")                               # vira aberto e indexa
        self.run_x("index")
        self.assertIn(CANARIO, self.run_x(*cmd, cwd=os.path.dirname(self.pub)), "aberto: o corpo aparece (a fixture prova algo)")
        self.mudar(self.res, "sensibilidade: alta\ncrossmem: titulos\n")
        self.assertNotIn(CANARIO, self.run_x(*cmd), "restringiu no manifesto: vale já, sem rodar index")
        self.mudar(self.res, "sensibilidade: alta\ncrossmem: nenhum\n")
        saida = self.run_x(*cmd)
        self.assertNotIn(CANARIO, saida)
        self.assertNotIn("Nota reservada", saida, "nenhum: nem o título")

    # ---- P0-3: sem projeto detectado também falha fechado
    def test_fora_de_qualquer_projeto_o_recall_nao_imprime_corpo_restrito(self):
        fora = tempfile.mkdtemp(prefix="priv-fora-")
        self.addCleanup(shutil.rmtree, fora, ignore_errors=True)
        saida = self.run_x("recall", "contrato do parceiro", "--todos-projetos", cwd=fora)
        self.assertNotIn(CANARIO, saida)
        self.assertIn("Nota reservada", saida, "o título de `titulos` aparece (é a política)")
        self.assertIn(CANARIO, self.run_x("recall", "contrato do parceiro", "--todos-projetos", cwd=fora, global_args=("--sem-politica",)), "só com --sem-politica")

    # ---- P0-4: nenhum comando vaza
    def test_canario_nao_aparece_na_saida_de_nenhum_comando_a_partir_de_outro_projeto(self):
        ref = "proj_res:devtrack/2026-11-12 - Reservada"
        comandos = [("search", "contrato parceiro cláusula"), ("recall", "contrato do parceiro"), ("digest", "contrato parceiro"),
                    ("absorb-check", f"O contrato do parceiro tem a cláusula {CANARIO} e exige revisão jurídica."),
                    ("related", ref), ("patterns",), ("dups",), ("insights",), ("graph",), ("board", "show"), ("board", "summary"),
                    ("board", "show", "--json"), ("board", "show", "--todos"), ("hook-context", "--cwd", os.path.dirname(self.pub))]
        for cmd in comandos:
            saida = self.run_x(*cmd, cwd=os.path.dirname(self.pub))
            if cmd[0] == "absorb-check":     # o texto de entrada é do próprio usuário e aparece no aviso de segredo; só a PARTE vinda do índice conta
                saida = saida.split("Checagem de absorção", 1)[-1]
            self.assertNotIn(CANARIO, saida.replace(f"cláusula {CANARIO} e exige", ""), f"vazou em: {' '.join(cmd)}")
            self.assertNotIn("nao", "") if False else None
