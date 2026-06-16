"""YouTube OAuth helpers — official Google libraries only (CLAUDE.md: no scraping).

Pure functions over google-auth-oauthlib + google-api-python-client; no DB here.
Token persistence lives in ``token_store``; the FastAPI routes orchestrate the two.

The google libraries ship no type stubs, so the Flow/Credentials objects cross
this module as ``Any`` — the same deliberate untyped seam as ``youtube.py``'s
videos_resource. Do not tighten it.
"""
from __future__ import annotations

import json
from typing import Any

from contentauto.platforms.youtube import YouTubeAdapter

# youtube scope = manage videos (status.publishAt scheduling needs write access)
SCOPES = ["https://www.googleapis.com/auth/youtube"]

_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
_TOKEN_URI = "https://oauth2.googleapis.com/token"


def build_flow(*, client_id: str, client_secret: str, redirect_uri: str) -> Any:
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": _AUTH_URI,
                "token_uri": _TOKEN_URI,
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = redirect_uri
    return flow


def login_url(flow: Any) -> tuple[str, str]:
    """Return (consent_url, state). offline+consent => refresh_token issued."""
    url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )
    return url, state


def fetch_credentials(flow: Any, code: str) -> Any:
    flow.fetch_token(code=code)
    return flow.credentials


def credentials_to_json(creds: Any) -> str:
    result: str = creds.to_json()
    return result


def _build_service(serviceName: str, version: str, credentials: Any, cache_discovery: bool) -> Any:
    # Wrapped so tests can monkeypatch without importing googleapiclient at module load.
    from googleapiclient.discovery import build

    return build(serviceName, version, credentials=credentials, cache_discovery=cache_discovery)


def adapter_from_json(token_json: str) -> YouTubeAdapter:
    """Rebuild a live YouTubeAdapter from a stored (decrypted) token JSON blob."""
    from google.oauth2.credentials import Credentials

    # from_authorized_user_info is untyped in google-auth; cross it as Any
    from_info: Any = Credentials.from_authorized_user_info
    creds = from_info(json.loads(token_json), SCOPES)
    service = _build_service("youtube", "v3", credentials=creds, cache_discovery=False)
    return YouTubeAdapter(videos_resource=service.videos())
