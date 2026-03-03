from app import create_app
from models import User, Event, Booking, Ticket, Seat
from extensions import db
import uuid

app = create_app()
with app.app_context():
    user = User.query.first()
    event = Event.query.get(1)
    
    if not user or not event:
        print("Missing user or event")
        exit(1)
        
    booking = Booking(
        user_id=user.id,
        event_id=event.id,
        total_amount=event.price,
        status='confirmed'
    )
    db.session.add(booking)
    db.session.commit()
    
    unique_code = str(uuid.uuid4()).split('-')[0].upper()
    ticket = Ticket(
        booking_id=booking.id,
        unique_code=unique_code,
        seat_number='A3'
    )
    db.session.add(ticket)
    db.session.commit()
    
    print(f"Created booking {booking.id} with ticket {unique_code}")
