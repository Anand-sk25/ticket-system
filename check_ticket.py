from app import create_app
from models import Ticket, Booking, Event
from datetime import datetime

app = create_app()
with app.app_context():
    ticket_code = '53250861'
    t = Ticket.query.filter_by(unique_code=ticket_code).first()
    if t:
        print(f'Ticket {t.unique_code}')
        print(f'  Generated at: {t.generated_at} (UTC)')
        
        booking = Booking.query.get(t.booking_id)
        print(f'  Booking Date: {booking.booking_date} (UTC)')
        
        event = booking.event
        print(f'  Event Title: {event.title}')
        print(f'  Event Start Time: {event.date_time}')
        
        now = datetime.now()
        print(f'  Current Server Local Time: {now}')
        
        if event.date_time < now:
            print('  STATUS: EVENT HAS STARTED/PASSED relative to server local time.')
        else:
            print('  STATUS: EVENT IS IN THE FUTURE relative to server local time.')
    else:
        print(f'Ticket {ticket_code} not found.')
