"""SettingsScreen — Groq API token entry and persistence."""
from __future__ import annotations

import json
from typing import Callable

import customtkinter as ctk

from app.config import CONFIG_DIR, CONFIG_FILE
from app.gui.theme import (
    BG_PRIMARY,
    BG_CARD,
    BG_BORDER,
    BG_INPUT,
    ACCENT_RED,
    ACCENT_RED_HOVER,
    ACCENT_TEAL,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    font_heading,
    font_body,
)


class SettingsScreen(ctk.CTkFrame):
    """Settings screen with Groq token entry and save to ~/.r-check/config.json."""

    def __init__(self, master: ctk.CTkBaseClass, nav_callback: Callable, **kwargs) -> None:
        super().__init__(master, fg_color=BG_PRIMARY, **kwargs)
        self._navigate = nav_callback
        self._build()

    def _build(self) -> None:
        # 1. Back button (top-left)
        ctk.CTkButton(
            self,
            text="< Voltar",
            fg_color="transparent",
            text_color=ACCENT_TEAL,
            hover_color=BG_CARD,
            command=lambda: self._navigate("home"),
        ).pack(anchor="w", pady=(16, 8), padx=16)

        # 2. Section title
        ctk.CTkLabel(
            self,
            text="Configuracoes",
            font=font_heading(22),
            text_color=TEXT_PRIMARY,
        ).pack(pady=(8, 16))

        # 3. Groq token card
        token_card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=BG_BORDER,
        )
        token_card.pack(fill="x", padx=32, pady=(0, 16))

        ctk.CTkLabel(
            token_card,
            text="Token Groq API",
            font=font_body(14),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=24, pady=(16, 2))

        ctk.CTkLabel(
            token_card,
            text="(usado para explicacoes de IA — Phase 4)",
            font=font_body(11),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=24, pady=(0, 8))

        self._token_entry = ctk.CTkEntry(
            token_card,
            width=500,
            fg_color=BG_INPUT,
            text_color=TEXT_PRIMARY,
            border_color=BG_BORDER,
            show="*",
            placeholder_text="gsk_...",
        )
        self._token_entry.pack(anchor="w", padx=24, pady=(0, 12))

        ctk.CTkButton(
            token_card,
            text="Salvar",
            fg_color=ACCENT_RED,
            hover_color=ACCENT_RED_HOVER,
            text_color="#ffffff",
            width=100,
            command=self._save_token,
        ).pack(anchor="w", padx=24, pady=(0, 8))

        self._status_label = ctk.CTkLabel(
            token_card,
            text="",
            font=font_body(11),
            text_color=ACCENT_TEAL,
        )
        self._status_label.pack(anchor="w", padx=24, pady=(0, 16))

        # 4. GitHub Token card
        gh_card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=BG_BORDER,
        )
        gh_card.pack(fill="x", padx=32, pady=(0, 16))

        ctk.CTkLabel(
            gh_card,
            text="GitHub Personal Access Token",
            font=font_body(14),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=24, pady=(16, 2))

        ctk.CTkLabel(
            gh_card,
            text="Necessário para clonar repositórios privados",
            font=font_body(11),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=24, pady=(0, 8))

        self._gh_token_entry = ctk.CTkEntry(
            gh_card,
            width=500,
            fg_color=BG_INPUT,
            text_color=TEXT_PRIMARY,
            border_color=BG_BORDER,
            show="*",
            placeholder_text="ghp_...",
        )
        self._gh_token_entry.pack(anchor="w", padx=24, pady=(0, 12))

        ctk.CTkButton(
            gh_card,
            text="Salvar",
            fg_color=ACCENT_RED,
            hover_color=ACCENT_RED_HOVER,
            text_color="#ffffff",
            width=100,
            command=self._save_gh_token,
        ).pack(anchor="w", padx=24, pady=(0, 8))

        self._gh_status_label = ctk.CTkLabel(
            gh_card,
            text="",
            font=font_body(11),
            text_color=ACCENT_TEAL,
        )
        self._gh_status_label.pack(anchor="w", padx=24, pady=(0, 16))

    def on_show(self, **kwargs) -> None:
        """Called by RCheckApp.show_screen — loads token from disk."""
        self._load_token()

    def _load_token(self) -> None:
        try:
            if CONFIG_FILE.exists():
                data = json.loads(CONFIG_FILE.read_text())
                groq = data.get("groq_token", "")
                self._token_entry.delete(0, "end")
                if groq:
                    self._token_entry.insert(0, groq)
                gh = data.get("github_token", "")
                self._gh_token_entry.delete(0, "end")
                if gh:
                    self._gh_token_entry.insert(0, gh)
        except (json.JSONDecodeError, OSError):
            pass

    def _save_config(self, key: str, value: str, status_label: ctk.CTkLabel) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data: dict = {}
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        data[key] = value
        CONFIG_FILE.write_text(json.dumps(data, indent=2))
        status_label.configure(text="Salvo!", text_color=ACCENT_TEAL)
        self.after(2000, lambda: status_label.configure(text=""))

    def _save_token(self) -> None:
        self._save_config("groq_token", self._token_entry.get().strip(), self._status_label)

    def _save_gh_token(self) -> None:
        self._save_config("github_token", self._gh_token_entry.get().strip(), self._gh_status_label)
