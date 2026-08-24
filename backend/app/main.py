from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import admin, advice, chat, health, knowledge, listings, vehicles
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging_config import configure_logging
from app.core.middleware import RequestContextMiddleware

configure_logging(debug=settings.DEBUG)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AutoAI — Independent AI car buying assistant for Pakistan's automotive "
        "market. Not affiliated with or endorsed by PakWheels."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(vehicles.router)
app.include_router(chat.router)
app.include_router(listings.router)
app.include_router(knowledge.router)
app.include_router(advice.router)
app.include_router(admin.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "AutoAI API",
        "docs": "/docs",
        "health": "/health",
        "search": "/api/vehicles/search",
        "vehicle_detail": "/api/vehicles/{id}",
        "recommend": "/api/vehicles/recommend",
        "compare": "/api/vehicles/compare",
        "extract": "/api/chat/extract",
        "analyze_listing": "/api/listings/analyze",
        "knowledge_ask": "/api/knowledge/ask",
        "buying_advice": "/api/advice/ask",
        "admin_metrics": "/api/admin/metrics",
        "maintenance": "/api/vehicles/maintenance",
        "disclaimer": "Independent proof of concept — not affiliated with PakWheels.",
    }
