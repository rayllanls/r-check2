# SecScan — Instruções para o Claude Code

## O que é este projeto
SecScan é uma ferramenta desktop de análise estática de segurança (SAST).
Roda 100% local na máquina do usuário, distribuída como binário único (.exe no
Windows, binário no Linux). O código analisado NUNCA sai da máquina do usuário.
Os únicos contatos externos permitidos são:
  1. Validação de licença via HTTPS para a license API
  2. Chamada à API do Llama 3.1 via Groq (apenas se o usuário configurou o token)

## Stack definida
- **GUI:**        CustomTkinter (Python)
- **Análise:**    Semgrep OSS, Trufflehog, Grype, Gitleaks (binários em /vendors/)
- **IA:**         Llama 3.1 via Groq API (token opcional, fornecido pelo usuário)
- **Relatório:**  Jinja2 → HTML com Chart.js, abre no browser local
- **Licença:**    JWT + validação via FastAPI (Railway) + Supabase
- **Build:**      PyInstaller + PyArmor → .exe Windows + binário Linux
- **CI/CD:**      GitHub Actions (build automático por release tag)
- **Testes:**     pytest + pytest-cov
- **Linting:**    ruff + mypy

## Fases do projeto — NUNCA pular etapas
1. **Core**     → ingestão (pasta local + clone git) + wrappers das ferramentas
2. **License**  → validação JWT + device fingerprint + grace period offline
3. **AI Layer** → integração Llama 3.1 via Groq (opcional, token do usuário)
4. **Report**   → HTML com gráficos Chart.js + export PDF
5. **GUI**      → CustomTkinter orquestrando tudo
6. **Build**    → PyInstaller spec + GitHub Actions CI/CD

---

## REGRAS DE SEGURANÇA — OBRIGATÓRIAS

### Execução de subprocessos
```python
# CORRETO — sempre lista de argumentos com timeout
subprocess.run(
    ["semgrep", "--config", "auto", path],
    capture_output=True,
    timeout=120
)

# PROIBIDO — jamais shell=True
subprocess.run(f"semgrep {path}", shell=True)  # NUNCA FAZER ISSO
```

### Secrets e credenciais
- NUNCA hardcode de tokens, API keys ou secrets no código
- NUNCA logar: tokens de licença, token Groq, paths do usuário, conteúdo de arquivos analisados
- Toda comunicação de rede: HTTPS obrigatório, sem exceção
- Token Groq fica em ~/.secscan/config.json com permissão de arquivo 600
- O .env nunca é commitado — apenas .env.example com valores fictícios

### Inputs do usuário
- Todo path: validar existência + sanitizar antes de passar a subprocessos
- Nunca seguir symlinks para fora do diretório alvo
- URLs de repositório: validar formato antes de clonar
- Clones de repo: sempre em diretório temporário isolado, apagado após análise

### Token Groq (IA opcional)
- Armazenado em ~/.secscan/config.json com permissão 600
- Nunca exibido em logs, telas de erro ou relatórios
- Se ausente: features de IA simplesmente não aparecem na GUI (sem erro intrusivo)
- Timeout máximo de 15 segundos em chamadas à Groq API

### Rede
- Endpoints externos: license API + Groq API (só se token configurado)
- Timeout obrigatório: máx 10s para licença, 15s para Groq
- Falha de rede não trava o app — grace period de 72h para licença offline

---

## REGRAS DE QUALIDADE

### Separação de camadas — NUNCA misturar
```
core/     → lógica pura. Zero GUI. Zero rede. Zero licença.
tools/    → wrappers das ferramentas externas. Só subprocess.
license/  → validação de licença. Zero GUI. Zero análise.
ai/       → integração Groq/Llama. Zero GUI. Retorna texto puro.
report/   → geração de relatório. Zero GUI.
gui/      → só UI. Importa do core. O core NUNCA importa da GUI.
```

### Padrões obrigatórios
- Type hints em TODAS as funções e métodos
- Docstrings em todas as classes e funções públicas
- Funções com mais de 40 linhas devem ser quebradas
- Usar dataclasses ou Pydantic para structs — nunca dicts soltos como interface pública
- Cada módulo novo DEVE ter arquivo de teste em /tests/

### Testes
- Rodar `pytest` antes de considerar qualquer tarefa concluída
- Mocks obrigatórios para: license API, Groq API, subprocessos, acesso a disco
- Testar SEMPRE os casos de falha: token inválido, ferramenta ausente,
  path inexistente, rede offline, timeout
- Cobertura mínima de 80% em core/, license/ e ai/

### Git (padrão GSD)
- Um commit atômico por tarefa
- Formato: feat(módulo): descrição / fix(módulo): descrição / test(módulo): descrição
- NUNCA commitar .env, tokens, credenciais ou binários das ferramentas vendor

---

## Desenvolvimento local (SEM compilar)
- Durante dev as ferramentas devem estar instaladas no sistema do desenvolvedor
- O app roda com: python app/main.py
- VendorResolver em tools/base.py detecta automaticamente: vendor embutido vs sistema
- Compilação com PyInstaller só ocorre quando TODAS as fases estiverem funcionais e testadas

---

## Planos e features por licença
```
FREE
  - Detecção de secrets/chaves (Trufflehog + Gitleaks)
  - Limite de 100 arquivos por análise
  - Relatório HTML básico (sem export PDF)
  - Sem IA

PRO ($9/mês)
  - SAST completo (Semgrep)
  - Análise de dependências CVE (Grype)
  - Relatório HTML completo + export PDF
  - IA: explicação dos achados em linguagem humana (Llama 3.1)
  - IA: sugestão de correção por vulnerabilidade
  - Arquivos e repositórios ilimitados

TEAM ($29/mês)
  - Tudo do PRO
  - Até 5 tokens ativos (dispositivos)
  - Análise de IaC: Dockerfile, docker-compose, Terraform
  - Regras Semgrep customizadas
```

---

## Comportamento da IA (Llama 3.1 via Groq)
A IA enriquece os achados — NÃO é o motor de análise.
Semgrep/Trufflehog encontram os problemas. A IA explica ao usuário:
- O que é a vulnerabilidade em linguagem simples
- Por que é perigosa no contexto específico do código encontrado
- Como corrigir com exemplo de código

A IA NUNCA decide o que é ou não vulnerabilidade.
Achados sem IA configurada mostram apenas a descrição técnica padrão da ferramenta.