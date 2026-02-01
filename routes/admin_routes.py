from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import Event, Coupon, Seat
from extensions import db
import os
from datetime import datetime
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    events = Event.query.all()
    return render_template('admin/dashboard.html', events=events)

@admin_bp.route('/event/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_event():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        venue = request.form.get('venue')
        date_str = request.form.get('date_time')
        total_seats = int(request.form.get('total_seats'))
        
        try:
            date_time = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('admin.new_event'))

        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename

        new_event = Event(
            title=title,
            description=description,
            price=price,
            venue=venue,
            date_time=date_time,
            total_seats=total_seats,
            image_filename=image_filename
        )
        db.session.add(new_event)
        db.session.commit()

        # Initialize seats (Default 6x8 grid for now as per JS)
        rows = 6
        cols = 8
        for r in range(rows):
            row_label = chr(65 + r)
            for c in range(1, cols + 1):
                seat = Seat(event_id=new_event.id, row=row_label, number=c, status='available')
                db.session.add(seat)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/event_form.html', event=None)

@admin_bp.route('/event/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    if request.method == 'POST':
        event.title = request.form.get('title')
        event.description = request.form.get('description')
        event.price = float(request.form.get('price'))
        event.venue = request.form.get('venue')
        event.total_seats = int(request.form.get('total_seats'))
        
        date_str = request.form.get('date_time')
        try:
            event.date_time = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('admin.edit_event', event_id=event.id))
            
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                event.image_filename = filename
                
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
        
    return render_template('admin/event_form.html', event=event)

@admin_bp.route('/event/delete/<int:event_id>', methods=['POST'])
@login_required
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Delete image file if it exists
    if event.image_filename:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], event.image_filename)
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                print(f"Error deleting image file: {e}")

    db.session.delete(event)
    db.session.commit()
    flash('Event deleted.', 'success')
    return redirect(url_for('admin.dashboard'))

