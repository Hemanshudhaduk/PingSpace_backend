from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os


DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.strip()

# Check if DATABASE_URL is set
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file. Please ensure it is set correctly for PostgreSQL.")

print(f"Connecting to database host: {DATABASE_URL.split('@')[-1].split(':')[0]}")
# Connect to the PostgreSQL database
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
