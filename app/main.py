from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import auth, products, materials, buyers, sales, expenses, dashboard
from app.routers import settings as settings_router
import app.models  # ensure all models are registered with Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


# Create app
app = FastAPI(
    lifespan=lifespan,
    title="CraftManager API",
    description="API for craft/handmade toy management system",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(materials.router, prefix="/api/v1")
app.include_router(buyers.router, prefix="/api/v1")
app.include_router(sales.router, prefix="/api/v1")
app.include_router(expenses.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(settings_router.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "CraftManager API",
        "version": "1.0.0",
        "docs": "/docs",
    }
