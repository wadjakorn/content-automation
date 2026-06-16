"""Encrypted OAuth-token persistence — Fernet ciphertext only, never plaintext.

One row per platform (``OAuthToken.platform`` is unique). save_token upserts.
Callers own the session lifecycle (flush/commit); these helpers only stage rows.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from contentauto.crypto import TokenCipher
from contentauto.models.content import OAuthToken


async def save_token(
    session: AsyncSession, cipher: TokenCipher, platform: str, token_json: str
) -> None:
    blob = cipher.encrypt(token_json)
    row = (
        await session.execute(select(OAuthToken).where(OAuthToken.platform == platform))
    ).scalar_one_or_none()
    if row is None:
        session.add(OAuthToken(platform=platform, ciphertext=blob))
    else:
        row.ciphertext = blob


async def load_token(
    session: AsyncSession, cipher: TokenCipher, platform: str
) -> str | None:
    row = (
        await session.execute(select(OAuthToken).where(OAuthToken.platform == platform))
    ).scalar_one_or_none()
    return None if row is None else cipher.decrypt(row.ciphertext)
