import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models import (
    User,
    Product,
    Material,
    ProductMaterial,
    Buyer,
    Sale,
    SaleItem,
    Expense,
)
from app.auth.utils import hash_password, create_access_token
import uuid
from datetime import datetime


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://craft_user:craft_pass@localhost:5433/craftmanager_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(async_engine):
    """Create a test database session"""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        future=True,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def client(async_engine):
    """Create test client with database dependency override"""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        future=True,
    )

    async def override_get_db():
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Clear database before each test
        async with async_session_maker() as session:
            await session.execute(text("TRUNCATE users, products, materials, product_materials, buyers, sales, sale_items, expenses RESTART IDENTITY CASCADE"))
            await session.commit()

        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def user(db_session):
    """Create a test user"""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=hash_password("testpassword"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(user):
    """Create auth headers for test user"""
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def second_user(db_session):
    """Create a second test user for isolation testing"""
    user = User(
        id=uuid.uuid4(),
        email="test2@example.com",
        hashed_password=hash_password("testpassword2"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def second_auth_headers(second_user):
    """Create auth headers for second test user"""
    token = create_access_token(data={"sub": str(second_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def material(user, db_session):
    """Create a test material"""
    material = Material(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Cotton",
        unit="g",
        price_per_unit="10.00",
        stock_qty="1000.000",
    )
    db_session.add(material)
    await db_session.commit()
    await db_session.refresh(material)
    return material


@pytest.fixture
async def product(user, db_session):
    """Create a test product"""
    product = Product(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Test Toy",
        description="A test toy",
        category="soft",
        sale_price="50.00",
        stock_qty=10,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


@pytest.fixture
async def buyer(user, db_session):
    """Create a test buyer"""
    buyer = Buyer(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Test Buyer",
        contact="+1234567890",
        notes="Test buyer",
    )
    db_session.add(buyer)
    await db_session.commit()
    await db_session.refresh(buyer)
    return buyer
