from app import app, db
from models import Staff, StaffArea, Shift, TimeOffRequest
from datetime import datetime, time, date, timedelta

def seed_database():
    with app.app_context():
        print("Clearing existing data...")
        TimeOffRequest.query.delete()
        Shift.query.delete()
        Staff.query.delete()
        StaffArea.query.delete()
        db.session.commit()
        
        print("Seeding staff areas...")
        areas = [
            StaffArea(name='Admitting', required_rn_count=2, required_tech_count=0),
            StaffArea(name='Recovery', required_rn_count=2, required_tech_count=0),
            StaffArea(name='Procedure Room 2', required_rn_count=0, required_tech_count=2),
            StaffArea(name='Procedure Room 3', required_rn_count=0, required_tech_count=2),
            StaffArea(name='Procedure Room 4', required_rn_count=0, required_tech_count=2),
            StaffArea(name='Scope Room', required_rn_count=0, required_tech_count=0, required_scope_tech_count=2,
                     special_rules='Primarily Olga and Jesus. Can substitute 1 scope tech with GI tech if needed.')
        ]
        db.session.add_all(areas)
        db.session.commit()
        print(f"Created {len(areas)} staff areas")
        
        print("Seeding staff members...")
        staff_members = [
            # 10-hour RNs
            Staff(name='Leah', role='RN', shift_length=10, days_per_week=4, is_per_diem=False),
            Staff(name='Alannah', role='RN', shift_length=10, days_per_week=4, is_per_diem=False),
            Staff(name='Mary', role='RN', shift_length=10, days_per_week=4, is_per_diem=False),
            Staff(name='Cameron', role='RN', shift_length=10, days_per_week=4, is_per_diem=False),
            
            # 8-hour RN
            Staff(name='Deepa', role='RN', shift_length=8, days_per_week=4, is_per_diem=False,
                 flexible_days_off='["Tuesday", "Thursday"]'),
            
            # Per Diem RNs
            Staff(name='Trisha', role='RN', shift_length=8, days_per_week=4, is_per_diem=True,
                 area_restrictions='["Recovery"]'),
            Staff(name='Debbie', role='RN', shift_length=8, days_per_week=4, is_per_diem=True,
                 area_restrictions='["Recovery"]'),
            Staff(name='Carolyn', role='RN', shift_length=8, days_per_week=4, is_per_diem=True,
                 area_restrictions='["Any"]'),
            
            # GI Techs
            Staff(name='Sam', role='GI_Tech', shift_length=8, days_per_week=4, is_per_diem=False,
                 required_days_off='["Wednesday"]'),
            Staff(name='Curtis', role='GI_Tech', shift_length=10, days_per_week=4, is_per_diem=False),
            Staff(name='Eileen', role='GI_Tech', shift_length=10, days_per_week=4, is_per_diem=False),
            Staff(name='Elizabeth', role='GI_Tech', shift_length=10, days_per_week=4, is_per_diem=False),
            Staff(name='Stefan', role='GI_Tech', shift_length=10, days_per_week=4, is_per_diem=False),
            Staff(name='Jess', role='GI_Tech', shift_length=10, days_per_week=4, is_per_diem=False,
                 start_time=time(6, 15)),
            
            # Scope Techs
            Staff(name='Olga', role='Scope_Tech', shift_length=8, days_per_week=5, is_per_diem=False,
                 start_time=time(7, 30)),
            Staff(name='Jesus', role='Scope_Tech', shift_length=8, days_per_week=5, is_per_diem=False,
                 start_time=time(9, 0)),
        ]
        db.session.add_all(staff_members)
        db.session.commit()
        print(f"Created {len(staff_members)} staff members")
        
        print("Seeding sample shifts...")
        today = date.today()
        monday = today - timedelta(days=today.weekday()) 
        
        leah = Staff.query.filter_by(name='Leah').first()
        mary = Staff.query.filter_by(name='Mary').first()
        curtis = Staff.query.filter_by(name='Curtis').first()
        jess = Staff.query.filter_by(name='Jess').first()
        olga = Staff.query.filter_by(name='Olga').first()
        jesus = Staff.query.filter_by(name='Jesus').first()
        
        admitting = StaffArea.query.filter_by(name='Admitting').first()
        recovery = StaffArea.query.filter_by(name='Recovery').first()
        proc_room_2 = StaffArea.query.filter_by(name='Procedure Room 2').first()
        scope_room = StaffArea.query.filter_by(name='Scope Room').first()
        
        sample_shifts = [
            # Monday shifts
            Shift(staff_id=leah.id, area_id=admitting.id, date=monday,
                 start_time=time(6, 15), end_time=time(16, 15)),
            Shift(staff_id=mary.id, area_id=recovery.id, date=monday,
                 start_time=time(7, 0), end_time=time(17, 0)),
            Shift(staff_id=jess.id, area_id=proc_room_2.id, date=monday,
                 start_time=time(6, 15), end_time=time(16, 15)),
            Shift(staff_id=curtis.id, area_id=proc_room_2.id, date=monday,
                 start_time=time(7, 0), end_time=time(17, 0)),
            Shift(staff_id=olga.id, area_id=scope_room.id, date=monday,
                 start_time=time(7, 30), end_time=time(15, 30)),
            Shift(staff_id=jesus.id, area_id=scope_room.id, date=monday,
                 start_time=time(9, 0), end_time=time(17, 0)),
            
            # Tuesday shifts
            Shift(staff_id=leah.id, area_id=admitting.id, date=monday + timedelta(days=1),
                 start_time=time(6, 15), end_time=time(16, 15)),
            Shift(staff_id=mary.id, area_id=recovery.id, date=monday + timedelta(days=1),
                 start_time=time(7, 0), end_time=time(17, 0)),
        ]
        db.session.add_all(sample_shifts)
        db.session.commit()
        print(f"Created {len(sample_shifts)} sample shifts")
        
        print("Seeding sample time-off requests...")
        next_week = monday + timedelta(days=7)
        time_off_requests = [
            TimeOffRequest(
                staff_id=curtis.id,
                start_date=next_week,
                end_date=next_week + timedelta(days=2),
                reason='Vacation',
                status='pending'
            )
        ]
        db.session.add_all(time_off_requests)
        db.session.commit()
        print(f"Created {len(time_off_requests)} time-off requests")
        
        print(" Database seeded successfully!")
        print(f"   - {len(areas)} staff areas")
        print(f"   - {len(staff_members)} staff members")
        print(f"   - {len(sample_shifts)} shifts")
        print(f"   - {len(time_off_requests)} time-off requests")


if __name__ == '__main__':
    seed_database()