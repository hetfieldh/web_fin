# app/routes/audit_log_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.audit_log_model import AuditLog
from app.models.usuario_model import Usuario 

audit_log_bp = Blueprint('audit_log_bp', __name__, template_folder='../templates/audit_logs')

@audit_log_bp.route('/')
@login_required
def list_audit_logs():
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar o log de auditoria.', 'danger')
        return redirect(url_for('dashboard_bp.dashboard'))

    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template('audit_logs/list.html', logs=logs)

def log_audit_event(user_id, username, event_type, ip_address=None, user_agent=None):
    new_log = AuditLog(
        user_id=user_id,
        username=username,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.session.add(new_log)
    db.session.commit()
