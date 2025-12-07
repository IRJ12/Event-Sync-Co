"""
Migration: 20231206_update_auth_system
Description: Updates authentication system to use username instead of email verification
             and adds default admin and teacher users.
"""

def upgrade():
    """Apply the migration."""
    from app import create_app
    from models import db, User, School

    app = create_app()
    with app.app_context():
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
                username='admin',
                email='admin@example.com',
                name='Admin User',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Create teacher user if not exists
        school = School.query.first()
        if school and not User.query.filter_by(email='teacher@example.com').first():
            teacher = User(
                username='teacher1',
                email='teacher@example.com',
                name='Teacher One',
                role='teacher',
                school_id=school.id,
                is_active=True
            )
            teacher.set_password('teacher123')
            db.session.add(teacher)
        
        db.session.commit()
        print("✅ Auth system update completed successfully!")

def downgrade():
    """Revert the migration."""
    from app import create_app
    from models import db, User

    app = create_app()
    with app.app_context():
        # Remove the test users we created
        for email in ['admin@example.com', 'teacher@example.com']:
            user = User.query.filter_by(email=email).first()
            if user:
                db.session.delete(user)
        
        db.session.commit()
        print("✅ Auth system changes reverted successfully!")

if __name__ == '__main__':
    upgrade()
