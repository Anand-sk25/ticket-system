from app import create_app
from extensions import db
from models import User

app = create_app()
with app.app_context():
    print("--- Users in Database ---")
    users = User.query.all()
    if not users:
        print("No users found.")
    for u in users:
        print(f"ID: {u.id} | Username: {u.username} | Email: {u.email} | Is Admin: {u.is_admin}")
    print("------------------------")
