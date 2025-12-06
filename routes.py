from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db
from models import User, School, Event
from forms import (LoginForm, RegistrationForm, EventForm, 
                  ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm)

def init_routes(app):
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                schools = School.query.all()
            elif current_user.role == 'teacher':
                schools = [current_user.school]
            else:  # student
                schools = School.query.all()
                
            # Add event counts to each school
            schools_with_counts = []
            for school in schools:
                school_data = {
                    'id': school.id,
                    'name': school.name,
                    'location': school.location,
                    'event_count': len(school.events)
                }
                schools_with_counts.append(school_data)
                
            return render_template('index.html', schools=schools_with_counts)
        return redirect(url_for('login'))

    @app.route('/school/<int:school_id>')
    @login_required
    def school_events(school_id):
        school = School.query.get_or_404(school_id)
        
        # Check if user has permission to view this school's events
        if current_user.role == 'teacher' and current_user.school_id != school_id:
            flash('You do not have permission to view events for this school.', 'danger')
            return redirect(url_for('index'))
            
        return render_template('school_events.html', school=school, events=school.events)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                if user.is_verified:
                    login_user(user, remember=True)
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('index'))
                else:
                    flash('Please verify your email before logging in.', 'warning')
            else:
                flash('Login failed. Check your email and password.', 'danger')
        return render_template('login.html', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        form = RegistrationForm()
        form.school_id.choices = [(s.id, s.name) for s in School.query.order_by('name').all()]
        
        if form.validate_on_submit():
            user = User(
                email=form.email.data,
                name=form.name.data,
                role=form.role.data,
                school_id=form.school_id.data,
                is_verified=False
            )
            user.set_password(form.password.data)
            
            # Generate verification token
            token = current_app.serializer.dumps(user.email, salt='email-verification')
            user.verification_token = token
            
            db.session.add(user)
            db.session.commit()
            
            # Send verification email
            verification_url = url_for('verify_email', token=token, _external=True)
            current_app.send_email(
                'Verify Your Email',
                user.email,
                f'Please click the following link to verify your email: {verification_url}'
            )
            
            flash('Registration successful! Please check your email to verify your account.', 'success')
            return redirect(url_for('login'))
            
        return render_template('register.html', form=form)

    @app.route('/verify-email/<token>')
    def verify_email(token):
        try:
            email = current_app.serializer.loads(token, salt='email-verification', max_age=86400)
        except:
            flash('The verification link is invalid or has expired.', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first_or_404()
        if user.is_verified:
            flash('Account already verified. Please login.', 'info')
        else:
            user.is_verified = True
            user.verification_token = None
            db.session.commit()
            flash('Email verified successfully! You can now log in.', 'success')
        
        return redirect(url_for('login'))

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/event/new/<int:school_id>', methods=['GET', 'POST'])
    @login_required
    def new_event(school_id):
        if current_user.role not in ['admin', 'teacher']:
            flash('You do not have permission to create events.', 'danger')
            return redirect(url_for('index'))
            
        if current_user.role == 'teacher' and current_user.school_id != school_id:
            flash('You can only create events for your own school.', 'danger')
            return redirect(url_for('index'))
        
        school = School.query.get_or_404(school_id)
        form = EventForm()
        
        if form.validate_on_submit():
            event = Event(
                title=form.title.data,
                description=form.description.data,
                date=form.date.data,
                school_id=school_id,
                created_by=current_user.id
            )
            db.session.add(event)
            db.session.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('school_events', school_id=school_id))
            
        return render_template('event_form.html', form=form, school=school, title='Create Event')

    @app.route('/event/edit/<int:event_id>', methods=['GET', 'POST'])
    @login_required
    def edit_event(event_id):
        event = Event.query.get_or_404(event_id)
        
        if current_user.role == 'teacher' and (current_user.school_id != event.school_id or current_user.id != event.created_by):
            flash('You can only edit your own events.', 'danger')
            return redirect(url_for('school_events', school_id=event.school_id))
        
        form = EventForm(obj=event)
        
        if form.validate_on_submit():
            event.title = form.title.data
            event.description = form.description.data
            event.date = form.date.data
            db.session.commit()
            flash('Event updated successfully!', 'success')
            return redirect(url_for('school_events', school_id=event.school_id))
            
        return render_template('event_form.html', form=form, school=event.school, title='Edit Event')

    @app.route('/event/delete/<int:event_id>', methods=['POST'])
    @login_required
    def delete_event(event_id):
        event = Event.query.get_or_404(event_id)
        school_id = event.school_id
        
        if current_user.role == 'teacher' and (current_user.school_id != event.school_id or current_user.id != event.created_by):
            flash('You can only delete your own events.', 'danger')
            return redirect(url_for('school_events', school_id=school_id))
        
        db.session.delete(event)
        db.session.commit()
        flash('Event deleted successfully!', 'success')
        return redirect(url_for('school_events', school_id=school_id))
