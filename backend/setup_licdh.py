"""
Setup script for Long Island Center for Digestive Health (LICDH)

Run with:  python setup_licdh.py

Temporary admin credentials:
  Email:    lauren@licdh.com
  Password: LICDH@2024!
  (Lauren can reset her password via the "Forgot password?" link once email is configured)
"""

from app import app, db
from models import Staff, StaffArea, Shift, TimeOffRequest, User, Clinic
from datetime import datetime, time, date, timedelta


def setup():
    with app.app_context():
        print("Setting up LICDH clinic...")

        # Find or create the LICDH clinic record
        clinic = Clinic.query.filter_by(invite_code='LICDH2026').first()
        if clinic:
            print("  Clearing existing LICDH data...")
            Shift.query.filter_by(clinic_id=clinic.id).delete()
            TimeOffRequest.query.filter_by(clinic_id=clinic.id).delete()
            User.query.filter_by(clinic_id=clinic.id).delete()
            Staff.query.filter_by(clinic_id=clinic.id).delete()
            StaffArea.query.filter_by(clinic_id=clinic.id).delete()
            db.session.commit()
        else:
            clinic = Clinic(
                name='Long Island Center for Digestive Health',
                invite_code='LICDH2026'
            )
            db.session.add(clinic)
            db.session.commit()
            print(f"  Clinic created: id={clinic.id}")

        # ── Areas ──────────────────────────────────────────────────────────
        print("Creating staff areas...")
        areas = [
            StaffArea(name='Admitting',        required_rn_count=2, required_tech_count=0, clinic_id=clinic.id),
            StaffArea(name='Recovery',          required_rn_count=2, required_tech_count=0, clinic_id=clinic.id),
            StaffArea(name='Procedure Room 1',  required_rn_count=0, required_tech_count=2, clinic_id=clinic.id),
            StaffArea(name='Procedure Room 2',  required_rn_count=0, required_tech_count=2, clinic_id=clinic.id),
            StaffArea(name='Procedure Room 3',  required_rn_count=0, required_tech_count=2, clinic_id=clinic.id),
            StaffArea(name='Procedure Room 4',  required_rn_count=0, required_tech_count=2, clinic_id=clinic.id),
            StaffArea(
                name='Scope Room',
                required_rn_count=0,
                required_tech_count=0,
                required_scope_tech_count=2,
                special_rules='Primarily Olga and Jesus. Can substitute 1 scope tech with GI tech if needed.',
                clinic_id=clinic.id
            ),
            StaffArea(name='Float',  required_rn_count=0, required_tech_count=0,
                      special_rules='1 staff slot -- flexible coverage as needed.', clinic_id=clinic.id),
            StaffArea(name='Charge', required_rn_count=0, required_tech_count=0,
                      special_rules='1 staff slot -- charge nurse role.', clinic_id=clinic.id),
        ]
        db.session.add_all(areas)
        db.session.commit()
        print(f"  {len(areas)} areas created")

        # ── Staff ───────────────────────────────────────────────────────────
        print("Creating staff members...")
        staff_members = [

            # Full-time 10hr RNs (4 days/week, 40hrs)
            Staff(name='Leah',    role='RN', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]', clinic_id=clinic.id),
            Staff(name='Alannah', role='RN', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]', clinic_id=clinic.id),
            Staff(name='Mary',    role='RN', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]', clinic_id=clinic.id),
            Staff(name='Cameron', role='RN', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]', clinic_id=clinic.id),

            # Part-time 8hr RN -- 4 days/week, must be off Tue OR Thu each week
            Staff(name='Deepa', role='RN', shift_length=8, days_per_week=4,
                  is_per_diem=False,
                  flexible_days_off='["Tuesday", "Thursday"]',
                  area_restrictions='["Any"]', clinic_id=clinic.id),

            # Per diem RNs (8hr, used as needed)
            Staff(name='Trisha',  role='RN', shift_length=8, days_per_week=4,
                  is_per_diem=True, area_restrictions='["Recovery"]', clinic_id=clinic.id),
            Staff(name='Debbie',  role='RN', shift_length=8, days_per_week=4,
                  is_per_diem=True, area_restrictions='["Recovery"]', clinic_id=clinic.id),
            Staff(name='Carolyn', role='RN', shift_length=8, days_per_week=4,
                  is_per_diem=True, area_restrictions='["Any"]', clinic_id=clinic.id),

            # GI Techs
            Staff(name='Sam',      role='GI_Tech', shift_length=8,  days_per_week=4,
                  is_per_diem=False,
                  required_days_off='["Wednesday"]',
                  area_restrictions='["Any"]', clinic_id=clinic.id),
            Staff(name='Curtis',   role='GI_Tech', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]', clinic_id=clinic.id),
            Staff(name='Eileen',   role='GI_Tech', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]', clinic_id=clinic.id),
            Staff(name='Elizabeth',role='GI_Tech', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]', clinic_id=clinic.id),
            Staff(name='Stefan',   role='GI_Tech', shift_length=10, days_per_week=4,
                  is_per_diem=False, area_restrictions='["Any"]', clinic_id=clinic.id),
            # Jess always starts at 6:15
            Staff(name='Jess',     role='GI_Tech', shift_length=10, days_per_week=4,
                  is_per_diem=False,
                  start_time=time(6, 15),
                  area_restrictions='["Any"]', clinic_id=clinic.id),

            # Scope Techs
            Staff(name='Olga',  role='Scope_Tech', shift_length=8, days_per_week=5,
                  is_per_diem=False,
                  start_time=time(7, 30),
                  area_restrictions='["Scope Room"]', clinic_id=clinic.id),
            Staff(name='Jesus', role='Scope_Tech', shift_length=8, days_per_week=5,
                  is_per_diem=False,
                  start_time=time(9, 0),
                  area_restrictions='["Scope Room"]', clinic_id=clinic.id),
        ]
        db.session.add_all(staff_members)
        db.session.commit()
        print(f"  {len(staff_members)} staff members created")

        # ── Sample shifts (current week Mon–Tue) ────────────────────────────
        print("Creating sample shifts for current week...")
        today  = date.today()
        monday = today - timedelta(days=today.weekday())

        leah     = Staff.query.filter_by(name='Leah',    clinic_id=clinic.id).first()
        alannah  = Staff.query.filter_by(name='Alannah', clinic_id=clinic.id).first()
        jess     = Staff.query.filter_by(name='Jess',    clinic_id=clinic.id).first()
        curtis   = Staff.query.filter_by(name='Curtis',  clinic_id=clinic.id).first()
        olga     = Staff.query.filter_by(name='Olga',    clinic_id=clinic.id).first()
        jesus    = Staff.query.filter_by(name='Jesus',   clinic_id=clinic.id).first()

        admitting  = StaffArea.query.filter_by(name='Admitting',        clinic_id=clinic.id).first()
        recovery   = StaffArea.query.filter_by(name='Recovery',          clinic_id=clinic.id).first()
        proc_room2 = StaffArea.query.filter_by(name='Procedure Room 2',  clinic_id=clinic.id).first()
        scope_room = StaffArea.query.filter_by(name='Scope Room',        clinic_id=clinic.id).first()

        sample_shifts = [
            # Monday
            Shift(staff_id=leah.id,    area_id=admitting.id,  date=monday,
                  start_time=time(6, 15), end_time=time(16, 15), clinic_id=clinic.id),
            Shift(staff_id=alannah.id, area_id=recovery.id,   date=monday,
                  start_time=time(7, 0),  end_time=time(17, 0),  clinic_id=clinic.id),
            Shift(staff_id=jess.id,    area_id=proc_room2.id, date=monday,
                  start_time=time(6, 15), end_time=time(16, 15), clinic_id=clinic.id),
            Shift(staff_id=curtis.id,  area_id=proc_room2.id, date=monday,
                  start_time=time(7, 0),  end_time=time(17, 0),  clinic_id=clinic.id),
            Shift(staff_id=olga.id,    area_id=scope_room.id, date=monday,
                  start_time=time(7, 30), end_time=time(15, 30), clinic_id=clinic.id),
            Shift(staff_id=jesus.id,   area_id=scope_room.id, date=monday,
                  start_time=time(9, 0),  end_time=time(17, 0),  clinic_id=clinic.id),

            # Tuesday
            Shift(staff_id=leah.id,    area_id=admitting.id,  date=monday + timedelta(days=1),
                  start_time=time(6, 15), end_time=time(16, 15), clinic_id=clinic.id),
            Shift(staff_id=alannah.id, area_id=recovery.id,   date=monday + timedelta(days=1),
                  start_time=time(7, 0),  end_time=time(17, 0),  clinic_id=clinic.id),
        ]
        db.session.add_all(sample_shifts)
        db.session.commit()
        print(f"  {len(sample_shifts)} sample shifts created")

        # ── Admin account ───────────────────────────────────────────────────
        print("Creating admin account for Lauren...")
        lauren = User(
            username='lauren',
            email='lauren@licdh.com',
            role='nurse_admin',
            clinic_id=clinic.id
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
        print("    Password: LICDH@2024!  (temporary -- reset via Forgot Password)")
        print("\n  Invite code: LICDH2026")


if __name__ == '__main__':
    setup()
