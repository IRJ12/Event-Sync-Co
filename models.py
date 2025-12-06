from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import time, datetime
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'teacher', or 'admin'
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True, nullable=True)
    
    school = db.relationship('School', back_populates='users')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class School(db.Model):
    __tablename__ = 'schools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    about = db.Column(db.Text, nullable=True)
    email = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    website = db.Column(db.String(200), nullable=True)
    logo_url = db.Column(db.String(200), nullable=True)
    
    # Relationships
    users = db.relationship('User', back_populates='school')
    events = db.relationship('Event', back_populates='school')
    contacts = db.relationship('Contact', back_populates='school')
    
    def __init__(self, **kwargs):
        super(School, self).__init__(**kwargs)
        if not self.about:
            self.about = f"{self.name} is a prestigious educational institution located in {self.location}."

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    
    school = db.relationship('School', back_populates='contacts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'position': self.position,
            'email': self.email,
            'phone': self.phone,
            'is_primary': self.is_primary
        }


class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False, default=time(9, 0))  # Default to 9:00 AM
    end_time = db.Column(db.Time, nullable=False, default=time(17, 0))   # Default to 5:00 PM
    location = db.Column(db.String(200), nullable=True)
    capacity = db.Column(db.Integer, nullable=True)
    registration_required = db.Column(db.Boolean, default=False)
    registration_deadline = db.Column(db.Date, nullable=True)
    price = db.Column(db.Float, default=0.0)
    image_url = db.Column(db.String(200), nullable=True)
    
    # Foreign keys
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    school = db.relationship('School', back_populates='events')
    registrations = db.relationship('EventRegistration', back_populates='event')
    
    @property
    def formatted_date(self):
        return self.date.strftime('%B %d, %Y')
        
    @property
    def formatted_time(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"
    
    def is_registration_open(self):
        if not self.registration_required:
            return True
        if not self.registration_deadline:
            return True
        return datetime.now().date() <= self.registration_deadline
    
    def available_spots(self):
        if not self.capacity:
            return float('inf')
        registered = EventRegistration.query.filter_by(event_id=self.id, status='confirmed').count()
        return max(0, self.capacity - registered)


class EventRegistration(db.Model):
    __tablename__ = 'event_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, attended
    payment_status = db.Column(db.String(20), default='unpaid')  # unpaid, paid, refunded
    payment_amount = db.Column(db.Float, default=0.0)
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_reference = db.Column(db.String(100), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='event_registrations')
    event = db.relationship('Event', back_populates='registrations')
