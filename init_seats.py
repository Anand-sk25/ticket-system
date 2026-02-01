from app import create_app
from extensions import db
from models import Event, Seat

app = create_app()
with app.app_context():
    events = Event.query.all()
    for event in events:
        # Check if seats already exist
        existing_seats = Seat.query.filter_by(event_id=event.id).count()
        if existing_seats == 0:
            print(f"Initializing seats for event: {event.title}")
            rows = 6
            cols = 8
            for r in range(rows):
                row_label = chr(65 + r)
                for c in range(1, cols + 1):
                    seat = Seat(event_id=event.id, row=row_label, number=c, status='available')
                    db.session.add(seat)
            db.session.commit()
        else:
            print(f"Seats already exist for event: {event.title}")
    print("Done.")
