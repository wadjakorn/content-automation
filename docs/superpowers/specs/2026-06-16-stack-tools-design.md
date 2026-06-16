# Stack & Tools Design — Phase 0

> Date: 2026-06-16 · Status: **approved design**, pre-build
> Scope: phase 0 = consistency engine (idea backlog → planning → script/storyboard →
> YouTube auto-schedule) **+ hard-rules gate only**. See `docs/06-build-phases.md`.

Purpose: pin every undecided slash-choice in `docs/04-infra-hybrid.md`
(`BullMQ/Celery`, `n8n→Temporal`, `Ollama/MLX`, …) to one concrete tool for phase 0,
with an explicit defer list and upgrade triggers. Honors the "don't over-engineer before
publishing consistently" rule.

## Decisions (forks resolved)

| Fork | Decision | Why |
|---|---|---|
| Language/runtime | **Python 3.12** | Wins the AI/data half (KB, calibration, clustering) that *is* this system's core; loses nothing on platform APIs — Google ships an official Python YouTube client. |
| Orchestration | **arq** (Redis async queue) | Tiny, runs on Pi 4B. Enough for phase-0 retries + scheduling. Temporal/n8n deferred. |
| LLM access | **`LLMClient` protocol** + Claude impl | Cheap insurance for the design's local/frontier hybrid routing; 2 call sites (generate + judge). |
| Gate scope | **Hard-rules-only** keyword gate | `06` lists no gates in phase 0; CLAUDE.md hard rules are always-on. Cheap keyword checks honor both. Full Lane A–D deferred. |

## Tooling

- **Python 3.12** · **uv** (env + deps) · **ruff** (lint + format) · **mypy** (types)
- **pytest** + **pytest-asyncio** (tests; TDD per project workflow)

## Services (docker-compose)

| Service | Tool | Role |
|---|---|---|
| DB | **Postgres 16 + pgvector** | knowledge base, content state, embeddings |
| Broker | **Redis** | arq backend |
| Worker | **arq** | pipeline stages, retries, scheduled publish fires |
| API | **FastAPI + uvicorn** | OAuth callback, YouTube webhooks, internal control |
| Ingress | **cloudflared** | single inbound tunnel (webhooks/OAuth), outbound-only, CGNAT-proof |

## Data layer

- **SQLAlchemy 2.0** (async) + **Alembic** migrations.
- **pydantic v2** = gate verdict models. Generated from / validated against `schemas/*.json`
  (JSON Schema draft 2020-12 ↔ pydantic is native). One model per schema:
  `LaneAVerdict`, `LaneBAdvisory`, `LaneCFactCheck`, `LaneDContext`, `MonitorSnapshot`.
- **Content item state machine** = explicit enum column (`idea→scripted→filming→editing→
  ready→scheduled→published`) + transition-guard functions in code. No FSM library
  (over-engineering for 7 states).

## LLM layer

- Define a small `LLMClient` **protocol**:
  - `generate(...)` — script, title, hook, storyboard (frontier).
  - `judge(...)` — returns a validated pydantic verdict via structured output.
- Phase-0 implementation = **anthropic SDK** (Claude), tool-use / structured output →
  pydantic model. Local **MLX/Ollama** implementation slots behind the protocol at phase 2
  without touching callers (matches the hybrid local/frontier routing in `04`).

## Hard-rules gate (the only gate in phase 0)

Cheap keyword/regex — no LLM-judge, no retrieval, no moderation API yet:

- **Health-claim detector** → emits a `lane-d-context` verdict with `action: "hold"`
  (CLAUDE.md: health/medical claims about a product = HOLD always; อย. legal exposure).
- **Disclosure check** — sponsored/gifted/affiliate without disclosure →
  `action: "block_until_disclosed"`.

Emits verdicts shaped to `schemas/lane-d-context.schema.json` so the full Lane A–D
cascade (LLM-judge + retrieval + moderation) is a drop-in replacement in a later phase,
not a rewrite.

## Platform adapters

- `PlatformAdapter` **ABC** + capability flags (`supports_native_schedule`,
  `requires_audit`, `can_fetch_comments`) per CLAUDE.md.
- `YouTubeAdapter` = **google-api-python-client** + **google-auth-oauthlib**
  (`status.publishAt` scheduling, `commentThreads.list`). Official API only — no scraping.
- IG / TikTok adapters = **stubs only** in phase 0 (flags set, methods raise
  `NotImplementedError`). Built phase 2 after Meta App Review / TikTok audit.

## Secrets & config

- **pydantic-settings** + `.env` (gitignored).
- OAuth tokens **Fernet-encrypted at rest** in Postgres — never plaintext, never committed
  (CLAUDE.md hard rule: no secrets/media in git).

## Deliberately deferred (YAGNI for phase 0)

| Deferred | Lands at | Upgrade trigger |
|---|---|---|
| MinIO / object storage | phase 2 | derivative assets need S3 API; until then SMB mount to NAS |
| Local LLM (MLX/Ollama) | phase 2 | Mac M5 arrives; bulk/private workloads (comment sentiment, transcription) |
| whisper / ffmpeg / OCR / vision | phase 1+ | production stages (transcript-based Gate 2) |
| web-search + fact-card retrieval | full Lane C | building the fact-check cascade |
| moderation API (Llama Guard / OpenAI Moderation) | full Lane A | building the policy cascade (skip Perspective — winding down 2026) |
| sentiment/topic clustering (hdbscan, scikit-learn) | phase 3 / monitor | post-publish monitor calibration |
| Temporal / n8n | phase 2–3 | multi-platform fan-out + long-running durable workflows |

## Deployment

- **Phase 0 (now)**: full compose on **Pi 4B** — postgres + redis + arq + fastapi +
  cloudflared. LLM = Claude API. NAS = SMB backup from day one.
- **Mac M5 arrives**: move compute + add a local-LLM container to the Mac; Pi demotes to
  heartbeat + tunnel 24/7. Same compose, different host.

## Open items for the implementation plan

- Exact pydantic ↔ JSON Schema binding approach (generate models from schema vs. hand-write
  + validate) — decide in plan.
- Concrete `arq` scheduling pattern for YouTube `publishAt` offload vs. self-fire fallback.
- DB schema for content items, KB entries, encrypted token store.
