from app import create_app
from models import Event, Booking, Ticket, User
from extensions import db
import uuid

app = create_app()
with app.app_context():
    # Find an open event
    event = Event.query.filter_by(is_seated=False).first()
    if not event:
        # Create one if none exists
        from datetime import datetime, timedelta
        event = Event(
            title="Open Event Test",
            description="Testing open seating",
            date_time=datetime.now() + timedelta(days=1),
            venue="Test Venue",
            price=10.0,
            is_seated=False,
            total_seats=100
        )
        db.session.add(event)
        db.session.commit()
        print(f"Created test open event: {event.id}")

    # Find a test user
    user = User.query.first()
    if not user:
        print("No users found. Please run create_admin.py first.")
        exit()

    print(f"Testing booking for event {event.id} (Seated: {event.is_seated})")
    
    try:
        # Simulate booking
        booking = Booking(
            user_id=user.id,
            event_id=event.id,
            total_amount=event.price,
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        
        # This is where it likely fails
        seat_label = "General Admission"
        print(f"Attempting to create ticket with seat_number: '{seat_label}' (Length: {len(seat_label)})")
        
        ticket = Ticket(
            booking_id=booking.id,
            unique_code=str(uuid.uuid4()).split('-')[0].upper(),
            seat_number=seat_label
        )
        db.session.add(ticket)
        db.session.commit()
        print("Booking successful (unexpected if bug exists)")
    except Exception as e:
        print(f"Booking FAILED as expected: {e}")
        db.session.rollback()
