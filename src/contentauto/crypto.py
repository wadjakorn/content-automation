from cryptography.fernet import Fernet


class TokenCipher:
    """Encrypt/decrypt OAuth token JSON for at-rest storage (CLAUDE.md: no plaintext secrets)."""

    def __init__(self, key: str) -> None:
        self._f = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> bytes:
        return self._f.encrypt(plaintext.encode())

    def decrypt(self, blob: bytes) -> str:
        return self._f.decrypt(blob).decode()
