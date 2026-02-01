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

    # Initialize database if on Vercel
    if IS_VERCEL:
        with app.app_context():
            db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
