"""
Demo clinic setup script.

Run with:  python setup_demo.py

Demo credentials:
  Admin:  admin@example.com / admin123
  Nurse:  lori@example.com  / nurse123
  Invite: DEMO2026
"""

from app import app, db
from models import Staff, StaffArea, Shift, TimeOffRequest, User, Clinic
from datetime import time


def setup():
    with app.app_context():
        print("Setting up Demo clinic...")

        clinic = Clinic.query.filter_by(invite_code='DEMO2026').first()
        if clinic:
            print("  Clearing existing Demo data...")
            Shift.query.filter_by(clinic_id=clinic.id).delete()
            TimeOffRequest.query.filter_by(clinic_id=clinic.id).delete()
            User.query.filter_by(clinic_id=clinic.id).delete()
            Staff.query.filter_by(clinic_id=clinic.id).delete()
            StaffArea.query.filter_by(clinic_id=clinic.id).delete()
            db.session.commit()
        else:
            clinic = Clinic(name='Demo GI Clinic', invite_code='DEMO2026')
            db.session.add(clinic)
            db.session.commit()
            print(f"  Clinic created: id={clinic.id}")

        # ── Areas ──────────────────────────────────────────────────────────
        print("Creating areas...")
        areas = [
            StaffArea(name='Admitting',       required_rn_count=2,              clinic_id=clinic.id),
            StaffArea(name='Recovery',         required_rn_count=2,              clinic_id=clinic.id),
            StaffArea(name='Procedure Room 1', required_tech_count=2,            clinic_id=clinic.id),
            StaffArea(name='Procedure Room 2', required_tech_count=2,            clinic_id=clinic.id),
            StaffArea(name='Procedure Room 3', required_tech_count=2,            clinic_id=clinic.id),
            StaffArea(
                name='Scope Room',
                required_scope_tech_count=2,
                special_rules='Riley and Taylor. Can substitute 1 scope tech with GI tech.',
                clinic_id=clinic.id
            ),
            StaffArea(name='Float',  special_rules='Flexible coverage as needed.', clinic_id=clinic.id),
            StaffArea(name='Charge', special_rules='Charge nurse role.',            clinic_id=clinic.id),
        ]
        db.session.add_all(areas)
        db.session.commit()
        print(f"  {len(areas)} areas created")

        # ── Staff ───────────────────────────────────────────────────────────
        print("Creating staff...")
        staff_members = [
            Staff(name='Alex Rivera', role='RN', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]', clinic_id=clinic.id),
            Staff(name='Sam Chen',    role='RN', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]', clinic_id=clinic.id),
            Staff(name='Dana Patel',  role='RN', shift_length=8,  days_per_week=4,
                  is_per_diem=False,
                  flexible_days_off='["Tuesday", "Thursday"]',
                  area_restrictions='["Any"]', clinic_id=clinic.id),
            Staff(name='Jordan Kim',  role='RN', shift_length=8,  days_per_week=4,
                  is_per_diem=True, area_restrictions='["Recovery"]', clinic_id=clinic.id),
            Staff(name='Casey Wong',  role='GI_Tech', shift_length=10, days_per_week=4,
                  is_per_diem=False,
                  start_time=time(6, 15),
                  area_restrictions='["Any"]', clinic_id=clinic.id),
            Staff(name='Morgan Lee',  role='GI_Tech', shift_length=8,  days_per_week=4,
                  is_per_diem=False,
                  required_days_off='["Wednesday"]',
                  area_restrictions='["Any"]', clinic_id=clinic.id),
            Staff(name='Riley Cruz',  role='Scope_Tech', shift_length=8, days_per_week=5,
                  is_per_diem=False,
                  start_time=time(7, 30),
                  area_restrictions='["Scope Room"]', clinic_id=clinic.id),
            Staff(name='Taylor Ngo',  role='Scope_Tech', shift_length=8, days_per_week=5,
                  is_per_diem=False,
                  start_time=time(9, 0),
                  area_restrictions='["Scope Room"]', clinic_id=clinic.id),
        ]
        db.session.add_all(staff_members)
        db.session.commit()
        print(f"  {len(staff_members)} staff members created")

        # ── Users ───────────────────────────────────────────────────────────
        print("Creating demo user accounts...")
        admin_user = User(
            username='demo.admin',
            email='admin@example.com',
            role='nurse_admin',
            clinic_id=clinic.id
        )
        admin_user.set_password('admin123')

        dana = Staff.query.filter_by(name='Dana Patel', clinic_id=clinic.id).first()
        nurse_user = User(
            username='lori',
            email='lori@example.com',
            role='nurse',
            clinic_id=clinic.id,
            staff_id=dana.id if dana else None
        )
        nurse_user.set_password('nurse123')

        db.session.add_all([admin_user, nurse_user])
        db.session.commit()

        print("\n  Demo setup complete!")
        print(f"   {len(areas)} areas, {len(staff_members)} staff")
        print("\n  Login credentials:")
        print("    Admin: admin@example.com / admin123")
        print("    Nurse: lori@example.com  / nurse123")
        print("    Invite code: DEMO2026")


if __name__ == '__main__':
    setup()
