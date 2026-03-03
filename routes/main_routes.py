from flask import Blueprint, render_template, send_from_directory, current_app
from models import Event
from flask_login import login_required, current_user
from datetime import datetime
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    now = datetime.now()
    events = Event.query.order_by(Event.date_time.asc()).all()
    for event in events:
        event.is_past = event.date_time < now
    return render_template('index.html', events=events, now=now)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@main_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
