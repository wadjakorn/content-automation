import json

import pytest
from cryptography.fernet import Fernet

from contentauto.crypto import TokenCipher
from contentauto.pipeline.worker import build_adapter
from contentauto.platforms import token_store, youtube_auth
from contentauto.platforms.local import LocalAdapter
from contentauto.platforms.youtube import YouTubeAdapter


@pytest.mark.asyncio
async def test_build_adapter_uses_youtube_when_token_present(session_maker, monkeypatch):
    cipher = TokenCipher(Fernet.generate_key().decode())
    token = json.dumps({
        "token": "at", "refresh_token": "rt", "client_id": "c",
        "client_secret": "s", "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": youtube_auth.SCOPES,
    })
    async with session_maker() as s:
        await token_store.save_token(s, cipher, "youtube", token)
        await s.commit()

    class _Svc:
        def videos(self):
            return "V"

    monkeypatch.setattr(youtube_auth, "_build_service", lambda *a, **k: _Svc())
    adapter = await build_adapter(session_maker, cipher)
    assert isinstance(adapter, YouTubeAdapter)


@pytest.mark.asyncio
async def test_build_adapter_falls_back_to_local_without_token(session_maker):
    cipher = TokenCipher(Fernet.generate_key().decode())
    adapter = await build_adapter(session_maker, cipher)
    assert isinstance(adapter, LocalAdapter)
