"""ResultsScreen — scan summary with per-scanner finding count cards, severity filter buttons,
scrollable findings list, and FindingDetailModal popup."""
from __future__ import annotations

import threading
from collections import Counter
from tkinter import messagebox
from typing import Callable, Optional

import customtkinter as ctk

from app.core.models import ScanResult
from app.config import load_groq_token
from app.ai.enricher import AIEnricher
from app.gui.theme import (
    BG_PRIMARY,
    BG_CARD,
    BG_BORDER,
    ACCENT_RED,
    ACCENT_RED_HOVER,
    ACCENT_TEAL,
    ACCENT_TEAL_HOVER,
    ACCENT_GREEN,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    STATUS_PENDING,
    font_heading,
    font_body,
    font_mono,
)
from app.report.generator import generate_report

# ---------------------------------------------------------------------------
# Severity display configuration
# ---------------------------------------------------------------------------
SEVERITY_COLOR = {
    "critical": "#e63946",
    "high":     "#ff6b35",
    "medium":   "#ffd166",
    "low":      "#06d6a0",
    "info":     "#888888",
}
SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


class ResultsScreen(ctk.CTkFrame):
    """Results summary screen: total finding count, per-scanner cards, scan info, and navigation."""

    def __init__(self, master: ctk.CTkBaseClass, nav_callback: Callable, **kwargs) -> None:
        super().__init__(master, fg_color=BG_PRIMARY, **kwargs)
        self._navigate = nav_callback
        self._result: Optional[ScanResult] = None
        self._cards_frame: Optional[ctk.CTkFrame] = None

        # Findings list state
        self._active_filters: set[str] = set(SEVERITY_ORDER)  # all active by default
        self._filter_buttons: dict[str, ctk.CTkButton] = {}
        self._finding_rows: list[tuple[str, ctk.CTkFrame]] = []  # (severity, frame)
        self._findings_scroll: Optional[ctk.CTkScrollableFrame] = None

        # AI enrichment state
        self._enricher: Optional[AIEnricher] = None
        self._open_modal: Optional[FindingDetailModal] = None
        self._ai_complete = False
        self._has_token = False

        self._build_static()

    def _build_static(self) -> None:
        """Create the fixed layout elements."""
        # 1. Title
        self._title = ctk.CTkLabel(
            self,
            text="Resultado do Scan",
            font=font_heading(22),
            text_color=TEXT_PRIMARY,
        )
        self._title.pack(pady=(24, 8))

        # 2. Total count label (large red number)
        self._total_label = ctk.CTkLabel(
            self,
            text="--",
            font=font_heading(32),
            text_color=ACCENT_RED,
        )
        self._total_label.pack(pady=(4, 16))

        # 3. Cards container (populated dynamically in on_show)
        self._cards_frame = ctk.CTkFrame(self, fg_color=BG_PRIMARY)
        self._cards_frame.pack(pady=(0, 4))

        # 4. Scan info label
        self._info_label = ctk.CTkLabel(
            self,
            text="",
            font=font_body(12),
            text_color=TEXT_SECONDARY,
        )
        self._info_label.pack(pady=(12, 4))

        # 5. Severity filter bar
        self._filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        self._filter_bar.pack(pady=(8, 4))

        filter_label = ctk.CTkLabel(
            self._filter_bar,
            text="Filtrar:",
            font=font_body(12),
            text_color=TEXT_SECONDARY,
        )
        filter_label.pack(side="left", padx=(0, 8))

        for level in SEVERITY_ORDER:
            color = SEVERITY_COLOR[level]
            btn = ctk.CTkButton(
                self._filter_bar,
                text=level.capitalize(),
                fg_color=color,
                hover_color=color,
                text_color="#111111",
                width=72,
                height=26,
                corner_radius=4,
                font=font_body(11),
                command=lambda lv=level: self._toggle_filter(lv),
            )
            btn.pack(side="left", padx=3)
            self._filter_buttons[level] = btn

        # 6. Scrollable findings container
        self._findings_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=BG_BORDER,
            height=280,
        )
        self._findings_scroll.pack(fill="x", padx=32, pady=(4, 8))

        # 7. Buttons row
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.pack(pady=(16, 24))

        ctk.CTkButton(
            buttons_frame,
            text="Novo Scan",
            fg_color=ACCENT_TEAL,
            hover_color=ACCENT_TEAL_HOVER,
            text_color="#ffffff",
            width=160,
            height=40,
            corner_radius=6,
            command=lambda: self._navigate("home"),
        ).pack(side="left", padx=(0, 12))

        self._report_btn = ctk.CTkButton(
            buttons_frame,
            text="Ver Relatório Completo",
            fg_color=BG_CARD,
            border_width=1,
            border_color=ACCENT_TEAL,
            text_color=ACCENT_TEAL,
            hover_color=BG_BORDER,
            width=200,
            height=40,
            corner_radius=6,
            state="disabled",
            command=self._open_report,
        )
        self._report_btn.pack(side="left", padx=(0, 12))


    def on_show(self, scan_result: Optional[ScanResult] = None, **kwargs) -> None:
        """Called by RCheckApp.show_screen — populates cards with results."""
        self._result = scan_result

        # Clear old cards
        if self._cards_frame:
            for widget in self._cards_frame.winfo_children():
                widget.destroy()

        if not scan_result:
            self._total_label.configure(text="Sem resultado")
            self._info_label.configure(text="")
            if hasattr(self, '_report_btn'):
                self._report_btn.configure(state="disabled")
            return

        total = len(scan_result.findings)
        self._total_label.configure(text=f"{total} findings")

        # Per-scanner breakdown
        counts: Counter = Counter()
        for f in scan_result.findings:
            for t in f.tool:
                counts[t] += 1
        for tool in scan_result.tools_used:
            count = counts.get(tool, 0)
            self._create_tool_card(tool, count)

        # Scan info
        duration = f"{scan_result.scan_duration_seconds:.1f}s"
        files = scan_result.scanned_files
        self._info_label.configure(
            text=f"{files} arquivos analisados em {duration}"
        )

        # Build findings list (sorted Critical-first)
        self._build_findings_list(scan_result.findings)

        if hasattr(self, '_report_btn'):
            self._report_btn.configure(state="normal")

        # Reset all filter buttons to active state
        self._active_filters = set(SEVERITY_ORDER)
        for level, btn in self._filter_buttons.items():
            color = SEVERITY_COLOR[level]
            btn.configure(fg_color=color, hover_color=color, text_color="#111111")

        # AI enrichment (async, daemon thread)
        self._ai_complete = False
        token = load_groq_token()
        self._has_token = bool(token)
        if token:
            self._enricher = AIEnricher(token)
            # Defer by one frame to let on_show() complete first (Pitfall 4)
            self.after(0, lambda: self._enricher.enrich_async(
                scan_result,
                on_finding_enriched=lambda f: self.after(0, lambda f=f: self._on_finding_enriched(f)),
                on_complete=lambda: self.after(0, self._on_ai_complete),
            ))

    def _on_finding_enriched(self, finding) -> None:
        """Called on main thread when one finding's AI content is ready."""
        # Update open modal if it shows this finding
        if (self._open_modal
                and self._open_modal.winfo_exists()
                and hasattr(self._open_modal, '_finding')
                and self._open_modal._finding is finding):
            self._open_modal.update_ai_content(finding)

    def _on_ai_complete(self) -> None:
        """Called on main thread when all AI enrichment is done."""
        self._ai_complete = True

    def _open_report(self) -> None:
        """Generate HTML report and open in browser. Runs in daemon thread (off Tkinter thread)."""
        if not self._result:
            return
        result = self._result

        def _run():
            try:
                generate_report(result, open_browser=True)
            except Exception as exc:
                # Schedule error dialog on main thread
                self.after(0, lambda: messagebox.showerror("Erro", f"Falha ao gerar relatório:\n{exc}"))

        threading.Thread(target=_run, daemon=True).start()

    def _create_tool_card(self, tool_name: str, count: int) -> None:
        """Create a per-scanner finding count card."""
        card = ctk.CTkFrame(
            self._cards_frame,
            fg_color=BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=BG_BORDER,
            width=180,
            height=90,
        )
        card.pack_propagate(False)
        card.pack(side="left", padx=8, pady=8)

        ctk.CTkLabel(
            card,
            text=tool_name.capitalize(),
            font=font_body(13),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(12, 2))

        color = ACCENT_RED if count > 0 else ACCENT_TEAL
        ctk.CTkLabel(
            card,
            text=str(count),
            font=font_heading(24),
            text_color=color,
        ).pack(pady=(2, 4))

        ctk.CTkLabel(
            card,
            text="findings",
            font=font_body(10),
            text_color=TEXT_SECONDARY,
        ).pack()

    # ------------------------------------------------------------------
    # Findings list methods
    # ------------------------------------------------------------------

    def _toggle_filter(self, level: str) -> None:
        """Toggle a severity filter and refresh the list."""
        if level in self._active_filters:
            self._active_filters.discard(level)
            # dim the button to show inactive state
            self._filter_buttons[level].configure(
                fg_color=BG_BORDER, hover_color=BG_BORDER, text_color=TEXT_MUTED
            )
        else:
            self._active_filters.add(level)
            color = SEVERITY_COLOR[level]
            self._filter_buttons[level].configure(
                fg_color=color, hover_color=color, text_color="#111111"
            )
        self._apply_filter()

    def _apply_filter(self) -> None:
        """Show or hide finding rows based on active_filters."""
        for severity, row_frame in self._finding_rows:
            if severity in self._active_filters:
                row_frame.pack(fill="x", padx=4, pady=2)
            else:
                row_frame.pack_forget()

    def _build_findings_list(self, findings: list) -> None:
        """Populate the scrollable findings list. Call from on_show() after clearing."""
        # Clear existing rows
        self._finding_rows.clear()
        if self._findings_scroll:
            for w in self._findings_scroll.winfo_children():
                w.destroy()

        # Sort Critical-first
        sorted_findings = sorted(
            findings,
            key=lambda f: SEVERITY_ORDER.index(f.severity.value)
        )

        for finding in sorted_findings:
            sev = finding.severity.value
            color = SEVERITY_COLOR.get(sev, "#888888")

            row = ctk.CTkFrame(
                self._findings_scroll,
                fg_color=BG_PRIMARY,
                corner_radius=4,
                border_width=1,
                border_color=BG_BORDER,
                height=36,
            )
            row.pack_propagate(False)

            # Severity badge
            badge = ctk.CTkLabel(
                row,
                text=sev.upper(),
                fg_color=color,
                text_color="#111111",
                font=font_body(10),
                width=70,
                corner_radius=3,
            )
            badge.pack(side="left", padx=(6, 8), pady=4)

            # Title
            title_lbl = ctk.CTkLabel(
                row,
                text=finding.title[:60] + ("..." if len(finding.title) > 60 else ""),
                font=font_body(12),
                text_color=TEXT_PRIMARY,
                anchor="w",
            )
            title_lbl.pack(side="left", fill="x", expand=True, padx=(0, 8))

            # File:line
            file_lbl = ctk.CTkLabel(
                row,
                text=f"{finding.file_path.split('/')[-1]}:{finding.line_number}",
                font=font_body(11),
                text_color=TEXT_SECONDARY,
            )
            file_lbl.pack(side="right", padx=(0, 8))

            # Bind click to open modal
            for widget in (row, badge, title_lbl, file_lbl):
                widget.bind("<Button-1>", lambda e, f=finding: self._open_finding_modal(f))

            self._finding_rows.append((sev, row))
            row.pack(fill="x", padx=4, pady=2)

    def _open_finding_modal(self, finding) -> None:
        """Open FindingDetailModal for the given finding."""
        self._open_modal = FindingDetailModal(
            self.winfo_toplevel(), finding, has_token=self._has_token
        )


# ---------------------------------------------------------------------------
# FindingDetailModal
# ---------------------------------------------------------------------------

class FindingDetailModal(ctk.CTkToplevel):
    """Popup modal showing full finding detail: title, severity, file:line, snippet, description.
    Per D-06: opens as CTkToplevel over the main window.
    Per D-07: uses Rakoon dark theme (BG_PRIMARY, BG_CARD, ACCENT_RED/TEAL).
    """

    def __init__(self, master, finding, has_token: bool = False) -> None:
        super().__init__(master, fg_color=BG_PRIMARY)
        self.title("Detalhe do Finding")
        self.geometry("700x750")
        self.resizable(False, False)
        # Grab focus so modal behaves as dialog
        self.grab_set()
        self.lift()
        self.focus_force()
        self._finding = finding
        self._has_token = has_token
        self._build(finding)

    def _build(self, finding) -> None:
        sev = finding.severity.value
        sev_color = SEVERITY_COLOR.get(sev, "#888888")

        # Header row: severity badge + title
        header = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            header,
            text=sev.upper(),
            fg_color=sev_color,
            text_color="#111111",
            font=font_body(11),
            width=80,
            corner_radius=0,
        ).pack(side="left", padx=(16, 12), pady=12)

        ctk.CTkLabel(
            header,
            text=finding.title,
            font=font_heading(14),
            text_color=TEXT_PRIMARY,
            anchor="w",
            wraplength=540,
        ).pack(side="left", fill="x", expand=True, pady=12)

        # File:line
        ctk.CTkLabel(
            self,
            text=f"{finding.file_path}  :  linha {finding.line_number}",
            font=font_body(11),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(10, 4))

        # Snippet (monospace, dark background)
        snippet_frame = ctk.CTkFrame(
            self, fg_color=BG_CARD, corner_radius=6, border_width=1, border_color=BG_BORDER
        )
        snippet_frame.pack(fill="x", padx=16, pady=(0, 8))

        snippet_text = ctk.CTkTextbox(
            snippet_frame,
            font=font_mono(12),
            fg_color=BG_CARD,
            text_color="#a9b1d6",
            height=140,
            wrap="none",
            activate_scrollbars=True,
        )
        snippet_text.pack(fill="x", padx=8, pady=8)
        snippet_text.insert("end", finding.snippet or "(sem snippet)")
        snippet_text.configure(state="disabled")

        # Description
        ctk.CTkLabel(
            self,
            text="Descricao:",
            font=font_body(12),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(4, 2))

        desc_text = ctk.CTkTextbox(
            self,
            font=font_body(12),
            fg_color=BG_CARD,
            text_color=TEXT_PRIMARY,
            height=100,
            wrap="word",
        )
        desc_text.pack(fill="x", padx=16, pady=(0, 8))
        desc_text.insert("end", finding.description or "(sem descricao)")
        desc_text.configure(state="disabled")

        # AI Explanation section
        ctk.CTkLabel(
            self,
            text="Explicacao IA:",
            font=font_body(12),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(8, 2))

        self._ai_explanation_box = ctk.CTkTextbox(
            self,
            font=font_body(12),
            fg_color=BG_CARD,
            text_color=TEXT_PRIMARY,
            height=80,
            wrap="word",
        )
        self._ai_explanation_box.pack(fill="x", padx=16, pady=(0, 4))
        if finding.ai_explanation:
            self._ai_explanation_box.insert("end", finding.ai_explanation)
        elif self._has_token:
            self._ai_explanation_box.insert("end", "Buscando explicacao IA...")
            self._ai_explanation_box.configure(text_color=TEXT_MUTED)
        else:
            self._ai_explanation_box.insert("end", "IA indisponivel — configure o token em Configuracoes")
            self._ai_explanation_box.configure(text_color=TEXT_MUTED)
        self._ai_explanation_box.configure(state="disabled")

        # AI Fix Suggestion section
        ctk.CTkLabel(
            self,
            text="Sugestao de Correcao:",
            font=font_body(12),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(4, 2))

        self._ai_fix_box = ctk.CTkTextbox(
            self,
            font=font_body(12),
            fg_color=BG_CARD,
            text_color=TEXT_PRIMARY,
            height=80,
            wrap="word",
        )
        self._ai_fix_box.pack(fill="x", padx=16, pady=(0, 4))
        if finding.ai_fix_suggestion:
            self._ai_fix_box.insert("end", finding.ai_fix_suggestion)
        elif self._has_token:
            self._ai_fix_box.insert("end", "Buscando sugestao...")
            self._ai_fix_box.configure(text_color=TEXT_MUTED)
        else:
            self._ai_fix_box.insert("end", "IA indisponivel — configure o token em Configuracoes")
            self._ai_fix_box.configure(text_color=TEXT_MUTED)
        self._ai_fix_box.configure(state="disabled")

        # Footer: Fechar button
        ctk.CTkButton(
            self,
            text="Fechar",
            fg_color=ACCENT_TEAL,
            hover_color=ACCENT_TEAL_HOVER,
            text_color="#ffffff",
            width=120,
            height=36,
            corner_radius=6,
            command=self.destroy,
        ).pack(pady=(4, 16))

    def update_ai_content(self, finding) -> None:
        """Update AI sections after enrichment. Must be called from main thread."""
        if not self.winfo_exists():
            return
        if finding.ai_explanation:
            self._ai_explanation_box.configure(state="normal")
            self._ai_explanation_box.delete("1.0", "end")
            self._ai_explanation_box.insert("end", finding.ai_explanation)
            self._ai_explanation_box.configure(text_color=TEXT_PRIMARY)
            self._ai_explanation_box.configure(state="disabled")
        if finding.ai_fix_suggestion:
            self._ai_fix_box.configure(state="normal")
            self._ai_fix_box.delete("1.0", "end")
            self._ai_fix_box.insert("end", finding.ai_fix_suggestion)
            self._ai_fix_box.configure(text_color=TEXT_PRIMARY)
            self._ai_fix_box.configure(state="disabled")
