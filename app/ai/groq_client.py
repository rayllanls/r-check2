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

    def enrich_batch(self, findings: list[Finding]) -> list[tuple[str, str]]:
        """Uma única chamada para todos os findings.

        Retorna lista de (explicação, sugestão) na mesma ordem dos findings.
        Itens sem resposta ficam como ('', '').
        """
        if not findings:
            return []

        lines = []
        for i, f in enumerate(findings, 1):
            lines.append(f"[{i}] {f.title}\n{f.snippet or ''}")

        prompt = (
            "Analise as vulnerabilidades de segurança abaixo e responda em blocos numerados.\n"
            "Para cada item use exatamente este formato (sem texto extra entre blocos):\n\n"
            "[N]\n"
            "EXPLICACAO: <o que é e por que é perigoso — máx 2 frases, sem código>\n"
            "CORRECAO: <trecho corrigido + 1 frase do que mudou>\n\n"
            "Vulnerabilidades:\n\n"
            + "\n\n".join(lines)
        )

        try:
            r = httpx.post(
                GROQ_API_URL,
                headers={"Authorization": f"Bearer {self._token}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150 * len(findings),
                    "temperature": 0.1,
                },
                timeout=NETWORK_TIMEOUT_GROQ,
            )
            if r.status_code == 200:
                return self._parse_batch(r.json()["choices"][0]["message"]["content"], len(findings))
        except Exception:
            pass
        return [("", "")] * len(findings)

    def _parse_batch(self, content: str, count: int) -> list[tuple[str, str]]:
        """Parseia resposta em blocos [N] para lista de (explicação, sugestão)."""
        results: dict[int, tuple[str, str]] = {}
        current_idx: int | None = None
        explanation = ""
        fix = ""

        for line in content.splitlines():
            line = line.strip()
            if line.startswith("[") and "]" in line:
                # salva bloco anterior
                if current_idx is not None:
                    results[current_idx] = (explanation.strip(), fix.strip())
                try:
                    current_idx = int(line[1:line.index("]")])
                except ValueError:
                    current_idx = None
                explanation = ""
                fix = ""
            elif line.upper().startswith("EXPLICACAO:"):
                explanation = line.split(":", 1)[1].strip()
            elif line.upper().startswith("CORRECAO:"):
                fix = line.split(":", 1)[1].strip()
            elif current_idx is not None:
                # continuação de linha longa
                if fix:
                    fix += " " + line
                elif explanation:
                    explanation += " " + line

        if current_idx is not None:
            results[current_idx] = (explanation.strip(), fix.strip())

        return [results.get(i, ("", "")) for i in range(1, count + 1)]

    # Mantidos para compatibilidade com testes unitários existentes
    def enrich_finding(self, finding: Finding) -> tuple[str, str]:
        results = self.enrich_batch([finding])
        return results[0]

    def explain_finding(self, finding: Finding) -> str:
        explanation, _ = self.enrich_finding(finding)
        return explanation

    def suggest_fix(self, finding: Finding) -> str:
        _, fix = self.enrich_finding(finding)
        return fix
