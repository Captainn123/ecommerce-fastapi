import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

# Get the URL from .env, but default to sqlite if it's missing
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecommerce.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
# ... keep the SessionLocal line the same ...



# SessionLocal is what we will use to query the database later
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)