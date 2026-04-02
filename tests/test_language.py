"""Testes de detecção de linguagem."""
from pathlib import Path
from app.core.language import detect_languages, count_files, select_rulesets


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


def test_select_rulesets_python():
    assert select_rulesets(["Python"]) == ["assets/rules/python"]


def test_select_rulesets_multiple():
    result = select_rulesets(["Python", "JavaScript"])
    assert len(result) == 2
    assert "assets/rules/python" in result
    assert "assets/rules/javascript" in result


def test_select_rulesets_unknown_language():
    assert select_rulesets(["Brainfuck"]) == []
