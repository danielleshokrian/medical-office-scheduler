"""
Setup script for Long Island Center for Digestive Health (LICDH)

Run with:  python setup_licdh.py

Temporary admin credentials:
  Email:    lauren@licdh.com
  Password: LICDH@2024!
  (Lauren can reset her password via the "Forgot password?" link once email is configured)
"""

from app import app, db
from models import Staff, StaffArea, Shift, TimeOffRequest, User
from datetime import datetime, time, date, timedelta


def setup():
    with app.app_context():
        print("Clearing existing data...")
        TimeOffRequest.query.delete()
        Shift.query.delete()
        User.query.delete()
        Staff.query.delete()
        StaffArea.query.delete()
        db.session.commit()

        # ── Areas ──────────────────────────────────────────────────────────
        print("Creating staff areas...")
        areas = [
            StaffArea(name='Admitting',       required_rn_count=2, required_tech_count=0),
            StaffArea(name='Recovery',         required_rn_count=2, required_tech_count=0),
            StaffArea(name='Procedure Room 2', required_rn_count=0, required_tech_count=2),
            StaffArea(name='Procedure Room 3', required_rn_count=0, required_tech_count=2),
            StaffArea(name='Procedure Room 4', required_rn_count=0, required_tech_count=2),
            StaffArea(
                name='Scope Room',
                required_rn_count=0,
                required_tech_count=0,
                required_scope_tech_count=2,
                special_rules='Primarily Olga and Jesus. Can substitute 1 scope tech with GI tech if needed.'
            ),
        ]
        db.session.add_all(areas)
        db.session.commit()
        print(f"  {len(areas)} areas created")

        # ── Staff ───────────────────────────────────────────────────────────
        print("Creating staff members...")
        staff_members = [

            # Full-time 10hr RNs (4 days/week, 40hrs)
            Staff(name='Leah',    role='RN', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]'),
            Staff(name='Alannah', role='RN', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]'),
            Staff(name='Mary',    role='RN', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]'),
            Staff(name='Cameron', role='RN', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]'),

            # Part-time 8hr RN — 4 days/week, must be off Tue OR Thu each week
            Staff(name='Deepa', role='RN', shift_length=8, days_per_week=4,
                  is_per_diem=False,
                  flexible_days_off='["Tuesday", "Thursday"]',
                  area_restrictions='["Any"]'),

            # Per diem RNs (8hr, used as needed)
            Staff(name='Trisha',  role='RN', shift_length=8, days_per_week=4,
                  is_per_diem=True, area_restrictions='["Recovery"]'),
            Staff(name='Debbie',  role='RN', shift_length=8, days_per_week=4,
                  is_per_diem=True, area_restrictions='["Recovery"]'),
            Staff(name='Carolyn', role='RN', shift_length=8, days_per_week=4,
                  is_per_diem=True, area_restrictions='["Any"]'),

            # GI Techs
            Staff(name='Sam',      role='GI_Tech', shift_length=8,  days_per_week=4,
                  is_per_diem=False,
                  required_days_off='["Wednesday"]',
                  area_restrictions='["Any"]'),
            Staff(name='Curtis',   role='GI_Tech', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]'),
            Staff(name='Eileen',   role='GI_Tech', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]'),
            Staff(name='Elizabeth',role='GI_Tech', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]'),
            Staff(name='Stefan',   role='GI_Tech', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]'),
            # Jess always starts at 6:15
            Staff(name='Jess',     role='GI_Tech', shift_length=10, days_per_week=4,
                  is_per_diem=False,
                  start_time=time(6, 15),
                  area_restrictions='["Any"]'),

            # Scope Techs
            Staff(name='Olga',  role='Scope_Tech', shift_length=8, days_per_week=5,
                  is_per_diem=False,
                  start_time=time(7, 30),
                  area_restrictions='["Scope Room"]'),
            Staff(name='Jesus', role='Scope_Tech', shift_length=8, days_per_week=5,
                  is_per_diem=False,
                  start_time=time(9, 0),
                  area_restrictions='["Scope Room"]'),
        ]
        db.session.add_all(staff_members)
        db.session.commit()
        print(f"  {len(staff_members)} staff members created")

        # ── Sample shifts (current week Mon–Tue) ────────────────────────────
        print("Creating sample shifts for current week...")
        today  = date.today()
        monday = today - timedelta(days=today.weekday())

        leah     = Staff.query.filter_by(name='Leah').first()
        alannah  = Staff.query.filter_by(name='Alannah').first()
        jess     = Staff.query.filter_by(name='Jess').first()
        curtis   = Staff.query.filter_by(name='Curtis').first()
        olga     = Staff.query.filter_by(name='Olga').first()
        jesus    = Staff.query.filter_by(name='Jesus').first()

        admitting  = StaffArea.query.filter_by(name='Admitting').first()
        recovery   = StaffArea.query.filter_by(name='Recovery').first()
        proc_room2 = StaffArea.query.filter_by(name='Procedure Room 2').first()
        scope_room = StaffArea.query.filter_by(name='Scope Room').first()

        sample_shifts = [
            # Monday
            Shift(staff_id=leah.id,    area_id=admitting.id,  date=monday,
                  start_time=time(6, 15), end_time=time(16, 15)),
            Shift(staff_id=alannah.id, area_id=recovery.id,   date=monday,
                  start_time=time(7, 0),  end_time=time(17, 0)),
            Shift(staff_id=jess.id,    area_id=proc_room2.id, date=monday,
                  start_time=time(6, 15), end_time=time(16, 15)),
            Shift(staff_id=curtis.id,  area_id=proc_room2.id, date=monday,
                  start_time=time(7, 0),  end_time=time(17, 0)),
            Shift(staff_id=olga.id,    area_id=scope_room.id, date=monday,
                  start_time=time(7, 30), end_time=time(15, 30)),
            Shift(staff_id=jesus.id,   area_id=scope_room.id, date=monday,
                  start_time=time(9, 0),  end_time=time(17, 0)),

            # Tuesday
            Shift(staff_id=leah.id,    area_id=admitting.id,  date=monday + timedelta(days=1),
                  start_time=time(6, 15), end_time=time(16, 15)),
            Shift(staff_id=alannah.id, area_id=recovery.id,   date=monday + timedelta(days=1),
                  start_time=time(7, 0),  end_time=time(17, 0)),
        ]
        db.session.add_all(sample_shifts)
        db.session.commit()
        print(f"  {len(sample_shifts)} sample shifts created")

        # ── Admin account ───────────────────────────────────────────────────
        print("Creating admin account for Lauren...")
        lauren = User(
            username='lauren',
            email='lauren@licdh.com',
            role='nurse_admin'
        )
        lauren.set_password('LICDH@2024!')
        db.session.add(lauren)
        db.session.commit()
        print("  Admin account created")

        # ── Summary ─────────────────────────────────────────────────────────
        print("\n  LICDH setup complete!")
        print(f"   {len(areas)} areas")
        print(f"   {len(staff_members)} staff members")
        print(f"   {len(sample_shifts)} sample shifts")
        print("\n  Admin login:")
        print("    Email:    lauren@licdh.com")
        print("    Password: LICDH@2024!  (temporary — reset via Forgot Password)")
        print("\n  Share your CLINIC_INVITE_CODE with nurses so they can register.")


if __name__ == '__main__':
    setup()
