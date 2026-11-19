"""Testes das regras de pendência (pend.py), da visibilidade no quadro e da conciliação com git (reconcile.py).

Tudo em mini-vaults e repositórios git temporários: HOME e banco isolados, nada dos seus projetos é tocado.
"""
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def dia(n):
    return (date.today() - timedelta(days=n)).isoformat()


def git(repo, *args, quando=None):
    env = dict(os.environ)
    if quando:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = f"{quando}T12:00:00"
    return subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", *args], check=True, capture_output=True, text=True, env=env)


def commitar(repo, assunto, arquivos, quando):
    for nome, conteudo in arquivos.items():
        write(os.path.join(repo, nome), conteudo)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", assunto, quando=quando)
    return git(repo, "rev-parse", "--short=7", "HEAD").stdout.strip()


MANIFESTO = "---\nschema: 2\nsensibilidade: normal\n{extra}backup: true\nmodulos: [devtrack]\npapeis:\n  devtrack: devtrack/\n---\n\n# m\n"


class PendTest(unittest.TestCase):
    """Regras puras, sem banco."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, SCRIPTS)
        sys.modules.pop("pend", None)
        cls.pend = importlib.import_module("pend")

    def test_ruido_so_vale_em_devtrack(self):
        p = self.pend
        self.assertEqual(p.ruido("O cache expira no tempo certo?"), "pergunta")
        self.assertEqual(p.ruido("Nenhum commit foi feito ainda"), "narrativo")
        self.assertEqual(p.ruido("Publicar a versão nova do serviço"), "")
        self.assertEqual(p.ruido("Reiniciar o celular: o serviço volta sozinho?", "checklist"), "",
                         "em CHECKLIST uma pergunta é uma verificação real")
        self.assertEqual(p.ruido("**Nenhum** commit feito", "devtrack"), "narrativo", "ignora marcação markdown")

    def _proj(self, itens, ultimo, vivos=()):
        todos = [{"text": t, "checked": ck, "data": d, "rel": f"devtrack/{d}.md", "kind": "devtrack", "line": i} for i, (t, ck, d) in enumerate(itens)]
        return self.pend.Projeto(todos, ultimo, vivos)

    def test_feito_com_outra_redacao(self):
        pj = self._proj([("Implementar exportação CSV dos relatórios mensais", False, "2026-01-01"),
                         ("Implementar exportação CSV dos relatórios", True, "2026-01-10")], "2026-01-10")
        estado, evid, _ = pj.classificar("Implementar exportação CSV dos relatórios mensais", "2026-01-01", "devtrack/2026-01-01.md")
        self.assertEqual(estado, "feito")
        self.assertIn("2026-01-10", evid)

    def test_repetido_quando_reescrito_em_aberto(self):
        pj = self._proj([("Revisar permissões do bucket de uploads", False, "2026-01-01"),
                         ("Revisar permissões do bucket de uploads do serviço", False, "2026-01-05")], "2026-01-05")
        self.assertEqual(pj.classificar("Revisar permissões do bucket de uploads", "2026-01-01", "devtrack/2026-01-01.md")[0], "repetido")

    def test_superado_exige_que_o_projeto_tenha_seguido(self):
        itens = [("Configurar rotação de logs do servidor", False, "2026-01-01")]
        seguiu = self._proj(itens, "2026-02-01")
        self.assertEqual(seguiu.classificar("Configurar rotação de logs do servidor", "2026-01-01", "devtrack/2026-01-01.md")[0], "superado")
        parado = self._proj(itens, "2026-01-05")
        self.assertEqual(parado.classificar("Configurar rotação de logs do servidor", "2026-01-01", "devtrack/2026-01-01.md")[0], "",
                         "projeto dormido: o item é o retrato mais recente, continua vivo")

    def test_estado_vivo_que_cita_o_item_impede_superado(self):
        itens = [("Migrar banco de dados para PostgreSQL 16", False, "2026-01-01")]
        vivo = self._proj(itens, "2026-03-01", ["Pendente: migrar banco de dados para PostgreSQL 16 ainda este mês."])
        estado, evid, _ = vivo.classificar("Migrar banco de dados para PostgreSQL 16", "2026-01-01", "devtrack/2026-01-01.md")
        self.assertEqual(estado, "")
        self.assertIn("estado vivo", evid)
        outro = self._proj(itens, "2026-03-01", ["Tema escuro do painel segue como está."])
        self.assertEqual(outro.classificar("Migrar banco de dados para PostgreSQL 16", "2026-01-01", "devtrack/2026-01-01.md")[0], "superado")

    def test_ruido_respeita_limite_de_palavra(self):
        self.assertEqual(self.pend.ruido("Nadador novo na equipe"), "", "'nada' dentro de outra palavra não é narrativo")
        self.assertEqual(self.pend.ruido("Nenhumas dúvidas restantes"), "", "\\b: só a palavra inteira")
        self.assertEqual(self.pend.ruido("Nenhum commit feito"), "narrativo")
        for tarefa in ("Ainda não existe teste para o parser", "Não foi testado em Windows o instalador", "Nada a ver: corrigir bug do login"):
            self.assertEqual(self.pend.ruido(tarefa), "", tarefa)

    def test_ponto_final_nao_muda_o_token(self):
        self.assertEqual(self.pend.tokens("Corrigir login do portal."), self.pend.tokens("Corrigir login do portal"))
        self.assertIn("checkout.ts", self.pend.tokens("Ajustar checkout.ts agora"), "o ponto de nome de arquivo fica")

    def test_pergunta_com_infinitivo_continua_tarefa(self):
        self.assertEqual(self.pend.ruido("Migrar o banco para o PostgreSQL 16?"), "", "infinitivo com ? ainda é tarefa")
        self.assertEqual(self.pend.ruido("Remover o cache antigo?"), "")
        self.assertEqual(self.pend.ruido("O cache expira no tempo certo?"), "pergunta")
        self.assertEqual(self.pend.ruido("Como migrar o banco?"), "pergunta")

    def test_risco_aberto_nunca_vira_superado(self):
        for t in ("Rotacionar o segredo vazado do serviço de pagamentos", "Liberar o deploy bloqueado pela revisão externa",
                  "Chave exposta no log do servidor de testes", "Fechar o item pendente do contrato com o parceiro"):
            pj = self._proj([(t, False, "2026-01-01")], "2026-03-01")
            estado, evid, _ = pj.classificar(t, "2026-01-01", "devtrack/2026-01-01.md")
            self.assertEqual(estado, "", t)
            self.assertIn("risco aberto", evid)
        comum = "Configurar rotação de logs do servidor"
        self.assertEqual(self._proj([(comum, False, "2026-01-01")], "2026-03-01").classificar(comum, "2026-01-01", "devtrack/2026-01-01.md")[0], "superado")

    def test_item_muito_curto_nao_e_julgado(self):
        pj = self._proj([("Ver isso", False, "2026-01-01")], "2026-06-01")
        self.assertEqual(pj.classificar("Ver isso", "2026-01-01", "devtrack/2026-01-01.md")[0], "")


class QuadroEConciliacaoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="pend-home-")
        os.environ["HOME"] = cls.home
        os.environ["SECONDBRAIN_XMEM_DB"] = os.path.join(cls.home, "xmem.db")
        sys.path.insert(0, SCRIPTS)
        for m in ("xmem", "_vault", "board", "pend", "reconcile"):
            sys.modules.pop(m, None)
        for m in ("xmem", "_vault", "pend", "board", "reconcile"):
            setattr(cls, m, importlib.import_module(m))
        proj = os.path.join(cls.home, "dev/proj_p")
        cls.proj = proj
        cls.vault = proj + "/ProjPSecondBrain"
        write(cls.vault + "/_secondbrain.md", MANIFESTO.format(extra="repos:\n  - codigo ativo\n  - antigo referencia   # só sob pedido\n"))
        d1, d2, d3 = dia(60), dia(30), dia(3)
        write(cls.vault + f"/devtrack/{d1} - Primeira.md",
              f"---\ntipo: devtrack\ndata: {d1}\n---\n\n# Primeira\n\n## Status\n\n"
              "- [ ] Implementar exportação CSV dos relatórios mensais\n- [ ] Configurar rotação de logs do servidor\n- [ ] Atualizar certificado TLS do ambiente de homologação\n- [ ] Renovar licença do monitoramento de métricas\n"
              "- [ ] Migrar banco de dados para PostgreSQL 16\n- [ ] O cache expira no tempo certo?\n- [ ] Nenhum commit foi feito ainda\n"
              "- [ ] Revisar permissões do bucket de uploads\n- [ ] Corrigir cálculo do frete para pedidos internacionais\n"
              "- [ ] Revisar documentação pagamentos integração parceiros\n- [ ] Ajustar `src/checkout.ts` para o novo fluxo\n"
              "- [ ] Ajustar `src/lib.ts` para a nova biblioteca\n")
        write(cls.vault + f"/devtrack/{d2} - Segunda.md",
              f"---\ntipo: devtrack\ndata: {d2}\n---\n\n# Segunda\n\n- [ ] Revisar permissões do bucket de uploads do serviço\n")
        write(cls.vault + f"/devtrack/{d3} - Terceira.md",
              f"---\ntipo: devtrack\ndata: {d3}\n---\n\n# Terceira\n\n- [x] Implementar exportação CSV dos relatórios\n- [ ] Revisar permissões do bucket de uploads do serviço\n")
        write(cls.vault + "/ESTADO.md", f"---\ntipo: estado\natualizado: {d3}\n---\n\n# Estado\n\nPendente: migrar banco de dados para PostgreSQL 16 em novembro.\n")
        # a memória do Claude e o CLAUDE.md também são estado vivo: o que eles citam não vira "superado"
        write(cls.xmem.mem_dir_for(proj) + "/project_notas.md",
              "---\nname: notas\ntype: project\n---\n\nLembrar de atualizar o certificado TLS do ambiente de homologação antes do deploy.\n")
        write(proj + "/CLAUDE.md", "# Regras\n\nRenovar a licença do monitoramento de métricas é obrigatório antes de qualquer release.\n")
        write(cls.vault + "/CHECKLIST.md", "# Checklist\n\n- [ ] Reiniciar o serviço: ele volta sozinho?\n")
        # repositório ativo (código) e de referência (antigo)
        cod, ant = proj + "/codigo", proj + "/antigo"
        for r in (cod, ant):
            os.makedirs(r)
            git(r, "init", "-q")
        cls.hash_real = None
        for i in range(60):                                  # um hash com letra e dígito, para o teste do "hash citado"
            h = commitar(cod, f"chore: ajuste interno {i}", {"interno.txt": f"v{i}\n"}, dia(25))
            if cls.pend_ok(h):
                cls.hash_real = h
                break
        commitar(cod, "Corrige cálculo do frete para pedidos internacionais", {"frete.py": "x = 1\n"}, dia(20))
        commitar(cod, "Atualiza documentação pagamentos", {"docs.md": "d\n"}, dia(20))
        commitar(cod, "wip", {"src/checkout.ts": "export {}\n"}, dia(18))
        commitar(cod, "reformata tudo", {f"massa/f{i}.txt": "x\n" for i in range(160)} | {"src/lib.ts": "export {}\n"}, dia(15))
        commitar(ant, "Revisa permissões do bucket de uploads do serviço", {"a.txt": "a\n"}, dia(10))
        write(cls.vault + f"/devtrack/{dia(2)} - Quarta.md",
              f"---\ntipo: devtrack\ndata: {dia(2)}\n---\n\n# Quarta\n\n- [ ] Commit `{cls.hash_real}` ainda não foi enviado ao remoto\n")
        cls.c = cls.xmem.index(quiet=True)

    @staticmethod
    def pend_ok(h):
        import re
        return bool(re.search(r"\d", h) and re.search(r"[a-f]", h) and not re.fullmatch(r"\d{7,8}", h))

    @classmethod
    def tearDownClass(cls):
        cls.c.close()
        shutil.rmtree(cls.home, ignore_errors=True)

    def todos(self):
        return {k["titulo"]: k for k in self.board.build(self.c, "proj_p", ocultos=True)}

    def test_continuidade_conta_quem_reaparece_e_quem_nunca(self):
        r = self.board.continuidade(self.c, "proj_p")
        t = r["_total"]
        self.assertEqual(t["itens"], t["reaparecem"] + t["nunca"])
        self.assertGreater(t["reaparecem"], 0, "o CSV (feito depois) e o bucket (reescrito) reaparecem")
        self.assertGreater(t["nunca"], 0, "a rotação de logs nunca mais apareceu")
        self.assertEqual(r["proj_p"]["itens"], t["itens"])

    def test_cada_pendencia_cai_no_lugar_certo(self):
        k = self.todos()
        self.assertEqual(k["Implementar exportação CSV dos relatórios mensais"]["status"], "feito")
        self.assertEqual(k["Implementar exportação CSV dos relatórios mensais"]["status_origem"], "evidencia")
        self.assertEqual(k["Configurar rotação de logs do servidor"]["oculto"], "superado")
        self.assertEqual(k["Migrar banco de dados para PostgreSQL 16"]["oculto"], "", "o ESTADO.md vivo o cita")
        self.assertEqual(k["Atualizar certificado TLS do ambiente de homologação"]["oculto"], "", "a memória do Claude o cita")
        self.assertEqual(k["Renovar licença do monitoramento de métricas"]["oculto"], "", "o CLAUDE.md o cita")
        self.assertEqual(k["O cache expira no tempo certo?"]["oculto"], "pergunta")
        self.assertEqual(k["Nenhum commit foi feito ainda"]["oculto"], "narrativo")
        self.assertEqual(k["Revisar permissões do bucket de uploads"]["oculto"], "repetido")
        self.assertEqual(k["Revisar permissões do bucket de uploads do serviço"]["oculto"], "", "a redação mais recente é a viva")
        self.assertEqual(k["Reiniciar o serviço: ele volta sozinho?"]["oculto"], "", "pergunta em CHECKLIST é verificação real")

    def test_build_esconde_por_padrao_e_nao_apaga(self):
        visiveis = {k["titulo"] for k in self.board.build(self.c, "proj_p")}
        self.assertNotIn("Configurar rotação de logs do servidor", visiveis)
        self.assertNotIn("O cache expira no tempo certo?", visiveis)
        self.assertIn("Migrar banco de dados para PostgreSQL 16", visiveis)
        self.assertIn("Configurar rotação de logs do servidor", self.todos(), "ocultos=True traz tudo")

    def test_resumo_conta_so_o_visivel_e_informa_os_ocultos(self):
        cards = self.board.build(self.c, "proj_p", ocultos=True)
        vis = self.board.summary(cards)["proj_p"]
        oc = self.board.resumo_ocultos(cards)["proj_p"]
        self.assertEqual(oc["pergunta"], 1)
        self.assertEqual(oc["narrativo"], 1)
        self.assertGreaterEqual(oc["superado"], 1)
        self.assertEqual(sum(vis.values()), len([k for k in cards if not k["oculto"]]))

    def test_open_items_le_do_quadro(self):
        textos = [t["text"] for t in self.xmem.open_items(self.c, project="proj_p", limit=100)]
        self.assertIn("Migrar banco de dados para PostgreSQL 16", textos)
        self.assertNotIn("Configurar rotação de logs do servidor", textos, "superado não conta como pendência aberta")
        self.assertNotIn("O cache expira no tempo certo?", textos)

    def test_insights_informa_ocultos_e_e_serializavel(self):
        d = self.xmem.insights_data(self.c)
        self.assertIn("proj_p", d["ocultos_por_projeto"])
        json.dumps(d)

    def test_decisao_no_quadro_vence_o_ocultar_automatico(self):
        k = self.todos()["Configurar rotação de logs do servidor"]
        self.board.apply_changes(self.c, "proj_p", [self.board.change_from_card(k, "a-fazer", etiquetas=["voltou"])])
        try:
            vis = {x["titulo"]: x for x in self.board.build(self.c, "proj_p")}
            self.assertIn("Configurar rotação de logs do servidor", vis, "quem decidiu no quadro.md manda mais que o motor")
            self.assertEqual(vis["Configurar rotação de logs do servidor"]["oculto"], "")
        finally:
            os.remove(os.path.join(self.vault, "quadro.md"))

    # ------------------------------------------------------------------ repos do manifesto
    def test_repos_declarados_com_papel(self):
        r = {os.path.basename(x["caminho"]): x for x in self._vault.read_repos(self.vault)}
        self.assertEqual(r["codigo"]["papel"], "ativo")
        self.assertEqual(r["antigo"]["papel"], "referencia")
        self.assertTrue(r["codigo"]["valido"])

    def test_repos_detectados_sem_manifesto_e_repo_quebrado(self):
        base = os.path.join(self.home, "dev/proj_q")
        vault = base + "/ProjQSecondBrain"
        write(vault + "/_secondbrain.md", MANIFESTO.format(extra=""))
        for sub in ("app", "referencias/velho"):
            os.makedirs(os.path.join(base, sub))
            git(os.path.join(base, sub), "init", "-q")
        os.makedirs(base + "/quebrado")
        write(base + "/quebrado/.git", "lixo\n")
        r = {os.path.relpath(x["caminho"], base): x for x in self._vault.read_repos(vault)}
        self.assertEqual(r["app"]["papel"], "ativo")
        self.assertEqual(r[os.path.join("referencias", "velho")]["papel"], "referencia", "pasta `referencias` = só sob pedido")
        self.assertFalse(r["quebrado"]["valido"], "`.git` que o git não reconhece é sinalizado, não ignorado em silêncio")

    def test_repo_quebrado_na_raiz_nao_esconde_os_repositorios_de_dentro(self):
        base = os.path.join(self.home, "dev/proj_r")
        vault = base + "/ProjRSecondBrain"
        write(vault + "/_secondbrain.md", MANIFESTO.format(extra=""))
        os.makedirs(base + "/.git/info")                      # `.git` quebrado: só uma pasta `info`, sem HEAD
        os.makedirs(base + "/interno")
        git(base + "/interno", "init", "-q")
        r = {os.path.relpath(x["caminho"], base): x for x in self._vault.read_repos(vault)}
        self.assertFalse(r["."]["valido"])
        self.assertTrue(r["interno"]["valido"], "o repositório válido de dentro continua sendo encontrado")

    # ------------------------------------------------------------------ conciliação
    def _propostas(self, **kw):
        repos = [r for r in self._vault.read_repos(self.vault) if r["valido"] and (r["papel"] == "ativo" or kw.get("referencias"))]
        props, _ = self.reconcile.propor(self.c, "proj_p", repos)
        return {p["titulo"]: p for p in props}

    def test_conciliacao_niveis(self):
        p = self._propostas()
        self.assertEqual(p["Corrigir cálculo do frete para pedidos internacionais"]["nivel"], "A", "commit com o mesmo assunto, 3+ termos")
        self.assertEqual(p["Revisar documentação pagamentos integração parceiros"]["nivel"], "B", "só 2 termos em comum: proposta, não ação")
        self.assertEqual(p["Ajustar `src/checkout.ts` para o novo fluxo"]["nivel"], "C", "arquivo citado foi alterado")
        hash_card = [t for t in p if self.hash_real in t]
        self.assertTrue(hash_card)
        self.assertEqual(p[hash_card[0]]["nivel"], "A", "o hash citado existe no git")

    def test_commit_em_massa_nao_prova_nada_sobre_um_arquivo(self):
        self.assertNotIn("Ajustar `src/lib.ts` para a nova biblioteca", self._propostas(), "o commit de 160 arquivos é ignorado no sinal de arquivo")

    def test_repo_de_referencia_so_entra_sob_pedido(self):
        alvo = "Revisar permissões do bucket de uploads"
        self.assertNotIn(alvo, self._propostas())
        self.assertIn(alvo, self._propostas(referencias=True))

    def test_aplicar_so_aceita_nivel_a_e_exige_confirmacao(self):
        base = dict(project="proj_p", json=False, desde=None, todas=False, incluir_referencias=False, aplicar="B", sim=False, dry_run=False, confirmo=False)
        with self.assertRaises(SystemExit):
            self.reconcile.cmd(Namespace(**base), self.c)
        with self.assertRaises(SystemExit) as e:
            self.reconcile.cmd(Namespace(**{**base, "aplicar": "A"}), self.c)
        self.assertIn("--sim", str(e.exception))
        self.assertFalse(os.path.exists(os.path.join(self.vault, "quadro.md")), "nada gravado sem confirmação")

    def test_aplicar_a_fecha_como_feito_com_etiqueta_e_backup_fora_do_vault(self):
        ns = Namespace(project="proj_p", json=False, desde=None, todas=False, incluir_referencias=False, aplicar="A", sim=True, dry_run=False, confirmo=False)
        notas = {os.path.join(r, f): open(os.path.join(r, f), encoding="utf-8").read()
                 for r, _d, fs in os.walk(self.vault) for f in fs if f.endswith(".md") and "/devtrack" in r}
        try:
            self.reconcile.cmd(ns, self.c)
            k = self.todos()["Corrigir cálculo do frete para pedidos internacionais"]
            self.assertEqual(k["status"], "feito")
            self.assertIn("reconciliado", k["etiquetas"])
            self.assertEqual(k["feito_em"], dia(20), "a data do commit que prova vira a data de conclusão (semana do calendário)")
            self.assertEqual(self.todos()["Ajustar `src/checkout.ts` para o novo fluxo"]["status"], "a-fazer", "nível C não é aplicado")
            self.assertIn("- [x] Corrigir cálculo do frete para pedidos internacionais", "".join(open(f, encoding="utf-8").read() for f in notas), "a caixa de origem também fecha")
        finally:
            os.path.exists(os.path.join(self.vault, "quadro.md")) and os.remove(os.path.join(self.vault, "quadro.md"))
            for f, txt in notas.items():            # a propagação gravou nas notas do fixture: devolve o original
                write(f, txt)
            self.c = self.xmem.index(quiet=True)

    def test_hashes_inexistentes(self):
        write(self.vault + f"/devtrack/{dia(1)} - Hashes.md",
              f"---\ntipo: devtrack\ndata: {dia(1)}\n---\n\n# Hashes\n\nCommit `{self.hash_real}` e o commit `abc1234` (que nunca existiu).\n")
        c = self.xmem.index(quiet=True)
        repos = [r for r in self._vault.read_repos(self.vault) if r["valido"]]
        faltam = {h for h, _ in self.reconcile.hashes_inexistentes(c, "proj_p", repos)}
        self.assertIn("abc1234", faltam)
        self.assertNotIn(self.hash_real, faltam)


if __name__ == "__main__":
    unittest.main()
