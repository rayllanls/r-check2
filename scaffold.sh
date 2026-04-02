#!/bin/bash
# SecScan — Script de scaffold do projeto
# Cria toda a estrutura, instala dependências e deixa pronto para rodar
# Uso: chmod +x scaffold.sh && ./scaffold.sh

set -e

echo "🛡  SecScan — Iniciando scaffold..."
echo ""

# ─── Verifica dependências do sistema ───────────────────────────────────────
check_command() {
  if ! command -v "$1" &>/dev/null; then
    echo "⚠  '$1' não encontrado. $2"
    return 1
  fi
  echo "✅ $1 encontrado"
  return 0
}

echo "── Verificando dependências do sistema ──"
check_command python3 "Instale em: https://python.org"
check_command pip3 "Vem junto com o Python"
check_command git "Instale em: https://git-scm.com" || true
echo ""

# ─── Cria diretórios ─────────────────────────────────────────────────────────
echo "── Criando estrutura de pastas ──"
mkdir -p app/core
mkdir -p app/tools
mkdir -p app/license
mkdir -p app/ai
mkdir -p app/report/templates
mkdir -p app/gui
mkdir -p vendors/win
mkdir -p vendors/linux
mkdir -p license-api/routes
mkdir -p build
mkdir -p tests
mkdir -p .github/workflows
echo "✅ Pastas criadas"
echo ""

# ─── Arquivos Python ─────────────────────────────────────────────────────────
echo "── Criando arquivos base ──"

touch app/__init__.py
touch app/core/__init__.py
touch app/tools/__init__.py
touch app/license/__init__.py
touch app/ai/__init__.py
touch app/report/__init__.py
touch app/gui/__init__.py
touch license-api/__init__.py
touch license-api/routes/__init__.py

# app/main.py
cat > app/main.py << 'EOF'
"""
SecScan — Entry point
Desenvolvimento: python app/main.py
"""
from app.gui.main_window import MainWindow


def main() -> None:
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
EOF

# app/config.py
cat > app/config.py << 'EOF'
"""
Configurações do SecScan.
Em desenvolvimento: DEV_MODE=True libera tudo sem licença.
"""
import os
from pathlib import Path

# ─── Modo de desenvolvimento ─────────────────────────────────────────────────
# Em dev, tudo fica liberado — sem validação de licença, todos os planos ativos
# Nunca commitar com DEV_MODE = True em produção
DEV_MODE: bool = os.getenv("SECSCAN_DEV", "true").lower() == "true"
DEV_PLAN: str  = "team"   # plano mais completo em dev

APP_VERSION = "0.1.0-dev"

# ─── Caminhos ────────────────────────────────────────────────────────────────
CONFIG_DIR  = Path.home() / ".secscan"
CONFIG_FILE = CONFIG_DIR / "config.json"

# ─── API (só usado fora do DEV_MODE) ─────────────────────────────────────────
LICENSE_API_URL          = os.getenv("SECSCAN_LICENSE_URL", "https://api.secscan.app")
GROQ_API_URL             = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL               = "llama-3.1-70b-versatile"
NETWORK_TIMEOUT_LICENSE  = 10   # segundos
NETWORK_TIMEOUT_GROQ     = 15   # segundos
LICENSE_GRACE_HOURS      = 72

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
    "team": ["trufflehog", "gitleaks", "semgrep", "grype", "checkov"],
}
EOF

# app/core/models.py
cat > app/core/models.py << 'EOF'
"""Modelos de dados do SecScan."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"
    INFO     = "info"


class FindingCategory(str, Enum):
    SECRET     = "secret"
    SAST       = "sast"
    DEPENDENCY = "dependency"
    IAC        = "iac"


@dataclass
class Finding:
    id: str
    title: str
    severity: Severity
    category: FindingCategory
    file_path: str
    line_number: int
    snippet: str
    description: str
    tool: str
    rule_id: str = ""
    ai_explanation: Optional[str] = None
    ai_fix_suggestion: Optional[str] = None


@dataclass
class ScanResult:
    project_path: str
    scanned_files: int
    languages_detected: list[str]
    findings: list[Finding]
    scan_duration_seconds: float
    tools_used: list[str]
    errors: list[str] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)
EOF

# app/core/ingestion.py
cat > app/core/ingestion.py << 'EOF'
"""Ingestão de código: pasta local e clone de repositório Git."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def resolve_local_path(path: str) -> Path:
    """Valida e retorna Path local. Raises ValueError se inválido."""
    p = Path(path).resolve()
    if not p.exists():
        raise ValueError(f"Caminho não encontrado: {path}")
    if not p.is_dir():
        raise ValueError(f"O caminho deve ser um diretório: {path}")
    return p


def clone_repository(url: str, target_dir: Optional[Path] = None) -> Path:
    """
    Clona repositório em diretório temporário isolado.
    O chamador é responsável por chamar cleanup_temp_dir() depois.
    """
    git_url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(git_url_pattern, url):
        raise ValueError(f"URL inválida: {url}")

    dest = target_dir or Path(tempfile.mkdtemp(prefix="secscan_"))
    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"Falha ao clonar: {result.stderr}")
    return dest


def cleanup_temp_dir(path: Path) -> None:
    """Remove diretório temporário de clone com segurança."""
    if path.exists() and "secscan_" in path.name:
        shutil.rmtree(path, ignore_errors=True)
EOF

# app/core/language.py
cat > app/core/language.py << 'EOF'
"""Detecção de linguagens de programação no projeto."""
from pathlib import Path
from collections import Counter

EXTENSION_MAP: dict[str, str] = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "JavaScript", ".tsx": "TypeScript", ".go": "Go",
    ".java": "Java", ".rb": "Ruby", ".php": "PHP", ".cs": "C#",
    ".cpp": "C++", ".c": "C", ".rs": "Rust", ".tf": "Terraform",
    ".yaml": "YAML", ".yml": "YAML", ".json": "JSON",
    ".env": "ENV", ".sh": "Shell", ".dockerfile": "Docker",
}

IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv",
    "venv", "env", "dist", "build", ".next", "vendor",
}


def detect_languages(project_path: Path) -> list[str]:
    """Detecta linguagens presentes, ordenadas por prevalência."""
    counts: Counter = Counter()
    for file in project_path.rglob("*"):
        if any(part in IGNORED_DIRS for part in file.parts):
            continue
        if file.is_file():
            lang = EXTENSION_MAP.get(file.suffix.lower())
            if lang:
                counts[lang] += 1
    return [lang for lang, _ in counts.most_common()]


def count_files(project_path: Path) -> int:
    """Conta arquivos analisáveis."""
    return sum(
        1 for f in project_path.rglob("*")
        if f.is_file()
        and not any(p in IGNORED_DIRS for p in f.parts)
        and f.suffix.lower() in EXTENSION_MAP
    )
EOF

# app/core/scanner.py
cat > app/core/scanner.py << 'EOF'
"""Orquestrador principal da análise."""
import time
from pathlib import Path
from typing import Callable, Optional

from app.config import DEV_MODE, DEV_PLAN, PLAN_TOOLS
from app.core.models import ScanResult
from app.core.language import detect_languages, count_files
from app.tools.semgrep import SemgrepTool
from app.tools.trufflehog import TrufflehogTool
from app.tools.grype import GrypeTool
from app.tools.gitleaks import GitleaksTool

TOOL_MAP = {
    "semgrep":    SemgrepTool,
    "trufflehog": TrufflehogTool,
    "grype":      GrypeTool,
    "gitleaks":   GitleaksTool,
}


class Scanner:
    """Orquestra ferramentas de análise e retorna ScanResult."""

    def __init__(
        self,
        plan: Optional[str] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> None:
        # Em DEV_MODE usa o plano mais completo independente de licença
        self.plan = plan or (DEV_PLAN if DEV_MODE else "free")
        self.on_progress = on_progress or (lambda msg: None)

    def _log(self, message: str) -> None:
        self.on_progress(message)

    def scan(self, project_path: Path) -> ScanResult:
        """Executa análise completa. Retorna ScanResult."""
        start = time.time()
        findings = []
        tools_used = []
        errors = []

        self._log("Detectando linguagens...")
        languages = detect_languages(project_path)
        file_count = count_files(project_path)
        self._log(f"{', '.join(languages) or 'desconhecido'} — {file_count} arquivos")

        for tool_name in PLAN_TOOLS.get(self.plan, []):
            tool_class = TOOL_MAP.get(tool_name)
            if not tool_class:
                continue
            self._log(f"Iniciando {tool_name}...")
            try:
                result = tool_class().run(project_path)
                findings.extend(result)
                tools_used.append(tool_name)
                self._log(f"{tool_name}: {len(result)} achados")
            except NotImplementedError:
                self._log(f"{tool_name}: ainda não implementado (TODO)")
            except Exception as e:
                errors.append(f"{tool_name}: {e}")
                self._log(f"Erro em {tool_name}: {e}")

        duration = time.time() - start
        self._log(f"Concluído em {duration:.1f}s — {len(findings)} achados totais")

        return ScanResult(
            project_path=str(project_path),
            scanned_files=file_count,
            languages_detected=languages,
            findings=findings,
            scan_duration_seconds=duration,
            tools_used=tools_used,
            errors=errors,
        )
EOF

# app/tools/base.py
cat > app/tools/base.py << 'EOF'
"""Classe base para wrappers de ferramentas. Resolve binário: vendor vs sistema."""
import platform
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.models import Finding

VENDOR_DIR = Path(__file__).parent.parent.parent / "vendors"


class BaseTool(ABC):
    tool_name: str = ""

    def resolve_binary(self) -> str:
        """Prioridade: vendor embutido → binário no PATH do sistema."""
        system = "win" if platform.system() == "Windows" else "linux"
        ext    = ".exe" if system == "win" else ""
        vendor = VENDOR_DIR / system / f"{self.tool_name}{ext}"

        if vendor.exists():
            return str(vendor)

        system_bin = shutil.which(self.tool_name)
        if system_bin:
            return system_bin

        raise FileNotFoundError(
            f"'{self.tool_name}' não encontrado no sistema.\n"
            f"Em desenvolvimento, instale a ferramenta globalmente."
        )

    @abstractmethod
    def run(self, project_path: Path) -> list[Finding]:
        """Executa análise e retorna achados."""
        ...
EOF

# Wrappers das ferramentas (stubs para implementar nas fases)
for tool in semgrep trufflehog grype gitleaks; do
  cap=$(echo "$tool" | sed 's/./\U&/')
  cat > app/tools/${tool}.py << EOF
"""Wrapper para ${tool}. Implementar na Fase 1."""
from pathlib import Path
from app.tools.base import BaseTool
from app.core.models import Finding


class ${cap}Tool(BaseTool):
    tool_name = "${tool}"

    def run(self, project_path: Path) -> list[Finding]:
        # TODO: Implementar chamada ao binário e parse do output JSON
        raise NotImplementedError("${cap}Tool não implementado ainda")
EOF
done

# app/license/fingerprint.py
cat > app/license/fingerprint.py << 'EOF'
"""Device fingerprint — vincula licença ao dispositivo."""
import hashlib
import platform
import uuid


def get_device_id() -> str:
    """ID único e estável do dispositivo. Sem dados pessoais."""
    raw = "|".join([
        platform.node(),
        platform.machine(),
        platform.processor(),
        str(uuid.getnode()),
    ])
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
EOF

# app/license/cache.py
cat > app/license/cache.py << 'EOF'
"""Cache de validação para uso offline."""
import time
from app.config import LICENSE_GRACE_HOURS


def is_within_grace_period(last_validated: float) -> bool:
    """Retorna True se ainda dentro do período de graça offline."""
    if last_validated == 0:
        return False
    elapsed_hours = (time.time() - last_validated) / 3600
    return elapsed_hours < LICENSE_GRACE_HOURS
EOF

# app/license/validator.py
cat > app/license/validator.py << 'EOF'
"""
Validação de licença.
Em DEV_MODE: sempre retorna válido sem bater na API.
"""
import time
from app.config import DEV_MODE, DEV_PLAN


class LicenseValidator:

    def validate(self, token: str = "") -> tuple[bool, str]:
        """
        Retorna (is_valid, plan).
        Em DEV_MODE sempre retorna (True, DEV_PLAN).
        """
        if DEV_MODE:
            return True, DEV_PLAN

        # TODO Fase 6: implementar validação real com a API
        raise NotImplementedError("Validação de licença implementar na Fase 6")
EOF

# app/ai/groq_client.py
cat > app/ai/groq_client.py << 'EOF'
"""
Integração Llama 3.1 via Groq API.
Token sempre fornecido pelo usuário — nunca hardcoded.
"""
import httpx
from app.config import GROQ_API_URL, GROQ_MODEL, NETWORK_TIMEOUT_GROQ
from app.core.models import Finding


class GroqAIClient:

    def __init__(self, token: str) -> None:
        if not token:
            raise ValueError("Token Groq não configurado")
        self._token = token

    def explain_finding(self, finding: Finding) -> str:
        """Explica o achado em linguagem simples. Retorna '' em caso de falha."""
        prompt = (
            f"Você é um especialista em segurança explicando para um dev iniciante.\n\n"
            f"Vulnerabilidade: {finding.title}\n"
            f"Arquivo: {finding.file_path} (linha {finding.line_number})\n"
            f"Código: {finding.snippet}\n\n"
            f"Explique: 1) O que é 2) Por que é perigoso 3) Como corrigir com exemplo. "
            f"Seja direto e conciso."
        )
        try:
            r = httpx.post(
                GROQ_API_URL,
                headers={"Authorization": f"Bearer {self._token}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.3,
                },
                timeout=NETWORK_TIMEOUT_GROQ,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
        return ""
EOF

# app/report/generator.py
cat > app/report/generator.py << 'EOF'
"""Geração do relatório HTML com Jinja2. Abre no browser local."""
import webbrowser
import tempfile
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from app.core.models import ScanResult

TEMPLATE_DIR = Path(__file__).parent / "templates"


def generate_report(result: ScanResult, open_browser: bool = True) -> Path:
    """Gera HTML e abre no browser. Retorna path do arquivo."""
    env      = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("report.html")
    html     = template.render(result=result)
    output   = Path(tempfile.gettempdir()) / "secscan_report.html"
    output.write_text(html, encoding="utf-8")
    if open_browser:
        webbrowser.open(output.as_uri())
    return output
EOF

# Template placeholder
cat > app/report/templates/report.html << 'EOF'
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><title>SecScan Report</title></head>
<body>
  <!-- TODO Fase 4: implementar template completo com Chart.js -->
  <h1>SecScan — Relatório</h1>
  <p>Projeto: {{ result.project_path }}</p>
  <p>Achados: {{ result.findings | length }}</p>
  {% for f in result.findings %}
    <div><strong>[{{ f.severity.value | upper }}] {{ f.title }}</strong>
    <p>{{ f.file_path }}:{{ f.line_number }}</p>
    <pre>{{ f.snippet }}</pre></div>
  {% endfor %}
</body>
</html>
EOF

# app/gui/main_window.py
cat > app/gui/main_window.py << 'EOF'
"""
Janela principal do SecScan.
TODO Fase 5: implementar GUI completa com CustomTkinter.
Por enquanto: modo CLI para testar o core.
"""
from app.config import DEV_MODE
from app.core.scanner import Scanner
from app.core.ingestion import resolve_local_path
from app.report.generator import generate_report


class MainWindow:
    def run(self) -> None:
        if DEV_MODE:
            self._run_cli_dev_mode()

    def _run_cli_dev_mode(self) -> None:
        """Modo CLI para desenvolvimento — testa o core sem GUI."""
        print("=" * 50)
        print("  SecScan — Modo desenvolvimento (DEV_MODE=True)")
        print("  Todos os planos liberados, sem validação de licença")
        print("=" * 50)

        path = input("\nCaminho do projeto para analisar: ").strip()
        if not path:
            print("Caminho vazio. Encerrando.")
            return

        try:
            project_path = resolve_local_path(path)
        except ValueError as e:
            print(f"Erro: {e}")
            return

        print(f"\nAnalisando: {project_path}\n")
        scanner = Scanner(on_progress=lambda msg: print(f"  → {msg}"))
        result  = scanner.scan(project_path)

        print(f"\n{'='*50}")
        print(f"  Resultado: {len(result.findings)} achados")
        print(f"  Críticos:  {result.critical_count}")
        print(f"  Altos:     {result.high_count}")
        print(f"{'='*50}\n")

        if result.findings:
            generate_report(result)
            print("Relatório aberto no browser.")
EOF

# ─── License API ─────────────────────────────────────────────────────────────
cat > license-api/main.py << 'EOF'
"""
SecScan License API.
TODO Fase 6: implementar validação real com Supabase.
"""
from fastapi import FastAPI

app = FastAPI(title="SecScan License API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/validate")
def validate(payload: dict) -> dict:
    # TODO Fase 6
    return {"valid": False, "plan": "free"}


@app.post("/activate")
def activate(payload: dict) -> dict:
    # TODO Fase 6
    return {"activated": False}
EOF

cat > license-api/requirements.txt << 'EOF'
fastapi==0.111.0
uvicorn==0.30.0
python-jose==3.3.0
supabase==2.4.0
httpx==0.27.0
EOF

# ─── Testes ──────────────────────────────────────────────────────────────────
cat > tests/__init__.py << 'EOF'
EOF

cat > tests/conftest.py << 'EOF'
"""Fixtures globais do pytest."""
import pytest
from pathlib import Path


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Projeto de exemplo com arquivo suspeito para testes."""
    (tmp_path / "config.py").write_text('STRIPE_KEY = "sk_live_1234hardcoded"\n')
    (tmp_path / "app.py").write_text('import os\nprint("hello")\n')
    (tmp_path / "requirements.txt").write_text("django==2.0.0\nrequests==2.20.0\n")
    return tmp_path
EOF

cat > tests/test_ingestion.py << 'EOF'
"""Testes de ingestão de código."""
import pytest
from pathlib import Path
from app.core.ingestion import resolve_local_path


def test_valid_path(tmp_path: Path) -> None:
    assert resolve_local_path(str(tmp_path)) == tmp_path.resolve()


def test_path_not_found() -> None:
    with pytest.raises(ValueError, match="não encontrado"):
        resolve_local_path("/caminho/inexistente/xyz")


def test_path_is_file_not_dir(tmp_path: Path) -> None:
    f = tmp_path / "arquivo.py"
    f.write_text("x = 1")
    with pytest.raises(ValueError, match="diretório"):
        resolve_local_path(str(f))
EOF

cat > tests/test_scanner.py << 'EOF'
"""Testes do orquestrador Scanner."""
import pytest
from pathlib import Path
from unittest.mock import patch
from app.core.scanner import Scanner
from app.core.models import ScanResult


def test_scanner_returns_scan_result(sample_project: Path) -> None:
    """Scanner deve retornar ScanResult mesmo com ferramentas não implementadas."""
    scanner = Scanner(plan="free")
    result  = scanner.scan(sample_project)
    assert isinstance(result, ScanResult)
    assert result.scanned_files >= 0


def test_scanner_dev_mode_uses_team_plan() -> None:
    """Em DEV_MODE o Scanner usa plano team automaticamente."""
    from app.config import DEV_MODE, DEV_PLAN
    if DEV_MODE:
        scanner = Scanner()
        assert scanner.plan == DEV_PLAN


def test_scanner_progress_callback(sample_project: Path) -> None:
    """Callback de progresso deve ser chamado durante a análise."""
    messages = []
    scanner  = Scanner(plan="free", on_progress=messages.append)
    scanner.scan(sample_project)
    assert len(messages) > 0
EOF

cat > tests/test_license.py << 'EOF'
"""Testes do sistema de licença."""
import time
import pytest
from app.license.cache import is_within_grace_period
from app.license.fingerprint import get_device_id
from app.license.validator import LicenseValidator


def test_grace_period_recent() -> None:
    assert is_within_grace_period(time.time() - 3600) is True  # 1h atrás


def test_grace_period_expired() -> None:
    assert is_within_grace_period(time.time() - 80 * 3600) is False  # 80h atrás


def test_grace_period_never() -> None:
    assert is_within_grace_period(0.0) is False


def test_device_id_stable() -> None:
    assert get_device_id() == get_device_id()
    assert len(get_device_id()) == 32


def test_validator_dev_mode() -> None:
    """Em DEV_MODE o validator deve sempre retornar válido."""
    from app.config import DEV_MODE
    if DEV_MODE:
        valid, plan = LicenseValidator().validate()
        assert valid is True
        assert plan == "team"
EOF

cat > tests/test_language.py << 'EOF'
"""Testes de detecção de linguagem."""
from pathlib import Path
from app.core.language import detect_languages, count_files


def test_detect_python(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("x = 1")
    (tmp_path / "utils.py").write_text("y = 2")
    langs = detect_languages(tmp_path)
    assert "Python" in langs


def test_ignores_node_modules(tmp_path: Path) -> None:
    nm = tmp_path / "node_modules"
    nm.mkdir()
    (nm / "index.js").write_text("var x = 1")
    (tmp_path / "app.py").write_text("x = 1")
    langs = detect_languages(tmp_path)
    assert langs == ["Python"]


def test_count_files(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x=1")
    (tmp_path / "b.js").write_text("var x=1")
    assert count_files(tmp_path) == 2
EOF

# ─── Arquivos raiz ────────────────────────────────────────────────────────────
cat > requirements.txt << 'EOF'
# GUI
customtkinter==5.2.2

# Templates e relatório
jinja2==3.1.4

# HTTP (licença + Groq)
httpx==0.27.0

# Dados
pydantic==2.7.0
python-jose==3.3.0

# Testes
pytest==8.2.0
pytest-cov==5.0.0

# Qualidade de código
ruff==0.4.4
mypy==1.10.0

# Build (só usar na fase final)
# pyinstaller==6.6.0
# pyarmor==8.5.0
EOF

cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests
addopts   = -v --tb=short
EOF

cat > ruff.toml << 'EOF'
line-length = 100
target-version = "py311"

[lint]
select = ["E", "F", "W", "I", "N"]
ignore = ["E501"]
EOF

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
.venv/
venv/
env/
*.egg-info/
dist/
build/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# SecScan — nunca commitar
.env
vendors/win/*.exe
vendors/linux/semgrep
vendors/linux/trufflehog
vendors/linux/grype
vendors/linux/gitleaks
vendors/linux/gitleaks
~/.secscan/

# OS
.DS_Store
Thumbs.db
EOF

cat > .env.example << 'EOF'
# Copie para .env para desenvolvimento local
# NUNCA commitar o .env real

# Controla o modo de desenvolvimento
# true  = tudo liberado, sem licença, plano team
# false = valida licença normalmente
SECSCAN_DEV=true

# URL da license API (em dev aponta para localhost)
SECSCAN_LICENSE_URL=http://localhost:8000

# Token Groq NÃO vai aqui — vai em ~/.secscan/config.json
EOF

cat > .env << 'EOF'
SECSCAN_DEV=true
SECSCAN_LICENSE_URL=http://localhost:8000
EOF

# GitHub Actions
cat > .github/workflows/release.yml << 'EOF'
name: Build Release
# Só roda quando você criar uma tag de versão: git tag v1.0.0 && git push --tags
on:
  push:
    tags: ['v*']

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt pyinstaller pyarmor
      - run: pyinstaller build/secscan_win.spec
      - uses: actions/upload-artifact@v4
        with: { name: secscan-windows, path: dist/secscan.exe }

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt pyinstaller pyarmor
      - run: pyinstaller build/secscan_linux.spec
      - uses: actions/upload-artifact@v4
        with: { name: secscan-linux, path: dist/secscan }

  release:
    needs: [build-windows, build-linux]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
      - uses: softprops/action-gh-release@v2
        with:
          files: |
            secscan-windows/secscan.exe
            secscan-linux/secscan
EOF

echo "✅ Arquivos criados"
echo ""

# ─── Instalação de dependências ──────────────────────────────────────────────
echo "── Instalando dependências ──"
pip3 install -r requirements.txt --break-system-packages --quiet
echo "✅ Dependências instaladas"
echo ""

# ─── Roda os testes para confirmar que está tudo ok ──────────────────────────
echo "── Rodando testes iniciais ──"
python3 -m pytest tests/ -v --tb=short 2>&1 | tail -20
echo ""

# ─── Resumo final ────────────────────────────────────────────────────────────
echo "════════════════════════════════════════════"
echo "  ✅ SecScan pronto para desenvolvimento!"
echo "════════════════════════════════════════════"
echo ""
echo ""
echo "  Para rodar o app (modo dev CLI):"
echo "    python app/main.py"
echo ""
echo "  Para rodar os testes:"
echo "    pytest"
echo ""
echo "  Próximos passos com o GSD:"
echo "    npx get-shit-done-cc --claude --local"
echo "    Abra o Claude Code → /gsd:new-project"
echo "    Cole o conteúdo de PROJECT_BRIEF.md"
echo "════════════════════════════════════════════"