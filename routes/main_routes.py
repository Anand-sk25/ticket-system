from flask import Blueprint, render_template, send_from_directory, current_app, abort
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

@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files. Tries UPLOAD_FOLDER first, then static/uploads fallback."""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # Primary: configured upload folder
    file_path = os.path.join(upload_folder, filename)
    if os.path.exists(file_path) and os.path.getsize(file_path) > 500:
        return send_from_directory(upload_folder, filename)
    
    # Fallback: static/uploads (always available in dev)
    static_uploads = os.path.join(current_app.root_path, 'static', 'uploads')
    static_path = os.path.join(static_uploads, filename)
    if os.path.exists(static_path) and os.path.getsize(static_path) > 500:
        return send_from_directory(static_uploads, filename)
    
    # File not found or too small (broken upload) → 404
    abort(404)
