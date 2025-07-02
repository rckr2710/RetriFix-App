from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import Settings

# DB_USER = "rf"
# DB_PASS = "rf"
# DB_HOST = "localhost"  # If FastAPI runs outside Docker. Use "db" if both are in same docker network.
# DB_PORT = "5432"
# DB_NAME = "rfdb"

# DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

DATABASE_URL = f"postgresql://{Settings.DB_USER}:{Settings.DB_PASS}@{Settings.DB_HOST}:{Settings.DB_PORT}/{Settings.DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
