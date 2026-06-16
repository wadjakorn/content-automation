import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient

from contentauto.api.app import create_app
from contentauto.crypto import TokenCipher
from contentauto.platforms import token_store


class _FakeCreds:
    def to_json(self):
        return '{"refresh_token": "rt", "token": "at"}'


class _FakeFlow:
    def __init__(self):
        self.redirect_uri = None
        self.credentials = _FakeCreds()
        self.fetched = None

    def authorization_url(self, **kw):
        return ("https://accounts.google.com/o/oauth2/auth?state=ST", "ST")

    def fetch_token(self, code):
        self.fetched = code


def _app(session_maker, cipher):
    return create_app(
        session_maker=session_maker,
        flow_factory=lambda: _FakeFlow(),
        cipher=cipher,
    )


@pytest.mark.asyncio
async def test_login_redirects_to_google(session_maker):
    cipher = TokenCipher(Fernet.generate_key().decode())
    app = _app(session_maker, cipher)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/oauth/youtube/login", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"].startswith("https://accounts.google.com")


@pytest.mark.asyncio
async def test_callback_exchanges_and_stores_token(session_maker):
    cipher = TokenCipher(Fernet.generate_key().decode())
    app = _app(session_maker, cipher)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        await c.get("/oauth/youtube/login", follow_redirects=False)  # stash state ST
        r = await c.get("/oauth/youtube/callback?code=AUTHCODE&state=ST")
    assert r.status_code == 200
    assert r.json() == {"status": "connected", "platform": "youtube"}

    async with session_maker() as s:
        assert await token_store.load_token(s, cipher, "youtube") == (
            '{"refresh_token": "rt", "token": "at"}'
        )


@pytest.mark.asyncio
async def test_callback_rejects_bad_state(session_maker):
    cipher = TokenCipher(Fernet.generate_key().decode())
    app = _app(session_maker, cipher)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        await c.get("/oauth/youtube/login", follow_redirects=False)
        r = await c.get("/oauth/youtube/callback?code=AUTHCODE&state=WRONG")
    assert r.status_code == 400  # CSRF state mismatch
