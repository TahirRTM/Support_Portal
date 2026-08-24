from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import admin_auth, admin_tickets, client_tickets, health, reference

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(reference.router)
api_router.include_router(client_tickets.router)
api_router.include_router(admin_auth.router)
api_router.include_router(admin_tickets.router)
