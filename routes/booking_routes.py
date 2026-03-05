from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import Event, Booking, Ticket, Seat, Coupon
from extensions import db
import uuid
from datetime import datetime

booking_bp = Blueprint('booking', __name__, url_prefix='/book')

@booking_bp.route('/<int:event_id>')
@login_required
def select_seats(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.date_time < datetime.now():
        flash('This event has already passed and tickets can no longer be booked.', 'error')
        return redirect(url_for('main.index'))
        
    # Fetch all seats for this event from the Seat model
    seats = Seat.query.filter_by(event_id=event_id).all()
    booked_seats = [f"{s.row}{s.number}" for s in seats if s.status == 'booked']
    
    return render_template('booking/seat_selection.html', event=event, booked_seats=booked_seats)

@booking_bp.route('/confirm', methods=['POST'])
@login_required
def confirm_booking():
    data = request.json
    event_id = data.get('event_id')
    selected_seats = data.get('seats') # List of strings like "A1", "A2"
    
    event = Event.query.get_or_404(event_id)
    
    if event.date_time < datetime.now():
        return jsonify({'status': 'error', 'message': 'This event has already passed. Booking is closed.'}), 400
        
    # Calculate total
    total_amount = len(selected_seats) * event.price
    
    # Create Booking
    booking = Booking(
        user_id=current_user.id,
        event_id=event.id,
        total_amount=total_amount,
        status='pending'
    )
    db.session.add(booking)
    db.session.commit()
    
    # Create Tickets and update Seat status
    for seat_label in selected_seats:
        # Parse seat label (e.g. "A1")
        row_label = seat_label[0]
        seat_num = int(seat_label[1:])
        
        # Update Seat status in DB
        seat = Seat.query.filter_by(event_id=event.id, row=row_label, number=seat_num).first()
        if seat:
            if seat.status == 'booked':
                return jsonify({'status': 'error', 'message': f'Seat {seat_label} is already booked.'}), 400
            seat.status = 'booked'
        
        # Generate unique code
        unique_code = str(uuid.uuid4()).split('-')[0].upper()
        
        ticket = Ticket(
            booking_id=booking.id,
            unique_code=unique_code,
            seat_id=seat.id if seat else None,
            seat_number=seat_label
        )
        db.session.add(ticket)
        
    db.session.commit()
    
    return jsonify({'status': 'success', 'booking_id': booking.id})

@booking_bp.route('/ticket/<int:booking_id>')
@login_required
def view_ticket(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized', 'error')
        return redirect(url_for('main.index'))
    
    if booking.status != 'confirmed' and not current_user.is_admin:
        flash('Your booking is pending admin approval. Tickets will be available once approved.', 'info')
        return redirect(url_for('booking.my_bookings'))
        
    return render_template('booking/confirmation.html', booking=booking)

@booking_bp.route('/my_bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    return render_template('booking/my_bookings.html', bookings=bookings)

@booking_bp.route('/verify/<code>')
@login_required
def verify_ticket(code):
    if not current_user.is_admin:
        flash('Access denied. Only authorized staff can verify tickets.', 'error')
        return redirect(url_for('main.index'))
        
    ticket = Ticket.query.filter_by(unique_code=code).first()
    if not ticket:
        return render_template('booking/verify_result.html', valid=False, message="Invalid Ticket Code")
        
    booking = Booking.query.get(ticket.booking_id)
    event = booking.event
    user = booking.user
    
    first_scan = False
    now = datetime.utcnow()
    
    # If not scanned yet, mark as scanned
    if not ticket.is_scanned:
        ticket.is_scanned = True
        ticket.scanned_at = now
        ticket.scanned_by_id = current_user.id
        db.session.commit()
        first_scan = True
    else:
        # Check if the SAME admin is scanning again
        if ticket.scanned_by_id == current_user.id:
            # User wants: "if the same admin... not say to verify again"
            # This means we treat it like a "success/first scan" result to suppress the warning
            first_scan = True
        else:
            # Grace period logic removed as we now track precisely who scanned it
            # Different admin or much later scan by someone else (though only admins can scan)
            first_scan = False
    
    return render_template('booking/verify_result.html', 
                           valid=True, 
                           ticket=ticket, 
                           event=event, 
                           user=user, 
                           seat=ticket.seat_number,
                           first_scan=first_scan)

@booking_bp.route('/scanner')
@login_required
def scanner():
    # Ideally restrict to admin or staff
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    return render_template('scanner.html')
