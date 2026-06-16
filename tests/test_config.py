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
