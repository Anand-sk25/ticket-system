from app import create_app
from models import Event, Seat
from extensions import db
import os

app = create_app()
with app.app_context():
    print("--- Events ---")
    events = Event.query.all()
    if not events:
        print("No events found.")
    for e in events:
        print(f"ID: {e.id}")
        print(f"Title: {e.title}")
        print(f"Date/Time: {e.date_time} (Type: {type(e.date_time)})")
        print(f"Image Filename: {e.image_filename}")
        print(f"Venue: {e.venue}")
        print("-" * 20)

    print("\n--- Upload folder ---")
    upload_folder = app.config['UPLOAD_FOLDER']
    print(f"UPLOAD_FOLDER iconfig: {upload_folder}")
    if os.path.exists(upload_folder):
        print(f"Contents of {upload_folder}:")
        print(os.listdir(upload_folder))
    else:
        print(f"Upload folder {upload_folder} does not exist!")
