# SecScan

## What This Is

SecScan is a desktop SAST (Static Application Security Testing) tool for developers who use AI coding tools (Cursor, Claude, ChatGPT) to generate code but lack a security background. It analyzes code locally using embedded open-source scanners, finds vulnerabilities, and explains problems in plain language with fix suggestions — all without sending code to any server.

## Core Value

Find the serious security flaws in AI-generated code before a bad actor does — locally, privately, no security expertise required.

## Requirements

### Validated

- [x] Run Semgrep, Trufflehog, Grype, and Gitleaks as embedded tools *(Validated in Phase 2)*
- [x] Trivy (SCA + IaC + secrets) and Checkov (IaC) as 5th and 6th scanner backends, wired into TEAM-tier orchestrator *(Validated in Phase 3.1)*

### Active

- [ ] Scan local folders and cloned Git repos for security vulnerabilities
- [ ] Auto-detect project language and select appropriate rules
- [ ] Explain findings in plain language via Groq/Llama 3.1 (optional, user-supplied token)
- [ ] Generate HTML report with severity charts, finding list, code snippets, and AI explanations
- [ ] Export report to PDF
- [ ] Desktop GUI (CustomTkinter, dark modern design) with real-time scan progress
- [ ] DEV_MODE=True unlocks all features locally without license validation
- [ ] Scan 500-file project in under 3 minutes
- [ ] License system with Freemium / PRO / TEAM tiers (Phase 6)
- [ ] Windows .exe and Linux binary via PyInstaller + PyArmor (Phase 7)

### Out of Scope

- Mobile (iOS/Android) — not the target platform
- OAuth GitHub/GitLab login — email/password sufficient for v1; deferred to v2
- Web dashboard — desktop-first product
- IDE plugins — deferred to v2
- Cloud-based scanning — local analysis is a core differentiator

## Context

- Target users are beginner-to-intermediate developers building SaaS with AI assistance; they don't know what SAST, SQL injection, or CVE means — all UX must be jargon-free.
- Majority of users are on Windows 10/11; Linux (Ubuntu 20.04+) is secondary.
- **Two-stage development strategy:**
  - **Stage 1 (Phases 1–5):** 100% local, no license, no compilation. `DEV_MODE=True` unlocks everything (Team plan). Focus entirely on making analysis work well and GUI look good.
  - **Stage 2 (Phases 6–7):** Only after everything works locally. Implement cloud license, binary compilation, and distribution.
- Embedded tool vendors: Semgrep OSS, Trufflehog, Grype, Gitleaks (bundled binaries — no user install required).
- AI layer is optional — if no Groq token is configured, findings still display without AI explanations.
- Final binary can be up to 600MB (tools bundled inside).

## Constraints

- **Tech Stack**: Python 3.11+, CustomTkinter GUI, PyInstaller+PyArmor for distribution — chosen for Windows compatibility and ease of bundling
- **Privacy**: Code never leaves the machine (until optional Groq API call with user's own token)
- **Performance**: 500-file project must complete in under 3 minutes
- **Offline**: After license is implemented, must work offline for 72 hours (grace period)
- **Licensing (Phase 6+)**: FastAPI + Railway + Supabase + Stripe + JWT + device fingerprint — not before Phase 6
- **Build (Phase 7 only)**: PyInstaller + PyArmor + GitHub Actions — not before Phase 7

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| DEV_MODE=True unlocks Team plan without license | Enables full feature development without building the license system first | — Pending |
| License and build deferred to Phases 6–7 | Avoid build/distribution complexity until core product is validated | — Pending |
| Groq/Llama 3.1 for AI explanations | Free tier available; user supplies their own token; no cloud dependency forced | — Pending |
| Embed scanner binaries (Semgrep, Trufflehog, Grype, Gitleaks) | Zero-install experience for end users; critical for Windows adoption | — Pending |
| Local HTML report opened in browser | Avoids building a full UI renderer; leverages Chart.js for free | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-01 after Phase 3.1 — TrivyTool + CheckovTool scanner backends complete*
