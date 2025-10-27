from app import app, db
from models import User

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print("Admin user already exists")
    else:
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('admin123')  
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin user created:")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   Email: admin@example.com")