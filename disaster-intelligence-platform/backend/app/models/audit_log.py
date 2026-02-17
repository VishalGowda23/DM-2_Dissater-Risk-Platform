"""
Audit log model for admin actions
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime

from app.db.database import Base


class AuditLog(Base):
    """Tracks admin actions like weight changes and risk overrides"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(100))
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(100))  # what was changed
    details = Column(JSON)  # old/new values
    ip_address = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "action": self.action,
            "resource": self.resource,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
