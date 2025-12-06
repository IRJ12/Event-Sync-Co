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

@main_bp.route('/event/new/<int:school_id>', methods=['GET', 'POST'])
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
        return redirect(url_for('main.school_events', school_id=school_id))
        
    return render_template('event_form.html', form=form, school=school, title='Create Event')

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
        event.title = form.title.data
        event.description = form.description.data
        event.date = form.date.data
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('main.school_events', school_id=event.school_id))
        
    return render_template('event_form.html', form=form, school=event.school, title='Edit Event')

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
