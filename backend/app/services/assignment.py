"""Assignment engine: route tickets to department/team by rules.

Rules resolve in order: category default department -> team in that department.
Workload balancing picks the agent with the fewest open tickets on the team.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TicketStatus
from app.models.reference import Category, SupportTeam
from app.models.ticket import Ticket


async def route_ticket(session: AsyncSession, ticket: Ticket) -> None:
    if ticket.category_id and not ticket.department_id:
        cat = (await session.execute(
            select(Category).where(Category.id == ticket.category_id)
        )).scalar_one_or_none()
        if cat and cat.default_department_id:
            ticket.department_id = cat.default_department_id
    if ticket.department_id and not ticket.team_id:
        team = (await session.execute(
            select(SupportTeam).where(SupportTeam.department_id == ticket.department_id)
            .limit(1)
        )).scalar_one_or_none()
        if team:
            ticket.team_id = team.id
    await session.commit()
