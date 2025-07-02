import pyotp

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_mfa_secret() -> str:
    return pyotp.random_base32()

def get_totp_uri(username: str, secret: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="Retrifix")

def verify_mfa_token(secret: str, token: str) -> bool:
    return pyotp.TOTP(secret).verify(token)
