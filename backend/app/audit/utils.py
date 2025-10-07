from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional
from uuid import UUID
import json

from ..models import AuditLog
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

async def log_audit_entry(
    db: AsyncSession,
    user_id: Optional[UUID],
    action: str,  # 'CREATE', 'UPDATE', 'DELETE'
    table_name: str,
    record_id: Optional[int],
    old_data: Optional[dict] = None,
    new_data: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log an audit entry to the audit_log table"""
    logger.debug(f"Auditing action: {action} on {table_name} ID: {record_id} by user: {user_id}")
    
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_data=json.dumps(old_data) if old_data else None,
        new_data=json.dumps(new_data) if new_data else None,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.utcnow()
    )
    
    db.add(audit_entry)
    # Note: We don't commit here to allow the calling function to manage the transaction