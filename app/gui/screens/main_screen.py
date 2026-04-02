"""HomeScreen — target selection (pasta local OU URL git), scanner list, Start Scan."""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk
from tkinter import filedialog

from app.config import DEV_MODE, DEV_PLAN, PLAN_TOOLS
from app.gui.theme import (
    BG_PRIMARY,
    BG_CARD,
    BG_BORDER,
    BG_INPUT,
    ACCENT_PRIMARY,
    ACCENT_PRIMARY_HOVER,
    ACCENT_SECONDARY_HOVER,
    ACCENT_RED,
    ACCENT_RED_HOVER,
    ACCENT_PURPLE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    font_heading,
    font_body,
    font_mono,
)

_TOOL_INFO = {
    "semgrep":    ("SAST", "Analisa padrões no código-fonte para encontrar falhas de segurança como injeção de SQL, XSS e uso de funções inseguras."),
    "trufflehog": ("SEC",  "Varre o histórico Git e o código em busca de credenciais, tokens de API e segredos expostos acidentalmente."),
    "grype":      ("SCA",  "Verifica dependências do projeto contra bancos de CVEs para encontrar pacotes com vulnerabilidades conhecidas."),
    "gitleaks":   ("GIT",  "Detecta segredos e chaves sensíveis no repositório Git, incluindo commits antigos e branches remotas."),
    "trivy":      ("IaC",  "Scanner multi-propósito: encontra CVEs em dependências, problemas em arquivos de infraestrutura (Terraform, Docker) e segredos no código."),
    "checkov":    ("CFG",  "Analisa arquivos de infraestrutura como código (Terraform, Kubernetes, Dockerfile) em busca de má configuração de segurança."),
}


class HomeScreen(ctk.CTkFrame):
    """Tela principal com seletor de modo, lista de scanners e botão de scan."""

    def __init__(self, master: ctk.CTkBaseClass, nav_callback: Callable, **kwargs) -> None:
        super().__init__(master, fg_color=BG_PRIMARY, **kwargs)
        self._navigate = nav_callback
        self._plan: str = DEV_PLAN if DEV_MODE else "free"
        self._mode = ctk.StringVar(value="  Pasta local  ")
        self._tooltip = None
        self._build()

    # ──────────────────────────────────────────────
    # Build
    # ──────────────────────────────────────────────

    def _build(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color=BG_PRIMARY, scrollbar_button_color=BG_BORDER)
        scroll.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(scroll, fg_color=BG_PRIMARY)
        inner.pack(fill="x", padx=48, pady=(32, 32))
        inner.columnconfigure(0, weight=1)

        # 1. Título
        title_frame = ctk.CTkFrame(inner, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", pady=(0, 24))

        ctk.CTkLabel(
            title_frame, text="Novo Scan.",
            font=font_heading(42), text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            title_frame,
            text="Analise código local ou repositório Git em busca de vulnerabilidades.",
            font=font_body(15), text_color=TEXT_SECONDARY,
        ).pack(anchor="w")

        # row placeholder
        ctk.CTkFrame(inner, fg_color="transparent", height=1).grid(row=1, column=0)

        # 2. Card de alvo
        target_card = ctk.CTkFrame(
            inner, fg_color=BG_CARD, corner_radius=16,
            border_width=1, border_color=BG_BORDER,
        )
        target_card.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        target_card.columnconfigure(0, weight=1)

        # Toggle modo
        toggle_row = ctk.CTkFrame(target_card, fg_color="transparent")
        toggle_row.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 16))

        ctk.CTkLabel(
            toggle_row, text="Origem",
            font=font_body(13), text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 16))

        ctk.CTkSegmentedButton(
            toggle_row,
            values=["  Pasta local  ", "  URL Git  "],
            variable=self._mode,
            command=self._on_mode_change,
            fg_color=BG_INPUT,
            selected_color=ACCENT_PRIMARY,
            selected_hover_color=ACCENT_PRIMARY_HOVER,
            unselected_color=BG_INPUT,
            unselected_hover_color=BG_BORDER,
            text_color=TEXT_PRIMARY,
            font=font_body(13),
            corner_radius=8,
        ).pack(side="left")

        # Frame pasta local
        self._local_frame = ctk.CTkFrame(target_card, fg_color="transparent")
        self._local_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 4))
        self._local_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self._local_frame, text="Caminho da pasta",
            font=font_body(13), text_color=TEXT_SECONDARY,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self._path_entry = ctk.CTkEntry(
            self._local_frame,
            fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
            border_color=BG_BORDER, border_width=1,
            corner_radius=10,
            placeholder_text="/caminho/do/projeto",
            font=font_mono(13), height=42,
        )
        self._path_entry.grid(row=1, column=0, sticky="ew", padx=(0, 12))

        ctk.CTkButton(
            self._local_frame,
            text="Selecionar",
            fg_color=BG_BORDER, hover_color=ACCENT_SECONDARY_HOVER,
            text_color=TEXT_PRIMARY, font=font_mono(12),
            width=120, height=42, corner_radius=8,
            command=self._browse_folder,
        ).grid(row=1, column=1, padx=(10, 0))

        ctk.CTkFrame(self._local_frame, fg_color="transparent", height=20).grid(row=2, column=0)

        # Frame URL git (oculto por padrão)
        self._git_frame = ctk.CTkFrame(target_card, fg_color="transparent")
        self._git_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 4))
        self._git_frame.columnconfigure(0, weight=1)
        self._git_frame.grid_remove()

        ctk.CTkLabel(
            self._git_frame, text="URL do repositório",
            font=font_body(13), text_color=TEXT_SECONDARY,
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        self._url_entry = ctk.CTkEntry(
            self._git_frame,
            fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
            border_color=BG_BORDER, border_width=1,
            corner_radius=10,
            placeholder_text="https://github.com/usuario/repositorio",
            font=font_mono(13), height=42,
        )
        self._url_entry.grid(row=1, column=0, sticky="ew")
        ctk.CTkFrame(self._git_frame, fg_color="transparent", height=20).grid(row=2, column=0)

        # 3. Card de scanners
        scanner_card = ctk.CTkFrame(
            inner, fg_color=BG_CARD, corner_radius=16,
            border_width=1, border_color=BG_BORDER,
        )
        scanner_card.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        scanner_card.columnconfigure((0, 1, 2), weight=1)

        header_row = ctk.CTkFrame(scanner_card, fg_color="transparent")
        header_row.grid(row=0, column=0, columnspan=3, sticky="ew", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            header_row, text="Ferramentas ativas",
            font=font_heading(15), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            header_row, text="clique para saber mais",
            font=font_body(11), text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(12, 0), pady=(2, 0))

        tools = PLAN_TOOLS[self._plan]
        for i, tool in enumerate(tools):
            col = i % 3
            row = 1 + i // 3
            abbr, desc = _TOOL_INFO.get(tool, ("?", "Ferramenta de análise de segurança."))
            self._make_tool_chip(scanner_card, tool, abbr, desc, row, col)

        ctk.CTkFrame(scanner_card, fg_color="transparent", height=14).grid(
            row=1 + (len(tools) - 1) // 3 + 1, column=0, columnspan=3
        )

        # 4. Linha inferior
        bottom_row = ctk.CTkFrame(inner, fg_color="transparent")
        bottom_row.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        bottom_row.columnconfigure(0, weight=1)

        ctk.CTkButton(
            bottom_row, text="Configurações",
            fg_color="transparent", text_color=TEXT_SECONDARY,
            hover_color=BG_CARD, font=font_body(13),
            command=lambda: self._navigate("settings"),
        ).pack(side="left")

        ctk.CTkButton(
            bottom_row, text="  Iniciar Scan  ",
            fg_color=ACCENT_PRIMARY, hover_color=ACCENT_PRIMARY_HOVER,
            text_color="#ffffff", font=font_heading(16),
            height=48, corner_radius=12,
            command=self._start_scan,
        ).pack(side="right")

    def _make_tool_chip(
        self, parent, tool: str, abbr: str, desc: str, row: int, col: int
    ) -> None:
        chip = ctk.CTkFrame(
            parent, fg_color=BG_INPUT, corner_radius=12,
            border_width=1, border_color=BG_BORDER,
            cursor="hand2",
        )
        chip.grid(row=row, column=col, sticky="ew", padx=10, pady=5)

        content = ctk.CTkFrame(chip, fg_color="transparent")
        content.pack(fill="x", padx=14, pady=12)

        # Badge colorido com abreviação
        badge = ctk.CTkLabel(
            content, text=abbr,
            fg_color="#181625", text_color=ACCENT_PURPLE,
            corner_radius=6,
            font=font_mono(11),
            width=40, height=24,
        )
        badge.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            content, text=tool.capitalize(),
            font=font_body(13), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        # Tooltip ao passar o mouse
        for widget in (chip, content, badge):
            widget.bind("<Enter>", lambda e, t=tool, d=desc: self._show_tooltip(e, t, d))
            widget.bind("<Leave>", lambda e: self._schedule_hide_tooltip())

    # ──────────────────────────────────────────────
    # Callbacks
    # ──────────────────────────────────────────────

    def _on_mode_change(self, value: str) -> None:
        if value.strip() == "Pasta local":
            self._git_frame.grid_remove()
            self._local_frame.grid()
        else:
            self._local_frame.grid_remove()
            self._git_frame.grid()

    def _browse_folder(self) -> None:
        path = filedialog.askdirectory(title="Selecione a pasta do projeto")
        if path:
            self._path_entry.delete(0, "end")
            self._path_entry.insert(0, path)

    def _start_scan(self) -> None:
        if self._mode.get().strip() == "Pasta local":
            target = self._path_entry.get().strip()
        else:
            target = self._url_entry.get().strip()
        if not target:
            from tkinter import messagebox
            messagebox.showwarning("r-check", "Informe um caminho ou URL antes de iniciar.")
            return
        self._navigate("progress", target=target, plan=self._plan)

    def _schedule_hide_tooltip(self) -> None:
        """Agenda o hide com delay para não fechar ao mover entre widgets filhos."""
        hide_id = self.after(120, self._hide_tooltip)
        self._tooltip_hide_id = hide_id

    def _show_tooltip(self, event, tool: str, desc: str) -> None:
        # Cancela hide agendado (mouse voltou ao chip)
        hide_id = getattr(self, "_tooltip_hide_id", None)
        if hide_id:
            self.after_cancel(hide_id)
            self._tooltip_hide_id = None
        self._hide_tooltip()
        tip = ctk.CTkToplevel(self)
        tip.overrideredirect(True)  # sem barra de título
        tip.attributes("-topmost", True)

        frame = ctk.CTkFrame(
            tip, fg_color=BG_CARD, corner_radius=12,
            border_width=1, border_color=BG_BORDER,
        )
        frame.pack(fill="both", expand=True, padx=1, pady=1)

        ctk.CTkLabel(
            frame, text=tool.capitalize(),
            font=font_heading(14), text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            frame, text=desc,
            font=font_body(12), text_color=TEXT_SECONDARY,
            wraplength=300, justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 12))

        # Posiciona perto do cursor
        tip.update_idletasks()
        x = event.x_root + 12
        y = event.y_root + 12
        tip.geometry(f"+{x}+{y}")
        self._tooltip = tip

    def _hide_tooltip(self) -> None:
        tip = getattr(self, "_tooltip", None)
        if tip and tip.winfo_exists():
            tip.destroy()
        self._tooltip = None

    def get_target(self) -> str:
        """Retorna o alvo atual. Usado em testes."""
        if self._mode.get().strip() == "Pasta local":
            return self._path_entry.get().strip()
        return self._url_entry.get().strip()
