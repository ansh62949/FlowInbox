import uuid
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.agent import AuditLog


class AuditLogger:
    """Records human-readable execution audit trails per agent run."""

    @staticmethod
    async def log_step(
        db: AsyncSession,
        user_id: uuid.UUID,
        agent_run_id: uuid.UUID,
        step_description: str,
        status: str = "info"
    ) -> None:
        log = AuditLog(
            user_id=user_id,
            agent_run_id=agent_run_id,
            step_description=step_description,
            status=status
        )
        db.add(log)
        await db.commit()

    @staticmethod
    async def get_run_audit_trail(db: AsyncSession, agent_run_id: uuid.UUID) -> List[Dict[str, Any]]:
        stmt = select(AuditLog).where(AuditLog.agent_run_id == agent_run_id).order_by(AuditLog.created_at.asc())
        res = await db.execute(stmt)
        logs = res.scalars().all()
        return [
            {
                "id": str(l.id),
                "step_description": l.step_description,
                "status": l.status,
                "timestamp": l.created_at.isoformat()
            }
            for l in logs
        ]
