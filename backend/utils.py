from models import Shift, TimeOffRequest, Staff, StaffArea
from datetime import datetime, timedelta
from db import db

def validate_shift(staff_id, area_id, date, start_time, end_time, shift_id=None):
    errors = []
    
    staff = Staff.query.get(staff_id)
    area = StaffArea.query.get(area_id)
    
    if not staff:
        return False, "Staff member not found"
    if not area:
        return False, "Area not found"
    
    start_dt = datetime.combine(date, start_time)
    end_dt = datetime.combine(date, end_time)
    shift_duration = (end_dt - start_dt).total_seconds() / 3600 
    
    # 1. Check shift length matches staff requirement
    if staff.shift_length == 8 and shift_duration != 8:
        errors.append(f"{staff.name} works 8-hour shifts. This shift is {shift_duration} hours.")
    elif staff.shift_length == 10 and shift_duration != 10:
        errors.append(f"{staff.name} works 10-hour shifts. This shift is {shift_duration} hours.")
    
    # 2. Check for double-booking (overlapping shifts)
    query = Shift.query.filter(
        Shift.staff_id == staff_id,
        Shift.date == date
    )
    if shift_id: 
        query = query.filter(Shift.id != shift_id)
    
    existing_shifts = query.all()
    for existing in existing_shifts:
        existing_start = datetime.combine(date, existing.start_time)
        existing_end = datetime.combine(date, existing.end_time)
        
        # Check for overlap
        if not (end_dt <= existing_start or start_dt >= existing_end):
            errors.append(f"{staff.name} is already scheduled {existing.start_time.strftime('%H:%M')}-{existing.end_time.strftime('%H:%M')} in {existing.area.name}")
    
    # 3. Check time-off conflicts
    time_off_requests = TimeOffRequest.query.filter(
        TimeOffRequest.staff_id == staff_id,
        TimeOffRequest.status == 'approved',
        TimeOffRequest.start_date <= date,
        TimeOffRequest.end_date >= date
    ).all()
    
    if time_off_requests:
        errors.append(f"{staff.name} has approved time-off on this date")
    
    # 4. Check required days off (must be off ALL of these days)
    if staff.required_days_off:
        import json
        required_off = json.loads(staff.required_days_off)
        day_of_week = date.strftime('%A')
        
        if day_of_week in required_off:
            errors.append(f"{staff.name} must be off on {day_of_week}s")

    # 5. Check flexible days off (must be off AT LEAST ONE of these days)
    if staff.flexible_days_off:
        import json
        flexible_off = json.loads(staff.flexible_days_off)
        day_of_week = date.strftime('%A')
        
        if day_of_week in flexible_off:
            monday = date - timedelta(days=date.weekday())
            
            for other_day in flexible_off:
                if other_day != day_of_week:
                    day_offset = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(other_day)
                    other_date = monday + timedelta(days=day_offset)
                    
                    existing_shifts = Shift.query.filter(
                        Shift.staff_id == staff_id,
                        Shift.date == other_date
                    )
                    if shift_id:
                        existing_shifts = existing_shifts.filter(Shift.id != shift_id)
                    
                    if existing_shifts.count() > 0:
                        days_str = ' or '.join(flexible_off)
                        errors.append(f"{staff.name} must have at least one of these days off: {days_str}. Already scheduled {other_day}.")
                        break
    
    # 6. Check 10-hour staff get at least 1 day off Mon-Fri
    if staff.shift_length == 10 and staff.days_per_week == 4:
        # Get Monday of the week
        monday = date - timedelta(days=date.weekday())
        week_dates = [monday + timedelta(days=i) for i in range(5)]  # Mon-Fri
        
        # Count scheduled days this week
        scheduled_query = Shift.query.filter(
            Shift.staff_id == staff_id,
            Shift.date.in_(week_dates)
        )
        if shift_id:
            scheduled_query = scheduled_query.filter(Shift.id != shift_id)
        
        scheduled_dates = {shift.date for shift in scheduled_query.all()}
        scheduled_dates.add(date) 
        
        if len(scheduled_dates) > 4:
            errors.append(f"{staff.name} works 4 days/week and must have at least 1 day off Mon-Fri. This would be their 5th day.")
    
    # 7. Check area restrictions for per diem staff
    if staff.area_restrictions and staff.area_restrictions != '["Any"]':
        import json
        allowed_areas = json.loads(staff.area_restrictions)
        if area.name not in allowed_areas:
            errors.append(f"{staff.name} can only work in: {', '.join(allowed_areas)}")
    
    # 8. Check start time rules for RNs
    if staff.role == 'RN':
        start_time_str = start_time.strftime('%H:%M')
        
        # Early nurses (6:15, 6:30) should be in Admitting
        if start_time_str in ['06:15', '06:30'] and area.name != 'Admitting':
            errors.append(f"RNs starting at {start_time_str} should be assigned to Admitting, not {area.name}")
        
        # 7:30 nurses should be in Recovery
        if start_time_str == '07:30' and area.name != 'Recovery':
            errors.append(f"RNs starting at 07:30 should be assigned to Recovery, not {area.name}")
    
    # 9. Check if start time is valid
    valid_start_times = ['06:15', '06:30', '07:00', '07:30']
    if start_time.strftime('%H:%M') not in valid_start_times:
        errors.append(f"Start time must be one of: {', '.join(valid_start_times)}")
    
    if errors:
        return False, " | ".join(errors)
    
    return True, "Valid"


def check_area_coverage(area_id, date):
    area = StaffArea.query.get(area_id)
    if not area:
        return False, ["Area not found"]
    
    shifts = Shift.query.filter(
        Shift.area_id == area_id,
        Shift.date == date
    ).all()
    
    rn_count = sum(1 for s in shifts if s.staff_member.role == 'RN')
    tech_count = sum(1 for s in shifts if s.staff_member.role == 'GI_Tech')
    scope_tech_count = sum(1 for s in shifts if s.staff_member.role == 'Scope_Tech')
    
    warnings = []

    if area.required_rn_count > 0 and rn_count < area.required_rn_count:
        warnings.append(f"Needs {area.required_rn_count - rn_count} more RN(s)")
    
    if area.required_tech_count > 0 and tech_count < area.required_tech_count:
        warnings.append(f"Needs {area.required_tech_count - tech_count} more Tech(s)")
    
    if area.required_scope_tech_count > 0 and scope_tech_count < area.required_scope_tech_count:
        warnings.append(f"Needs {area.required_scope_tech_count - scope_tech_count} more Scope Tech(s)")
    
    is_covered = len(warnings) == 0
    
    return is_covered, warnings