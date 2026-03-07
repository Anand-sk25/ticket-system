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
    """Serve uploaded files with multiple fallbacks for Vercel persistence."""
    # 1. Check ephemeral storage (/tmp on Vercel)
    tmp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(tmp_path):
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    
    # 2. Check the repo's permanent static/uploads (for files pushed via Git)
    # We use an absolute path based on the root of the app
    static_repo_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
    if os.path.exists(static_repo_path):
        return send_from_directory(os.path.join(current_app.root_path, 'static', 'uploads'), filename)
    
    # 3. Fallback to just the static folder generally
    static_dir = os.path.join(current_app.root_path, 'static')
    full_static_path = os.path.join(static_dir, filename)
    if os.path.exists(full_static_path):
        return send_from_directory(static_dir, filename)

    abort(404)
