from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Default to a local SQLite database for zero-config startup
# To use PostgreSQL, set DATABASE_URL="postgresql://user:password@localhost:5432/workout_tracker"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./workout_tracker.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
