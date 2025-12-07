from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from extensions import db
from models import User, School
from forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if user.is_active:
                login_user(user, remember=True)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('main.index'))
            else:
                flash('This account has been deactivated.', 'warning')
        else:
            flash('Login failed. Check your username and password.', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = RegistrationForm()
    # Only show schools for teacher registration
    form.school_id.choices = [(0, '-- Select School --')] + [(s.id, s.name) for s in School.query.order_by('name').all()]
    
    if form.validate_on_submit():
        try:
            # Check if username already exists
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already taken. Please choose a different one.', 'danger')
                return redirect(url_for('auth.register'))
                
            # Check if email already exists
            if User.query.filter_by(email=form.email.data).first():
                flash('Email already registered. Please use a different email or login.', 'danger')
                return redirect(url_for('auth.register'))
            
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data,
                name=form.name.data,
                role=form.role.data,
                school_id=form.school_id.data if form.role.data == 'teacher' and form.school_id.data != 0 else None,
                is_active=True
            )
            user.set_password(form.password.data)
            
            # Generate verification token
            token = current_app.serializer.dumps(user.email, salt='email-verification')
            user.verification_token = token
            
            db.session.add(user)
            db.session.commit()
            
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during registration: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Current password is incorrect.', 'danger')
    
    return render_template('auth/change_password.html', form=form)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate password reset token
            token = current_app.serializer.dumps(user.email, salt='password-reset')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # Send password reset email
            current_app.send_email(
                'Reset Your Password',
                user.email,
                f'Click the following link to reset your password: {reset_url}'
            )
        
        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    try:
        email = current_app.serializer.loads(token, salt='password-reset', max_age=3600)  # 1 hour expiry
    except Exception as e:
        current_app.logger.error(f"Password reset error: {str(e)}")
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.filter_by(email=email).first_or_404()
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset! You can now log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)
