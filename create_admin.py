from app import create_app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

app = create_app()

def create_admin():
    with app.app_context():
        print("--- Create Admin User ---")
        username = input("Enter Admin Username: ")
        email = input("Enter Admin Email: ")
        password = input("Enter Admin Password: ")
        
        # Check if user exists
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        
        if existing_user:
            print("User already exists!")
            update = input("Do you want to promote this user to Admin? (y/n): ")
            if update.lower() == 'y':
                existing_user.is_admin = True
                db.session.commit()
                print(f"User {existing_user.username} is now an Admin!")
            return

        new_admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=True,
            semester='Admin',
            department='Administration'
        )
        
        db.session.add(new_admin)
        db.session.commit()
        print("Admin user created successfully!")

if __name__ == "__main__":
    create_admin()
