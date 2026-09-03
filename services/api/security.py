from passlib.hash import bcrypt

try:
    from .dependencies import create_access_token, get_current_user, oauth2_scheme
except ImportError:
    from dependencies import create_access_token, get_current_user, oauth2_scheme


def hash_password(password: str) -> str:
    return bcrypt.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.verify(password, hashed_password)