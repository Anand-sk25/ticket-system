from app import create_app
from models import Event
from datetime import datetime

app = create_app()
with app.app_context():
    events = Event.query.all()
    print(f'Current Server Time (now): {datetime.now()}')
    print(f'Current Server Time (utcnow): {datetime.utcnow()}')
    print('\nEvents in database:')
    for e in events:
        is_past = e.date_time < datetime.now()
        print(f'ID: {e.id}')
        print(f'  Title: {e.title}')
        print(f'  Scheduled Time: {e.date_time}')
        print(f'  Is Past? {is_past}')
        print('-' * 20)
