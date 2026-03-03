import os
import sqlite3
from app import create_app
from extensions import db
from models import User, Event, Seat, Booking, Ticket, Coupon
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- CONFIGURATION ---
# Live Database URL
# You can find this in your Vercel Dashboard -> Storage -> Postgres -> .env.local
# It should look like: postgresql://default:password@host.postgres.vercel-storage.com:5432/verceldb
LIVE_DATABASE_URL = input("\n[STEP 1] Enter your Vercel DATABASE_URL (or press Enter to skip): ").strip()

if not LIVE_DATABASE_URL:
    print("No URL provided. Seeking from environment variable...")
    LIVE_DATABASE_URL = os.environ.get('DATABASE_URL')
    
if not LIVE_DATABASE_URL:
    print("Error: No DATABASE_URL found. Please provide it to sync data.")
    exit()

if LIVE_DATABASE_URL.startswith("postgres://"):
    LIVE_DATABASE_URL = LIVE_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Local SQLite path
LOCAL_DB_PATH = os.path.join('instance', 'mgm_events.db')
if not os.path.exists(LOCAL_DB_PATH):
    # Try current directory if instance folder is not used
    LOCAL_DB_PATH = 'mgm_events.db'

if not os.path.exists(LOCAL_DB_PATH):
    print(f"Error: Local database not found at {LOCAL_DB_PATH}")
    exit()

def migrate():
    app = create_app()
    
    # Connect to Local SQLite
    print(f"Reading local data from {LOCAL_DB_PATH}...")
    local_conn = sqlite3.connect(LOCAL_DB_PATH)
    local_conn.row_factory = sqlite3.Row
    
    # Connect to Live Postgres
    print("Connecting to LIVE database...")
    engine = create_engine(LIVE_DATABASE_URL)
    
    # Ensure tables exist in the LIVE database
    print("Ensuring tables exist in LIVE database...")
    from extensions import db as ext_db
    ext_db.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    live_session = Session()

    try:
        # 1. Clear Live Tables (Optional, but recommended for clean sync)
        confirm = input("Clear all data in LIVE database before syncing? (y/n): ")
        if confirm.lower() == 'y':
            print("Cleaning live database...")
            live_session.query(Ticket).delete()
            live_session.query(Booking).delete()
            live_session.query(Seat).delete()
            live_session.query(Coupon).delete()
            live_session.query(Event).delete()
            live_session.query(User).delete()
            live_session.commit()

        # 2. Sync Users
        print("Syncing Users...")
        users = local_conn.execute("SELECT * FROM user").fetchall()
        for u in users:
            new_u = User(id=u['id'], username=u['username'], email=u['email'], 
                         password_hash=u['password_hash'], phone=u['phone'], 
                         branch=u['branch'], department=u['department'], is_admin=u['is_admin'])
            live_session.merge(new_u)
        
        # 3. Sync Events
        print("Syncing Events...")
        events = local_conn.execute("SELECT * FROM event").fetchall()
        for e in events:
            new_e = Event(id=e['id'], title=e['title'], description=e['description'], 
                          date_time=e['date_time'], venue=e['venue'], price=e['price'], 
                          image_filename=e['image_filename'], total_seats=e['total_seats'])
            live_session.merge(new_e)

        # 4. Sync Seats
        print("Syncing Seats...")
        seats = local_conn.execute("SELECT * FROM seat").fetchall()
        for s in seats:
            new_s = Seat(id=s['id'], event_id=s['event_id'], row=s['row'], 
                         number=s['number'], status=s['status'], tier=s['tier'])
            live_session.merge(new_s)

        # 5. Sync Coupons
        print("Syncing Coupons...")
        coupons = local_conn.execute("SELECT * FROM coupon").fetchall()
        for c in coupons:
            new_c = Coupon(id=c['id'], code=c['code'], discount_percent=c['discount_percent'], 
                           event_id=c['event_id'], is_active=c['is_active'])
            live_session.merge(new_c)

        # 6. Sync Bookings
        print("Syncing Bookings...")
        bookings = local_conn.execute("SELECT * FROM booking").fetchall()
        for b in bookings:
            new_b = Booking(id=b['id'], user_id=b['user_id'], event_id=b['event_id'], 
                            booking_date=b['booking_date'], total_amount=b['total_amount'], status=b['status'])
            live_session.merge(new_b)

        # 7. Sync Tickets
        print("Syncing Tickets...")
        tickets = local_conn.execute("SELECT * FROM ticket").fetchall()
        for t in tickets:
            new_t = Ticket(id=t['id'], booking_id=t['booking_id'], seat_id=t['seat_id'], 
                           seat_number=t['seat_number'], unique_code=t['unique_code'], 
                           is_scanned=t['is_scanned'], scanned_at=t['scanned_at'], 
                           generated_at=t['generated_at'])
            live_session.merge(new_t)

        live_session.commit()
        print("--- SUCCESS! Local data has been moved to the Live Database ---")

    except Exception as ex:
        live_session.rollback()
        print(f"An error occurred: {ex}")
    finally:
        live_session.close()
        local_conn.close()

if __name__ == "__main__":
    migrate()
