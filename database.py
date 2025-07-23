from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from config import settings


DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASS}@{os.getenv("DB_HOST","localhost")}:{settings.DB_PORT}/{settings.DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
