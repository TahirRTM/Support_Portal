"""Public reference data used by the client create form."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import db_session
from app.models.reference import Category, Priority

router = APIRouter(prefix="/reference", tags=["reference"])


class Option(BaseModel):
    id: str
    name: str


@router.get("/categories", response_model=list[Option])
async def list_categories(session: AsyncSession = Depends(db_session)) -> list[Option]:
    rows = (await session.execute(select(Category).order_by(Category.name))).scalars()
    return [Option(id=str(c.id), name=c.name) for c in rows]


@router.get("/priorities", response_model=list[Option])
async def list_priorities(session: AsyncSession = Depends(db_session)) -> list[Option]:
    rows = (await session.execute(select(Priority).order_by(Priority.rank))).scalars()
    return [Option(id=str(p.id), name=p.name) for p in rows]
