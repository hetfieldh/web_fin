# app/models/audit_log_model.py
from app import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True) 
    username = db.Column(db.String(80), nullable=False) 
    event_type = db.Column(db.String(50), nullable=False) 
    timestamp = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True) 
    user_agent = db.Column(db.String(255), nullable=True) 

    user = db.relationship('Usuario', backref=db.backref('audit_logs', lazy=True))

    def __repr__(self):
        return f"<AuditLog {self.event_type} - User: {self.username} - {self.timestamp}>"
