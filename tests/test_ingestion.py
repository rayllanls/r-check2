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
