# Phase 3: Results Display + HTML Report - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Exibir findings na app com filtros, gerar relatório HTML com Chart.js (offline), e exportar PDF. O usuário consegue ler todos os achados do scan — tanto na GUI quanto no relatório HTML aberto no browser. Criação de findings e execução de scan são fases anteriores.

</domain>

<decisions>
## Implementation Decisions

### ResultsScreen — Estrutura da tela

- **D-01:** Expandir a `ResultsScreen` existente — cards de resumo por scanner no topo (já implementados), lista completa de findings abaixo com scroll (`CTkScrollableFrame`), tudo numa tela única. Não criar nova tela separada.
- **D-02:** Findings ordenados Critical-first (Critical → High → Medium → Low → Info).
- **D-03:** Cada linha de finding mostra: badge de severidade colorido, título, arquivo:linha. Colunas compactas, sem snippet visível na lista.
- **D-04:** Filtros de severidade como botões toggle acima da lista (um botão por nível: Critical / High / Medium / Low / Info). Selecionar filtra a lista em tempo real. Todos ativos por padrão.
- **D-05:** Botão "Ver Relatório Completo" (atualmente disabled) passa a chamar `generate_report()` e abrir no browser.

### Finding detail — Interação de clique

- **D-06:** Clique num finding abre **modal/popup** (`CTkToplevel`) sobre a tela, mostrando: título completo, severidade, arquivo:linha, snippet de código (fonte mono, fundo escuro), descrição completa. Botão "Fechar" para dispensar.
- **D-07:** O modal usa o mesmo tema dark Rakoon da app (BG_PRIMARY, BG_CARD, ACCENT_RED/TEAL do `theme.py`).

### HTML Report — Visual

- **D-08:** Report usa **fundo branco / light theme** — profissional, legível, imprime bem para PDF. Não replica o dark theme da app.
- **D-09:** Header do report traz: logo Rakoon (inline base64), nome do projeto, data/hora do scan, total de findings.
- **D-10:** Chart.js **bundled localmente** (arquivo JS copiado para `app/report/static/chart.min.js`, injetado inline via Jinja2 `{% include %}`). Zero chamadas a CDN — funciona offline.
- **D-11:** Gráfico de distribuição por severidade: **doughnut chart** com cores: Critical=#e63946, High=#ff6b35, Medium=#ffd166, Low=#06d6a0, Info=#888888.
- **D-12:** Tabela de findings abaixo do gráfico: colunas Severidade / Título / Ferramenta / Arquivo:Linha / Snippet (truncado a 3 linhas). Clique na linha expande o snippet completo (JavaScript puro no HTML).
- **D-13:** Template Jinja2 em `app/report/templates/report.html` — substitui o stub atual.

### PDF Export — Implementação

- **D-14:** Botão "Exportar PDF" na ResultsScreen chama `export_pdf(result)` em thread separada (não bloqueia GUI).
- **D-15:** `export_pdf()` usa **WeasyPrint** para renderizar o mesmo HTML report → PDF. O HTML é gerado internamente (sem abrir browser).
- **D-16:** `tkinter.filedialog.asksaveasfilename()` abre dialog para o usuário escolher onde salvar (extensão `.pdf`, nome padrão `secscan_report_YYYYMMDD.pdf`).
- **D-17:** WeasyPrint adicionado a `requirements.txt`. Na Fase 7 (PyInstaller), o `--collect-all weasyprint` será necessário — anotar no CLAUDE.md como decisão futura.

### Claude's Discretion

- Cores exatas dos badges de severidade na GUI (manter consistência com theme.py STATUS_* se conveniente)
- Número exato de linhas visíveis na lista antes de scroll
- Animação ou transição do modal (se CTk suportar nativamente)
- CSS exato do report HTML (spacing, tipografia além das decisões acima)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Código existente a modificar/estender
- `app/gui/screens/results_screen.py` — ResultsScreen stub (cards por scanner + botão disabled); Phase 3 expande esta tela
- `app/report/generator.py` — `generate_report()` com Jinja2 + webbrowser; expandir para incluir `export_pdf()`
- `app/report/templates/report.html` — template stub a substituir completamente
- `app/core/models.py` — `Finding`, `ScanResult`, `Severity` — campos disponíveis para template e GUI
- `app/gui/theme.py` — paleta de cores e fontes Rakoon; usar para modal e badges

### Design e branding
- `rakoon_logo.png` — logo oficial (raiz do projeto); injetar inline como base64 no HTML report
- `inspiracao/index.html` — referência de estilo visual Rakoon

### Restrições do projeto
- `CLAUDE.md` — queue.Queue off main thread obrigatório; WeasyPrint deve rodar fora da thread Tkinter
- `.planning/REQUIREMENTS.md` — RPT-01 a RPT-05 (texto completo dos requisitos desta fase)
- `.planning/STATE.md` — decisões acumuladas das fases anteriores

### Dependências
- `requirements.txt` — adicionar `weasyprint` nesta fase

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/gui/theme.py` — BG_PRIMARY, BG_CARD, BG_BORDER, ACCENT_RED, ACCENT_TEAL, TEXT_PRIMARY, TEXT_SECONDARY, font_heading(), font_body(), font_mono() — usar em todo widget novo
- `app/core/models.py:ScanResult` — já tem `critical_count`, `high_count`, `medium_count` como properties; `findings` é lista ordenável por `.severity`
- `app/gui/screens/results_screen.py:ResultsScreen._cards_frame` — cards por scanner já implementados; preservar e adicionar lista abaixo
- `app/report/generator.py:generate_report()` — lógica de Jinja2 + temp file + webbrowser já funcionando; reutilizar para PDF path

### Established Patterns
- Threading: scan roda em `Thread(daemon=True)` + `root.after(100ms)` polling via queue — PDF export deve seguir o mesmo padrão (`Thread` + callback de conclusão)
- Navigation: `nav_callback` injetado na construção da tela — sem imports circulares
- Screen hook: `on_show(scan_result=...)` — ResultsScreen já recebe ScanResult ao ser exibida
- Widget pattern: `CTkScrollableFrame` já usado em outras telas para listas longas

### Integration Points
- `ResultsScreen.on_show(scan_result)` — ponto de entrada dos dados; lista de findings disponível aqui
- Botão "Ver Relatorio Completo" em `results_screen.py:84` — já existe, apenas mudar `state="disabled"` e adicionar `command`
- `generate_report()` em `app/report/generator.py` — adicionar função `export_pdf()` no mesmo módulo
- `CTkToplevel` para modal — sem setup adicional, apenas instanciar sobre a janela principal

</code_context>

<specifics>
## Specific Ideas

- Modal de finding: deve ser abrível e fechável rapidamente — usuário vai clicar em vários findings seguidos durante revisão
- Report HTML: profissional o suficiente para enviar a um gerente ou cliente — não parece um debug dump
- Exportar PDF: nome padrão do arquivo deve incluir data (`secscan_report_20260331.pdf`) para facilitar arquivamento

</specifics>

<deferred>
## Deferred Ideas

- Sorting clicável por coluna na lista de findings — Phase 5 polish
- Busca/search textual na lista de findings — backlog
- Exportar findings como CSV/JSON — backlog
- AI explanations no modal de finding — Phase 4 (campos `ai_explanation` e `ai_fix_suggestion` já existem no modelo, Phase 4 os preenche)

</deferred>

---

*Phase: 03-results-display-html-report*
*Context gathered: 2026-03-31*
