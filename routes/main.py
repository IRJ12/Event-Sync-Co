from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models import School, Event
from forms import EventForm

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
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
    return redirect(url_for('auth.login'))

@main_bp.route('/school/<int:school_id>')
@login_required
def school_events(school_id):
    school = School.query.get_or_404(school_id)
    
    # Check if user has permission to view this school's events
    if current_user.role == 'teacher' and current_user.school_id != school_id:
        flash('You do not have permission to view events for this school.', 'danger')
        return redirect(url_for('main.index'))
        
    return render_template('school_events.html', school=school, events=school.events)

@main_bp.route('/school/<int:school_id>/event/new', methods=['GET', 'POST'])
@login_required
def new_event(school_id):
    # Check permissions
    if current_user.role not in ['admin', 'teacher']:
        flash('You do not have permission to create events.', 'danger')
        return redirect(url_for('main.index'))
        
    if current_user.role == 'teacher' and current_user.school_id != school_id:
        flash('You can only create events for your own school.', 'danger')
        return redirect(url_for('main.index'))
    
    school = School.query.get_or_404(school_id)
    form = EventForm()
    
    # Debug: Print current working directory and template path
    import os
    from flask import current_app
    print("Current working directory:", os.getcwd())
    print("Template folder:", os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates')))
    print("Template exists:", os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'templates', 'event_form.html')))
    
    if form.validate_on_submit():
        from datetime import datetime, time
        import os
        from werkzeug.utils import secure_filename
        
        try:
            # Combine date and time
            event_datetime = datetime.combine(
                form.date.data,
                datetime.strptime(form.time.data, '%H:%M').time()
            )
            
            # Handle image upload
            image_path = None
            if form.image.data:
                image = form.image.data
                filename = secure_filename(image.filename)
                # Create uploads directory if it doesn't exist
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                # Save file with timestamp to avoid filename conflicts
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{timestamp}_{filename}"
                image_path = os.path.join('uploads', filename)
                image.save(os.path.join(current_app.static_folder, image_path))
            
            # Create event
            event = Event(
                title=form.title.data,
                description=form.description.data,
                date=event_datetime,
                location=form.location.data,
                image_path=image_path,  # Save the relative path to the image
                school_id=school_id,
                created_by=current_user.id
            )
            
            db.session.add(event)
            db.session.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('main.school_events', school_id=school_id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating event: {str(e)}")
            flash('An error occurred while creating the event. Please try again.', 'error')
    
    # Render the form with is_edit=False since this is for creating a new event
    from flask import render_template
    return render_template(
        'event_form.html',
        form=form,
        school=school,
        title='Create Event',
        is_edit=False
    )

@main_bp.route('/event/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check permissions
    if current_user.role == 'teacher' and (current_user.school_id != event.school_id or current_user.id != event.created_by):
        flash('You can only edit your own events.', 'danger')
        return redirect(url_for('main.school_events', school_id=event.school_id))
    
    form = EventForm(obj=event)
    
    if form.validate_on_submit():
        try:
            # Update basic fields
            event.title = form.title.data
            event.description = form.description.data
            event.date = form.date.data
            event.location = form.location.data
            
            # Handle image upload if a new image was provided
            if form.image.data:
                import os
                from werkzeug.utils import secure_filename
                
                # Delete old image if it exists
                if event.image_path:
                    try:
                        os.remove(os.path.join(current_app.static_folder, event.image_path))
                    except OSError:
                        pass  # Ignore if file doesn't exist
                
                # Save new image
                image = form.image.data
                filename = secure_filename(image.filename)
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{timestamp}_{filename}"
                image_path = os.path.join('uploads', filename)
                image.save(os.path.join(current_app.static_folder, image_path))
                event.image_path = image_path
            
            db.session.commit()
            flash('Event updated successfully!', 'success')
            return redirect(url_for('main.school_events', school_id=event.school_id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating event: {str(e)}")
            flash('An error occurred while updating the event. Please try again.', 'error')
    
    # Pre-fill time field from the event's datetime
    if event.date:
        form.time.data = event.date.strftime('%H:%M')
        
    return render_template(
        'event_form.html',
        form=form,
        school=event.school,
        title='Edit Event',
        is_edit=True
    )

@main_bp.route('/event/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    school_id = event.school_id
    
    # Check permissions
    if current_user.role == 'teacher' and (current_user.school_id != event.school_id or current_user.id != event.created_by):
        flash('You can only delete your own events.', 'danger')
        return redirect(url_for('main.school_events', school_id=school_id))
    
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('main.school_events', school_id=school_id))

@main_bp.route('/contact')
def contact():
    return render_template('contact.html', title='Contact Us')

@main_bp.route('/student-demo')
def student_demo():
    return render_template('student_demo.html')
