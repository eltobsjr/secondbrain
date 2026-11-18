"""Testes do xmem com um mini-vault de fixture (HOME e banco isolados; não toca nos seus vaults).

Rodar: python3 -I -m unittest discover -s tests -p 'test_*.py'
"""
import importlib
import os
import shutil
import sys
import tempfile
import time
import unittest
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)


MANIFEST = "---\nschema: 2\nsensibilidade: {sens}\nbackup: true\nmodulos: [devtrack, decisoes]\npapeis:\n  devtrack: devtrack/\n  decisoes: decisions/\n  estado: ESTADO.md\n---\n\n# m\n"


class XmemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="xmem-home-")
        os.environ["HOME"] = cls.home
        os.environ["SECONDBRAIN_XMEM_DB"] = os.path.join(cls.home, "xmem.db")
        sys.path.insert(0, SCRIPTS)
        for m in ("xmem", "_vault"):
            sys.modules.pop(m, None)
        cls.xmem = importlib.import_module("xmem")
        a = os.path.join(cls.home, "dev/proj_a/ProjASecondBrain")
        b = os.path.join(cls.home, "dev/proj_b/ProjBSecondBrain")
        write(a + "/_secondbrain.md", MANIFEST.format(sens="normal"))
        write(b + "/_secondbrain.md", MANIFEST.format(sens="alta"))
        old = (date.today() - timedelta(days=40)).isoformat()
        write(a + "/decisions/001 - Cache em Redis.md",
              "---\ntipo: decisao\ndata: 2026-01-10\nstatus: aceita\n---\n\n# 001 — Cache em Redis\n\n## Contexto\n\nUsamos Redis para cache das consultas de relatório com expiração de 10 minutos.\n")
        write(a + "/decisions/002 - Cache em memória.md",
              "---\ntipo: decisao\ndata: 2026-03-02\nstatus: aceita\nsubstitui: \"[[decisions/001 - Cache em Redis]]\"\n---\n\n# 002 — Cache em memória\n\n## Contexto\n\nTroca do Redis por cache em memória do processo para consultas de relatório, expiração de 10 minutos.\n")
        write(a + f"/devtrack/{old} - Setup.md",
              f"---\ntipo: devtrack\ndata: {old}\n---\n\n# {old} — Setup\n\n## Status\n\n- [ ] Configurar rotação de logs do servidor\n- [x] Criar banco\n")
        write(b + "/decisions/001 - Segredo do contrato.md",
              "---\ntipo: decisao\ndata: 2026-02-01\n---\n\n# 001 — Segredo do contrato\n\n## Contexto\n\nO contrato com o parceiro exige expiração do cache de relatório em 10 minutos, confidencial.\n")
        mem = cls.xmem.mem_dir_for(os.path.dirname(a))
        write(mem + "/feedback_x.md", "---\nname: feedback-x\ndescription: Nunca usar display none; preferir template vazio\nmetadata:\n  type: feedback\n---\n\nTexto curto sobre estilos.\n")
        cls.a, cls.b = a, b
        cls.c = cls.xmem.index(quiet=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.home, ignore_errors=True)

    def test_reindexar_nota_alterada_nao_quebra_nem_deixa_lixo_na_busca(self):
        """Regressão: apagar trechos sem apagar o FTS fazia o índice quebrar ao alterar a última nota indexada."""
        path = os.path.join(self.a, "devtrack", "zz-ultima-nota.md")
        write(path, "---\ntipo: devtrack\ndata: 2026-11-01\n---\n\n# Ultima\n\n## Status\n\n- [ ] primeira versao do texto exclusivo alfa\n")
        c = self.xmem.index(quiet=True)
        write(path, "---\ntipo: devtrack\ndata: 2026-11-01\n---\n\n# Ultima\n\n## Status\n\n- [ ] segunda versao do texto exclusivo beta\n")
        os.utime(path, (time.time() + 5, time.time() + 5))
        c = self.xmem.index(quiet=True)   # não pode levantar IntegrityError
        orfas = c.execute("select count(*) from chunks_fts where rowid not in (select id from chunks)").fetchone()[0]
        self.assertEqual(orfas, 0, "nenhuma linha de FTS sem trecho correspondente")
        hits = [h["row"]["rel"] for h in self.xmem.hybrid(c, "texto exclusivo beta", k=5)]
        self.assertIn("devtrack/zz-ultima-nota.md", hits)

    def test_indexa_vaults_e_memoria(self):
        n = self.c.execute("select count(*) from notes").fetchone()[0]
        self.assertGreaterEqual(n, 5)
        mem = self.c.execute("select count(*) from notes where kind='memory'").fetchone()[0]
        self.assertEqual(mem, 1)

    def test_description_do_frontmatter_e_buscavel(self):
        r = self.xmem.hybrid(self.c, "nunca usar display none", k=3)
        self.assertTrue(any("feedback_x" in h["row"]["rel"] for h in r))

    def test_busca_oculta_nota_substituida(self):
        r = self.xmem.hybrid(self.c, "cache de relatório expiração 10 minutos", k=8, project="proj_a")
        rels = [h["row"]["rel"] for h in r]
        self.assertTrue(any("002" in x for x in rels))
        self.assertFalse(any("001 - Cache em Redis" in x for x in rels), "a decisão substituída não deve aparecer por padrão")

    def test_all_mostra_substituida(self):
        r = self.xmem.hybrid(self.c, "Redis cache relatório", k=8, project="proj_a", include_inactive=True)
        self.assertTrue(any("001 - Cache em Redis" in h["row"]["rel"] for h in r))

    def test_linhagem(self):
        nid = self.c.execute("select id from notes where rel like '%002 - Cache%'").fetchone()[0]
        chain = self.xmem.lineage(self.c, nid)
        self.assertEqual(len(chain), 2)
        self.assertEqual([bool(x["inactive"]) for x in chain], [True, False])

    def test_privacidade_so_titulo_em_outro_projeto(self):
        r = self.xmem.hybrid(self.c, "contrato parceiro confidencial", k=3)
        row = r[0]["row"]
        self.assertEqual(row["project"], "proj_b")
        self.assertEqual(self.xmem.visible(row, "proj_a"), "titulos")
        self.assertEqual(self.xmem.visible(row, "proj_b"), "completo")
        self.assertEqual(self.xmem.visible(row, None), "completo", "busca solta/GUI vê tudo")

    def test_item_em_aberto_parado(self):
        itens = self.xmem.open_items(self.c, project="proj_a")
        parado = [i for i in itens if "rotação de logs" in i["text"]]
        self.assertEqual(len(parado), 1)
        self.assertGreater(parado[0]["idade"], self.xmem.STALE_OPEN_DAYS)
        self.assertFalse([i for i in itens if "Criar banco" in i["text"]], "item concluído não é aberto")

    def test_origem_liga_projetos_diferentes(self):
        write(self.a + "/decisions/003 - Outra.md",
              "---\ntipo: decisao\ndata: 2026-04-01\norigem: \"proj_b:decisions/001 - Segredo do contrato\"\n---\n\n# 003 — Outra\n\nTexto qualquer sobre outro assunto totalmente distinto.\n")
        self.xmem.index(quiet=True)
        c = self.xmem.connect()
        r = c.execute("select count(*) from edges e join notes a on a.id=e.src join notes b on b.id=e.dst where a.project='proj_a' and b.project='proj_b' and e.type='references' and e.origin='manual'").fetchone()[0]
        self.assertEqual(r, 1)

    def test_segredo_detectado(self):
        achados = [d for p, d in self.xmem.SECRET_PATTERNS if self.xmem.re.search(p, "token ghp_" + "a" * 36)]
        self.assertIn("GitHub PAT", achados)

    def test_indexacao_incremental_e_remocao(self):
        p = self.a + "/devtrack/novo.md"
        write(p, "---\ntipo: devtrack\n---\n\n# Novo\n\nTexto único zeppelin xylofone.\n")
        time.sleep(0.01)
        self.xmem.index(quiet=True)
        c = self.xmem.connect()
        self.assertTrue(self.xmem.hybrid(c, "zeppelin xylofone", k=3))
        os.remove(p)
        self.xmem.index(quiet=True)
        self.assertFalse(self.xmem.hybrid(self.xmem.connect(), "zeppelin xylofone", k=3))

    def test_arestas_automaticas_sem_duplicata_e_sem_registro(self):
        c = self.xmem.connect()
        auto = [dict(r) for r in c.execute(
            "select src, dst, type, origin, score from edges where origin='auto'")]
        pares = [(min(e["src"], e["dst"]), max(e["src"], e["dst"])) for e in auto]
        self.assertEqual(len(pares), len(set(pares)), "cada par aparece uma vez só")
        kinds = {r["id"]: r["kind"] for r in c.execute("select id, kind from notes")}
        for e in auto:
            self.assertIn(kinds[e["src"]], self.xmem.KNOWLEDGE_KINDS)
            self.assertIn(kinds[e["dst"]], self.xmem.KNOWLEDGE_KINDS)
            self.assertGreaterEqual(e["score"], self.xmem.AUTO_MIN)

    def test_grafo_marca_cruzamento_entre_projetos(self):
        c = self.xmem.connect()
        g = self.xmem.graph_data(c, None, 0.0)
        self.assertTrue(g["nodes"])
        self.assertTrue(all("grau" in n and "cross" in e for n in g["nodes"] for e in g["edges"]))
        proj = {n["id"]: n["project"] for n in g["nodes"]}
        for e in g["edges"]:
            self.assertEqual(e["cross"], proj[e["src"]] != proj[e["dst"]])
        auto_forte = self.xmem.graph_data(c, None, 0.9)
        self.assertLessEqual(len(auto_forte["edges"]), len(g["edges"]))
        self.assertTrue(all(e["origin"] != "auto" or e["score"] >= 0.9 for e in auto_forte["edges"]))

    def test_layout_do_grafo_e_deterministico_e_cacheado(self):
        c = self.xmem.connect()
        g = self.xmem.graph_data(c, None, 0.0)
        a = self.xmem.graph_layout(g, recompute=True)
        b = self.xmem.graph_layout(g, recompute=True)
        self.assertEqual(len(a), len(g["nodes"]))
        self.assertEqual(a, b, "mesmo grafo => mesmas posições")
        self.assertTrue(os.path.isfile(self.xmem.GRAPH_LAYOUT_PATH), "layout fica em cache")
        self.assertEqual(self.xmem.graph_signature(g), self.xmem.graph_signature(self.xmem.graph_data(c, None, 0.0)))


if __name__ == "__main__":
    unittest.main()
