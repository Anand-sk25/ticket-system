from flask import Blueprint, render_template
from models import Event
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    events = Event.query.all()
    return render_template('index.html', events=events)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)
