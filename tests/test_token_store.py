import pytest
from cryptography.fernet import Fernet

from contentauto.crypto import TokenCipher
from contentauto.models.content import OAuthToken
from contentauto.platforms import token_store


@pytest.mark.asyncio
async def test_save_then_load_roundtrip(db_session):
    cipher = TokenCipher(Fernet.generate_key().decode())
    await token_store.save_token(db_session, cipher, "youtube", '{"refresh_token": "rt"}')
    await db_session.flush()

    loaded = await token_store.load_token(db_session, cipher, "youtube")
    assert loaded == '{"refresh_token": "rt"}'

    # stored ciphertext must NOT be the plaintext token at rest
    row = await db_session.get(OAuthToken, 1)
    assert b'{"refresh_token": "rt"}' not in row.ciphertext
    assert row.ciphertext.startswith(b"gAAAA")  # Fernet token prefix


@pytest.mark.asyncio
async def test_save_upserts_existing_platform(db_session):
    cipher = TokenCipher(Fernet.generate_key().decode())
    await token_store.save_token(db_session, cipher, "youtube", "old")
    await token_store.save_token(db_session, cipher, "youtube", "new")
    await db_session.flush()
    assert await token_store.load_token(db_session, cipher, "youtube") == "new"


@pytest.mark.asyncio
async def test_load_missing_returns_none(db_session):
    cipher = TokenCipher(Fernet.generate_key().decode())
    assert await token_store.load_token(db_session, cipher, "youtube") is None
