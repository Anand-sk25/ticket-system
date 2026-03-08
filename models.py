from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    semester = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(200), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    organized_by = db.Column(db.String(100), nullable=True)
    total_seats = db.Column(db.Integer, default=100)
    is_seated = db.Column(db.Boolean, default=True)
    ticket_image_filename = db.Column(db.String(200), nullable=True)
    ticket_image_url = db.Column(db.String(500), nullable=True)
    # Relationships with explicit cascade behavior
    seats = db.relationship('Seat', backref='event', lazy=True, cascade='all, delete-orphan')
    coupons = db.relationship('Coupon', backref='event', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='event', lazy=True, cascade='all, delete-orphan')

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), nullable=False)
    row = db.Column(db.String(5), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='available') # available, booked, locked
    tier = db.Column(db.String(20), default='Standard') # Standard, VIP

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    tickets = db.relationship('Ticket', backref='booking', lazy=True, cascade='all, delete-orphan')

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id', ondelete='CASCADE'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id', ondelete='SET NULL'), nullable=True) # Optional if open seating
    seat_number = db.Column(db.String(100), nullable=True) # e.g. "A1" or "General Admission"
    unique_code = db.Column(db.String(100), unique=True, nullable=False)
    is_scanned = db.Column(db.Boolean, default=False)
    scanned_at = db.Column(db.DateTime, nullable=True)
    scanned_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    scanned_by = db.relationship('User', foreign_keys=[scanned_by_id], backref='scanned_tickets', lazy=True)

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percent = db.Column(db.Float, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), nullable=True) # Null means global coupon
    is_active = db.Column(db.Boolean, default=True)
