from app import create_app
from models import Booking, Ticket, User

app = create_app()
with app.app_context():
    bookings = Booking.query.all()
    print(f"Total bookings: {len(bookings)}")
    for b in bookings:
        user = User.query.get(b.user_id)
        print(f"ID: {b.id}, User: {user.username if user else 'N/A'}, Status: {b.status}, Tickets: {len(b.tickets)}")
        for t in b.tickets:
            print(f"  Ticket ID: {t.id}, Code: {t.unique_code}")
