"""Shared header bar — r-check brand logo + name + plan badge."""
import customtkinter as ctk
import webbrowser
from pathlib import Path
from app.config import DEV_MODE, APP_VERSION
from app.gui.theme import (
    BG_PRIMARY, BG_BORDER, ACCENT_RED, ACCENT_PURPLE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    font_heading, font_body, font_mono,
)

WEBSITE_URL = "https://rayllan.com.br/r-recon"

FAVICON_PATH = Path(__file__).resolve().parents[3] / "app" / "favicon.svg"


class HeaderBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=BG_PRIMARY, height=64, **kwargs)
        self.configure(border_width=0)
        self._sep = ctk.CTkFrame(master, fg_color=BG_BORDER, height=1)
        self.pack_propagate(False)
        self._build()

    def _build(self) -> None:
        # Logo: ">_" em vermelho (símbolo terminal do SVG)
        ctk.CTkLabel(
            self, text=">_",
            font=ctk.CTkFont(family="JetBrains Mono", size=18, weight="bold"),
            text_color=ACCENT_RED,
        ).pack(side="left", padx=(20, 6), pady=12)

        # Nome: "r-" roxo + "check" branco
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(side="left", pady=12)

        ctk.CTkLabel(
            name_frame, text="r-",
            font=font_heading(22), text_color=ACCENT_PURPLE,
        ).pack(side="left")

        ctk.CTkLabel(
            name_frame, text="check",
            font=font_heading(22), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        # Versão
        ctk.CTkLabel(
            self, text=f"v{APP_VERSION}",
            font=font_body(11), text_color=TEXT_MUTED,
        ).pack(side="left", padx=(8, 0), pady=(20, 12))

        # Link do site
        site_btn = ctk.CTkLabel(
            self, text="rayllan.com.br/r-recon",
            font=font_body(11), text_color=TEXT_SECONDARY,
            cursor="hand2",
        )
        site_btn.pack(side="right", padx=(0, 20), pady=12)
        site_btn.bind("<Button-1>", lambda e: webbrowser.open(WEBSITE_URL))
        site_btn.bind("<Enter>", lambda e: site_btn.configure(text_color=ACCENT_PURPLE))
        site_btn.bind("<Leave>", lambda e: site_btn.configure(text_color=TEXT_SECONDARY))

        # Badge DEV
        if DEV_MODE:
            ctk.CTkLabel(
                self, text="DEV",
                fg_color=ACCENT_RED, text_color="#ffffff",
                corner_radius=4,
                font=ctk.CTkFont(family="JetBrains Mono", size=10, weight="bold"),
                width=40, height=22,
            ).pack(side="right", padx=(20, 8), pady=21)
