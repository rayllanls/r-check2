"""Per-scanner status row widget for the progress screen."""
import customtkinter as ctk
from app.gui.theme import (
    BG_CARD,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    STATUS_PENDING,
    STATUS_RUNNING,
    STATUS_DONE,
    STATUS_ERROR,
    font_body,
)

ICON_MAP = {
    "pending": "○",
    "running": "◉",
    "done": "✓",
    "error": "✗",
}

COLOR_MAP = {
    "pending": STATUS_PENDING,
    "running": STATUS_RUNNING,
    "done": STATUS_DONE,
    "error": STATUS_ERROR,
}


class ScannerRow(ctk.CTkFrame):
    """Displays a single scanner tool's status: icon + name + finding count."""

    def __init__(self, master, tool_name: str, **kwargs):
        super().__init__(master, fg_color=BG_CARD, corner_radius=6, height=40, **kwargs)
        self.pack_propagate(False)

        self._status = "pending"
        self._tool_name = tool_name

        self._icon_label = ctk.CTkLabel(
            self,
            text=ICON_MAP["pending"],
            text_color=COLOR_MAP["pending"],
            font=font_body(14),
            width=24,
        )
        self._icon_label.pack(side="left", padx=(12, 4), pady=6)

        self._name_label = ctk.CTkLabel(
            self,
            text=tool_name.capitalize(),
            text_color=TEXT_PRIMARY,
            font=font_body(13),
        )
        self._name_label.pack(side="left", padx=(4, 0), pady=6)

        self._count_label = ctk.CTkLabel(
            self,
            text="",
            text_color=TEXT_SECONDARY,
            font=font_body(11),
        )
        self._count_label.pack(side="right", padx=(0, 12), pady=6)

    def set_status(self, status: str, count: int = 0) -> None:
        """Update row to pending/running/done/error with optional finding count."""
        self._status = status
        self._icon_label.configure(
            text=ICON_MAP.get(status, "?"),
            text_color=COLOR_MAP.get(status, STATUS_PENDING),
        )
        if status == "done":
            self._count_label.configure(
                text=f"{count} findings",
                text_color=STATUS_DONE,
            )
        elif status == "error":
            self._count_label.configure(
                text="error",
                text_color=STATUS_ERROR,
            )

    @property
    def status(self) -> str:
        return self._status
