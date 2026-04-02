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


LANGUAGE_TO_LOCAL_RULESET: dict[str, str] = {
    "Python":     "assets/rules/python",
    "JavaScript": "assets/rules/javascript",
    "TypeScript": "assets/rules/typescript",
    "Go":         "assets/rules/go",
    "Java":       "assets/rules/java",
    "Ruby":       "assets/rules/ruby",
    "PHP":        "assets/rules/php",
}

# Semgrep registry fallback (used when local rules aren't bundled yet — dev mode)
LANGUAGE_TO_REGISTRY_RULESET: dict[str, str] = {
    "Python":     "p/python",
    "JavaScript": "p/javascript",
    "TypeScript": "p/typescript",
    "Go":         "p/golang",
    "Java":       "p/java",
    "Ruby":       "p/ruby",
    "PHP":        "p/php",
}


def select_rulesets(languages: list[str]) -> list[str]:
    """Return list of --config paths for detected languages.
    Uses local bundled rules when available, falls back to semgrep registry."""
    result = []
    for lang in languages:
        local = LANGUAGE_TO_LOCAL_RULESET.get(lang)
        if local and Path(local).exists():
            result.append(local)
        elif lang in LANGUAGE_TO_REGISTRY_RULESET:
            result.append(LANGUAGE_TO_REGISTRY_RULESET[lang])
    return result
