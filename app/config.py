"""
Configurações do r-check.
Em desenvolvimento: DEV_MODE=True libera tudo sem licença.
"""
import os
from pathlib import Path

# ─── Modo de desenvolvimento ─────────────────────────────────────────────────
# Em dev, tudo fica liberado — sem validação de licença, todos os planos ativos
# Nunca commitar com DEV_MODE = True em produção
DEV_MODE: bool = os.getenv("RCHECK_DEV", "true").lower() == "true"
DEV_PLAN: str  = "team"   # plano mais completo em dev

APP_VERSION = "0.1.0-dev"

# ─── Caminhos ────────────────────────────────────────────────────────────────
CONFIG_DIR  = Path.home() / ".r-check"
CONFIG_FILE = CONFIG_DIR / "config.json"

# ─── API (só usado fora do DEV_MODE) ─────────────────────────────────────────
LICENSE_API_URL          = os.getenv("RCHECK_LICENSE_URL", "https://api.r-check.app")
GROQ_API_URL             = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL               = "llama-3.1-8b-instant"
NETWORK_TIMEOUT_LICENSE  = 10   # segundos
NETWORK_TIMEOUT_GROQ     = 15   # segundos
LICENSE_GRACE_HOURS      = 72


def load_groq_token() -> str:
    """Read Groq token from ~/.r-check/config.json. Returns '' if absent."""
    import json
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text()).get("groq_token", "")
    except (json.JSONDecodeError, OSError):
        pass
    return ""


def load_github_token() -> str:
    """Read GitHub PAT from ~/.r-check/config.json. Returns '' if absent."""
    import json
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text()).get("github_token", "")
    except (json.JSONDecodeError, OSError):
        pass
    return ""

# ─── Limites por plano ───────────────────────────────────────────────────────
PLAN_LIMITS: dict[str, int | None] = {
    "free": 100,   # máx de arquivos
    "pro":  None,  # ilimitado
    "team": None,  # ilimitado
}

# Ferramentas disponíveis por plano
PLAN_TOOLS: dict[str, list[str]] = {
    "free": ["trufflehog", "gitleaks"],
    "pro":  ["trufflehog", "gitleaks", "semgrep", "grype"],
    "team": ["trufflehog", "gitleaks", "semgrep", "grype", "trivy", "checkov"],
}
