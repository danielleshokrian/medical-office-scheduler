"""
Weekly schedule generator for LICDH GI Lab.
- Deterministic rule-based algorithm builds the base schedule
- Optional plain-English AI adjustment layer on top (requires OPENAI_API_KEY)
"""

import os
import json
from datetime import timedelta
from db import db
from models import Staff, StaffArea, TimeOffRequest

# ── OpenAI — loaded lazily so a missing/broken install never crashes the backend ──
def _get_openai_client():
    try:
        from openai import OpenAI
        key = os.getenv("OPENAI_API_KEY")
        return OpenAI(api_key=key) if key else None
    except Exception:
        return None


# ── Low-level shift builder (module-level to avoid closure issues) ─────────────
def _make_shift(staff, area, date_str, start_str):
    h, m = int(start_str[:2]), int(start_str[3:])
    return {
        'staff_id':   staff.id,
        'area_id':    area.id,
        'date':       date_str,
        'start_time': start_str,
        'end_time':   f"{h + staff.shift_length:02d}:{m:02d}",
    }


def apply_ai_adjustments(shifts, instruction, staff_list, area_list):
    """
    Takes a deterministic schedule and applies plain-English tweaks via OpenAI.
    Returns (adjusted_shifts, note_string).
    Falls back to original shifts if anything fails.
    """
    client = _get_openai_client()
    if not client:
        return shifts, "OpenAI not configured — base schedule kept"

    staff_by_id = {s.id: s for s in staff_list}
    area_by_id  = {a.id: a for a in area_list}

    readable = [
        {
            'staff_id':   sh['staff_id'],
            'staff_name': (staff_by_id.get(sh['staff_id']) or type('', (), {'name': '?'})()).name,
            'area_id':    sh['area_id'],
            'area_name':  (area_by_id.get(sh['area_id'])  or type('', (), {'name': '?'})()).name,
            'date':       sh['date'],
            'start_time': sh['start_time'],
            'end_time':   sh['end_time'],
        }
        for sh in shifts
    ]

    roster = [
        {'id': s.id, 'name': s.name, 'role': s.role, 'shift_length': s.shift_length}
        for s in staff_list
    ]

    prompt = f"""You are adjusting a pre-built medical GI lab weekly schedule.

CURRENT SCHEDULE:
{json.dumps(readable, indent=2)}

STAFF ROSTER:
{json.dumps(roster, indent=2)}

ADJUSTMENT REQUESTED:
{instruction}

RULES YOU MUST NOT VIOLATE:
1. No staff member may appear twice on the same date
2. Scope Room must have exactly 2 people every day
3. Admitting must have exactly 2 RNs every day
4. Recovery must have exactly 2 RNs every day
5. Only use staff IDs and area IDs from the lists above

Return ONLY the complete modified schedule as a JSON array with these exact fields:
[{{"staff_id": 1, "area_id": 2, "date": "YYYY-MM-DD", "start_time": "HH:MM", "end_time": "HH:MM"}}]
No markdown fences, no explanation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Scheduling assistant. Return ONLY valid JSON array."},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.2,
            max_tokens=12000,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]).strip()
            if content.startswith("json"):
                content = content[4:].strip()

        adjusted = json.loads(content)

        # Guard: strip duplicates
        seen, deduped = set(), []
        for sh in adjusted:
            key = (sh['staff_id'], sh['date'])
            if key not in seen:
                seen.add(key)
                deduped.append(sh)

        return deduped, f"AI applied: {instruction}"

    except Exception as e:
        print(f"[scheduler] AI adjustment failed: {e}")
        return shifts, f"AI adjustment failed — base schedule kept"


def generate_weekly_schedule(week_start_date, fill_empty_only=False,
                             existing_shifts=None, ai_instruction=None,
                             active_rooms=None):
    """
    Deterministic rule-based weekly schedule for LICDH.
    Optionally applies an AI plain-English adjustment on top.
    Returns: {success, shifts, message, validation_errors}
    """
    warnings   = []
    all_shifts = []

    # ── Load ──────────────────────────────────────────────────────────────────
    staff_list  = Staff.query.filter_by(is_active=True).all()
    area_map    = {a.name: a for a in StaffArea.query.all()}
    week_end    = week_start_date + timedelta(days=4)
    weekdays    = [week_start_date + timedelta(days=i) for i in range(5)]

    if not staff_list:
        return {'success': False, 'shifts': [],
                'message': 'No active staff found. Run setup_licdh.py first.',
                'validation_errors': []}

    # ── Build blocked set: (staff_id, 'YYYY-MM-DD') ───────────────────────────
    blocked = set()

    for t in TimeOffRequest.query.filter(
        TimeOffRequest.status == 'approved',
        TimeOffRequest.start_date <= week_end,
        TimeOffRequest.end_date >= week_start_date
    ).all():
        cur = t.start_date
        while cur <= t.end_date:
            if week_start_date <= cur <= week_end:
                blocked.add((t.staff_id, cur.strftime('%Y-%m-%d')))
            cur += timedelta(days=1)

    for s in staff_list:
        if s.required_days_off:
            for day_name in json.loads(s.required_days_off):
                for d in weekdays:
                    if d.strftime('%A') == day_name:
                        blocked.add((s.id, d.strftime('%Y-%m-%d')))

    # ── Assign 1 rotating day off per week for every 4-day/week non-per-diem staff ──
    four_day = [s for s in staff_list if s.days_per_week == 4 and not s.is_per_diem]

    off_count = {d.strftime('%Y-%m-%d'): 0 for d in weekdays}
    for (_, ds) in blocked:
        if ds in off_count:
            off_count[ds] += 1

    for s in four_day:
        free = [d for d in weekdays if (s.id, d.strftime('%Y-%m-%d')) not in blocked]
        if len(free) <= 4:
            continue  # already has a blocked day this week

        if s.flexible_days_off:
            flex = json.loads(s.flexible_days_off)
            preferred = [d for d in free if d.strftime('%A') in flex]
            pool = preferred if preferred else free
        else:
            pool = free

        chosen = min(pool, key=lambda d: off_count[d.strftime('%Y-%m-%d')])
        ds = chosen.strftime('%Y-%m-%d')
        blocked.add((s.id, ds))
        off_count[ds] += 1

    # ── RN slot definitions — no Charge/Float in auto-schedule ──────────────
    RN_SLOTS = [
        ('06:15', 'Admitting'),
        ('06:30', 'Admitting'),
        ('07:30', 'Recovery'),
        ('07:30', 'Recovery'),
    ]

    ALL_PROC_ROOMS = ['Procedure Room 1', 'Procedure Room 2',
                      'Procedure Room 3', 'Procedure Room 4']

    # ── Build each day ────────────────────────────────────────────────────────
    for day_idx, day in enumerate(weekdays):
        date_str = day.strftime('%Y-%m-%d')

        today       = [s for s in staff_list if (s.id, date_str) not in blocked]
        rns         = sorted([s for s in today if s.role == 'RN'         and not s.is_per_diem], key=lambda s: s.name)
        gi_techs    = sorted([s for s in today if s.role == 'GI_Tech'],                           key=lambda s: s.name)
        scope_techs = sorted([s for s in today if s.role == 'Scope_Tech'],                        key=lambda s: s.name)

        assigned = set()

        # ── Scope Room ────────────────────────────────────────────────────────
        scope_area = area_map.get('Scope Room')
        for st in scope_techs:
            if scope_area and st.id not in assigned:
                start = st.start_time.strftime('%H:%M') if st.start_time else '07:30'
                all_shifts.append(_make_shift(st, scope_area, date_str, start))
                assigned.add(st.id)

        if len(scope_techs) < 2:
            sub = next((gt for gt in gi_techs if gt.id not in assigned), None)
            if sub and scope_area:
                all_shifts.append(_make_shift(sub, scope_area, date_str, '07:00'))
                assigned.add(sub.id)
                warnings.append(f"{date_str}: {sub.name} (GI Tech) covering Scope Room")

        # ── Which procedure rooms are open today? ─────────────────────────────
        if active_rooms and date_str in active_rooms:
            day_rooms = [r for r in ALL_PROC_ROOMS if r in active_rooms[date_str]]
        else:
            day_rooms = ALL_PROC_ROOMS

        # ── GI Techs — put exactly 1 per active room (opener slot first) ─────
        gi_pool = [s for s in gi_techs if s.id not in assigned]
        jess   = next((s for s in gi_pool if s.name == 'Jess'),   None)
        curtis = next((s for s in gi_pool if s.name == 'Curtis'), None)
        opener = jess or curtis
        if opener:
            gi_pool = [opener] + [s for s in gi_pool if s.id != opener.id]

        gi_ptr = 0
        for room_name in day_rooms:
            room = area_map.get(room_name)
            if not room or gi_ptr >= len(gi_pool):
                continue
            gt = gi_pool[gi_ptr]
            start = gt.start_time.strftime('%H:%M') if gt.start_time else (
                '06:15' if gi_ptr == 0 else ('07:00' if gi_ptr % 2 == 0 else '07:30')
            )
            if gt.id not in assigned:
                all_shifts.append(_make_shift(gt, room, date_str, start))
                assigned.add(gt.id)
            gi_ptr += 1

        # ── RNs → Admitting (2) + Recovery (2), then rotate into rooms ───────
        # Rotate RN order by day so early/late slots distribute fairly
        rn_pool = rns[:]
        if rn_pool:
            offset  = day_idx % len(rn_pool)
            rn_pool = rn_pool[offset:] + rn_pool[:offset]

        # Mandatory admitting/recovery slots
        for i, rn in enumerate(rn_pool[:4]):
            start, area_name = RN_SLOTS[i]
            area = area_map.get(area_name)
            if area and rn.id not in assigned:
                all_shifts.append(_make_shift(rn, area, date_str, start))
                assigned.add(rn.id)

        # Extra RNs (5th+) rotate into procedure rooms as 2nd person.
        # Rotate which room gets the RN each day so it varies across the week.
        extra_rns = [rn for rn in rn_pool[4:] if rn.id not in assigned]
        if extra_rns and day_rooms:
            rotated_rooms = day_rooms[day_idx % len(day_rooms):] + day_rooms[:day_idx % len(day_rooms)]
            for rn, room_name in zip(extra_rns, rotated_rooms):
                room = area_map.get(room_name)
                if room and rn.id not in assigned:
                    all_shifts.append(_make_shift(rn, room, date_str, '07:00'))
                    assigned.add(rn.id)

        # ── Fill remaining procedure room slots (2nd person) with GI techs ───
        for room_name in day_rooms:
            room = area_map.get(room_name)
            if not room:
                continue
            in_room = sum(1 for sh in all_shifts
                          if sh['date'] == date_str and sh['area_id'] == room.id)
            while in_room < 2 and gi_ptr < len(gi_pool):
                gt = gi_pool[gi_ptr]
                gi_ptr += 1
                if gt.id not in assigned:
                    start = gt.start_time.strftime('%H:%M') if gt.start_time else '07:30'
                    all_shifts.append(_make_shift(gt, room, date_str, start))
                    assigned.add(gt.id)
                    in_room += 1
            if in_room < 2:
                warnings.append(f"{date_str}: {room_name} short-staffed ({in_room}/2)")

        # Coverage checks
        for area_name, req in [('Admitting', 2), ('Recovery', 2)]:
            a = area_map.get(area_name)
            if a:
                n = sum(1 for sh in all_shifts
                        if sh['date'] == date_str and sh['area_id'] == a.id)
                if n < req:
                    warnings.append(f"{date_str}: {area_name} has {n}/{req} RNs — add per diem if needed")

    # ── Optional AI adjustment ─────────────────────────────────────────────────
    ai_note = None
    final_shifts = all_shifts
    if ai_instruction and ai_instruction.strip():
        final_shifts, ai_note = apply_ai_adjustments(
            all_shifts, ai_instruction.strip(),
            staff_list, list(area_map.values())
        )

    all_notes = warnings + ([ai_note] if ai_note else [])
    base_msg = f"Generated {len(final_shifts)} shifts"
    if warnings:
        base_msg += f" ({len(warnings)} warnings)"
    if ai_note and "failed" not in ai_note:
        base_msg += " — AI adjusted"

    return {
        'success': True,
        'shifts':  final_shifts,
        'message': base_msg,
        'validation_errors': all_notes,
    }
