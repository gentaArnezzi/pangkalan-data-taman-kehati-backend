from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.auth.utils import get_current_super_admin
from app.utils.logging_config import get_logger
from sqlalchemy import text, select
from app.models import AuditLog, User as UserModel
from app.schemas.users import UserResponse

router = APIRouter()
logger = get_logger(__name__)

@router.get("/", response_model=List[dict])  # Simplified response for now
async def read_audit_log(
    table_name: Optional[str] = None,
    record_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    size: int = 20,
    current_user=Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get audit log entries (super_admin only)"""
    logger.info(f"Fetching audit logs - user: {current_user.email}, table_name: {table_name}, record_id: {record_id}")
    
    skip = (page - 1) * size
    
    query = select(AuditLog).offset(skip).limit(size).order_by(AuditLog.created_at.desc())
    
    filters = []
    if table_name:
        filters.append(AuditLog.table_name == table_name)
    
    if record_id:
        filters.append(AuditLog.record_id == record_id)
        
    if date_from:
        filters.append(AuditLog.created_at >= date_from)
    
    if date_to:
        filters.append(AuditLog.created_at <= date_to)
    
    if filters:
        from sqlalchemy import and_
        query = query.filter(and_(*filters))
    
    result = await db.execute(query)
    audit_logs = result.scalars().all()
    
    # Convert to proper format including user info
    log_responses = []
    for log in audit_logs:
        user_info = None
        if log.user_id:
            user_result = await db.execute(
                select(UserModel.email, UserModel.nama).filter(UserModel.id == log.user_id)
            )
            user_row = user_result.first()
            if user_row:
                user_info = {"id": str(log.user_id), "email": user_row.email, "nama": user_row.nama}
        
        log_responses.append({
            "id": log.id,
            "user": user_info,
            "action": log.action,
            "table_name": log.table_name,
            "record_id": log.record_id,
            "old_data": log.old_data,
            "new_data": log.new_data,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at
        })
    
    logger.info(f"Successfully returned {len(log_responses)} audit log entries")
    return log_responses