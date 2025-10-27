import os
import json
from datetime import datetime, timedelta
from openai import OpenAI
from db import db
from models import Staff, StaffArea, Shift, TimeOffRequest
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def validate_and_fix_schedule(shifts, staff_info, area_info, time_off_info, weekdays):
    """
    Validate AI-generated schedule and fix violations.
    Returns (valid_shifts, errors)
    """
    valid_shifts = []
    errors = []
    
    # Group shifts by staff_id and date for easy lookup
    staff_schedule = defaultdict(list)
    
    for shift in shifts:
        staff_id = shift['staff_id']
        date = shift['date']
        area_id = shift['area_id']
        
        # Find staff info
        staff = next((s for s in staff_info if s['id'] == staff_id), None)
        if not staff:
            errors.append(f"Invalid staff_id {staff_id}")
            continue
        
        # Validation 1: Check required days off
        day_of_week = datetime.strptime(date, '%Y-%m-%d').strftime('%A')
        if day_of_week in staff['required_days_off']:
            errors.append(f"Skipped: {staff['name']} cannot work on {day_of_week} (required day off)")
            continue
        
        # Validation 2: Check approved time-off
        time_off_conflict = any(
            to['staff_id'] == staff_id and 
            to['start_date'] <= date <= to['end_date']
            for to in time_off_info
        )
        if time_off_conflict:
            errors.append(f"Skipped: {staff['name']} has time-off on {date}")
            continue
        
        # Validation 3: Check for double-booking
        if any(s['date'] == date for s in staff_schedule[staff_id]):
            errors.append(f"Skipped: {staff['name']} already scheduled on {date}")
            continue
        
        # Validation 4: Verify area exists
        area = next((a for a in area_info if a['id'] == area_id), None)
        if not area:
            errors.append(f"Invalid area_id {area_id}")
            continue
        
        # Shift is valid!
        valid_shifts.append(shift)
        staff_schedule[staff_id].append(shift)
    
    # Validation 5: Check flexible days off
    for staff in staff_info:
        if staff['flexible_days_off']:
            staff_shifts = staff_schedule[staff['id']]
            shift_days = [datetime.strptime(s['date'], '%Y-%m-%d').strftime('%A') for s in staff_shifts]
            
            # Must be off at least ONE of the flexible days
            if all(day in shift_days for day in staff['flexible_days_off']):
                errors.append(f"Warning: {staff['name']} should have at least one of {staff['flexible_days_off']} off")
    
    return valid_shifts, errors


def generate_weekly_schedule(week_start_date, fill_empty_only=False, existing_shifts=None):
    """
    Generate a weekly schedule using OpenAI API with validation.
    """
    try:
        # Fetch data
        staff_list = Staff.query.filter_by(is_active=True).all()
        area_list = StaffArea.query.all()
        week_end = week_start_date + timedelta(days=4)

        time_off = TimeOffRequest.query.filter(
            TimeOffRequest.status == "approved",
            TimeOffRequest.start_date <= week_end,
            TimeOffRequest.end_date >= week_start_date
        ).all()

        # Serialize staff info
        staff_info = []
        for s in staff_list:
            staff_info.append({
                "id": s.id,
                "name": s.name,
                "role": s.role,
                "shift_length": s.shift_length,
                "days_per_week": s.days_per_week,
                "start_time": s.start_time.strftime('%H:%M') if s.start_time else None,
                "is_per_diem": s.is_per_diem,
                "required_days_off": json.loads(s.required_days_off) if s.required_days_off else [],
                "flexible_days_off": json.loads(s.flexible_days_off) if s.flexible_days_off else []
            })

        # Area info
        area_info = []
        for a in area_list:
            area_info.append({
                "id": a.id,
                "name": a.name,
                "required_rn_count": a.required_rn_count,
                "required_tech_count": a.required_tech_count,
                "required_scope_tech_count": a.required_scope_tech_count
            })

        # Time off info
        time_off_info = []
        for t in time_off:
            time_off_info.append({
                "staff_id": t.staff_id,
                "staff_name": t.staff_member.name,
                "start_date": t.start_date.strftime('%Y-%m-%d'),
                "end_date": t.end_date.strftime('%Y-%m-%d')
            })

        # Generate weekdays
        weekdays = []
        for i in range(5): 
            day = week_start_date + timedelta(days=i)
            weekdays.append({
                'date': day.strftime('%Y-%m-%d'),
                'day_name': day.strftime('%A')
            })

        # Build prompt
        prompt = f"""
Generate a weekly schedule for a medical GI lab.

CRITICAL DATES (use these exact dates):
{json.dumps(weekdays, indent=2)}

STAFF (use exact IDs):
{json.dumps(staff_info, indent=2)}

AREAS (use exact IDs):
{json.dumps(area_info, indent=2)}

APPROVED TIME-OFF (do not schedule):
{json.dumps(time_off_info, indent=2)}

RULES:
1. Each area needs 2 staff per day
2. Match staff roles to area requirements
3. Generate approximately 60 shifts total (12 per day × 5 days)
4. Use the exact staff_id and area_id values provided above
5. RNs for Admitting/Recovery, GI Techs for procedure rooms, Scope Techs for Scope Room

OUTPUT FORMAT - VALID JSON ONLY, NO MARKDOWN OR EXPLANATIONS:
[
  {{"staff_id": 1, "area_id": 1, "date": "2025-10-27", "start_time": "06:15", "end_time": "16:15"}},
  {{"staff_id": 2, "area_id": 1, "date": "2025-10-27", "start_time": "06:30", "end_time": "16:30"}}
]
"""

        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a scheduling assistant. Return ONLY valid JSON array, no markdown, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=12000
        )

        content = response.choices[0].message.content.strip()

        # Logging
        print("\n" + "="*80)
        print("RAW AI RESPONSE (first 500 chars):")
        print("="*80)
        print(content[:500])
        print("="*80 + "\n")

        # Clean JSON
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])  # Remove first and last line
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        # Parse AI output
        try:
            ai_shifts = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"Content that failed: {content[:1000]}")
            raise Exception(f"AI returned invalid JSON: {str(e)}")

        # VALIDATE AND FIX
        valid_shifts, validation_errors = validate_and_fix_schedule(
            ai_shifts, 
            staff_info, 
            area_info, 
            time_off_info, 
            weekdays
        )

        print(f"\n✅ Valid shifts: {len(valid_shifts)} out of {len(ai_shifts)}")
        print(f"⚠️ Validation errors: {len(validation_errors)}")
        for error in validation_errors[:10]:
            print(f"  - {error}")

        return {
            "success": True,
            "shifts": valid_shifts,
            "message": f"✅ Generated {len(valid_shifts)} valid shifts ({len(ai_shifts) - len(valid_shifts)} filtered out)",
            "validation_errors": validation_errors[:20]
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "shifts": [],
            "message": f"❌ Failed to generate schedule: {str(e)}",
            "validation_errors": []
        }
