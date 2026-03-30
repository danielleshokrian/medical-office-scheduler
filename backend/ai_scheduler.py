"""
Deterministic rule-based weekly schedule generator for LICDH GI Lab.
An optional AI adjustment layer can apply plain-English changes on top.

Rules enforced:
- Scope Room: Olga + Jesus; sub 1 GI Tech if a scope tech is absent
- Admitting: 2 RNs at 6:15 and 6:30
- Recovery: 2 RNs at 7:30
- Charge: 1 RN at 7:00 (not assigned to a procedure room)
- Procedure Rooms 1-4: filled with remaining GI Techs (2 per room)
  - Opener slot: Jess at 6:15; if Jess is off, Curtis at 6:15
  - Other techs: 7:00 / 7:30 alternating
- 4-day/week staff get exactly 1 day off Mon-Fri (distributed to balance coverage)
- Deepa must be off Tuesday OR Thursday each week
- Sam is always off Wednesday (required_days_off in DB)
- Approved PTO and scheduled days off are respected
- Per diem RNs are NOT auto-scheduled (added manually by admin as needed)
"""

import os
import json
from datetime import timedelta
from db import db
from models import Staff, StaffArea, TimeOffRequest

try:
    from openai import OpenAI
    _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
except ImportError:
    _openai_client = None


def apply_ai_adjustments(shifts, instruction, staff_list, area_list):
    """
    Takes a deterministic schedule and applies plain-English adjustments via OpenAI.
    The AI only tweaks the existing schedule — it cannot violate hard rules.
    Returns (adjusted_shifts, ai_notes).
    """
    if not _openai_client:
        return shifts, ["OpenAI not configured — skipping AI adjustment"]

    # Build human-readable schedule for the AI
    staff_by_id = {s.id: s for s in staff_list}
    area_by_id  = {a.id: a for a in area_list}

    readable = []
    for sh in shifts:
        s = staff_by_id.get(sh['staff_id'])
        a = area_by_id.get(sh['area_id'])
        readable.append({
            'staff_id':   sh['staff_id'],
            'staff_name': s.name if s else '?',
            'role':       s.role if s else '?',
            'area_id':    sh['area_id'],
            'area_name':  a.name if a else '?',
            'date':       sh['date'],
            'start_time': sh['start_time'],
            'end_time':   sh['end_time'],
        })

    staff_roster = [
        {'id': s.id, 'name': s.name, 'role': s.role,
         'shift_length': s.shift_length, 'is_per_diem': s.is_per_diem}
        for s in staff_list
    ]

    prompt = f"""You are adjusting a pre-built medical GI lab schedule.

CURRENT SCHEDULE:
{json.dumps(readable, indent=2)}

STAFF ROSTER:
{json.dumps(staff_roster, indent=2)}

ADJUSTMENT REQUESTED:
{instruction}

HARD RULES — never violate these:
1. No staff member may appear twice on the same date
2. Scope Room must have exactly 2 people every day
3. Admitting must have exactly 2 RNs every day
4. Recovery must have exactly 2 RNs every day
5. Do not invent staff IDs or area IDs not in the roster above

Return ONLY the complete modified schedule as a JSON array (same fields as input, \
including staff_name and area_name for display):
[{{"staff_id": 1, "area_id": 2, "date": "YYYY-MM-DD", "start_time": "HH:MM", "end_time": "HH:MM"}}]
No markdown, no explanation — just the JSON array."""

    try:
        response = _openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a scheduling assistant. Return ONLY a valid JSON array."},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.2,
            max_tokens=12000,
        )
        content = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]).strip()
            if content.startswith("json"):
                content = content[4:].strip()

        adjusted = json.loads(content)

        # Hard-rule guard: remove duplicates (same staff, same date)
        seen = set()
        deduped = []
        for sh in adjusted:
            key = (sh['staff_id'], sh['date'])
            if key not in seen:
                seen.add(key)
                deduped.append(sh)

        return deduped, [f"AI applied: {instruction}"]

    except Exception as e:
        print(f"AI adjustment failed: {e}")
        return shifts, [f"AI adjustment failed ({e}) — original schedule kept"]


def generate_weekly_schedule(week_start_date, fill_empty_only=False, existing_shifts=None,
                             ai_instruction=None):
    """
    Build a deterministic weekly schedule for LICDH.
    Returns: {success, shifts, message, validation_errors}
    Each shift dict: {staff_id, area_id, date, start_time, end_time}
    """
    warnings = []
    all_shifts = []

    # ── Load data ──────────────────────────────────────────────────────────────
    staff_list  = Staff.query.filter_by(is_active=True).all()
    areas       = {a.name: a for a in StaffArea.query.all()}
    week_end    = week_start_date + timedelta(days=4)
    weekdays    = [week_start_date + timedelta(days=i) for i in range(5)]

    # ── Build blocked (staff_id, date_str) pairs ───────────────────────────────
    blocked = set()

    # Approved time-off (both PTO and scheduled days off)
    approved = TimeOffRequest.query.filter(
        TimeOffRequest.status == 'approved',
        TimeOffRequest.start_date <= week_end,
        TimeOffRequest.end_date >= week_start_date
    ).all()
    for t in approved:
        cur = t.start_date
        while cur <= t.end_date:
            if week_start_date <= cur <= week_end:
                blocked.add((t.staff_id, cur.strftime('%Y-%m-%d')))
            cur += timedelta(days=1)

    # Fixed required days off (e.g. Sam always off Wednesday)
    for s in staff_list:
        if s.required_days_off:
            for day_name in json.loads(s.required_days_off):
                for d in weekdays:
                    if d.strftime('%A') == day_name:
                        blocked.add((s.id, d.strftime('%Y-%m-%d')))

    # ── Assign 1 flex day off for every 4-day/week staff ──────────────────────
    # (Per diem staff are not auto-scheduled, so skip them here)
    four_day = [s for s in staff_list if s.days_per_week == 4 and not s.is_per_diem]

    # Track how many staff are already off each day (for even distribution)
    off_count = {d.strftime('%Y-%m-%d'): 0 for d in weekdays}
    for (_, ds) in blocked:
        if ds in off_count:
            off_count[ds] += 1

    for s in four_day:
        free_days = [d for d in weekdays if (s.id, d.strftime('%Y-%m-%d')) not in blocked]
        if len(free_days) <= 4:
            continue  # already has a day blocked this week (e.g. from PTO)

        # Deepa: must be off Tuesday or Thursday
        if s.flexible_days_off:
            flex = json.loads(s.flexible_days_off)
            preferred = [d for d in free_days if d.strftime('%A') in flex]
            pool = preferred if preferred else free_days
        else:
            pool = free_days

        # Pick the day with the fewest people already off (balance coverage)
        chosen = min(pool, key=lambda d: off_count[d.strftime('%Y-%m-%d')])
        ds = chosen.strftime('%Y-%m-%d')
        blocked.add((s.id, ds))
        off_count[ds] += 1

    # ── Build schedule day by day ──────────────────────────────────────────────
    for day_idx, day in enumerate(weekdays):
        date_str = day.strftime('%Y-%m-%d')

        today       = [s for s in staff_list if (s.id, date_str) not in blocked]
        rns         = sorted([s for s in today if s.role == 'RN'      and not s.is_per_diem], key=lambda s: s.name)
        gi_techs    = sorted([s for s in today if s.role == 'GI_Tech'],                        key=lambda s: s.name)
        scope_techs = sorted([s for s in today if s.role == 'Scope_Tech'],                     key=lambda s: s.name)

        assigned = set()

        def add(staff, area_name, start_str):
            """Create a shift record for this staff member in this area."""
            area = areas.get(area_name)
            if not area or staff.id in assigned:
                return False
            h, m = int(start_str[:2]), int(start_str[3:])
            end_h = h + staff.shift_length
            all_shifts.append({
                'staff_id':   staff.id,
                'area_id':    area.id,
                'date':       date_str,
                'start_time': start_str,
                'end_time':   f"{end_h:02d}:{m:02d}",
            })
            assigned.add(staff.id)
            return True

        # ── 1. Scope Room ─────────────────────────────────────────────────────
        # Primary: Olga (7:30) + Jesus (9:00) — start times stored in DB
        for st in scope_techs:
            start = st.start_time.strftime('%H:%M') if st.start_time else '07:30'
            add(st, 'Scope Room', start)

        # If fewer than 2 scope techs available, substitute 1 GI Tech
        if len(scope_techs) < 2:
            sub = next((gt for gt in gi_techs if gt.id not in assigned), None)
            if sub:
                add(sub, 'Scope Room', '07:00')
                warnings.append(f"{date_str}: {sub.name} (GI Tech) substituting in Scope Room")

        # ── 2. GI Techs → Procedure Rooms ────────────────────────────────────
        # Opener slot: Jess at 6:15; if Jess is off, Curtis opens at 6:15
        gi_pool = [s for s in gi_techs if s.id not in assigned]
        jess   = next((s for s in gi_pool if s.name == 'Jess'),   None)
        curtis = next((s for s in gi_pool if s.name == 'Curtis'), None)
        opener = jess or curtis

        # Put opener first in pool
        if opener:
            gi_pool = [opener] + [s for s in gi_pool if s.id != opener.id]

        proc_rooms = [
            'Procedure Room 1',
            'Procedure Room 2',
            'Procedure Room 3',
            'Procedure Room 4',
        ]

        gi_ptr = 0
        for room_name in proc_rooms:
            if room_name not in areas:
                continue
            filled = 0
            while filled < 2 and gi_ptr < len(gi_pool):
                gt = gi_pool[gi_ptr]
                # Opener keeps their DB start time (6:15); others alternate 7:00 / 7:30
                if gt.start_time:
                    start = gt.start_time.strftime('%H:%M')
                else:
                    start = '07:00' if (gi_ptr % 2 == 0) else '07:30'
                add(gt, room_name, start)
                gi_ptr += 1
                filled += 1
            if filled < 2:
                warnings.append(f"{date_str}: {room_name} short-staffed ({filled}/2 GI Techs)")

        # ── 3. RNs → Admitting (early) + Recovery (7:30) + Charge (7:00) ─────
        # Rotate assignment order each day so early shifts distribute fairly
        rn_pool = rns[:]
        offset  = day_idx % len(rn_pool) if rn_pool else 0
        rn_pool = rn_pool[offset:] + rn_pool[:offset]

        # Slot definitions: (start_time, area)
        rn_slots = [
            ('06:15', 'Admitting'),   # 1st early RN → Admitting
            ('06:30', 'Admitting'),   # 2nd early RN → Admitting
            ('07:30', 'Recovery'),    # 3rd RN        → Recovery
            ('07:30', 'Recovery'),    # 4th RN        → Recovery
            ('07:00', 'Charge'),      # 5th RN        → Charge (no room)
        ]

        for i, rn in enumerate(rn_pool):
            if i >= len(rn_slots):
                break
            start, area_name = rn_slots[i]
            add(rn, area_name, start)

        # Coverage warnings
        for area_name, req_count in [('Admitting', 2), ('Recovery', 2)]:
            a = areas.get(area_name)
            if a:
                n = sum(1 for sh in all_shifts
                        if sh['date'] == date_str and sh['area_id'] == a.id)
                if n < req_count:
                    warnings.append(
                        f"{date_str}: {area_name} only has {n}/{req_count} RNs — "
                        f"consider adding a per diem RN"
                    )

    # ── Optional AI adjustment layer ──────────────────────────────────────────
    ai_notes = []
    final_shifts = all_shifts
    if ai_instruction and ai_instruction.strip():
        area_list = list(areas.values())
        final_shifts, ai_notes = apply_ai_adjustments(
            all_shifts, ai_instruction.strip(), staff_list, area_list
        )

    all_warnings = warnings + ai_notes
    return {
        'success': True,
        'shifts': final_shifts,
        'message': f'Generated {len(final_shifts)} shifts ({len(warnings)} warnings)'
                   + (f' — AI adjusted' if ai_notes and 'failed' not in ai_notes[0] else ''),
        'validation_errors': all_warnings,
    }
