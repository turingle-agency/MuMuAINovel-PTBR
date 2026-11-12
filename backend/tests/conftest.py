import os
import tempfile

# Antes de qualquer import de `app`: banco SQLite temporário e logs só no console.
_TMP_DIR = tempfile.mkdtemp(prefix="mumu-tests-")
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_TMP_DIR}/test.db")
os.environ.setdefault("LOG_TO_FILE", "false")

import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402


@pytest_asyncio.fixture
async def db_session(tmp_path):
    """AsyncSession em um SQLite temporário com todas as tabelas criadas."""
    from app.database import Base  # importa todos os modelos; não importa app.main

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/test.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_codex_cooldown():
    """A memória de falhas do Codex é global ao processo; isola cada teste."""
    from app.services.ai_providers.codex_provider import reset_codex_cooldown

    reset_codex_cooldown()
    yield
    reset_codex_cooldown()
