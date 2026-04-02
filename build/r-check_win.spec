# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — r-check Windows build.

Estrutura de saída:
  dist/r-check/
    r-check.exe          ← executável principal
    gitleaks.exe         ← scanner (copiado de vendors/win/)
    trivy.exe
    grype.exe
    trufflehog.exe
    semgrep.exe
    checkov.exe (wrapper script gerado pelo pip)
    _internal/           ← libs Python (PyInstaller --onedir)
"""
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).parent  # raiz do repo

# ── Dados a incluir ──────────────────────────────────────────────────────────
datas = []

# Favicon SVG
datas += [(str(ROOT / "app" / "favicon.svg"), ".")]

# Templates de relatório HTML
datas += collect_data_files("app.report", includes=["templates/*.html"])

# CustomTkinter themes e assets
datas += collect_data_files("customtkinter")

# Assets (regras do semgrep, etc.)
datas += [(str(ROOT / "assets"), "assets")]

# ── Binários dos scanners (vendors/win/) ─────────────────────────────────────
binaries = []
vendor_win = ROOT / "vendors" / "win"
for exe in vendor_win.glob("*.exe"):
    binaries += [(str(exe), ".")]

# ── Hidden imports ───────────────────────────────────────────────────────────
hidden_imports = [
    # GUI
    "customtkinter",
    "PIL",
    "PIL._tkinter_finder",
    # Templates
    "jinja2",
    "jinja2.ext",
    "markupsafe",
    # HTTP
    "httpx",
    "httpcore",
    "anyio",
    "certifi",
    # Dados
    "pydantic",
    "pydantic.v1",
    "pydantic_core",
    # App internals
    "app",
    "app.ai",
    "app.core",
    "app.gui",
    "app.gui.screens",
    "app.gui.widgets",
    "app.report",
    "app.tools",
    "app.license",
    # Tkinter
    "tkinter",
    "tkinter.filedialog",
    "tkinter.messagebox",
    "tkinter.ttk",
]

hidden_imports += collect_submodules("app")

# ── Análise ──────────────────────────────────────────────────────────────────
a = Analysis(
    [str(ROOT / "app" / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Removidos da build
        "weasyprint",
        "pytest",
        "mypy",
        "ruff",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # --onedir: binários ficam separados
    name="r-check",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX pode causar falsos positivos em antivírus
    console=False,      # sem janela de console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "app" / "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="r-check",
)
