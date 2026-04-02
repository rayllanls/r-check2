# Phase 3: Results Display + HTML Report - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in CONTEXT.md — this log preserves the discussion.

**Date:** 2026-03-31
**Phase:** 03-results-display-html-report
**Mode:** discuss
**Areas discussed:** ResultsScreen scope, Finding detail interaction, HTML report theme, PDF export

## Gray Areas Presented

### ResultsScreen — Estrutura da tela
| Opção | Descrição |
|-------|-----------|
| A (chosen) | Expandir a tela atual — cards no topo + lista abaixo, tela única |
| B | Nova tela separada (FindingsScreen) |
| C | Substituir cards pela lista diretamente |

### Finding detail — Interação de clique
| Opção | Descrição |
|-------|-----------|
| A | Expand inline (accordion) |
| B (chosen) | Modal/popup (CTkToplevel) |
| C | Painel lateral |

### HTML Report — Visual
| Opção | Descrição |
|-------|-----------|
| A | Dark Rakoon (consistente com app) |
| B (chosen) | Light / fundo branco — imprime bem, aspecto profissional |
| C | Dark para tela + @media print claro |

### PDF Export — Implementação
| Opção | Descrição |
|-------|-----------|
| A | WeasyPrint na GUI (path fixo) |
| B | window.print() no HTML |
| C (chosen) | WeasyPrint + filedialog (usuário escolhe onde salvar) |

## Corrections Made

Nenhuma — usuário confirmou as opções apresentadas diretamente.

## Decisions Applied

- D-01 a D-05: ResultsScreen expandida, lista Critical-first, filtros como botões toggle
- D-06 a D-07: Modal CTkToplevel com tema dark da app
- D-08 a D-13: Report light theme, Chart.js bundled, doughnut chart, tabela com expand
- D-14 a D-17: WeasyPrint em thread + filedialog, nome padrão com data
