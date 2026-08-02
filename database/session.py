from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    future=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# Notice:
    # expire_on_commit=False avoids unnecessary database reloads.
    # autoflush=False gives us explicit control.
    # future=True enables SQLAlchemy 2.x behavior.