import pyotp

def generate_mfa_secret() -> str:
    return pyotp.random_base32()

def get_totp_uri(username: str, secret: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="Retrifix")

def verify_mfa_token(secret: str, token: str) -> bool:
    return pyotp.TOTP(secret).verify(token)
