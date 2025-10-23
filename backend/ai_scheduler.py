from dotenv import load_dotenv
load_dotenv()
import os
import json
from datetime import datetime, timedelta
from models import Staff, StaffArea, Shift, TimeOffRequest
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_weekly_schedule(week_start_date, fill_empty_only=False, existing_shifts=None):
    """
    Generate a weekly schedule using AI
    
    Args:
        week_start_date: Monday of the week to schedule (datetime.date)
        fill_empty_only: If True, only fill gaps. If False, generate full schedule
        existing_shifts: List of existing shifts (for fill_empty_only mode)
    
    Returns:
        List of shift dictionaries to create
    """
    
    staff_list = Staff.query.filter_by(is_active=True).all()
    
    areas = StaffArea.query.all()
    
    # Get approved time-off for this week
    week_end = week_start_date + timedelta(days=4)  # Friday
    time_off = TimeOffRequest.query.filter(
        TimeOffRequest.status == 'approved',
        TimeOffRequest.start_date <= week_end,
        TimeOffRequest.end_date >= week_start_date
    ).all()
    
    staff_info = []
    for s in staff_list:
        staff_dict = {
            'id': s.id,
            'name': s.name,
            'role': s.role,
            'shift_length': s.shift_length,
            'days_per_week': s.days_per_week,
            'start_time': s.start_time.strftime('%H:%M') if s.start_time else None,
            'is_per_diem': s.is_per_diem,
            'area_restrictions': json.loads(s.area_restrictions) if s.area_restrictions else ["Any"],
            'required_days_off': json.loads(s.required_days_off) if s.required_days_off else [],
            'flexible_days_off': json.loads(s.flexible_days_off) if s.flexible_days_off else []
        }
        staff_info.append(staff_dict)
    
    area_info = []
    area_id_map = {}
    for a in areas:
        area_dict = {
            'id': a.id,
            'name': a.name,
            'required_rn_count': a.required_rn_count,
            'required_tech_count': a.required_tech_count,
            'required_scope_tech_count': a.required_scope_tech_count
        }
        area_info.append(area_dict)
        area_id_map[a.name] = a.id
    admitting_id = area_id_map.get('Admitting')
    recovery_id = area_id_map.get('Recovery')
    proc2_id = area_id_map.get('Procedure Room 2')
    proc3_id = area_id_map.get('Procedure Room 3')
    proc4_id = area_id_map.get('Procedure Room 4')
    scope_id = area_id_map.get('Scope Room')

    
    time_off_info = []
    for t in time_off:
        time_off_info.append({
            'staff_id': t.staff_id,
            'staff_name': t.staff_member.name,
            'start_date': t.start_date.strftime('%Y-%m-%d'),
            'end_date': t.end_date.strftime('%Y-%m-%d')
        })
    
    existing_shifts_info = []
    if fill_empty_only and existing_shifts:
        for shift in existing_shifts:
            existing_shifts_info.append({
                'staff_id': shift.staff_id,
                'staff_name': shift.staff_member.name,
                'area_id': shift.area_id,
                'area_name': shift.area.name,
                'date': shift.date.strftime('%Y-%m-%d'),
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M')
            })
    
    weekdays = []
    for i in range(5): 
        day = week_start_date + timedelta(days=i)
        weekdays.append({
            'date': day.strftime('%Y-%m-%d'),
            'day_name': day.strftime('%A')
        })

# Build the prompt
    if fill_empty_only:
        prompt = f"""You are a medical office scheduling assistant. Generate shift assignments to FILL GAPS in an existing schedule.


    EXISTING SHIFTS:
    {json.dumps(existing_shifts_info, indent=2)}

    DO NOT create shifts for staff/areas/dates that already have shifts above.
    ONLY suggest new shifts to fill understaffed areas.

    """
    else:
        prompt = f"""You are a medical office scheduling assistant. Generate a COMPLETE weekly schedule from scratch for a medical office.

    IMPORTANT: This is a REAL medical office. The schedule MUST meet all staffing requirements and constraints.

    """

    prompt += f"""
    WEEK TO SCHEDULE: {week_start_date.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}
    Days: Monday, Tuesday, Wednesday, Thursday, Friday (5 days total)

    STAFF AVAILABLE:
    {json.dumps(staff_info, indent=2)}

    AREAS THAT EXIST (USE THESE EXACT IDs):
    {json.dumps(area_info, indent=2)}

    CRITICAL: You MUST use these exact area_id values in your output:
    - Admitting: area_id = {admitting_id}
    - Recovery: area_id = {recovery_id}
    - Procedure Room 2: area_id = {proc2_id}
    - Procedure Room 3: area_id = {proc3_id}
    - Procedure Room 4: area_id = {proc4_id}
    - Scope Room: area_id = {scope_id}

    APPROVED TIME-OFF (DO NOT schedule these staff on these dates):
    {json.dumps(time_off_info, indent=2)}

    ====== CRITICAL STAFFING REQUIREMENTS (MUST BE MET EVERY DAY) ======

    ADMITTING (area_id: {admitting_id}):
    - MUST have exactly 2 RNs per day
    - These RNs should start at 6:15 AM or 6:30 AM
    - Rotate different RNs through Admitting each day

    RECOVERY (area_id: {recovery_id}):
    - MUST have exactly 2 RNs per day
    - These RNs should start at 7:30 AM (or 7:00 AM)
    - Rotate different RNs through Recovery each day

    PROCEDURE ROOM 2 (area_id: {proc2_id}):
    - MUST have exactly 2 people per day
    - Can be: 2 GI Techs, OR 2 RNs, OR 1 GI Tech + 1 RN
    - Rotate staff through this room each day

    PROCEDURE ROOM 3 (area_id: {proc3_id}):
    - MUST have exactly 2 people per day
    - Can be: 2 GI Techs, OR 2 RNs, OR 1 GI Tech + 1 RN
    - Rotate staff through this room each day

    PROCEDURE ROOM 4 (area_id: {proc4_id}):
    - MUST have exactly 2 people per day
    - Can be: 2 GI Techs, OR 2 RNs, OR 1 GI Tech + 1 RN
    - Rotate staff through this room each day

    SCOPE ROOM (area_id: {scope_id}):
    - MUST have exactly 2 Scope Techs per day (Olga and Jesus)
    - If one is absent, substitute 1 Scope Tech with 1 GI Tech
    - Check time-off before assigning

    ====== START TIME REQUIREMENTS (MANDATORY) ======

    EVERY DAY MUST HAVE:
    - Exactly 1 RN starting at 6:15 AM (assign to Admitting)
    - Exactly 1 RN starting at 6:30 AM (assign to Admitting)
    - Exactly 2 RNs starting at 7:30 AM (assign to Recovery)
    - RNs can also start at 7:00 AM if needed (assign to Recovery or Admitting)

    TECH START TIMES:
    - Exactly 1 Tech starting at 6:00 AM (Jess preferred, Curtis if Jess is off)
    - Other Techs start at 7:00 AM or 7:30 AM
    - Distribute tech start times to ensure coverage

    ====== SHIFT LENGTH RULES (MANDATORY - MUST FOLLOW) ======

    10-HOUR SHIFT STAFF (work EXACTLY 4 days/week, NOT 5):
    {json.dumps([s for s in staff_info if s['shift_length'] == 10], indent=2)}

    CRITICAL: These staff work ONLY 4 days out of Monday-Friday. They get 1 weekday off.
    - Leah: Works 4 days, OFF 1 day (rotate which day across different weeks)
    - Alannah: Works 4 days, OFF 1 day
    - Mary: Works 4 days, OFF 1 day
    - Cameron: Works 4 days, OFF 1 day
    - Curtis: Works 4 days, OFF 1 day
    - Eileen: Works 4 days, OFF 1 day
    - Elizabeth: Works 4 days, OFF 1 day
    - Stefan: Works 4 days, OFF 1 day
    - Jess: Works 4 days, OFF 1 day

    Distribute their off days: Don't give everyone Monday off. Spread it: Mon, Tue, Wed, Thu, Fri.
    End time calculation: start + 10 hours (e.g., 6:15 start → 16:15 end)

    8-HOUR SHIFT STAFF:
    {json.dumps([s for s in staff_info if s['shift_length'] == 8], indent=2)}

    Work their specified days_per_week (check each person's days_per_week value).
    End time calculation: start + 8 hours (e.g., 7:30 start → 15:30 end)

    ====== CONSTRAINT RULES (MANDATORY) ======

    1. REQUIRED DAYS OFF: 
    - Sam MUST be off on Wednesday (required_days_off: ["Wednesday"])
    - Do NOT schedule Sam on ANY Wednesday

    2. FLEXIBLE DAYS OFF: If staff has flexible_days_off, they MUST be off AT LEAST ONE of those days
    - Example: If flexible_days_off: ["Tuesday", "Thursday"], must be off Tuesday OR Thursday (or both)

    3. AREA RESTRICTIONS: Per diem staff can ONLY work in their allowed areas

    4. TIME-OFF: Do NOT schedule staff during approved time-off periods

    5. NO DOUBLE BOOKING: Each staff member can only have 1 shift per day

    6. 4-DAY LIMIT: Staff working 10-hour shifts can have AT MOST 4 shifts in the week

    ====== ROTATION STRATEGY (CRITICAL FOR QUALITY) ======

    RNs CAN AND SHOULD WORK IN PROCEDURE ROOMS!

    RN ROTATION EXAMPLES:
    - Leah Monday: Admitting, Tuesday: OFF, Wednesday: Procedure Room 2, Thursday: Recovery, Friday: Procedure Room 3
    - Alannah Monday: Recovery, Tuesday: Procedure Room 2, Wednesday: OFF, Thursday: Admitting, Friday: Procedure Room 4
    - Mary Monday: Procedure Room 2, Tuesday: Recovery, Wednesday: Admitting, Thursday: OFF, Friday: Procedure Room 3
    - Cameron Monday: Procedure Room 3, Tuesday: Admitting, Wednesday: Recovery, Thursday: Procedure Room 4, Friday: OFF

    Mix RNs into procedure rooms! Don't just use GI Techs.
    Each RN should work in at least 2-3 different areas during their 4 working days.

    GI TECH ROTATION:
    - Curtis: Rotate between Procedure Rooms 2, 3, 4 (works 4 days, 1 day off)
    - Eileen: Rotate between Procedure Rooms 2, 3, 4 (works 4 days, 1 day off)
    - Elizabeth: Rotate between Procedure Rooms 2, 3, 4 (works 4 days, 1 day off)
    - Stefan: Rotate between Procedure Rooms 2, 3, 4 (works 4 days, 1 day off)
    - Jess: First tech at 6:00 AM, rotate between Procedure Rooms (works 4 days, 1 day off)
    - Sam: Rotate between Procedure Rooms (MUST be OFF Wednesday, works 3 other days)

    SCOPE TECHS (8-hour, 5 days/week):
    - Olga: Scope Room every day she works (works 5 days)
    - Jesus: Scope Room every day he works (works 5 days)

    ====== STEP-BY-STEP SCHEDULING PROCESS ======

    For EACH day (Monday through Friday):

    STEP 1 - Check who is available today:
    a. Remove staff on required days off (Sam on Wednesday)
    b. Remove staff on approved time-off
    c. Remove staff who already worked 4 days (if 10-hour shift)
    d. For flexible days off, make sure they get at least 1 off during the week

    STEP 2 - Assign RNs (need 4 total per day):
    a. Assign 1 RN to Admitting (area_id: {admitting_id}) at 6:15 AM
    b. Assign 1 RN to Admitting (area_id: {admitting_id}) at 6:30 AM
    c. Assign 2 RNs to Recovery (area_id: {recovery_id}) at 7:30 AM
    d. REMEMBER: You have Leah, Alannah, Mary, Cameron (all work 4 days)
    e. Each should be OFF 1 different day
    f. Rotate them through different areas each day they work

    STEP 3 - Assign Scope Room (area_id: {scope_id}):
    a. Assign Olga at 7:30 AM (8-hour shift, ends 15:30)
    b. Assign Jesus at 9:00 AM (8-hour shift, ends 17:00)
    c. If one is on time-off, substitute with a GI Tech

    STEP 4 - Assign Opening Tech (6:00 AM):
    a. Usually Jess (if not off and hasn't worked 4 days yet)
    b. Otherwise Curtis
    c. Assign to any Procedure Room

    STEP 5 - Fill Procedure Rooms (need 2 people each):
    a. Procedure Room 2 (area_id: {proc2_id}): Use GI Techs OR RNs
    b. Procedure Room 3 (area_id: {proc3_id}): Use GI Techs OR RNs  
    c. Procedure Room 4 (area_id: {proc4_id}): Use GI Techs OR RNs
    d. IMPORTANT: Mix in RNs! Don't only use GI Techs
    e. Example: Room 2 could have 1 RN + 1 GI Tech
    f. Start times for techs: 7:00 AM or 7:30 AM
    g. Remember Sam CANNOT work Wednesday

    STEP 6 - Verify constraints for EACH staff member:
    a. Count shifts for each person - 10-hour staff should have EXACTLY 4 (not 5!)
    b. 8-hour staff should have their specified days_per_week
    c. Sam has 0 shifts on Wednesday? ✓
    d. Everyone with flexible days off has at least 1 off? ✓
    e. No one scheduled during time-off? ✓
    f. Each person worked in multiple different areas? ✓

    STEP 7 - Final verification before output:
    CRITICAL CHECKS:
    - Leah: Count her shifts. Should be exactly 4, not 5. ✓
    - Alannah: Count her shifts. Should be exactly 4, not 5. ✓
    - Mary: Count her shifts. Should be exactly 4, not 5. ✓
    - Cameron: Count her shifts. Should be exactly 4, not 5. ✓
    - Curtis: Should be exactly 4, not 5. ✓
    - All other 10-hour staff: Exactly 4 shifts each. ✓
    - Sam: Zero shifts on Wednesday. ✓
    - Did you use RNs in procedure rooms? ✓
    - Did each person rotate areas? ✓

    ====== EXAMPLE OUTPUT STRUCTURE (for reference) ======

    Here's what ONE DAY (Monday) should look like (you need 5 days like this):

    Monday, Oct 20, 2025:
    [
    {{"staff_id": 18, "area_id": {admitting_id}, "date": "2025-10-20", "start_time": "06:15", "end_time": "16:15"}},  // Leah in Admitting
    {{"staff_id": 19, "area_id": {admitting_id}, "date": "2025-10-20", "start_time": "06:30", "end_time": "16:30"}},  // Alannah in Admitting
    {{"staff_id": 20, "area_id": {recovery_id}, "date": "2025-10-20", "start_time": "07:30", "end_time": "17:30"}},  // Mary in Recovery
    {{"staff_id": 21, "area_id": {recovery_id}, "date": "2025-10-20", "start_time": "07:30", "end_time": "17:30"}},  // Cameron in Recovery
    {{"staff_id": 32, "area_id": {scope_id}, "date": "2025-10-20", "start_time": "07:30", "end_time": "15:30"}},  // Olga in Scope Room
    {{"staff_id": 33, "area_id": {scope_id}, "date": "2025-10-20", "start_time": "09:00", "end_time": "17:00"}},  // Jesus in Scope Room
    {{"staff_id": 30, "area_id": {proc2_id}, "date": "2025-10-20", "start_time": "06:00", "end_time": "16:00"}},  // Jess in Proc Room 2
    {{"staff_id": 26, "area_id": {proc2_id}, "date": "2025-10-20", "start_time": "07:00", "end_time": "17:00"}},  // Curtis in Proc Room 2
    {{"staff_id": 27, "area_id": {proc3_id}, "date": "2025-10-20", "start_time": "07:00", "end_time": "17:00"}},  // Eileen in Proc Room 3
    {{"staff_id": 28, "area_id": {proc3_id}, "date": "2025-10-20", "start_time": "07:30", "end_time": "17:30"}},  // Elizabeth in Proc Room 3
    {{"staff_id": 29, "area_id": {proc4_id}, "date": "2025-10-20", "start_time": "07:00", "end_time": "17:00"}},  // Stefan in Proc Room 4
    {{"staff_id": 25, "area_id": {proc4_id}, "date": "2025-10-20", "start_time": "07:00", "end_time": "15:00"}}   // Sam in Proc Room 4
    ]

    That's 12 shifts for Monday. You need to generate similar for Tuesday, Wednesday, Thursday, Friday.
    Total: 12 × 5 = 60 shifts minimum.

    Now generate the FULL week with proper rotation and constraints!

  ====== SHIFT COUNT REQUIREMENTS ======

    YOU MUST GENERATE EXACTLY THE RIGHT NUMBER OF SHIFTS!

    DAILY REQUIREMENTS (EVERY DAY):
    - 2 RNs in Admitting = 2 shifts
    - 2 RNs in Recovery = 2 shifts
    - 2 people in Procedure Room 2 = 2 shifts
    - 2 people in Procedure Room 3 = 2 shifts
    - 2 people in Procedure Room 4 = 2 shifts
    - 2 people in Scope Room = 2 shifts

    TOTAL PER DAY: 12 shifts minimum

    WEEKLY TOTAL (5 days): 12 shifts/day × 5 days = 60 shifts MINIMUM

    If you generate less than 60 shifts, you are missing required coverage!

    VERIFY YOUR OUTPUT:
    - Monday: Count shifts. Should be at least 12. ✓
    - Tuesday: Count shifts. Should be at least 12. ✓
    - Wednesday: Count shifts. Should be at least 12. ✓
    - Thursday: Count shifts. Should be at least 12. ✓
    - Friday: Count shifts. Should be at least 12. ✓
    - TOTAL: Should be 60-65 shifts ✓

    If your output has only 42 shifts, YOU ARE MISSING ENTIRE AREAS!

    ====== OUTPUT FORMAT PART 1 ======

    Return ONLY a valid JSON array with 60-65 shift objects.

    BEFORE YOU OUTPUT, COUNT:
    - How many shifts on Monday? (need 12)
    - How many shifts on Tuesday? (need 12)
    - How many shifts on Wednesday? (need 12)
    - How many shifts on Thursday? (need 12)
    - How many shifts on Friday? (need 12)
    - Total shifts? (need 60-65)

    If count is less than 60, ADD MORE SHIFTS to fill gaps!

    Each area needs 2 people every single day. Do not leave areas empty.

        ====== OUTPUT FORMAT PART 2 ======

    Return ONLY a valid JSON array. Each shift object:
    {{
    "staff_id": <number>,
    "area_id": <number>,
    "date": "YYYY-MM-DD",
    "start_time": "HH:MM",
    "end_time": "HH:MM"
    }}

    EXPECTED SHIFT COUNTS (verify before outputting):
    - Leah: 4 shifts (10-hour staff)
    - Alannah: 4 shifts (10-hour staff)
    - Mary: 4 shifts (10-hour staff)
    - Cameron: 4 shifts (10-hour staff)
    - Curtis: 4 shifts (10-hour staff)
    - Eileen: 4 shifts (10-hour staff)
    - Elizabeth: 4 shifts (10-hour staff)
    - Stefan: 4 shifts (10-hour staff)
    - Jess: 4 shifts (10-hour staff)
    - Sam: 4 shifts total, 0 on Wednesday (8-hour, 4 days/week, off Wed)
    - Olga: 5 shifts (8-hour, 5 days/week)
    - Jesus: 5 shifts (8-hour, 5 days/week)

    Total expected: approximately 60-65 shifts for the week.

    DO NOT include any explanation, markdown, or extra text - ONLY the JSON array.

    TRIPLE-CHECK before submitting:
    1. No 10-hour staff has more than 4 shifts
    2. Sam has 0 shifts on any Wednesday
    3. RNs appear in Procedure Rooms (not just Admitting/Recovery)
    4. Each person rotates through different areas
    5. All 6 areas are staffed every day
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a medical office scheduling expert. You generate optimal schedules that meet all staffing requirements and constraints."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=10000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
            content = content.strip()
        
        suggested_shifts = json.loads(content)
        
        return {
            'success': True,
            'shifts': suggested_shifts,
            'message': f'Generated {len(suggested_shifts)} shift suggestions'
        }
        
    except Exception as e:
        return {
            'success': False,
            'shifts': [],
            'message': f'Failed to generate schedule: {str(e)}'
        }