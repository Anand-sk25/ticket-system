from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import Event, Coupon, Seat, Ticket, Booking, User
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
    now = datetime.now()
    events = Event.query.all()
    for event in events:
        event.is_past = event.date_time < now
        
    # Fetch recent tickets to show member names and scan details
    recent_tickets = db.session.query(Ticket, Booking, Event, User).join(
        Booking, Ticket.booking_id == Booking.id
    ).join(
        Event, Booking.event_id == Event.id
    ).join(
        User, Booking.user_id == User.id
    ).order_by(Ticket.generated_at.desc()).limit(50).all()
    
    # Fetch pending bookings
    pending_bookings = Booking.query.filter_by(status='pending').order_by(Booking.booking_date.desc()).all()
    
    return render_template('admin/dashboard.html', events=events, recent_tickets=recent_tickets, now=now, pending_bookings=pending_bookings)

@admin_bp.route('/booking/approve/<int:booking_id>', methods=['POST'])
@login_required
@admin_required
def approve_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'confirmed'
    db.session.commit()
    flash('Booking approved!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/booking/reject/<int:booking_id>', methods=['POST'])
@login_required
@admin_required
def reject_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'rejected'
    
    # Release seats
    for ticket in booking.tickets:
        if ticket.seat_id:
            seat = Seat.query.get(ticket.seat_id)
            if seat:
                seat.status = 'available'
    
    db.session.commit()
    flash('Booking rejected and seats released.', 'warning')
    return redirect(url_for('admin.dashboard'))

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

            image_filename=image_filename,
            organized_by=request.form.get('organized_by')
        )
        db.session.add(new_event)
        db.session.commit()

        def get_row_label(idx):
            res = ""
            while idx >= 0:
                res = chr(65 + (idx % 26)) + res
                idx = (idx // 26) - 1
            return res

        cols = 10
        total_created = 0
        r = 0
        while total_created < total_seats:
            row_label = get_row_label(r)
            for c in range(1, cols + 1):
                if total_created >= total_seats:
                    break
                seat = Seat(event_id=new_event.id, row=row_label, number=c, status='available')
                db.session.add(seat)
                total_created += 1
            r += 1
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
        event.organized_by = request.form.get('organized_by')
        new_total_seats = int(request.form.get('total_seats'))
        
        current_seats = Seat.query.filter_by(event_id=event.id).order_by(Seat.id).all()
        current_count = len(current_seats)

        if new_total_seats > current_count:
            diff = new_total_seats - current_count
            cols = 10
            r = current_count // cols
            c_start = (current_count % cols) + 1
            
            def get_row_label(idx):
                res = ""
                while idx >= 0:
                    res = chr(65 + (idx % 26)) + res
                    idx = (idx // 26) - 1
                return res
            
            total_added = 0
            while total_added < diff:
                row_label = get_row_label(r)
                for c in range(c_start, cols + 1):
                    if total_added >= diff:
                        break
                    seat = Seat(event_id=event.id, row=row_label, number=c, status='available')
                    db.session.add(seat)
                    total_added += 1
                r += 1
                c_start = 1
                
        elif new_total_seats < current_count:
            excess = current_count - new_total_seats
            for seat in reversed(current_seats):
                if excess <= 0:
                    break
                if seat.status == 'available':
                    db.session.delete(seat)
                    excess -= 1
            if excess > 0:
                flash(f'Could only remove {current_count - new_total_seats - excess} seats because others are booked. {excess} more need to be cancelled first.', 'warning')
                new_total_seats = current_count - excess
        
        event.total_seats = new_total_seats
        
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

