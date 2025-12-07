from app import create_app, db
from models import User, School

def init_db():
    app = create_app()
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create a default school
        school = School(
            name='Default School',
            location='Default Location',
            email='school@example.com',
            phone='123-456-7890'
        )
        db.session.add(school)
        db.session.commit()
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            name='Admin User',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create teacher user
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
        
        # Create student user
        student = User(
            username='student1',
            email='student@example.com',
            name='Student One',
            role='student',
            school_id=school.id,
            is_active=True
        )
        student.set_password('student123')
        db.session.add(student)
        
        db.session.commit()
        print("Database initialized with default data!")

if __name__ == '__main__':
    init_db()
