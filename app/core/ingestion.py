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


def _inject_token(url: str, token: str) -> str:
    """Injeta PAT na URL: https://TOKEN@github.com/..."""
    return re.sub(r"^(https?://)", rf"\1{token}@", url)


def clone_repository(
    url: str,
    target_dir: Optional[Path] = None,
    github_token: str = "",
    timeout: int = 600,
) -> Path:
    """Clona repositório em diretório temporário isolado.

    Args:
        url: URL do repositório (https).
        target_dir: Diretório destino (cria temp se None).
        github_token: PAT para repositórios privados.
        timeout: Timeout em segundos (padrão 10min).

    Raises:
        ValueError: URL inválida.
        PermissionError: Repositório privado sem token.
        RuntimeError: Falha no clone (inclui mensagem do git).
    """
    git_url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(git_url_pattern, url):
        raise ValueError(f"URL inválida: {url}")

    clone_url = _inject_token(url, github_token) if github_token else url
    dest = target_dir or Path(tempfile.mkdtemp(prefix="r-check_"))

    try:
        import platform
        creationflags = 0x08000000 if platform.system() == "Windows" else 0
        result = subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, str(dest)],
            capture_output=True, text=True, timeout=timeout,
            creationflags=creationflags,
        )
    except subprocess.TimeoutExpired:
        shutil.rmtree(dest, ignore_errors=True)
        raise RuntimeError(
            f"Clone cancelado: repositório demorou mais de {timeout//60} minutos. "
            "Verifique sua conexão ou tente um repositório menor."
        )

    if result.returncode != 0:
        shutil.rmtree(dest, ignore_errors=True)
        stderr = result.stderr.strip()
        # Detecta erro de autenticação e dá mensagem clara
        if "authentication" in stderr.lower() or "repository not found" in stderr.lower() or "403" in stderr:
            raise PermissionError(
                "Repositório privado ou não encontrado. "
                "Configure um GitHub Token nas Configurações."
            )
        if github_token and ("invalid username" in stderr.lower() or "bad credentials" in stderr.lower()):
            raise PermissionError("GitHub Token inválido ou sem permissão neste repositório.")
        raise RuntimeError(f"Falha ao clonar: {stderr}")

    return dest


def cleanup_temp_dir(path: Path) -> None:
    """Remove diretório temporário de clone com segurança."""
    if path.exists() and "r-check_" in path.name:
        shutil.rmtree(path, ignore_errors=True)
