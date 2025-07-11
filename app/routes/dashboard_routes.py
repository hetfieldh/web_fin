# app/routes/dashboard_routes.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard_bp', __name__, template_folder='../templates')

@dashboard_bp.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')
