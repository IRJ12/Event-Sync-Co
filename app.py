import os
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
from extensions import db, login_manager

# Import models to ensure they are registered with SQLAlchemy
from models import User, School, Event

# Load environment variables
load_dotenv()

def create_app():
    # Initialize Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_events.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    csrf.init_app(app)

    # Email configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'eventsyncandco@gmail.com'
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Set this in your .env file
    app.config['MAIL_DEFAULT_SENDER'] = 'eventsyncandco@gmail.com'
    
    # Initialize extensions
    mail = Mail()
    mail.init_app(app)

    # Initialize serializer
    app.serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    app.mail = mail  # Make mail instance available throughout the app
    
    # Configure email sending (in production, replace with a real email service)
    def send_email(subject, recipient, template):
        # This is a placeholder that just prints to the console
        print(f"Email to {recipient} - Subject: {subject}")
        print(template)
        return True
    
    app.send_email = send_email
    
    # Register blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Error handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app

def create_sample_data():
    # Create sample schools if they don't exist
    schools_data = [
        {'name': 'Greenwood High', 'location': 'Bangalore'},
        {'name': 'Delhi Public School', 'location': 'New Delhi'},
        {'name': 'Mumbai International School', 'location': 'Mumbai'},
        {'name': 'Chennai Public School', 'location': 'Chennai'},
    ]
    
    for school_data in schools_data:
        if not School.query.filter_by(name=school_data['name']).first():
            school = School(**school_data)
            db.session.add(school)
    
    # Create admin user if not exists
    if not User.query.filter_by(email='admin@example.com').first():
        admin = User(
            email='admin@example.com',
            name='Admin User',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
    
    db.session.commit()

def init_db():
    # Create the application instance
    app = create_app()
    
    with app.app_context():
        # Create all database tables
        db.create_all()
        # Add sample data
        # create_sample_data()
    
    return app

# Create the application instance
app = create_app()

# Set up user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    # Initialize the database
    init_db()
    # Run the application
    app.run(debug=True)
