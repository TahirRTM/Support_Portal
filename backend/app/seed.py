"""Idempotent, deterministic seed.

Seeds roles, permissions, departments, teams, categories, priorities, and an
initial admin. The admin password is read from ADMIN_BOOTSTRAP_PASSWORD; it is
never hardcoded. Running multiple times makes no duplicate rows.

Usage: python -m app.seed
"""
from __future__ import annotations

import asyncio
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.core.logging import configure_logging, get_logger
from app.models.reference import Category, Department, Priority, SupportTeam
from app.models.user import Permission, Role, User
from app.security.passwords import hash_password

log = get_logger(__name__)

PERMISSIONS = [
    "ticket.read", "ticket.update", "ticket.assign", "ticket.reply",
    "ticket.delete", "user.manage", "role.manage", "kb.manage",
    "settings.manage", "analytics.read", "audit.read",
]

ROLES = {
    "admin": PERMISSIONS,
    "supervisor": ["ticket.read", "ticket.update", "ticket.assign", "ticket.reply",
                   "kb.manage", "analytics.read"],
    "agent": ["ticket.read", "ticket.update", "ticket.reply"],
}

DEPARTMENTS = [("Technical Support", "technical-support"),
               ("Billing", "billing"), ("General", "general")]
TEAMS = [("Tier 1", "tier-1", "technical-support"),
         ("Tier 2", "tier-2", "technical-support"),
         ("Billing Team", "billing-team", "billing")]
CATEGORIES = [("Technical Issue", "technical-issue", "technical-support"),
              ("Billing Question", "billing-question", "billing"),
              ("Feature Request", "feature-request", "general"),
              ("General Inquiry", "general-inquiry", "general")]
# name, slug, rank, response_min, resolution_min
PRIORITIES = [("Urgent", "urgent", 10, 60, 480),
              ("High", "high", 20, 120, 960),
              ("Medium", "medium", 30, 240, 1920),
              ("Low", "low", 40, 480, 3840)]


async def _get_or_create(session: AsyncSession, model, *, defaults=None, **filters):
    obj = (await session.execute(select(model).filter_by(**filters))).scalar_one_or_none()
    if obj:
        return obj, False
    obj = model(**filters, **(defaults or {}))
    session.add(obj)
    await session.flush()
    return obj, True


async def seed() -> None:
    async with SessionLocal() as session:
        perms: dict[str, Permission] = {}
        for code in PERMISSIONS:
            p, _ = await _get_or_create(session, Permission, code=code)
            perms[code] = p
        roles: dict[str, Role] = {}
        for slug, codes in ROLES.items():
            r, _ = await _get_or_create(session, Role, slug=slug,
                                        defaults={"name": slug.title()})
            r.permissions = [perms[c] for c in codes]
            roles[slug] = r
        deps: dict[str, Department] = {}
        for name, slug in DEPARTMENTS:
            d, _ = await _get_or_create(session, Department, slug=slug,
                                        defaults={"name": name})
            deps[slug] = d
        for name, slug, dep_slug in TEAMS:
            await _get_or_create(session, SupportTeam, slug=slug,
                                 defaults={"name": name, "department_id": deps[dep_slug].id})
        for name, slug, dep_slug in CATEGORIES:
            await _get_or_create(session, Category, slug=slug,
                                 defaults={"name": name,
                                           "default_department_id": deps[dep_slug].id})
        for name, slug, rank, resp, res in PRIORITIES:
            await _get_or_create(session, Priority, slug=slug,
                                 defaults={"name": name, "rank": rank,
                                           "sla_response_minutes": resp,
                                           "sla_resolution_minutes": res})

        admin_email = os.getenv("ADMIN_BOOTSTRAP_EMAIL", "admin@example.com").lower()
        admin_pw = os.getenv("ADMIN_BOOTSTRAP_PASSWORD")
        existing = (await session.execute(
            select(User).where(User.email == admin_email)
        )).scalar_one_or_none()
        if not existing:
            if not admin_pw:
                log.warning("admin_not_seeded_no_password",
                            hint="set ADMIN_BOOTSTRAP_PASSWORD to seed the admin user")
            else:
                user = User(email=admin_email, full_name="Administrator",
                            password_hash=hash_password(admin_pw), is_active=True,
                            is_superuser=True)
                user.roles = [roles["admin"]]
                session.add(user)
                log.info("admin_seeded", email=admin_email)
        await session.commit()
        log.info("seed_complete")


if __name__ == "__main__":
    configure_logging()
    asyncio.run(seed())
