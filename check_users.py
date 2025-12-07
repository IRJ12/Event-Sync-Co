# check_users.py
from app import create_app
from models import User, School, db

def check_and_fix_teacher():
    app = create_app()
    with app.app_context():
        print("=== Checking Database ===")
        
        # Check all users
        users = User.query.all()
        if users:
            print("\nExisting Users:")
            for user in users:
                print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {user.role}, Active: {user.is_active}")
        else:
            print("\nNo users found in the database.")
        
        # Check if teacher1 exists
        teacher = User.query.filter_by(username='teacher1').first()
        if not teacher:
            print("\nCreating teacher1 user...")
            # Create a school if none exists
            school = School.query.first()
            if not school:
                school = School(name='Default School', location='Default Location')
                db.session.add(school)
                db.session.commit()
                print("Created default school")
            
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
            db.session.commit()
            print("✅ Created teacher1 user with password 'teacher123'")
        else:
            print("\nUpdating teacher1 user...")
            # Ensure teacher is active and has correct password
            teacher.is_active = True
            teacher.set_password('teacher123')
            db.session.commit()
            print("✅ Updated teacher1 user (active, password reset to 'teacher123')")
        
        print("\n=== Verification ===")
        teacher = User.query.filter_by(username='teacher1').first()
        if teacher and teacher.check_password('teacher123'):
            print("✅ Teacher login should work with:")
            print(f"   Username: teacher1")
            print(f"   Password: teacher123")
            print("\nTry logging in at http://localhost:5000/auth/login")
        else:
            print("❌ Failed to set up teacher user correctly")

if __name__ == '__main__':
    check_and_fix_teacher()
