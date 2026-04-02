# PROJECT BRIEF — SecScan
> Cole este conteúdo quando o GSD perguntar sobre o projeto em /gsd:new-project

---

## Descrição do produto
SecScan é uma ferramenta desktop de análise de segurança de código (SAST) voltada para
desenvolvedores que usam vibe coding e ferramentas de IA para gerar código, mas não têm
formação em segurança. Analisa o código localmente, encontra vulnerabilidades e explica
os problemas em linguagem simples com sugestões de correção.

## Público-alvo
Desenvolvedores iniciantes e intermediários construindo SaaS com IA (Cursor, Claude,
ChatGPT). Maioria no Windows. Não sabem o que é SAST, SQL injection ou CVE.

## Proposta de valor
"Seu código gerado por IA provavelmente tem falhas de segurança sérias. O SecScan
encontra antes que alguém mal-intencionado encontre. Roda na sua máquina, seu código
nunca vai para nenhum servidor."

## Stack técnica
- Linguagem: Python 3.11+
- GUI: CustomTkinter
- Ferramentas: Semgrep OSS, Trufflehog, Grype, Gitleaks (binários embutidos)
- IA: Llama 3.1 via Groq API (token opcional fornecido pelo usuário)
- Relatório: Jinja2 + HTML + Chart.js (abre no browser local)
- Licença: JWT + FastAPI (Railway) + Supabase — IMPLEMENTAR SÓ NA FASE 6
- Build: PyInstaller + PyArmor — IMPLEMENTAR SÓ NA FASE 7
- Testes: pytest | Linting: ruff + mypy

## Estratégia de desenvolvimento — IMPORTANTE
O projeto é desenvolvido em duas grandes etapas:

ETAPA 1 (Fases 1 a 5): App funciona 100% local, sem licença, sem compilar.
DEV_MODE=True libera tudo (plano team) sem validar nada.
Foco total em fazer a análise funcionar bem e a GUI ficar boa.

ETAPA 2 (Fases 6 e 7): Só depois que tudo funcionar localmente.
Implementa licença em nuvem, compilação do binário e distribuição.

## Fases do roadmap

Fase 1 — Core de análise
  Wrappers das 4 ferramentas (Semgrep, Trufflehog, Grype, Gitleaks)
  Modelos de dados (Finding, ScanResult, Severity)
  Ingestão: pasta local + clone de repo Git
  Detecção de linguagem automática
  Scanner orquestrador com callbacks de progresso
  Testes unitários de todas as camadas core

Fase 2 — Camada de IA (Llama 3.1 via Groq)
  Cliente Groq com timeout e fallback silencioso
  Prompts de explicação e sugestão de correção
  Configuração do token pelo usuário (~/.secscan/config.json)
  Testes com mock da API Groq

Fase 3 — Relatório HTML
  Template Jinja2 com Chart.js (gráficos de severidade e categoria)
  Lista de achados com snippet de código
  Explicações da IA integradas no relatório
  Export para PDF
  Abre automaticamente no browser local

Fase 4 — GUI CustomTkinter
  Janela principal: seleção de fonte, análises por plano, botão de scan
  Tela de progresso com log em tempo real
  Tela de configurações: token Groq
  Design dark, moderno, com logo
  Badge de plano (em dev sempre mostra "DEV")

Fase 5 — Integração e polish
  Tudo funcionando junto: GUI → Scanner → Relatório
  Testes de integração end-to-end
  Tratamento de erros amigável na GUI
  Performance: projetos médios em menos de 3 minutos

Fase 6 — Sistema de licença (DEPOIS que tudo funcionar)
  License API com FastAPI + Supabase
  Validação JWT + device fingerprint
  Grace period offline de 72h
  Freemium + PRO + TEAM
  Integração com Stripe

Fase 7 — Build e distribuição (ÚLTIMA fase)
  PyInstaller spec com vendors embutidos
  PyArmor para ofuscação
  GitHub Actions: .exe Windows + binário Linux
  GitHub Releases automatizado

## Modelo de negócio (implementar na Fase 6)
FREE: secrets/chaves, até 100 arquivos, sem PDF, sem IA
PRO ($9/mês): SAST completo, CVE, PDF, IA, ilimitado
TEAM ($29/mês): tudo do PRO + 5 dispositivos + IaC + regras customizadas

## Requisitos não funcionais
- Funciona offline por 24h (após implementar licença)
- Progresso em tempo real na GUI (nunca parecer travado)
- Projeto de 500 arquivos em menos de 3 minutos
- Binário final pode ter até 600MB
- Windows 10/11 e Ubuntu 20.04+

## Fora do escopo v1
- Mobile (iOS/Android)
- OAuth GitHub/GitLab (v2)
- Dashboard web
- Plugin para IDEs (v2)