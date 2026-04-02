"""r-check theme — brand colors and font factories."""
import customtkinter as ctk

# Background
BG_PRIMARY = "#08070a"
BG_CARD    = "#111019"
BG_BORDER  = "#272436"
BG_INPUT   = "#0d0b11"

# Accent — primary CTA (blue)
ACCENT_PRIMARY       = "#2563eb"
ACCENT_PRIMARY_HOVER = "#1d4ed8"

# Accent — secondary (cyan)
ACCENT_SECONDARY       = "#38bdf8"
ACCENT_SECONDARY_HOVER = "#0ea5e9"

# Accent — brand purple (logo "r-")
ACCENT_PURPLE = "#9d00ff"

# Accent — destructive / critical
ACCENT_RED       = "#ff4757"
ACCENT_RED_HOVER = "#ff6b81"

# Accent — success
ACCENT_GREEN = "#4caf50"

# Aliases kept for backward compat (older screens use ACCENT_TEAL)
ACCENT_TEAL       = ACCENT_SECONDARY
ACCENT_TEAL_HOVER = ACCENT_SECONDARY_HOVER

# Text
TEXT_PRIMARY   = "#edeaf5"
TEXT_SECONDARY = "#7c7990"
TEXT_MUTED     = "#3d3a4a"

# Status
STATUS_PENDING = "#7c7990"
STATUS_RUNNING = ACCENT_PRIMARY
STATUS_DONE    = ACCENT_GREEN
STATUS_ERROR   = ACCENT_RED


def font_heading(size: int = 18) -> ctk.CTkFont:
    return ctk.CTkFont(family="JetBrains Mono", size=size, weight="bold")


def font_body(size: int = 13) -> ctk.CTkFont:
    return ctk.CTkFont(family="Inter", size=size, weight="normal")


def font_mono(size: int = 12) -> ctk.CTkFont:
    return ctk.CTkFont(family="JetBrains Mono", size=size, weight="normal")
