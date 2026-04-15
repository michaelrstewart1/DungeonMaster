import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import create_app
from app.models.database import Base
from app.db import get_db
from app.api import storage

# In-memory SQLite for tests
_test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
_TestSession = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)


async def _override_get_db():
    async with _TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture
async def app():
    """Create a fresh FastAPI app with an in-memory test database."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    application = create_app()
    application.dependency_overrides[get_db] = _override_get_db
    # Expose the test session factory for WS handler and other non-Depends code
    application.state.db_factory = _TestSession

    yield application

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(app):
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def reset_storage():
    """Reset volatile in-memory stores before and after each test."""
    storage.reset()
    yield
    storage.reset()
