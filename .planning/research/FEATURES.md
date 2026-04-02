# Feature Research

**Domain:** Desktop SAST / code security analysis tool for non-security developers (vibe coders)
**Researched:** 2026-03-29
**Confidence:** MEDIUM — Based on training knowledge of Snyk, SonarQube, Semgrep, CodeQL, Bandit, Grype, Gitleaks, Trufflehog as of August 2025. Web access was unavailable. Confidence is MEDIUM (not LOW) because these are mature, stable tools with consistent documented feature sets; no major feature changes were imminent at cutoff.

---

## What the Landscape Looks Like

The SAST/code security tool ecosystem splits into two populations:

**Enterprise/Pro tools** (Snyk, SonarQube, Veracode, Checkmarx): designed for security teams operating CI/CD pipelines. Feature-rich, configuration-heavy, output in SARIF/JSON/XML. Assume the reader understands CVE numbers, CWE IDs, CVSS scores, and OWASP categories.

**Developer-adjacent tools** (Semgrep OSS, Bandit, ESLint-security, CodeQL): CLI-first, integrates into IDE or CI. Output is terse (file:line:rule). No explanation, no prioritization beyond severity level. Assumes developer can look up what "sql-injection/tainted-input" means.

**Secret scanners** (Gitleaks, Trufflehog): purpose-built for credentials in code/git history. Single-purpose, very little UX.

**SCA / dependency scanners** (Grype, OWASP Dependency-Check, Snyk Open Source): match packages against CVE databases. Output is package name + CVE ID + CVSS score.

None of these tools are designed for the target user (beginner dev, no security background, generated code from AI). This is the gap SecScan fills.

---

## Feature Landscape

### Table Stakes (Users Expect These)

These are baseline expectations established by every comparable tool. Missing any of these makes the product feel broken or incomplete, even to beginner users.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Folder / project scan | The core action — "scan my project" is the first thing any user tries | LOW | Walk the file tree, pass to scanner backends |
| Language auto-detection | Users don't know what rules apply to Python vs JS; they just want "scan" | LOW | Detect by extension + package files; apply appropriate ruleset per scanner |
| Severity levels (Critical / High / Medium / Low) | Every scanner uses this; users learn it from docs/blog posts and expect to filter by it | LOW | Map scanner-native severities to a normalized 4-tier system |
| Finding list with file + line number | The minimum output to act on — "which file, which line?" | LOW | Core data from all scanner outputs |
| Finding title / rule name | Identifies what the problem is called | LOW | Pulled directly from scanner output |
| Scan progress feedback | Users with large projects need to know something is happening | LOW | Progress bar or live log during scan |
| Summary counts | "How many critical findings?" — first thing a user reads in any report | LOW | Aggregate counts per severity tier |
| Exportable report | Users want to share results or keep a record | MEDIUM | HTML is sufficient for v1; PDF is a nice-to-have |
| Re-scan without re-configuring | Second scan must be as easy as first | LOW | Persist last scan target; "scan again" button |
| Ignore / suppress a finding | False positives exist; users need a way to dismiss them | MEDIUM | Persist suppression list per project path |

### Differentiators (Competitive Advantage)

These features are not found in standard SAST tools (or exist only in enterprise tiers behind paywalls). For the target user, these transform "I can't act on this output" into "I know what to do next."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Plain-language explanation of each finding | Target users don't know what "SQL injection via unsanitized user input" means. A sentence like "Your app lets users run database commands — an attacker could delete all your data" is actionable. | MEDIUM | AI layer (Groq/Llama 3.1) generates this per finding. Falls back gracefully to rule description if no token. |
| Concrete fix suggestion (not just "sanitize input") | "Add `parameterized_query(user_input)` on line 42" beats "avoid unsanitized input." Beginners need code-level guidance. | HIGH | AI-generated; requires good prompt engineering with code context |
| "Why this matters" severity framing | CVSS scores mean nothing to beginners. "This could let an attacker read your database" is the signal they need. | LOW | Static copy per vulnerability category; AI can personalize |
| Local-only privacy guarantee | AI-generated code is often proprietary or embarrassing. The promise "your code never leaves your machine" is a hard differentiator vs Snyk/Sonar cloud products. | LOW-MEDIUM | Architecture decision, not a feature to build — but must be prominently communicated in UX |
| Zero-install experience | Target users are not sysadmins. They will not configure PATH, install Docker, or manage Python environments. Bundled binaries behind a GUI removes all friction. | HIGH | PyInstaller bundle with embedded Semgrep/Trufflehog/Grype/Gitleaks binaries; primary engineering challenge |
| Unified multi-scanner output | Semgrep finds code bugs, Gitleaks finds secrets, Grype finds vulnerable packages — three separate tools with three separate output formats. Merging them into one normalized view is not done by any free tool. | MEDIUM | Data normalization layer; define common Finding schema |
| AI assistant context awareness | When a finding was introduced by AI-generated code (e.g., detected via comment patterns or recency), surface that context. "This code was likely generated — AI often makes this mistake with database queries." | HIGH | Speculative; requires heuristics or git blame analysis. Post-MVP. |
| Triage mode: "Fix these first" ordering | Severity alone is a poor guide. A Critical finding in a library file that's never called is less urgent than a High in the main request handler. Basic file-path heuristics (main.py, app.py, routes/) can weight findings. | MEDIUM | Heuristic scoring on top of severity; can be simple v1 |
| Scan history / delta view | "Did the new code I added introduce new vulnerabilities?" is the right question after each coding session. Comparing to a previous scan baseline requires persisting results. | HIGH | Requires local scan result storage + diff logic; v2 feature |
| Freemium gating that makes sense to non-security users | Competitors gate on "number of contributors" or "private repos" — meaningless to a solo vibe coder. Gate on something they understand: number of projects, AI explanations per month, or team sharing. | MEDIUM | Phase 6 concern; but the gating design must be decided early to avoid rework |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| SARIF / JSON / XML export | Enterprise tools export to these formats; power users ask for them | Zero value to target users; adds surface area with no beginner benefit; creates expectation of IDE integration (out of scope) | HTML report is the export. If devs want SARIF they are not the target user. |
| Custom rule editor | "Can I add my own rules?" sounds powerful | Semgrep rule syntax has a steep learning curve; supporting custom rules means supporting a rule authoring UX; beginners won't use it; it pulls focus from the core problem | Expose the ability to disable built-in rules (suppression) rather than add new ones |
| CI/CD integration / GitHub Actions step | Logical next step after desktop tool | Shifts product from desktop to DevOps tooling, a completely different buyer and use case; increases support surface dramatically | Keep desktop-first; if CI integration is requested by many users, it's a signal to build a separate CLI mode, not integrate into the GUI |
| Full IDE plugin | Users ask "can this be in Cursor?" | Building IDE extensions (VS Code, JetBrains, Cursor) is a distinct engineering track; each has its own extension API; maintenance overhead; Semgrep already has IDE plugins | "Open in editor" links in the report; v2 consideration after desktop is validated |
| Team dashboard / cloud sync | "Share results with my team" sounds collaborative | Requires cloud backend, authentication, data storage, privacy policy, GDPR surface area; destroys the "local only" differentiator | PDF/HTML report sharing via file; TEAM tier in v2 can add optional self-hosted sync |
| Auto-fix / one-click patch application | "Just fix it for me" is the natural request | Auto-applying patches to code is dangerous — it can break logic, introduce new bugs, lose context; creates liability; code diffs are complex to apply safely | Show the fix suggestion; let the user apply it (copy-paste or "open in editor" at line) |
| Vulnerability score weighting (custom CVSS) | Security professionals want to tune scoring | Completely inaccessible to beginners; adds UI complexity for zero beginner value | Use normalized 4-tier severity; explain severity in plain language instead |
| Real-time / watch mode scanning | "Scan on save" sounds useful | Continuous scanning of a large project is CPU-intensive; on-save scanning with multiple scanners adds seconds of lag per save; beginners coding with AI may make dozens of saves per minute | On-demand scan with "scan again" button; fast enough at <3min/500 files |

---

## Feature Dependencies

```
[Folder scan]
    └──requires──> [Language auto-detection]
                       └──requires──> [Scanner backend execution]
                                          └──requires──> [Bundled binaries (Semgrep/Grype/Gitleaks/Trufflehog)]

[Finding list]
    └──requires──> [Folder scan]
    └──requires──> [Output normalization (common Finding schema)]

[Severity display]
    └──requires──> [Output normalization]

[Summary counts / charts]
    └──requires──> [Finding list]
    └──requires──> [Severity display]

[HTML report]
    └──requires──> [Finding list]
    └──requires──> [Summary counts]

[PDF export]
    └──requires──> [HTML report]

[Plain-language explanation]
    └──requires──> [Finding list]
    └──enhances──> [HTML report]

[Fix suggestion]
    └──requires──> [Plain-language explanation]
    └──requires──> [Finding list with code context]

[Triage ordering]
    └──requires──> [Finding list]
    └──enhances──> [Severity display]

[Ignore/suppress finding]
    └──requires──> [Finding list]
    └──requires──> [Persistent config store (per-project)]

[Scan history / delta]
    └──requires──> [Finding list]
    └──requires──> [Persistent scan result storage]
    └──conflicts──> [Simplicity for v1]

[Freemium gating]
    └──requires──> [License system (Phase 6+)]
    └──conflicts──> [Full local feature access during dev (DEV_MODE)]
```

### Dependency Notes

- **Bundled binaries are the foundation of everything:** Semgrep, Grype, Gitleaks, and Trufflehog must run reliably before any feature above them can be built. This is the highest-risk dependency.
- **Output normalization unlocks the UI:** All four scanners produce different output formats (JSON, text, SARIF). A common `Finding` data model must be established early; every UI component depends on it.
- **AI explanations enhance but don't block:** Plain-language explanations are a differentiator but can be added after the core scan-and-display loop works. The finding must exist first.
- **Suppress/ignore requires persistence:** Needs a local config file (JSON/SQLite per project path). Introducing this also unlocks scan preferences storage generally.
- **Scan history is a v2 feature:** It requires a storage layer (SQLite) and diff logic that adds significant complexity without being needed to validate the core value proposition.
- **PDF export requires HTML report:** Don't skip HTML to go straight to PDF. HTML via browser print or a headless renderer (weasyprint/playwright) generates PDF; the HTML report is therefore always the canonical output.

---

## MVP Definition

### Launch With (v1)

Minimum to validate "find security issues in AI-generated code, explain them simply."

- [ ] Folder scan targeting a local path — the single trigger action
- [ ] Language auto-detection + appropriate scanner invocation — no user configuration needed
- [ ] All four embedded scanner backends run: Semgrep (code), Gitleaks (secrets in files), Trufflehog (secrets in git history), Grype (dependency CVEs)
- [ ] Normalized finding list (title, severity, file, line, rule) — the core data structure
- [ ] Severity tier display (Critical / High / Medium / Low) with counts — first thing user reads
- [ ] Plain-language explanation per finding via Groq/Llama 3.1 (with graceful fallback if no token) — the core differentiator
- [ ] HTML report with summary charts + finding list + code snippets + explanations — shareable artifact
- [ ] Real-time scan progress in GUI — prevents "is it frozen?" anxiety
- [ ] Re-scan button — second scan must be instant

### Add After Validation (v1.x)

Add these once users are actively scanning and providing feedback.

- [ ] Ignore / suppress a finding — first thing power users ask for when false positives appear
- [ ] PDF export — requested by users who share reports with clients or employers
- [ ] Fix suggestion (code-level) — upgrade from "here's what's wrong" to "here's how to fix it"; requires prompt engineering validation
- [ ] Triage ordering ("fix these first" heuristic) — add once users report difficulty prioritizing many findings
- [ ] Scan history / delta view — add once users have scanned the same project multiple times

### Future Consideration (v2+)

Defer until product-market fit is established and the desktop product is stable.

- [ ] IDE plugin (VS Code / Cursor extension) — separate engineering track; validate desktop first
- [ ] CI/CD integration — different buyer/use-case; defer
- [ ] Team dashboard / cloud sync — requires cloud backend; destroys local-only differentiator until explicitly planned
- [ ] Custom rule editor — power user feature; not the target persona
- [ ] Auto-fix / one-click patch — high liability, high complexity; defer until AI fix quality is validated

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Folder scan + embedded scanners running | HIGH | HIGH | P1 |
| Language auto-detection | HIGH | LOW | P1 |
| Normalized finding list (title, severity, file, line) | HIGH | MEDIUM | P1 |
| Scan progress UI | HIGH | LOW | P1 |
| Plain-language explanation (AI layer) | HIGH | MEDIUM | P1 |
| HTML report with charts | HIGH | MEDIUM | P1 |
| Re-scan button | HIGH | LOW | P1 |
| Severity counts / summary | HIGH | LOW | P1 |
| Ignore / suppress finding | MEDIUM | MEDIUM | P2 |
| PDF export | MEDIUM | LOW-MEDIUM | P2 |
| Fix suggestion (code-level) | HIGH | HIGH | P2 |
| Triage ordering heuristic | MEDIUM | MEDIUM | P2 |
| Scan history / delta | MEDIUM | HIGH | P3 |
| IDE plugin | HIGH | HIGH | P3 |
| CI/CD integration | LOW (target user) | HIGH | P3 |
| Custom rule editor | LOW (target user) | HIGH | P3 |
| Auto-fix / one-click patch | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | Snyk Code | Semgrep OSS | SonarQube (Community) | Our Approach |
|---------|-----------|-------------|----------------------|--------------|
| Code vulnerability scanning | Yes (cloud-based, IDE/CI) | Yes (CLI, local) | Yes (server, local or cloud) | Local, embedded — no server required |
| Secret detection | Via Snyk Secrets (paid) | Via partner rules | Limited in Community tier | Gitleaks + Trufflehog bundled |
| Dependency CVE scanning | Yes (Snyk Open Source) | Not built-in | Yes (separate plugin) | Grype bundled |
| Plain-language explanation | Yes, AI-powered (paid tier) | No | No (technical descriptions) | Yes, via Groq/Llama — and free tier includes it |
| Fix suggestions | Yes, AI code suggestions (paid) | No | No | v1.x — code-level suggestions via AI |
| Desktop GUI | No (IDE plugin + web) | No (CLI only) | Yes (web UI, server required) | Yes — primary interface |
| Local-only (no code upload) | No — code sent to Snyk servers | Yes (OSS runner) | Yes (self-hosted) | Yes — hard guarantee, communicated in UX |
| Zero-install for end user | No (requires npm/brew/docker) | No (requires Python/pip) | No (requires JVM + server) | Yes — bundled binaries, one .exe/.bin |
| Beginner-friendly UX | No (assumes security knowledge) | No (CLI, jargon-heavy) | No (assumes security knowledge) | Yes — jargon-free, explanations required |
| Scan history / trends | Yes (Snyk dashboard) | No | Yes (SonarQube metrics) | v2 |
| Suppress false positives | Yes | Yes (via inline comments) | Yes | v1.x |
| Report export | Yes (PDF, web dashboard) | No | Yes (web UI export) | HTML v1, PDF v1.x |

---

## Sources

- Snyk Code product documentation (training knowledge, HIGH confidence for feature existence, MEDIUM for current pricing/tier details)
- Semgrep documentation and CLI behavior (training knowledge, HIGH confidence — Semgrep OSS is stable and well-documented)
- SonarQube Community Edition feature set (training knowledge, HIGH confidence — Community vs Developer tier split is well-established)
- CodeQL / GitHub Advanced Security (training knowledge, HIGH confidence — GitHub's own product, stable)
- Bandit (Python SAST) behavior (training knowledge, HIGH confidence — unmaintained but behavior is fixed)
- Grype, Gitleaks, Trufflehog behavior (training knowledge, HIGH confidence — these are the actual embedded tools; behavior observed from OSS repos)
- OWASP Top 10 (2021 edition) as the canonical vulnerability category reference
- Note: WebSearch and WebFetch were unavailable during this research session. All findings are from training data (cutoff August 2025). Recommend spot-checking Snyk and Semgrep pricing/tier pages before using competitor analysis in marketing copy.

---

*Feature research for: Desktop SAST tool targeting non-security developers (vibe coders)*
*Researched: 2026-03-29*
