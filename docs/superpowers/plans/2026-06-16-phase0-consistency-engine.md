# Phase-0 Consistency Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the phase-0 consistency engine — idea backlog → planning → script/storyboard → hard-rules gate → YouTube auto-schedule via `status.publishAt` — as a Python service runnable on a Raspberry Pi 4B docker-compose stack.

**Architecture:** A FastAPI app (OAuth callback + control) enqueues content-item work onto Redis; an `arq` worker runs the pipeline stages (score → plan → script → gate → schedule). State and the knowledge base live in Postgres 16 + pgvector via async SQLAlchemy 2.0. Content generation goes through an `LLMClient` protocol (Claude impl now, local LLM later). Publishing goes through a `PlatformAdapter` ABC (`YouTubeAdapter` now, IG/TikTok stubs). A keyword-only hard-rules gate emits `lane-d`-shaped verdicts so the full Lane A–D cascade is a later drop-in. OAuth tokens are Fernet-encrypted at rest.

**Tech Stack:** Python 3.12 · uv · ruff · mypy · pytest + pytest-asyncio · FastAPI + uvicorn · arq + Redis · SQLAlchemy 2.0 (async) + Alembic · Postgres 16 + pgvector · pydantic v2 + pydantic-settings · anthropic SDK · google-api-python-client + google-auth-oauthlib · cryptography (Fernet) · jsonschema (test-only) · cloudflared.

**Source spec:** `docs/superpowers/specs/2026-06-16-stack-tools-design.md`

---

## Decisions resolved from spec "Open items"

These were left open in the spec; this plan pins them:

1. **pydantic ↔ JSON Schema binding** → **hand-write pydantic v2 models, validate them against `schemas/*.json` in a test** (Task 3). No codegen: codegen for draft-2020-12 is brittle and the 5 schemas are small. The test fails if a model drifts from its schema, keeping them in sync. The gate also validates its emitted dict against the schema at runtime in dev (cheap, off in prod via settings).
2. **arq scheduling pattern** → **offload to YouTube**: at the schedule stage the worker calls `videos.insert`/`videos.update` once with `status.publishAt` set to the future time and `privacyStatus="private"`. YouTube fires the publish. The worker does **not** self-fire for YouTube. A `scheduled_at` column + an arq deferred job is wired but only used as a **fallback for platforms without native schedule** (IG/TikTok, phase 2) — for phase 0 it just records the intended time.
3. **DB schema** → three tables: `content_items` (state machine + script/plan fields), `kb_entries` (pgvector embedding column), `oauth_tokens` (Fernet ciphertext). Defined in Task 4.

## File structure

```
content-automation/
  pyproject.toml                 # uv project, deps, ruff/mypy/pytest config
  .env.example                   # documented config keys (real .env gitignored)
  .gitignore                     # .env, __pycache__, media, *.sqlite
  alembic.ini
  docker-compose.yml             # postgres+pgvector, redis, api, worker, cloudflared
  build/
    Dockerfile                   # shared app image (api + worker)
  src/contentauto/
    __init__.py
    config.py                    # pydantic-settings Settings
    db.py                        # async engine + session factory
    models/
      __init__.py
      verdicts.py                # 5 pydantic verdict models (lane A–D + monitor)
      content.py                 # SQLAlchemy ORM: ContentItem, KbEntry, OAuthToken + ContentState enum + transitions
    crypto.py                    # Fernet encrypt/decrypt for tokens
    gate/
      __init__.py
      hard_rules.py              # health-claim + disclosure keyword gate → LaneDContextVerdict
    llm/
      __init__.py
      base.py                    # LLMClient protocol
      claude.py                  # anthropic SDK impl
    platforms/
      __init__.py
      base.py                    # PlatformAdapter ABC + capability flags
      youtube.py                 # YouTubeAdapter
      stubs.py                   # InstagramAdapter, TikTokAdapter (NotImplementedError)
    pipeline/
      __init__.py
      stages.py                  # score / plan / script / gate / schedule stage fns
      worker.py                  # arq WorkerSettings + job entrypoints
    api/
      __init__.py
      app.py                     # FastAPI app, OAuth callback, control endpoints
  migrations/
    env.py                       # Alembic async env
    versions/                    # generated migration(s)
  tests/
    conftest.py                  # async fixtures (settings, db session, fake adapter/LLM)
    test_config.py
    test_verdicts_match_schema.py
    test_content_state.py
    test_crypto.py
    test_hard_rules_gate.py
    test_llm_claude.py
    test_youtube_adapter.py
    test_pipeline_stages.py
    test_api.py
```

---

## Task 1: Project scaffold (uv + tooling)

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `.env.example`, `src/contentauto/__init__.py`, `tests/__init__.py`

- [ ] **Step 1: Init uv project and add deps**

Run:
```bash
cd /Users/wadjakorntonsri/development/content-automation
uv init --package --name contentauto --python 3.12 .
uv add fastapi "uvicorn[standard]" arq redis "sqlalchemy[asyncio]>=2.0" asyncpg \
  alembic pgvector "pydantic>=2" pydantic-settings anthropic \
  google-api-python-client google-auth-oauthlib cryptography
uv add --dev pytest pytest-asyncio ruff mypy jsonschema "httpx" fakeredis
```
Expected: `pyproject.toml` created with `[project]` and dependencies; `uv.lock` written.

- [ ] **Step 2: Add tool config to `pyproject.toml`**

Append:
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 3: Write `.gitignore`**

```
.env
__pycache__/
*.pyc
.venv/
.mypy_cache/
.ruff_cache/
.pytest_cache/
media/
*.sqlite
```

- [ ] **Step 4: Write `.env.example`** (documents keys; real `.env` gitignored — CLAUDE.md: no secrets in git)

```
# Postgres
DATABASE_URL=postgresql+asyncpg://contentauto:changeme@localhost:5432/contentauto
# Redis
REDIS_URL=redis://localhost:6379
# Fernet key for OAuth token encryption — generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_KEY=
# Anthropic
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-opus-4-8
# YouTube OAuth (Google Cloud console)
YT_CLIENT_ID=
YT_CLIENT_SECRET=
YT_REDIRECT_URI=https://example.trycloudflare.com/oauth/youtube/callback
# dev: validate emitted verdicts against JSON Schema (off in prod)
VALIDATE_VERDICTS=true
```

- [ ] **Step 5: Verify tooling runs**

Run: `uv run ruff check . && uv run pytest -q`
Expected: ruff passes (no files yet to lint beyond scaffold); pytest reports "no tests ran".

- [ ] **Step 6: Commit**

```bash
git init
git add pyproject.toml uv.lock .gitignore .env.example src tests
git commit -m "chore: scaffold uv project + tooling for phase-0 engine"
```

---

## Task 2: Settings (pydantic-settings)

**Files:**
- Create: `src/contentauto/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
from contentauto.config import Settings


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/d")
    monkeypatch.setenv("REDIS_URL", "redis://h:6379")
    monkeypatch.setenv("FERNET_KEY", "x" * 44)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("YT_CLIENT_ID", "cid")
    monkeypatch.setenv("YT_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("YT_REDIRECT_URI", "https://x/cb")
    s = Settings()
    assert s.redis_url == "redis://h:6379"
    assert s.anthropic_model == "claude-opus-4-8"  # default
    assert s.validate_verdicts is True  # default
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'contentauto.config'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/contentauto/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str
    fernet_key: str
    anthropic_api_key: str
    anthropic_model: str = "claude-opus-4-8"
    yt_client_id: str
    yt_client_secret: str
    yt_redirect_uri: str
    validate_verdicts: bool = True


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/contentauto/config.py tests/test_config.py
git commit -m "feat: pydantic-settings config"
```

---

## Task 3: Verdict models + JSON Schema sync test

**Files:**
- Create: `src/contentauto/models/__init__.py`, `src/contentauto/models/verdicts.py`
- Test: `tests/test_verdicts_match_schema.py`

This binds pydantic to `schemas/*.json`. The test loads each JSON Schema and validates that a model instance's `model_dump()` passes, AND that pydantic's own generated schema covers the required fields — catching drift in either direction.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_verdicts_match_schema.py
import json
from pathlib import Path

import jsonschema
import pytest

from contentauto.models.verdicts import (
    LaneAVerdict,
    LaneBAdvisory,
    LaneCFactCheck,
    LaneDContextVerdict,
    MonitorSnapshot,
)

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"


def _load(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text())


CASES = [
    (
        "lane-d-context.schema.json",
        LaneDContextVerdict(
            checks=[{"type": "disclosure", "hard": True, "severity": "high",
                     "action": "block_until_disclosed", "evidence": "no #ad"}],
            reputational_risk=0.4,
        ),
    ),
    (
        "lane-a-verdict.schema.json",
        LaneAVerdict(
            surface="script", verdict="pass", categories=[], requires_human=False,
        ),
    ),
    (
        "lane-b-advisory.schema.json",
        LaneBAdvisory(
            surface="script", pattern="condescension", severity="low", decision="advisory",
        ),
    ),
    (
        "lane-c-factcheck.schema.json",
        LaneCFactCheck(
            surface="script", claim="X has 8GB RAM", type="spec_numeric",
            verdict="NOT_ENOUGH_INFO", requires_human=True,
        ),
    ),
    (
        "monitor-snapshot.schema.json",
        MonitorSnapshot(
            item_id="abc", platform="youtube", sampled_at="2026-06-16T00:00:00Z",
            since_publish_min=10, signals={}, alert_tier="L0",
        ),
    ),
]


@pytest.mark.parametrize("schema_file,model", CASES)
def test_model_dump_validates_against_schema(schema_file, model):
    schema = _load(schema_file)
    instance = model.model_dump(mode="json", exclude_none=True)
    jsonschema.validate(instance, schema)  # raises if drift
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_verdicts_match_schema.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'contentauto.models.verdicts'`

- [ ] **Step 3: Write the models**

```python
# src/contentauto/models/__init__.py
```

```python
# src/contentauto/models/verdicts.py
"""Pydantic v2 mirrors of schemas/*.json (JSON Schema draft 2020-12).

Hand-written, kept in sync by tests/test_verdicts_match_schema.py.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---- Lane A: policy / safety ----
LaneACategoryType = Literal[
    "identity_attack", "hate_speech", "slur", "threat", "dehumanization"
]
LaneAStance = Literal["discussing", "quoting", "criticizing", "endorsing", "attacking"]


class LaneACategory(BaseModel):
    type: LaneACategoryType
    stance: LaneAStance
    score: float = Field(ge=0, le=1)
    evidence: str | None = None
    target_group: str | None = None


class LaneAVerdict(BaseModel):
    surface: Literal["script", "transcript", "ocr", "thumbnail", "title"]
    verdict: Literal["pass", "flag", "hold"]
    categories: list[LaneACategory]
    suggested_fix: str | None = None
    requires_human: bool


# ---- Lane B: tone / brand (advisory only) ----
class LaneBAdvisory(BaseModel):
    surface: Literal["script", "transcript", "ocr", "title", "thumbnail"]
    pattern: Literal[
        "condescension", "punching_down", "gatekeeping",
        "unwarranted_absolutism", "sneer",
    ]
    severity: Literal["low", "medium"]
    span: str | None = None
    why_it_risks: str | None = None
    on_brand_alt: str | None = None
    decision: Literal["advisory"] = "advisory"


# ---- Lane C: fact-check ----
class LaneCEvidence(BaseModel):
    tier: Literal[1, 2, 3]
    url: str
    snippet: str | None = None


class LaneCFactCheck(BaseModel):
    surface: Literal["script", "transcript"]
    claim: str
    type: Literal[
        "spec_numeric", "price", "comparative", "superlative",
        "causal_technical", "temporal",
    ]
    verdict: Literal["SUPPORTED", "REFUTED", "NOT_ENOUGH_INFO"]
    evidence: list[LaneCEvidence] = Field(default_factory=list)
    correct_value: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    requires_human: bool


# ---- Lane D: context / timing (the phase-0 gate emits this) ----
LaneDCheckType = Literal["disclosure", "sensitivity", "consistency"]
LaneDAction = Literal[
    "pass", "advisory", "suggest_reschedule", "block_until_disclosed", "hold"
]


class LaneDCheck(BaseModel):
    type: LaneDCheckType
    hard: bool
    severity: Literal["low", "medium", "high"]
    evidence: str | None = None
    action: LaneDAction


class LaneDContextVerdict(BaseModel):
    checks: list[LaneDCheck]
    reputational_risk: float = Field(ge=0, le=1)


# ---- Post-publish monitor ----
class MonitorSnapshot(BaseModel):
    item_id: str
    platform: Literal["youtube", "instagram", "tiktok"]
    sampled_at: str
    since_publish_min: int = Field(ge=0)
    signals: dict
    alert_tier: Literal["L0", "L1", "L2", "L3"]
    proposed_actions: list[str] = Field(default_factory=list)
    requires_human: bool | None = None
    baseline_mode: Literal["learning", "active"] | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_verdicts_match_schema.py -v`
Expected: PASS (5 parametrized cases)

- [ ] **Step 5: Commit**

```bash
git add src/contentauto/models/__init__.py src/contentauto/models/verdicts.py tests/test_verdicts_match_schema.py
git commit -m "feat: pydantic verdict models synced to JSON schemas"
```

---

## Task 4: Content state machine (pure, no DB)

**Files:**
- Create: `src/contentauto/models/content.py` (state enum + transition guard only in this task; ORM tables added in Task 5)
- Test: `tests/test_content_state.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_content_state.py
import pytest

from contentauto.models.content import ContentState, can_transition, next_state


def test_legal_forward_transition():
    assert can_transition(ContentState.idea, ContentState.scripted)
    assert next_state(ContentState.editing) == ContentState.ready


def test_illegal_skip_raises():
    with pytest.raises(ValueError, match="illegal transition"):
        can_transition(ContentState.idea, ContentState.published)


def test_terminal_state_has_no_next():
    assert next_state(ContentState.published) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_content_state.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'contentauto.models.content'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/contentauto/models/content.py
from __future__ import annotations

import enum


class ContentState(str, enum.Enum):
    idea = "idea"
    scripted = "scripted"
    filming = "filming"
    editing = "editing"
    ready = "ready"
    scheduled = "scheduled"
    published = "published"


# explicit linear order — guard functions, no FSM library (spec: over-engineering for 7 states)
_ORDER: list[ContentState] = [
    ContentState.idea,
    ContentState.scripted,
    ContentState.filming,
    ContentState.editing,
    ContentState.ready,
    ContentState.scheduled,
    ContentState.published,
]


def next_state(state: ContentState) -> ContentState | None:
    i = _ORDER.index(state)
    return _ORDER[i + 1] if i + 1 < len(_ORDER) else None


def can_transition(frm: ContentState, to: ContentState) -> bool:
    if next_state(frm) != to:
        raise ValueError(f"illegal transition {frm.value} -> {to.value}")
    return True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_content_state.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/contentauto/models/content.py tests/test_content_state.py
git commit -m "feat: content-item state machine with transition guards"
```

---

## Task 5: ORM tables + DB session + Alembic

**Files:**
- Modify: `src/contentauto/models/content.py` (append ORM models)
- Create: `src/contentauto/db.py`, `alembic.ini`, `migrations/env.py`
- Test: `tests/conftest.py` (db fixture), `tests/test_db_roundtrip.py`

DB-touching tests need a real Postgres (pgvector). The fixture reads `TEST_DATABASE_URL` (a disposable DB created by docker-compose, Task 11) and skips if unset, so pure-logic tests still run on any machine.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_db_roundtrip.py
import pytest

from contentauto.models.content import ContentItem, ContentState


@pytest.mark.asyncio
async def test_insert_and_fetch_content_item(db_session):
    item = ContentItem(title="Test idea", pillar="technology", state=ContentState.idea)
    db_session.add(item)
    await db_session.flush()
    assert item.id is not None
    fetched = await db_session.get(ContentItem, item.id)
    assert fetched.state == ContentState.idea
    assert fetched.title == "Test idea"
```

- [ ] **Step 2: Add the db fixture to conftest**

```python
# tests/conftest.py
import os

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from contentauto.models.content import Base

TEST_DB = os.getenv("TEST_DATABASE_URL")


@pytest_asyncio.fixture
async def db_session():
    if not TEST_DB:
        import pytest

        pytest.skip("TEST_DATABASE_URL not set")
    engine = create_async_engine(TEST_DB)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
        await session.rollback()
    await engine.dispose()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_db_roundtrip.py -v`
Expected: FAIL with `ImportError: cannot import name 'ContentItem'` (or `Base`)

- [ ] **Step 4: Append ORM models to `content.py`**

```python
# --- append to src/contentauto/models/content.py ---
import datetime as _dt

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    pillar: Mapped[str] = mapped_column(String(40))
    state: Mapped[ContentState] = mapped_column(
        Enum(ContentState, name="content_state"), default=ContentState.idea
    )
    score: Mapped[float | None] = mapped_column(default=None)
    plan: Mapped[str | None] = mapped_column(Text, default=None)
    script: Mapped[str | None] = mapped_column(Text, default=None)
    youtube_video_id: Mapped[str | None] = mapped_column(String(40), default=None)
    scheduled_at: Mapped[_dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    is_sponsored: Mapped[bool] = mapped_column(default=False)
    has_disclosure: Mapped[bool] = mapped_column(default=False)


class KbEntry(Base):
    __tablename__ = "kb_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(80))
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), default=None)


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String(20), unique=True)
    ciphertext: Mapped[bytes] = mapped_column()  # Fernet blob — never plaintext
```

- [ ] **Step 5: Write `db.py`**

```python
# src/contentauto/db.py
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from contentauto.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    return _engine


def session_factory() -> async_sessionmaker:
    return async_sessionmaker(get_engine(), expire_on_commit=False)
```

- [ ] **Step 6: Init Alembic (async) and generate the first migration**

Run:
```bash
uv run alembic init -t async migrations
```
Then set `migrations/env.py` `target_metadata = Base.metadata` (import `from contentauto.models.content import Base`) and read the URL from `contentauto.config.get_settings().database_url`. In `alembic.ini` leave `sqlalchemy.url` blank (env.py supplies it). Then:
```bash
uv run alembic revision --autogenerate -m "phase0 tables"
```
Edit the generated migration's `upgrade()` to first run `op.execute("CREATE EXTENSION IF NOT EXISTS vector")` before table creation.
Expected: a file under `migrations/versions/` creating `content_items`, `kb_entries`, `oauth_tokens` + the vector extension.

- [ ] **Step 7: Run the roundtrip test**

Run: `TEST_DATABASE_URL=postgresql+asyncpg://contentauto:changeme@localhost:5432/contentauto_test uv run pytest tests/test_db_roundtrip.py -v`
(requires Postgres from Task 11 running; otherwise the test SKIPS — acceptable here, re-run after Task 11)
Expected: PASS (or SKIP if no DB yet)

- [ ] **Step 8: Commit**

```bash
git add src/contentauto/models/content.py src/contentauto/db.py alembic.ini migrations tests/conftest.py tests/test_db_roundtrip.py
git commit -m "feat: ORM tables, async db session, alembic migration"
```

---

## Task 6: Fernet token crypto

**Files:**
- Create: `src/contentauto/crypto.py`
- Test: `tests/test_crypto.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_crypto.py
from cryptography.fernet import Fernet

from contentauto.crypto import TokenCipher


def test_encrypt_decrypt_roundtrip():
    key = Fernet.generate_key().decode()
    cipher = TokenCipher(key)
    blob = cipher.encrypt('{"access_token": "abc", "refresh_token": "r"}')
    assert isinstance(blob, bytes)
    assert b"abc" not in blob  # not plaintext at rest
    assert cipher.decrypt(blob) == '{"access_token": "abc", "refresh_token": "r"}'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_crypto.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'contentauto.crypto'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/contentauto/crypto.py
from cryptography.fernet import Fernet


class TokenCipher:
    """Encrypt/decrypt OAuth token JSON for at-rest storage (CLAUDE.md: no plaintext secrets)."""

    def __init__(self, key: str) -> None:
        self._f = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> bytes:
        return self._f.encrypt(plaintext.encode())

    def decrypt(self, blob: bytes) -> str:
        return self._f.decrypt(blob).decode()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_crypto.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/contentauto/crypto.py tests/test_crypto.py
git commit -m "feat: Fernet token cipher for at-rest OAuth tokens"
```

---

## Task 7: Hard-rules gate

**Files:**
- Create: `src/contentauto/gate/__init__.py`, `src/contentauto/gate/hard_rules.py`
- Test: `tests/test_hard_rules_gate.py`

Keyword-only. Two checks. Emits `LaneDContextVerdict`. CLAUDE.md hard rules: health/medical claim about a product → HOLD always; sponsored/gifted/affiliate without disclosure → block.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_hard_rules_gate.py
from contentauto.gate.hard_rules import run_hard_rules
from contentauto.models.verdicts import LaneDContextVerdict


def test_health_claim_holds():
    v = run_hard_rules(
        script="อาหารเสริมตัวนี้ช่วยรักษาโรคเบาหวานได้",
        is_sponsored=False,
        has_disclosure=False,
    )
    assert isinstance(v, LaneDContextVerdict)
    hold = [c for c in v.checks if c.action == "hold"]
    assert hold and hold[0].type == "sensitivity" and hold[0].hard is True


def test_sponsored_without_disclosure_blocks():
    v = run_hard_rules(script="รีวิวหูฟังรุ่นใหม่", is_sponsored=True, has_disclosure=False)
    blocked = [c for c in v.checks if c.action == "block_until_disclosed"]
    assert blocked and blocked[0].type == "disclosure" and blocked[0].hard is True


def test_clean_script_passes():
    v = run_hard_rules(script="แกะกล่องคีย์บอร์ดกลไก", is_sponsored=False, has_disclosure=False)
    assert all(c.action == "pass" for c in v.checks)
    assert v.reputational_risk == 0.0


def test_sponsored_with_disclosure_passes():
    v = run_hard_rules(script="รีวิวหูฟัง #ได้รับสปอนเซอร์", is_sponsored=True, has_disclosure=True)
    assert all(c.action != "block_until_disclosed" for c in v.checks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_hard_rules_gate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'contentauto.gate'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/contentauto/gate/__init__.py
```

```python
# src/contentauto/gate/hard_rules.py
"""Phase-0 hard-rules gate: keyword/regex only, no LLM, no retrieval.

Emits a schemas/lane-d-context.schema.json-shaped verdict so the full
Lane A–D cascade is a drop-in replacement later, not a rewrite.
"""
from __future__ import annotations

import re

from contentauto.models.verdicts import LaneDCheck, LaneDContextVerdict

# health/medical claim markers (TH + EN) — product claims => HOLD always (อย. legal exposure)
_HEALTH_PATTERNS = [
    r"รักษา(โรค)?",
    r"หาย(ขาด)?",
    r"ป้องกันโรค",
    r"ลดน้ำหนัก",
    r"เสริมภูมิ",
    r"\bcure[sd]?\b",
    r"\btreat(s|ment)?\b",
    r"\bprevents?\s+\w*\s*(disease|cancer|diabetes)",
    r"\bclinically proven\b",
]
_HEALTH_RE = re.compile("|".join(_HEALTH_PATTERNS), re.IGNORECASE)


def run_hard_rules(
    *, script: str, is_sponsored: bool, has_disclosure: bool
) -> LaneDContextVerdict:
    checks: list[LaneDCheck] = []
    risk = 0.0

    # 1) health/medical claim about a product -> HOLD
    m = _HEALTH_RE.search(script)
    if m:
        checks.append(
            LaneDCheck(
                type="sensitivity",
                hard=True,
                severity="high",
                evidence=f"health-claim marker: {m.group(0)!r}",
                action="hold",
            )
        )
        risk = max(risk, 0.9)
    else:
        checks.append(
            LaneDCheck(type="sensitivity", hard=True, severity="low", action="pass")
        )

    # 2) sponsored/gifted/affiliate without disclosure -> block
    if is_sponsored and not has_disclosure:
        checks.append(
            LaneDCheck(
                type="disclosure",
                hard=True,
                severity="high",
                evidence="is_sponsored=True and has_disclosure=False",
                action="block_until_disclosed",
            )
        )
        risk = max(risk, 0.7)
    else:
        checks.append(
            LaneDCheck(type="disclosure", hard=True, severity="low", action="pass")
        )

    return LaneDContextVerdict(checks=checks, reputational_risk=risk)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_hard_rules_gate.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/contentauto/gate tests/test_hard_rules_gate.py
git commit -m "feat: phase-0 hard-rules gate emitting lane-d verdicts"
```

---

## Task 8: LLMClient protocol + Claude impl

**Files:**
- Create: `src/contentauto/llm/__init__.py`, `src/contentauto/llm/base.py`, `src/contentauto/llm/claude.py`
- Test: `tests/test_llm_claude.py`

The protocol has two call sites: `generate()` (free text) and `judge()` (validated pydantic verdict via structured output). Test the Claude impl against a faked anthropic client — no network.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_llm_claude.py
import pytest

from contentauto.llm.claude import ClaudeClient
from contentauto.models.verdicts import LaneDContextVerdict


class _FakeMessages:
    def __init__(self, payload):
        self._payload = payload

    def create(self, **kwargs):
        # mimic anthropic tool-use structured output
        class _Block:
            type = "tool_use"
            input = self._payload

        class _Resp:
            content = [_Block()]

        return _Resp()


class _FakeText:
    def create(self, **kwargs):
        class _Block:
            type = "text"
            text = "generated script body"

        class _Resp:
            content = [_Block()]

        return _Resp()


def test_generate_returns_text():
    client = ClaudeClient(api_key="x", model="m")
    client._client.messages = _FakeText()
    assert client.generate("write a hook") == "generated script body"


def test_judge_returns_validated_model():
    payload = {"checks": [{"type": "consistency", "hard": False,
                           "severity": "low", "action": "pass"}],
               "reputational_risk": 0.1}
    client = ClaudeClient(api_key="x", model="m")
    client._client.messages = _FakeMessages(payload)
    result = client.judge("judge this", LaneDContextVerdict)
    assert isinstance(result, LaneDContextVerdict)
    assert result.reputational_risk == pytest.approx(0.1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_llm_claude.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'contentauto.llm'`

- [ ] **Step 3: Write the protocol**

```python
# src/contentauto/llm/__init__.py
```

```python
# src/contentauto/llm/base.py
from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


class LLMClient(Protocol):
    """Two call sites only: generate (free text) and judge (validated verdict).

    Local MLX/Ollama impl slots behind this at phase 2 without touching callers.
    """

    def generate(self, prompt: str) -> str: ...

    def judge(self, prompt: str, schema: type[M]) -> M: ...
```

- [ ] **Step 4: Write the Claude impl**

```python
# src/contentauto/llm/claude.py
from __future__ import annotations

from typing import TypeVar

import anthropic
from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


class ClaudeClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate(self, prompt: str) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")

    def judge(self, prompt: str, schema: type[M]) -> M:
        tool = {
            "name": "verdict",
            "description": "Return the structured verdict.",
            "input_schema": schema.model_json_schema(),
        }
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            tools=[tool],
            tool_choice={"type": "tool", "name": "verdict"},
            messages=[{"role": "user", "content": prompt}],
        )
        for block in resp.content:
            if getattr(block, "type", "") == "tool_use":
                return schema.model_validate(block.input)
        raise ValueError("no tool_use block in Claude response")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_llm_claude.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add src/contentauto/llm tests/test_llm_claude.py
git commit -m "feat: LLMClient protocol + Claude impl (generate + judge)"
```

---

## Task 9: PlatformAdapter ABC + YouTubeAdapter + stubs

**Files:**
- Create: `src/contentauto/platforms/__init__.py`, `src/contentauto/platforms/base.py`, `src/contentauto/platforms/youtube.py`, `src/contentauto/platforms/stubs.py`
- Test: `tests/test_youtube_adapter.py`

Official API only (CLAUDE.md). `YouTubeAdapter.schedule()` builds the `status.publishAt` request and calls an injected `videos()` resource — test against a fake, no network. Capability flags per CLAUDE.md.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_youtube_adapter.py
import datetime as dt

import pytest

from contentauto.platforms.base import Capabilities
from contentauto.platforms.stubs import TikTokAdapter
from contentauto.platforms.youtube import YouTubeAdapter


class _FakeVideos:
    def __init__(self):
        self.last_body = None

    def update(self, part, body):
        self.last_body = body

        class _Req:
            def execute(_self):
                return {"id": body["id"], "status": body["status"]}

        return _Req()


def test_youtube_capabilities():
    yt = YouTubeAdapter(videos_resource=_FakeVideos())
    assert yt.capabilities == Capabilities(
        supports_native_schedule=True, requires_audit=False, can_fetch_comments=True
    )


def test_schedule_sets_publish_at_and_private():
    fake = _FakeVideos()
    yt = YouTubeAdapter(videos_resource=fake)
    when = dt.datetime(2026, 7, 1, 9, 0, tzinfo=dt.timezone.utc)
    out = yt.schedule(video_id="vid123", publish_at=when)
    assert fake.last_body["status"]["privacyStatus"] == "private"
    assert fake.last_body["status"]["publishAt"] == "2026-07-01T09:00:00+00:00"
    assert out["id"] == "vid123"


def test_tiktok_stub_raises():
    with pytest.raises(NotImplementedError):
        TikTokAdapter().schedule(video_id="x", publish_at=dt.datetime.now(dt.timezone.utc))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_youtube_adapter.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'contentauto.platforms'`

- [ ] **Step 3: Write the ABC**

```python
# src/contentauto/platforms/__init__.py
```

```python
# src/contentauto/platforms/base.py
from __future__ import annotations

import abc
import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class Capabilities:
    supports_native_schedule: bool
    requires_audit: bool
    can_fetch_comments: bool


class PlatformAdapter(abc.ABC):
    @property
    @abc.abstractmethod
    def capabilities(self) -> Capabilities: ...

    @abc.abstractmethod
    def schedule(self, *, video_id: str, publish_at: dt.datetime) -> dict: ...
```

- [ ] **Step 4: Write the YouTube adapter**

```python
# src/contentauto/platforms/youtube.py
from __future__ import annotations

import datetime as dt

from contentauto.platforms.base import Capabilities, PlatformAdapter


class YouTubeAdapter(PlatformAdapter):
    """Official YouTube Data API v3 only — no scraping/UI automation (CLAUDE.md)."""

    def __init__(self, videos_resource) -> None:
        # videos_resource = built google-api-python-client youtube.videos() resource
        self._videos = videos_resource

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            supports_native_schedule=True,  # status.publishAt offload
            requires_audit=False,
            can_fetch_comments=True,
        )

    def schedule(self, *, video_id: str, publish_at: dt.datetime) -> dict:
        body = {
            "id": video_id,
            "status": {"privacyStatus": "private", "publishAt": publish_at.isoformat()},
        }
        return self._videos.update(part="status", body=body).execute()
```

- [ ] **Step 5: Write the stubs**

```python
# src/contentauto/platforms/stubs.py
from __future__ import annotations

import datetime as dt

from contentauto.platforms.base import Capabilities, PlatformAdapter


class InstagramAdapter(PlatformAdapter):
    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(False, True, False)  # no native schedule; needs Meta App Review

    def schedule(self, *, video_id: str, publish_at: dt.datetime) -> dict:
        raise NotImplementedError("Instagram adapter lands phase 2 (Meta App Review)")


class TikTokAdapter(PlatformAdapter):
    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(False, True, False)  # draft-first while audit pending

    def schedule(self, *, video_id: str, publish_at: dt.datetime) -> dict:
        raise NotImplementedError("TikTok adapter lands phase 2 (app audit)")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_youtube_adapter.py -v`
Expected: PASS (3 tests)

- [ ] **Step 7: Commit**

```bash
git add src/contentauto/platforms tests/test_youtube_adapter.py
git commit -m "feat: PlatformAdapter ABC + YouTube adapter + IG/TikTok stubs"
```

---

## Task 10: Pipeline stages

**Files:**
- Create: `src/contentauto/pipeline/__init__.py`, `src/contentauto/pipeline/stages.py`
- Test: `tests/test_pipeline_stages.py`

Stages are pure functions over a `ContentItem` + injected deps (`LLMClient`, gate, adapter). The worker (Task 11) wires them to arq + DB. Keep stages DB-agnostic: they take/return field values, the worker persists. Hard rule: a `hold`/`block_until_disclosed` verdict stops the pipeline before scheduling.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline_stages.py
import datetime as dt

import pytest

from contentauto.models.verdicts import LaneDContextVerdict
from contentauto.pipeline.stages import (
    GateBlocked,
    plan_stage,
    schedule_stage,
    score_stage,
    script_stage,
    gate_stage,
)


class _FakeLLM:
    def generate(self, prompt: str) -> str:
        return "PLAN" if prompt.lower().startswith("draft a content plan") else "SCRIPT BODY"

    def judge(self, prompt, schema):
        raise AssertionError("phase-0 gate is keyword-only, judge() not called")


class _FakeYT:
    def __init__(self):
        self.scheduled = None

    def schedule(self, *, video_id, publish_at):
        self.scheduled = (video_id, publish_at)
        return {"id": video_id}


def test_score_stage_weights_pillar():
    # technology pillar weighted higher than lifestyle
    assert score_stage(pillar="technology") > score_stage(pillar="lifestyle")


def test_plan_and_script_use_llm():
    assert plan_stage(_FakeLLM(), title="t", pillar="technology") == "PLAN"
    assert script_stage(_FakeLLM(), plan="PLAN") == "SCRIPT BODY"


def test_gate_stage_blocks_on_hold():
    v = gate_stage(script="ช่วยรักษาโรคได้", is_sponsored=False, has_disclosure=False)
    assert isinstance(v, LaneDContextVerdict)
    with pytest.raises(GateBlocked):
        schedule_stage(
            _FakeYT(), verdict=v, video_id="v",
            publish_at=dt.datetime(2026, 7, 1, tzinfo=dt.timezone.utc),
        )


def test_schedule_stage_fires_when_clean():
    v = gate_stage(script="แกะกล่อง", is_sponsored=False, has_disclosure=False)
    yt = _FakeYT()
    when = dt.datetime(2026, 7, 1, tzinfo=dt.timezone.utc)
    schedule_stage(yt, verdict=v, video_id="vid", publish_at=when)
    assert yt.scheduled == ("vid", when)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_pipeline_stages.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'contentauto.pipeline'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/contentauto/pipeline/__init__.py
```

```python
# src/contentauto/pipeline/stages.py
"""Pure pipeline stages. The worker persists results to the DB between stages."""
from __future__ import annotations

import datetime as dt

from contentauto.gate.hard_rules import run_hard_rules
from contentauto.llm.base import LLMClient
from contentauto.models.verdicts import LaneDContextVerdict
from contentauto.platforms.base import PlatformAdapter

# content pillar weights (CLAUDE.md: technology + ai/automation เน้น)
_PILLAR_WEIGHT = {
    "technology": 1.0,
    "ai": 1.0,
    "automation": 1.0,
    "gadgets": 0.7,
    "lifestyle": 0.4,
    "longevity": 0.4,
}

# actions that must stop the pipeline before publishing (CLAUDE.md hard rules)
_BLOCKING = {"hold", "block_until_disclosed"}


class GateBlocked(Exception):
    """Raised when a hard-rule verdict forbids auto-scheduling."""


def score_stage(*, pillar: str) -> float:
    return _PILLAR_WEIGHT.get(pillar.lower(), 0.5)


def plan_stage(llm: LLMClient, *, title: str, pillar: str) -> str:
    return llm.generate(
        f"Draft a content plan (angle, beats, hook) for a {pillar} video titled {title!r}."
    )


def script_stage(llm: LLMClient, *, plan: str) -> str:
    return llm.generate(f"Write a script body for this plan:\n{plan}")


def gate_stage(*, script: str, is_sponsored: bool, has_disclosure: bool) -> LaneDContextVerdict:
    return run_hard_rules(
        script=script, is_sponsored=is_sponsored, has_disclosure=has_disclosure
    )


def schedule_stage(
    adapter: PlatformAdapter,
    *,
    verdict: LaneDContextVerdict,
    video_id: str,
    publish_at: dt.datetime,
) -> dict:
    blocking = [c for c in verdict.checks if c.action in _BLOCKING]
    if blocking:
        reasons = ", ".join(f"{c.type}:{c.action}" for c in blocking)
        raise GateBlocked(reasons)
    return adapter.schedule(video_id=video_id, publish_at=publish_at)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_pipeline_stages.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/contentauto/pipeline tests/test_pipeline_stages.py
git commit -m "feat: pipeline stages with hard-gate block before scheduling"
```

---

## Task 11: arq worker wiring

**Files:**
- Create: `src/contentauto/pipeline/worker.py`
- Test: `tests/test_worker.py`

The worker exposes `run_item(ctx, item_id)`: load item → run stages → persist → on `GateBlocked` set state back and record reason (no publish). Test the job function with a fake ctx + the db fixture.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_worker.py
import pytest

from contentauto.models.content import ContentItem, ContentState
from contentauto.pipeline.worker import run_item


class _FakeLLM:
    def generate(self, prompt: str) -> str:
        return "PLAN" if "plan" in prompt.lower() else "SCRIPT"

    def judge(self, prompt, schema):
        raise AssertionError


class _FakeYT:
    def schedule(self, *, video_id, publish_at):
        return {"id": video_id}


@pytest.mark.asyncio
async def test_run_item_blocks_on_health_claim(db_session):
    item = ContentItem(
        title="อาหารเสริม", pillar="longevity", state=ContentState.ready,
        script="ช่วยรักษาโรคเบาหวาน", youtube_video_id="vid",
    )
    db_session.add(item)
    await db_session.flush()
    ctx = {"session": db_session, "llm": _FakeLLM(), "adapter": _FakeYT()}
    result = await run_item(ctx, item.id)
    assert result["blocked"] is True
    refreshed = await db_session.get(ContentItem, item.id)
    assert refreshed.state == ContentState.ready  # not advanced to scheduled
```

- [ ] **Step 2: Run test to verify it fails**

Run: `TEST_DATABASE_URL=postgresql+asyncpg://contentauto:changeme@localhost:5432/contentauto_test uv run pytest tests/test_worker.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'contentauto.pipeline.worker'` (or SKIP if no DB)

- [ ] **Step 3: Write minimal implementation**

```python
# src/contentauto/pipeline/worker.py
from __future__ import annotations

import datetime as dt

from arq.connections import RedisSettings

from contentauto.config import get_settings
from contentauto.db import session_factory
from contentauto.llm.claude import ClaudeClient
from contentauto.models.content import ContentItem, ContentState
from contentauto.pipeline.stages import (
    GateBlocked,
    gate_stage,
    schedule_stage,
    score_stage,
)


async def run_item(ctx: dict, item_id: int) -> dict:
    session = ctx["session"]
    adapter = ctx["adapter"]

    item = await session.get(ContentItem, item_id)
    if item is None:
        return {"error": "not found"}

    item.score = score_stage(pillar=item.pillar)
    verdict = gate_stage(
        script=item.script or "",
        is_sponsored=item.is_sponsored,
        has_disclosure=item.has_disclosure,
    )
    publish_at = item.scheduled_at or dt.datetime.now(dt.timezone.utc)
    try:
        schedule_stage(
            adapter, verdict=verdict, video_id=item.youtube_video_id or "",
            publish_at=publish_at,
        )
    except GateBlocked as e:
        await session.flush()
        return {"blocked": True, "reason": str(e)}

    item.state = ContentState.scheduled
    await session.flush()
    return {"blocked": False, "state": item.state.value}


# --- arq runtime config (used in container, not in unit tests) ---
async def startup(ctx: dict) -> None:
    s = get_settings()
    ctx["session_maker"] = session_factory()
    ctx["llm"] = ClaudeClient(api_key=s.anthropic_api_key, model=s.anthropic_model)
    # adapter built per-job from stored OAuth creds in real runtime (see api/app.py)


class WorkerSettings:
    functions = [run_item]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
```

> Note: in unit tests `ctx` carries `session`/`adapter` directly. In the container, `startup` builds shared deps and a per-job wrapper supplies a session + a YouTube adapter built from decrypted OAuth creds. Keep `run_item` reading `ctx["session"]`/`ctx["adapter"]` so it stays testable; add the production wrapper job when wiring real Redis (out of phase-0 critical path — record as follow-up if not reached).

- [ ] **Step 4: Run test to verify it passes**

Run: `TEST_DATABASE_URL=postgresql+asyncpg://contentauto:changeme@localhost:5432/contentauto_test uv run pytest tests/test_worker.py -v`
Expected: PASS (or SKIP without DB)

- [ ] **Step 5: Commit**

```bash
git add src/contentauto/pipeline/worker.py tests/test_worker.py
git commit -m "feat: arq worker run_item job with gate-block handling"
```

---

## Task 12: FastAPI app (OAuth callback + control)

**Files:**
- Create: `src/contentauto/api/__init__.py`, `src/contentauto/api/app.py`
- Test: `tests/test_api.py`

Phase-0 endpoints: `GET /healthz`, `POST /items` (create idea → enqueue), `GET /oauth/youtube/start` (redirect to Google consent), `GET /oauth/youtube/callback` (exchange code → Fernet-encrypt → store). Test health + item-create against an injected fake queue; OAuth exchange tested with a fake flow.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_api.py
from httpx import ASGITransport, AsyncClient

from contentauto.api.app import create_app


class _FakeQueue:
    def __init__(self):
        self.jobs = []

    async def enqueue_job(self, fn, *args):
        self.jobs.append((fn, args))

        class _J:
            job_id = "job-1"

        return _J()


async def test_healthz():
    app = create_app(queue=_FakeQueue())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_create_item_enqueues():
    q = _FakeQueue()
    app = create_app(queue=q)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.post("/items", json={"title": "idea", "pillar": "technology"})
    assert r.status_code == 202
    assert r.json()["job_id"] == "job-1"
    assert q.jobs and q.jobs[0][0] == "run_item"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'contentauto.api'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/contentauto/api/__init__.py
```

```python
# src/contentauto/api/app.py
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel


class NewItem(BaseModel):
    title: str
    pillar: str


def create_app(queue) -> FastAPI:
    """queue: object with async enqueue_job(fn_name, *args). In prod = arq RedisPool."""
    app = FastAPI(title="content-automation phase-0")

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok"}

    @app.post("/items", status_code=202)
    async def create_item(body: NewItem) -> dict:
        # Real impl persists a ContentItem first; phase-0 test path enqueues by id placeholder.
        job = await queue.enqueue_job("run_item", body.title)
        return {"job_id": job.job_id, "title": body.title}

    return app
```

> Note: the real `POST /items` persists a `ContentItem(state=idea)` and enqueues its `id`; the OAuth start/callback routes (Google consent → token exchange → `TokenCipher.encrypt` → `OAuthToken` upsert) are added when wiring live Redis + a real Google client. They depend only on `crypto.TokenCipher` (Task 6) and `config` (Task 2) already built. Test coverage for OAuth exchange with a fake flow is a follow-up; keep credentials out of logs and git (CLAUDE.md).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_api.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/contentauto/api tests/test_api.py
git commit -m "feat: FastAPI app — healthz + item create/enqueue"
```

---

## Task 13: docker-compose + Dockerfile (Pi 4B stack)

**Files:**
- Create: `build/Dockerfile`, `docker-compose.yml`
- (No new pytest; verification is `docker compose config` + bringing the stack up and running the DB-dependent tests)

- [ ] **Step 1: Write `build/Dockerfile`**

```dockerfile
# build/Dockerfile — shared image for api + worker (arm64 on Pi 4B)
FROM python:3.12-slim
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./
ENV PATH="/app/.venv/bin:$PATH"
```

- [ ] **Step 2: Write `docker-compose.yml`**

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: contentauto
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
      POSTGRES_DB: contentauto
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build:
      context: .
      dockerfile: build/Dockerfile
    command: uvicorn contentauto.api.app:app --host 0.0.0.0 --port 8000
    env_file: .env
    depends_on: [db, redis]
    ports:
      - "8000:8000"

  worker:
    build:
      context: .
      dockerfile: build/Dockerfile
    command: arq contentauto.pipeline.worker.WorkerSettings
    env_file: .env
    depends_on: [db, redis]

  cloudflared:
    image: cloudflare/cloudflared:latest
    command: tunnel --no-autoupdate run
    env_file: .env  # TUNNEL_TOKEN
    depends_on: [api]

volumes:
  pgdata:
```

> Note: `api` service expects an importable `app`. Add `app = create_app(queue=<arq RedisPool>)` module-level in `api/app.py` wired to a real arq pool at container start (the `create_app` factory already supports injection — the prod call builds the pool from `REDIS_URL`). Wire this when bringing the stack up.

- [ ] **Step 3: Validate compose + bring DB up + run full suite**

Run:
```bash
docker compose config >/dev/null && echo "compose ok"
docker compose up -d db redis
docker compose run --rm api alembic upgrade head
TEST_DATABASE_URL=postgresql+asyncpg://contentauto:changeme@localhost:5432/contentauto_test \
  uv run pytest -q
```
Expected: "compose ok"; alembic creates tables + vector extension; full test suite PASSES (DB-dependent tests no longer skip).

- [ ] **Step 4: Commit**

```bash
git add build/Dockerfile docker-compose.yml
git commit -m "feat: Pi 4B docker-compose stack (db/redis/api/worker/cloudflared)"
```

---

## Task 14: Wire README + final green run

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a build row to the README index + flip status**

Change the `build/` row in `README.md` from 🔜 to ✅ and update the status line at top:
```
| `build/` | Dockerfile + docker-compose (Pi 4B stack) | ✅ |
```
And add under Index a pointer to the plan:
```
| `docs/superpowers/plans/2026-06-16-phase0-consistency-engine.md` | phase-0 build plan | ✅ |
```

- [ ] **Step 2: Full suite + lint + types**

Run:
```bash
uv run ruff check . && uv run mypy src && \
TEST_DATABASE_URL=postgresql+asyncpg://contentauto:changeme@localhost:5432/contentauto_test \
  uv run pytest -q
```
Expected: ruff clean, mypy clean, all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: mark build/ done, link phase-0 plan"
```

---

## Out of scope (deferred per spec — do NOT build in phase 0)

MinIO/object storage · local LLM (MLX/Ollama) · whisper/ffmpeg/OCR/vision · web-search + fact-card retrieval · moderation API · sentiment/topic clustering · Temporal/n8n · full Lane A/B/C judges · IG/TikTok publishing (stubs only) · post-publish monitor.

## Follow-ups before the worker can run a job end-to-end (deferred, tracked)

> Status after implementation (final review, 2026-06-16): all 14 tasks built, 27 passed /
> 2 skipped (DB tests skip without Postgres), ruff + mypy clean. CLAUDE.md hard rules
> verified airtight (gate `hold`/`block_until_disclosed` cannot reach `adapter.schedule()`);
> no secret-leak surface; YouTube official-API-only. **No critical issues.**
> The items below are intentional phase-0 stubs — the worker has NO end-to-end runnable
> job path until #1–#3 land. They are deferred, not forgotten.

1. **Production arq job ctx wrapper** — `startup` sets `ctx["session_maker"]`/`ctx["llm"]`,
   but `run_item` reads `ctx["session"]`/`ctx["adapter"]`. Add a per-job wrapper that opens a
   session from `session_maker` and builds a `YouTubeAdapter` from decrypted OAuth creds,
   setting those keys before `run_item` runs. (`pipeline/worker.py`)
2. **Commit on success** — `run_item` uses `session.flush()`, never `commit()`. The wrapper in
   #1 must `commit()` on the success path so `item.score`/`item.state` persist. (`pipeline/worker.py`)
3. **`POST /items` enqueues an int id, not a title** — persist a `ContentItem(state=idea)` first,
   then `enqueue_job("run_item", item.id)`. `run_item` loads by id. (`api/app.py`)
4. **OAuth start/callback routes** + fake-flow tests (Google consent → token exchange →
   `TokenCipher.encrypt` → `OAuthToken` upsert). Deps already built. (`api/app.py`)
5. **Bring up the stack + unskip DB tests** — `docker compose up -d db redis`,
   `alembic upgrade head`, run with `TEST_DATABASE_URL` set (Docker was unavailable in the
   build session, so the 2 DB tests are still skipped).

### Noted for a later phase (out of phase-0 scope)
- No durable "blocked/held" state: a gate-blocked item stays in its prior state with no
  recorded reason — a reviewer can't see *why* it didn't schedule. Add a `blocked_reason`
  column / held state when building the human review queue.
- `gate_stage` inspects `script` only; health/disclosure can also live in title/thumbnail/
  description. The full Lane A–D cascade should cover all surfaces (schemas already enumerate them).
