<div align="center">

# `>_ r-check`

**Análise de segurança de código para quem usa IA para programar.**

Encontra vulnerabilidades, segredos expostos e CVEs no seu código — tudo local, sem enviar nada para servidores.

[![Release](https://img.shields.io/github/v/release/rayllanls/r-check?style=flat-square&color=9d00ff)](https://github.com/rayllanls/r-check/releases)
[![Build](https://img.shields.io/github/actions/workflow/status/rayllanls/r-check/release.yml?style=flat-square)](https://github.com/rayllanls/r-check/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey?style=flat-square)]()

</div>

---

## O problema

Ferramentas como Cursor, Claude e ChatGPT geram código funcional, mas frequentemente com falhas de segurança sérias — SQL injection, segredos hardcoded, dependências com CVEs críticos. Quem usa IA para programar geralmente não tem formação em segurança para identificar esses problemas.

O r-check resolve isso: uma varredura completa, resultado em segundos, explicações em linguagem simples.

---

## Funcionalidades

| Scanner | O que encontra |
|---|---|
| **Semgrep** | Vulnerabilidades no código-fonte (SQL injection, XSS, funções inseguras) |
| **Trufflehog** | Segredos e tokens expostos no histórico Git |
| **Gitleaks** | Credenciais e chaves sensíveis em commits antigos |
| **Grype** | CVEs em dependências (pip, npm, cargo, etc.) |
| **Trivy** | Problemas em Dockerfile, Terraform e dependências |
| **Checkov** | Má configuração em infraestrutura como código |

- Analisa **pasta local** ou **repositório Git** (público ou privado)
- Explicações de cada vulnerabilidade geradas por **IA (Llama 3.1 via Groq)**
- Relatório HTML com gráficos, snippets de código e sugestões de correção
- **100% local** — seu código nunca sai da sua máquina

---

## Download

Baixe a versão mais recente na aba [**Releases**](https://github.com/rayllanls/r-check/releases).

1. Extraia o `.zip`
2. Execute `r-check.exe`
3. Nenhuma instalação necessária — tudo embutido

> Compatível com Windows 10/11 (x64).

---

## Rodando em desenvolvimento

**Requisitos:** Python 3.11+, Git

```bash
git clone https://github.com/rayllanls/r-check.git
cd r-check
pip install -r requirements.txt
python -m app.main
```

Em modo dev todas as ferramentas ficam liberadas (plano team) sem validação de licença.

Os scanners precisam estar instalados no sistema ou em `vendors/linux/`:

```bash
# Exemplo — instalar no Linux
brew install gitleaks trivy grype
pip install semgrep checkov
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh
```

---

## Configuração opcional

### Token Groq (IA)

Para ativar as explicações de IA, obtenha um token gratuito em [console.groq.com](https://console.groq.com) e configure em **Configurações** dentro do app.

### GitHub Token (repositórios privados)

Para escanear repos privados, gere um Personal Access Token em [github.com/settings/tokens](https://github.com/settings/tokens) com permissão `repo` e configure em **Configurações**.

---

## Planos

| | Free | Pro | Team |
|---|:---:|:---:|:---:|
| Secrets (Trufflehog + Gitleaks) | ✓ | ✓ | ✓ |
| SAST (Semgrep) | — | ✓ | ✓ |
| CVEs (Grype) | — | ✓ | ✓ |
| IaC (Trivy + Checkov) | — | — | ✓ |
| Explicações IA | — | ✓ | ✓ |

---

## Stack

- **GUI:** CustomTkinter (Python)
- **Scanners:** Semgrep · Trufflehog · Gitleaks · Grype · Trivy · Checkov
- **IA:** Llama 3.1 via Groq API
- **Relatório:** Jinja2 + HTML + Chart.js
- **Build:** PyInstaller + GitHub Actions

---

## Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE) para detalhes.
