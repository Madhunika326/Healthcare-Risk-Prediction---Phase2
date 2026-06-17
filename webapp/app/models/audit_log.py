"""
Audit Log database model
"""

from datetime import datetime
from app import db


class AuditLog(db.Model):
    """Audit log model for tracking user activities"""
    
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(50))  # 'Prediction', 'User', 'Settings', etc.
    resource_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)  # JSON
    new_values = db.Column(db.Text)  # JSON
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    status = db.Column(db.String(20))  # 'Success', 'Failed', 'Warning'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.action}: {self.resource_type} {self.resource_id}>'
    
    @staticmethod
    def log_action(user_id, action, resource_type=None, resource_id=None,
                   old_values=None, new_values=None, details=None,
                   ip_address=None, user_agent=None, status='Success'):
        """Create an audit log entry"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
        db.session.add(audit_log)
        db.session.commit()
        return audit_log
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
