from flask import Flask
from extensions import db, login_manager
import os
from dotenv import load_dotenv

def create_app():
    # Load environment variables from .env file
    load_dotenv()
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev_secret_key_change_in_production'
    
    # Check if running on Vercel
    IS_VERCEL = "VERCEL" in os.environ
    
    if IS_VERCEL:
        db_path = os.path.join('/tmp', 'mgm_events.db')
        upload_path = os.path.join('/tmp', 'uploads')
    else:
        db_path = os.path.join(app.instance_path, 'mgm_events.db')
        upload_path = os.path.join(app.root_path, 'static', 'uploads')

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
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

    # Mail Configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

    # Initialize Extensions
    from extensions import db, login_manager, mail
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)

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

    # Handle file too large errors gracefully
    from flask import jsonify
    @app.errorhandler(413)
    def file_too_large(e):
        from flask import flash, redirect, url_for, request as req
        flash('File is too large. Maximum upload size is 16MB.', 'error')
        return redirect(req.referrer or url_for('main.index'))
        
    def run_migrations():
        """Automatically add missing columns to existing tables in production."""
        try:
            # Check User table for semester column
            with db.engine.connect() as conn:
                # For PostgreSQL/SQLite compatibility, we check column existence
                inspector = db.inspect(db.engine)
                
                # Migrate User table
                user_cols = [c['name'] for c in inspector.get_columns('user')]
                if 'semester' not in user_cols:
                    db.session.execute(db.text('ALTER TABLE "user" ADD COLUMN semester VARCHAR(100)'))
                if 'phone' not in user_cols:
                    db.session.execute(db.text('ALTER TABLE "user" ADD COLUMN phone VARCHAR(20)'))
                if 'department' not in user_cols:
                    db.session.execute(db.text('ALTER TABLE "user" ADD COLUMN department VARCHAR(100)'))
                
                # Migrate Event table
                event_cols = [c['name'] for c in inspector.get_columns('event')]
                if 'is_seated' not in event_cols:
                    db.session.execute(db.text('ALTER TABLE event ADD COLUMN is_seated BOOLEAN DEFAULT TRUE'))
                if 'total_seats' not in event_cols:
                    db.session.execute(db.text('ALTER TABLE event ADD COLUMN total_seats INTEGER DEFAULT 100'))
                if 'organized_by' not in event_cols:
                    db.session.execute(db.text('ALTER TABLE event ADD COLUMN organized_by VARCHAR(100)'))
                if 'ticket_image_filename' not in event_cols:
                    db.session.execute(db.text('ALTER TABLE event ADD COLUMN ticket_image_filename VARCHAR(200)'))
                if 'ticket_image_url' not in event_cols:
                    db.session.execute(db.text('ALTER TABLE event ADD COLUMN ticket_image_url VARCHAR(500)'))

                # Migrate Ticket table for scanning fields
                ticket_cols = [c['name'] for c in inspector.get_columns('ticket')]
                if 'is_scanned' not in ticket_cols:
                    db.session.execute(db.text('ALTER TABLE ticket ADD COLUMN is_scanned BOOLEAN DEFAULT FALSE'))
                if 'scanned_at' not in ticket_cols:
                    db.session.execute(db.text('ALTER TABLE ticket ADD COLUMN scanned_at TIMESTAMP'))
                if 'scanned_by_id' not in ticket_cols:
                    db.session.execute(db.text('ALTER TABLE ticket ADD COLUMN scanned_by_id INTEGER'))
                if 'generated_at' not in ticket_cols:
                    db.session.execute(db.text('ALTER TABLE ticket ADD COLUMN generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
                
                db.session.commit()
                print("Migrations completed successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Migration Error: {e}")

    # Initialize database and seed admin
    with app.app_context():
        db.create_all()
        run_migrations()
        
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
                semester='Admin',
                department='Administration'
            )
            db.session.add(new_admin)
            db.session.commit()
            print(f"Admin {admin_email} created.")
        elif not admin.is_admin:
            admin.is_admin = True
            db.session.commit()
            print(f"User {admin_email} promoted to Admin.")

        # Check for persistence warnings
        app.config['PERSISTENCE_WARNING'] = IS_VERCEL and not DATABASE_URL
        app.config['IMAGE_PERSISTENCE_WARNING'] = IS_VERCEL

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
