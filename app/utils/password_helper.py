import hashlib
import bcrypt


def _prepare(password: str) -> bytes:
    """Pre-hash with SHA-256 so bcrypt never receives more than 32 bytes,
    safely supporting passwords longer than bcrypt's 72-byte limit."""
    return hashlib.sha256(password.encode("utf-8")).digest()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(_prepare(plain), hashed.encode("utf-8"))
