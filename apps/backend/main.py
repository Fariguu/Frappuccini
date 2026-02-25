"""
Entry point FastAPI per il backend Frappuccini.
Solo creazione app, CORS e montaggio router.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, map as map_routes, traffic
from config import CORS_ORIGINS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(map_routes.router)
app.include_router(traffic.router)
