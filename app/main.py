from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import settings
from app.database import engine, Base
from app.routers import auth, products, materials, sales, expenses, dashboard
from app.routers import channels
from app.routers import settings as settings_router
from app.routers import fair_prep
import app.models


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Migrate existing sales table: add channel_id if only buyer_id exists
        await conn.execute(text("""
            DO $$ BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='sales' AND column_name='buyer_id'
                ) AND NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='sales' AND column_name='channel_id'
                ) THEN
                    ALTER TABLE sales ADD COLUMN channel_id UUID
                        REFERENCES sales_channels(id) ON DELETE SET NULL;
                END IF;
            END $$;
        """))
    yield


app = FastAPI(
    lifespan=lifespan,
    title="CraftManager API",
    description="API for craft/handmade toy management system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(materials.router, prefix="/api/v1")
app.include_router(channels.router, prefix="/api/v1")
app.include_router(sales.router, prefix="/api/v1")
app.include_router(expenses.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(settings_router.router, prefix="/api/v1")
app.include_router(fair_prep.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"name": "CraftManager API", "version": "1.0.0", "docs": "/docs"}
