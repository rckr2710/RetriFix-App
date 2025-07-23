from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    UPLOAD_DIR : str
    # LDAP_SERVER : str
    ADMIN_DN : str
    ADMIN_PASSWORD : str
    BASE_DN : str

    class Config:
        env_file = ".env"

# Singleton pattern to reuse settings
settings = Settings()
