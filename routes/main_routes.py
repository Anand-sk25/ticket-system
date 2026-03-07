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
    """Serve uploaded files. Tries ephemeral /tmp first, then persistent static/uploads fallback."""
    # 1. Try the configured UPLOAD_FOLDER (might be /tmp on Vercel)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, filename)
    if os.path.exists(file_path):
        return send_from_directory(upload_folder, filename)
    
    # 2. Try the project's static/uploads folder (persistent images pushed via Git)
    static_uploads = os.path.join(current_app.root_path, 'static', 'uploads')
    static_path = os.path.join(static_uploads, filename)
    if os.path.exists(static_path):
        return send_from_directory(static_uploads, filename)
    
    # 3. Last resort: direct static lookup
    abort(404)
