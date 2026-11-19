"""Os números que a documentação afirma têm de bater com o repositório (a auditoria achou vários desencontros)."""
import json
import os
import re
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def ler(*p):
    with open(os.path.join(RAIZ, *p), encoding="utf-8") as fh:
        return fh.read()


class DocsTest(unittest.TestCase):
    def test_numero_de_skills(self):
        n = len([d for d in os.listdir(os.path.join(RAIZ, "skills")) if os.path.isfile(os.path.join(RAIZ, "skills", d, "SKILL.md"))])
        for arq in ("README.md", "CLAUDE.md", ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
            achados = {int(x) for x in re.findall(r"\b(\d+) skills\b", ler(*arq.split("/")))}
            self.assertTrue(achados, f"{arq} deveria dizer quantas skills existem")
            self.assertEqual(achados, {n}, f"{arq} diz {achados}, existem {n}")

    def test_versoes_iguais(self):
        v = json.loads(ler("package.json"))["version"]
        self.assertEqual(json.loads(ler(".claude-plugin", "plugin.json"))["version"], v)
        self.assertEqual(json.loads(ler(".claude-plugin", "marketplace.json"))["plugins"][0]["version"], v)
        ultima = re.search(r"^## \[(\d+\.\d+\.\d+)\]", ler("CHANGELOG.md"), re.M).group(1)
        self.assertEqual(ultima, v, "a versão mais nova do CHANGELOG é a do plugin")

    def test_arquitetura_na_versao_atual(self):
        v = json.loads(ler("package.json"))["version"]
        self.assertIn(f"versao: {v}", ler("docs", "ARQUITETURA-MEMORIA-CRUZADA.md")[:200])

    def test_decisoes_citadas_existem_no_numero_certo(self):
        # CLAUDE.md cita o intervalo das decisões do vault local (que não está no repositório): ao menos o formato é válido
        m = re.search(r"decisions/(\d{3})` a `(\d{3})", ler("CLAUDE.md"))
        self.assertTrue(m and int(m.group(1)) < int(m.group(2)))

    def test_secoes_da_arquitetura_em_ordem(self):
        nums = re.findall(r"^## (\d+(?:\.\d+)?)[. ]", ler("docs", "ARQUITETURA-MEMORIA-CRUZADA.md"), re.M)
        chaves = [tuple(int(x) for x in n.split(".")) for n in nums]
        self.assertEqual(chaves, sorted(chaves), f"seções fora de ordem: {nums}")


if __name__ == "__main__":
    unittest.main()


class FontesTest(unittest.TestCase):
    def test_priority_nao_gera_caixas_e_skills_apontam_para_a_tabela(self):
        pri = ler("skills", "secondbrain-priority", "SKILL.md")
        modelo = pri[pri.index("## Passo 4"):pri.index("## Passo 5")]
        self.assertNotIn("- [ ]", modelo, "a visão de prioridades não pode ter caixas: o quadro as leria de volta")
        for s in ("priority", "resume", "standup"):
            self.assertIn("board show", ler("skills", f"secondbrain-{s}", "SKILL.md"), s)
        self.assertTrue(os.path.isfile(os.path.join(RAIZ, "references", "fontes-de-verdade.md")))


class DevtrackEnxutoTest(unittest.TestCase):
    def test_skill_do_devtrack_abaixo_de_120_linhas_e_usa_o_motor(self):
        txt = ler("skills", "secondbrain-devtrack", "SKILL.md")
        self.assertLess(len(txt.splitlines()), 120)
        self.assertIn("session-close", txt)
