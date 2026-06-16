from cryptography.fernet import Fernet

from contentauto.crypto import TokenCipher


def test_encrypt_decrypt_roundtrip():
    key = Fernet.generate_key().decode()
    cipher = TokenCipher(key)
    blob = cipher.encrypt('{"access_token": "abc", "refresh_token": "r"}')
    assert isinstance(blob, bytes)
    assert b"abc" not in blob  # not plaintext at rest
    assert cipher.decrypt(blob) == '{"access_token": "abc", "refresh_token": "r"}'
