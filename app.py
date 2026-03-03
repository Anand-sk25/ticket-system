from flask import Flask
from extensions import db, login_manager
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev_secret_key_change_in_production'
    
    # Check if running on Vercel
    IS_VERCEL = "VERCEL" in os.environ
    
    if IS_VERCEL:
        db_path = os.path.join('/tmp', 'mgm_events.db')
        upload_path = os.path.join('/tmp', 'uploads')
    else:
        db_path = os.path.join(app.instance_path, 'mgm_events.db')
        upload_path = os.path.join(app.root_path, 'static/uploads')

    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Fix for Heroku/Vercel Postgres URLs which might start with postgres:// instead of postgresql://
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = upload_path

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Ensure instance folder exists for local dev
    if not IS_VERCEL:
        os.makedirs(app.instance_path, exist_ok=True)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.main_routes import main_bp
    from routes.admin_routes import admin_bp
    from routes.booking_routes import booking_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(booking_bp)

    # Initialize database and seed admin
    with app.app_context():
        db.create_all()
        
        # Auto-seed admin from environment variables or default email
        admin_email = os.environ.get('ADMIN_EMAIL') or 'ask208238@gmail.com'
        admin_password = os.environ.get('ADMIN_PASSWORD') or 'admin123'
        
        from werkzeug.security import generate_password_hash
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            new_admin = User(
                username='admin',
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                is_admin=True,
                branch='Admin',
                department='Administration'
            )
            db.session.add(new_admin)
            db.session.commit()
            print(f"Admin {admin_email} created.")
        elif not admin.is_admin:
            admin.is_admin = True
            db.session.commit()
            print(f"User {admin_email} promoted to Admin.")

        # Check for persistence warning
        if IS_VERCEL and not DATABASE_URL:
            app.config['PERSISTENCE_WARNING'] = True
        else:
            app.config['PERSISTENCE_WARNING'] = False

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
