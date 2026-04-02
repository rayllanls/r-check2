"""Classe base para wrappers de ferramentas. Resolve binário: MEIPASS → vendor → sistema."""
import platform
import shutil
import sys
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.models import Finding

VENDOR_DIR = Path(__file__).parent.parent.parent / "vendors"


class BaseTool(ABC):
    tool_name: str = ""

    def resolve_binary(self) -> str:
        """Prioridade: sys._MEIPASS (PyInstaller frozen) → vendor embutido → PATH do sistema."""
        import os
        system = "win" if platform.system() == "Windows" else "linux"
        ext = ".exe" if system == "win" else ""

        # 1. PyInstaller frozen mode
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            frozen_bin = Path(sys._MEIPASS) / f"{self.tool_name}{ext}"
            if frozen_bin.exists():
                return str(frozen_bin)

        # 2. Vendor directory
        vendor = VENDOR_DIR / system / f"{self.tool_name}{ext}"
        if vendor.exists():
            return str(vendor)

        # 3. System PATH (includes ~/.local/bin explicitly for desktop/RDP sessions)
        extra_paths = [
            Path.home() / ".local" / "bin",
            Path("/usr/local/bin"),
        ]
        
        # Use os.pathsep (';' on Windows, ':' on Unix)
        search_path = os.pathsep.join(
            [str(p) for p in extra_paths if p.exists()] + 
            [os.environ.get("PATH", "")]
        )
        
        system_bin = shutil.which(self.tool_name, path=search_path)
        if system_bin:
            return system_bin

        raise FileNotFoundError(
            f"'{self.tool_name}' not found. "
            f"Instale globalmente ou coloque em vendors/{system}/."
        )

    def get_creationflags(self) -> int:
        """Return CREATE_NO_WINDOW on Windows to prevent console popup."""
        if platform.system() == "Windows":
            return 0x08000000  # subprocess.CREATE_NO_WINDOW
        return 0

    @abstractmethod
    def run(self, project_path: Path) -> list[Finding]:
        """Executa análise e retorna achados."""
        ...
