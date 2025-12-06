import os
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, current_user
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
from extensions import db, login_manager

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

    # Import and register routes
    from routes import init_routes
    init_routes(app)

    return app

def create_sample_data():
    from models import School, User
    
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
            is_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
    
    db.session.commit()

# Create the application instance
app = create_app()

# User profile and settings
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Current password is incorrect.', 'danger')
    
    return render_template('profile.html', form=form)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate password reset token
            token = app.serializer.dumps(user.email, salt='password-reset')
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Send reset email
            send_email(
                'Reset Your Password',
                user.email,
                f'To reset your password, visit the following link: {reset_url}\n\nIf you did not make this request, simply ignore this email.'
            )
            
        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    try:
        email = current_app.serializer.loads(token, salt='password-reset', max_age=3600)  # 1 hour expiry
    except:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))
    
    user = User.query.filter_by(email=email).first_or_404()
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset! You can now log in with your new password.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_sample_data()
    app.run(debug=True)
