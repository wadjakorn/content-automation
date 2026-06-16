import json

from contentauto.platforms import youtube_auth
from contentauto.platforms.youtube import YouTubeAdapter


def test_login_url_points_at_google_and_returns_state():
    flow = youtube_auth.build_flow(
        client_id="cid", client_secret="secret",
        redirect_uri="http://localhost:8000/oauth/youtube/callback",
    )
    url, state = youtube_auth.login_url(flow)
    assert url.startswith("https://accounts.google.com/o/oauth2/auth")
    assert "access_type=offline" in url
    assert "prompt=consent" in url  # force refresh_token issuance
    assert state  # opaque CSRF token


def test_adapter_from_json_builds_youtube_adapter(monkeypatch):
    captured = {}

    class _Service:
        def videos(self):
            return "VIDEOS_RESOURCE"

    def _fake_build(serviceName, version, credentials, cache_discovery):
        captured["args"] = (serviceName, version, cache_discovery)
        return _Service()

    monkeypatch.setattr(youtube_auth, "_build_service", _fake_build)
    token_json = json.dumps({
        "token": "at", "refresh_token": "rt", "client_id": "cid",
        "client_secret": "sec", "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/youtube"],
    })
    adapter = youtube_auth.adapter_from_json(token_json)
    assert isinstance(adapter, YouTubeAdapter)
    assert captured["args"] == ("youtube", "v3", False)
