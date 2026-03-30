"""
One-time script to link existing User accounts to Staff records by first name.
Run with: python fix_staff_links.py
"""
from app import app, db
from models import User, Staff

with app.app_context():
    users = User.query.filter_by(staff_id=None, role='nurse').all()
    if not users:
        print("No unlinked nurse accounts found.")
    for user in users:
        first_name = user.username.split('.')[0]  # username is first.last
        match = Staff.query.filter(
            db.func.lower(Staff.name).like(db.func.lower(first_name) + '%')
        ).first()
        if match:
            user.staff_id = match.id
            print(f"  Linked {user.email} -> {match.name}")
        else:
            print(f"  No match found for {user.email} (first name: {first_name})")
    db.session.commit()
    print("Done.")
