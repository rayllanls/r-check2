# Requirements: SecScan

**Defined:** 2026-03-29
**Core Value:** Encontrar falhas sérias de segurança no código gerado por IA antes que alguém mal-intencionado encontre — localmente, de forma privada, sem exigir conhecimento de segurança.

## v1 Requirements

### Scan — Entrada e ingestão

- [x] **SCAN-01**: Usuário pode selecionar uma pasta local para scan recursivo de segurança
- [x] **SCAN-02**: Usuário pode informar uma URL de repositório Git público para clonar e scannar
- [x] **SCAN-03**: Sistema detecta automaticamente a(s) linguagem(ns) do projeto e seleciona as regras adequadas

### Scan — Backends

- [x] **BACK-01**: Semgrep executa análise SAST e retorna achados com arquivo, linha e descrição
- [ ] **BACK-02**: Trufflehog escaneia histórico Git em busca de secrets expostos
- [x] **BACK-03**: Grype verifica dependências do projeto contra banco de CVEs
- [ ] **BACK-04**: Gitleaks escaneia arquivos do projeto em busca de chaves e credenciais expostas
- [x] **BACK-05**: Scanner orquestrador executa as 4 ferramentas em paralelo e emite callbacks de progresso em tempo real

### Dados — Modelos de domínio

- [x] **DATA-01**: Modelo `Finding` contém: título, severidade, arquivo, linha, descrição, ferramenta de origem e snippet de código
- [x] **DATA-02**: Modelo `ScanResult` contém: lista de findings, metadados do scan e duração
- [x] **DATA-03**: Enum `Severity` define os níveis: Critical, High, Medium, Low, Info

### IA — Explicações e sugestões (Groq / Llama 3.1)

- [x] **AI-01**: Usuário pode configurar seu token Groq em `~/.secscan/config.json`
- [x] **AI-02**: Cada finding exibe uma explicação em linguagem simples gerada pelo Llama 3.1 via Groq
- [x] **AI-03**: Cada finding exibe uma sugestão de correção gerada pelo Llama 3.1 via Groq
- [x] **AI-04**: Quando nenhum token está configurado, o produto funciona normalmente sem explicações de IA (fallback silencioso)

### Relatório HTML

- [x] **RPT-01**: Scan gera relatório HTML com gráficos de distribuição de severidade e por categoria (Chart.js embutido localmente)
- [x] **RPT-02**: Relatório exibe lista de achados com snippet de código por finding
- [ ] **RPT-03**: Relatório exibe explicações e sugestões de correção da IA quando disponíveis
- [ ] **RPT-04**: Relatório abre automaticamente no browser local após o scan
- [ ] **RPT-05**: Usuário pode exportar o relatório para PDF

### GUI — CustomTkinter

- [x] **GUI-01**: Janela principal permite selecionar pasta local ou informar URL Git, com listagem de análises disponíveis por plano e botão de iniciar scan
- [ ] **GUI-02**: Tela de progresso exibe log em tempo real durante o scan (nunca parece travado)
- [x] **GUI-03**: Tela de configurações permite inserir e salvar o token Groq
- [ ] **GUI-04**: Interface tem design dark, moderno, com logo e badge de plano (sempre mostra "DEV" em modo de desenvolvimento)
- [x] **GUI-05**: `DEV_MODE=True` habilita todas as funcionalidades do plano TEAM sem validação de licença

### Integração e polish

- [ ] **INT-01**: Fluxo completo funciona de ponta a ponta: GUI → Scanner → Relatório
- [ ] **INT-02**: Scan de projeto com 500 arquivos conclui em menos de 3 minutos
- [ ] **INT-03**: Erros comuns (pasta inválida, ferramentas ausentes, timeout de rede) exibem mensagens amigáveis na GUI sem jargão técnico
- [ ] **INT-04**: Testes de integração cobrem o fluxo end-to-end

### Licença (Fase 6 — somente após Fases 1–5 funcionando)

- [ ] **LIC-01**: Backend de licença valida JWT + device fingerprint via FastAPI + Supabase (Railway)
- [ ] **LIC-02**: App funciona offline por até 72 horas após última validação bem-sucedida
- [ ] **LIC-03**: Plano FREE: scan de secrets/chaves, máximo 100 arquivos, sem PDF, sem IA
- [ ] **LIC-04**: Plano PRO ($9/mês): SAST completo, CVEs, PDF, IA, arquivos ilimitados, 1 dispositivo
- [ ] **LIC-05**: Plano TEAM ($29/mês): tudo do PRO + 5 dispositivos + IaC + regras customizadas
- [ ] **LIC-06**: Integração com Stripe para cobrança recorrente

### Build e distribuição (Fase 7 — última fase)

- [ ] **BUILD-01**: App compila para `.exe` Windows via PyInstaller (`--onedir`) com binários dos scanners embutidos
- [ ] **BUILD-02**: App compila para binário Linux (Ubuntu 20.04+)
- [ ] **BUILD-03**: Código Python é ofuscado via PyArmor antes do build final
- [ ] **BUILD-04**: GitHub Actions executa build automatizado e publica release no GitHub Releases

## v2 Requirements

### Social e colaboração

- **COLLAB-01**: Login via OAuth GitHub/GitLab
- **COLLAB-02**: Compartilhamento de relatório via link público
- **COLLAB-03**: Dashboard web com histórico de scans

### IDE e CI/CD

- **IDE-01**: Plugin para VS Code / Cursor com scan inline
- **CICD-01**: Integração com GitHub Actions / GitLab CI como step de pipeline

### Histórico e delta

- **HIST-01**: Histórico de scans anteriores com comparação de delta (achados novos vs. resolvidos)
- **HIST-02**: Gráfico de evolução de segurança ao longo do tempo

## Out of Scope

| Feature | Motivo |
|---------|--------|
| App mobile (iOS/Android) | Plataforma errada para o público-alvo |
| Dashboard web (v1) | Desktop-first; cloud destrói o diferencial de privacidade local |
| Auto-fix / patch automático | Alta responsabilidade; adiar até qualidade de IA ser comprovada |
| Scan em tempo real (watch mode) | Complexidade desnecessária para v1 |
| Regras SAST customizadas no FREE/PRO | Reservado para TEAM; complexidade de UX alta |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCAN-01 | Phase 1 | Complete |
| SCAN-02 | Phase 1 | Complete |
| SCAN-03 | Phase 1 | Complete |
| BACK-01 | Phase 1 | Complete |
| BACK-02 | Phase 1 | Pending |
| BACK-03 | Phase 1 | Complete |
| BACK-04 | Phase 1 | Pending |
| BACK-05 | Phase 1 | Complete |
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| GUI-01 | Phase 2 | Complete |
| GUI-02 | Phase 2 | Pending |
| GUI-03 | Phase 2 | Complete |
| GUI-04 | Phase 2 | Pending |
| GUI-05 | Phase 2 | Complete |
| RPT-01 | Phase 3 | Complete |
| RPT-02 | Phase 3 | Complete |
| RPT-03 | Phase 3 | Pending |
| RPT-04 | Phase 3 | Pending |
| RPT-05 | Phase 3 | Pending |
| AI-01 | Phase 4 | Complete |
| AI-02 | Phase 4 | Complete |
| AI-03 | Phase 4 | Complete |
| AI-04 | Phase 4 | Complete |
| INT-01 | Phase 5 | Pending |
| INT-02 | Phase 5 | Pending |
| INT-03 | Phase 5 | Pending |
| INT-04 | Phase 5 | Pending |
| LIC-01 | Phase 6 | Pending |
| LIC-02 | Phase 6 | Pending |
| LIC-03 | Phase 6 | Pending |
| LIC-04 | Phase 6 | Pending |
| LIC-05 | Phase 6 | Pending |
| LIC-06 | Phase 6 | Pending |
| BUILD-01 | Phase 7 | Pending |
| BUILD-02 | Phase 7 | Pending |
| BUILD-03 | Phase 7 | Pending |
| BUILD-04 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 35 total
- Mapped to phases: 35
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-29*
*Last updated: 2026-03-29 — traceability corrected to match roadmap build order (GUI Phase 2, RPT Phase 3, AI Phase 4, INT Phase 5)*
