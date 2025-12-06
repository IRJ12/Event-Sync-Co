from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# This is needed to avoid circular imports
# Import models here to ensure they are registered with SQLAlchemy
from models import User, School, Event, EventRegistration
