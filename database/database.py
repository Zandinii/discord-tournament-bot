from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///tournament.db')

# Skapa async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Sätt till True för att se SQL queries
    future=True
)

# Session factory
async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base class för models
Base = declarative_base()

async def init_db():
    """Skapa alla tabeller i databasen"""
    # VIKTIGT: Importera models här för att Base ska känna till dem
    from database import models  # Detta laddar alla models
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Databas initierad!")

async def get_session() -> AsyncSession:
    """Hämta en databas-session"""
    async with async_session() as session:
        yield session