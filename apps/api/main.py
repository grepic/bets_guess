"""SmartBets Pro API - Main FastAPI application."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routes import catalog, games, odds, predictions, admin, builder, signals


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: seed demo stores. Shutdown: cleanup."""
    from apps.api.services.demo_seed import seed_demo_data
    from apps.api.routes import signals as signals_module

    data = seed_demo_data()
    signals_module._signals_store.extend(data["signals"])
    signals_module._moves_store.extend(data["moves"])
    signals_module._adjusted_store.extend(data["adjusted_predictions"])
    yield


app = FastAPI(
    title="SmartBets Pro API",
    description=(
        "Sports analytics platform providing probability estimates, fair odds, "
        "and value identification across NBA, NHL, Soccer, and Tennis markets.\n\n"
        "**DISCLAIMER**: This platform provides statistical analysis only. "
        "Probabilities are model estimates, NOT guarantees. "
        "All sports betting involves risk. Never bet more than you can afford to lose.\n\n"
        "**Responsible Gambling**: If you or someone you know has a gambling problem, "
        "call 1-800-522-4700 (National Problem Gambling Helpline)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router)
app.include_router(games.router)
app.include_router(odds.router)
app.include_router(predictions.router)
app.include_router(admin.router)
app.include_router(builder.router)
app.include_router(signals.router)


@app.get("/")
async def root():
    return {
        "name": "SmartBets Pro API",
        "version": "1.0.0",
        "status": "running",
        "sports": ["soccer", "nba", "nhl", "tennis"],
        "disclaimer": (
            "This platform provides statistical analysis and probability estimates only. "
            "These are NOT guarantees of outcomes. All sports betting involves risk."
        ),
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
