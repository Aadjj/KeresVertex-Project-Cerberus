from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import config

engine_args = {
    "echo": config.settings.DEBUG,
    "future": True,
}

if "sqlite" in config.settings.DATABASE_URL:
    engine_args["poolclass"] = StaticPool
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(config.settings.DATABASE_URL, **engine_args)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)