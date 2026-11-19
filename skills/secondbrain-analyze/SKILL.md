---
name: secondbrain-analyze
description: |
  Realiza uma análise completa, profunda e estratégica do projeto — técnica, arquitetural,
  funcional, visual e de produto. Identifica pontos fortes, gargalos, riscos, inconsistências
  e oportunidades de melhoria. Produz um relatório estruturado em 16 dimensões com nota geral,
  top 10 problemas, top 10 pontos fortes e plano de evolução técnica e de produto.
  
  Use esta skill sempre que o usuário pedir para:
  - "/analyze"
  - "/analyse"
  - "analisa o projeto"
  - "faz uma análise completa"
  - "revisão técnica do projeto"
  - "auditoria do produto"
  - "avalia a arquitetura"
  - "quais são os problemas do projeto"
  - "o que pode melhorar no projeto"
  - "análise estratégica"
  - "pontos fortes e fracos do projeto"
  - "nota para o projeto"
  - "o que está bom e o que está ruim"
  - quando o usuário quiser uma visão global e crítica do estado atual do projeto
---

# SecondBrain — Analyze

> **Vault:** antes de ler ou gravar, resolva o vault e os caminhos conforme `references/vault-resolve.md` (manifesto `_secondbrain.md`; se faltar, migração assistida sem mover nada). Neste arquivo, `{vault}` é a pasta do vault e `{devtrack}`, `{decisoes}`, `{features}`, `{prioridade}` etc. são os caminhos que o manifesto dá a cada papel (sem manifesto, valem os padrões).

Análise completa, profunda e estratégica do projeto — técnica, arquitetural, funcional, visual e de produto.

---

## Passo 1 — Coletar contexto do projeto

Execute em paralelo para explorar o ecossistema completo:

```bash
# Estrutura do projeto
find . -maxdepth 3 -not -path '*/.git/*' -not -path '*/node_modules/*' \
  -not -path '*/__pycache__/*' -not -path '*/.next/*' -not -path '*/dist/*' \
  | sort

# Stack e dependências
cat package.json 2>/dev/null
cat pyproject.toml 2>/dev/null
cat requirements.txt 2>/dev/null
cat Cargo.toml 2>/dev/null
cat go.mod 2>/dev/null
cat pom.xml 2>/dev/null
cat Gemfile 2>/dev/null

# Infraestrutura
cat docker-compose.yml 2>/dev/null
cat Dockerfile 2>/dev/null
ls .github/workflows/ 2>/dev/null
cat vercel.json 2>/dev/null
cat fly.toml 2>/dev/null

# Git history
git log --oneline -30 2>/dev/null
git log --stat --since="90 days ago" --oneline 2>/dev/null | head -50

# Testes
find . -name "*.test.*" -o -name "*.spec.*" -o -name "*_test.*" \
  -not -path '*/node_modules/*' 2>/dev/null | head -20
ls tests/ 2>/dev/null
ls __tests__/ 2>/dev/null

# README e docs
cat README.md 2>/dev/null | head -80
ls docs/ 2>/dev/null
```

Leia também:
1. Memória do projeto em `~/.claude/projects/.../memory/` — especialmente `project_overview.md`
2. Vault SecondBrain — `*SecondBrain/*Visão Geral*.md` se existir
3. Os arquivos mais importantes de cada camada (entry points, controllers, componentes principais)

Não leia tudo — leia o suficiente para entender cada dimensão. Vá a fundo nos arquivos que parecerem problemáticos.

---

## Passo 2 — Explorar cada camada

Com base na stack detectada no Passo 1, explore as camadas relevantes:

**Backend (se houver):** entry points, rotas, controllers, serviços, middlewares, autenticação, validação, tratamento de erros.

**Frontend (se houver):** estrutura de componentes, estado global, roteamento, chamadas de API, performance, responsividade.

**Banco de dados (se houver):** schema, migrations, queries, índices, relacionamentos.

**Infraestrutura:** CI/CD, deploy, variáveis de ambiente, secrets, monitoramento.

**Segurança:** exposição de dados sensíveis, validação de entrada, autenticação, dependências vulneráveis.

Adapte ao que o projeto tem. Um projeto CLI não tem frontend; um script Python não tem banco de dados. Seja honesto sobre o que consegue avaliar pelo código.

---

## Passo 3 — Gerar o relatório de análise

Escreva o relatório completo seguindo esta estrutura exata:

---

> **Modelo 1** (`references/analyze-modelos.md`, seção "Modelo 1"): abra-o e preencha. Não o reproduza de memória.

---

## Passo 4 — Padrões de qualidade da análise

Antes de escrever, verifique mentalmente:

- **Seja específico:** cite nomes de arquivo, função ou linha quando apontar um problema. "O arquivo `src/auth/middleware.js` não valida o token de expiração" é útil. "A autenticação tem problemas" não é.
- **Seja calibrado:** separe riscos críticos de problemas de estilo. Não trate tudo como urgente.
- **Seja honesto sobre incerteza:** se não conseguiu avaliar uma dimensão pelo código, diga explicitamente o que ficou fora do escopo.
- **Seja acionável:** cada problema deve ter uma direção de solução. Crítica sem sugestão não ajuda.
- **Seja justo:** reconheça o que está funcionando bem antes de criticar. Projetos sempre têm pontos fortes reais.
- **Evite o genérico:** observações que se aplicariam a qualquer projeto são ruído. Cada achado deve ser fundamentado em algo que você realmente encontrou.

---

## Passo 5 — Gerar o arquivo de contexto geral (obrigatório)

**Sempre gere este arquivo após o relatório — sem precisar perguntar ao usuário.**

Salve em `PROJECT_CONTEXT.md` na raiz do projeto. Este arquivo é lido pelo Claude no início de cada sessão para recuperar contexto sem re-analisar o projeto inteiro.

O arquivo deve ser **denso e conciso** — não é um resumo do relatório, é um mapa de contexto para o Claude operar com autonomia. Escreva pensando em alguém que vai ler isso em 30 segundos e sair codando.

> **Modelo 2** (`references/analyze-modelos.md`, seção "Modelo 2"): abra-o e preencha. Não o reproduza de memória.

Confirme após salvar:
```
✓ PROJECT_CONTEXT.md criado/atualizado na raiz do projeto.
  Claude lerá este arquivo automaticamente no início das próximas sessões.
```

---

## Passo 6 — Salvar análise completa no vault (opcional)

Pergunte ao usuário:
> "Quer salvar a análise completa no vault do SecondBrain também?"

Se sim:

```bash
ls *SecondBrain/ 2>/dev/null
```

Salve em:
- `{vault}/{analise}/Análise Completa — {data}.md` (papel `analise` do manifesto; padrão `analise/`, sem acento)
- Se a pasta não existir, crie-a e registre o papel `analise` no manifesto.

Confirme:
```
✓ Análise completa salva em: {caminho completo}
```

Se o usuário quiser usar como base para o documento de **Visão Geral do Produto**, ofereça:
> "Posso usar esta análise para gerar ou atualizar o documento de Visão Geral do projeto (`{NomeProjeto} — Visão Geral.md`). Quer que eu faça isso?"
