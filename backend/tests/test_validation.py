import json
from datetime import date

def test_double_booking_prevention(client, sample_staff, sample_areas):
    shift1 = {
        'staff_id': sample_staff[0],
        'area_id': sample_areas[0],
        'date': '2025-10-27',
        'start_time': '07:00',
        'end_time': '17:00'
    }
    
    response1 = client.post('/shifts',
                           data=json.dumps(shift1),
                           content_type='application/json')
    assert response1.status_code == 201
    
    shift2 = {
        'staff_id': sample_staff[0],
        'area_id': sample_areas[1],
        'date': '2025-10-27',
        'start_time': '08:00',
        'end_time': '18:00'
    }
    response2 = client.post('/shifts',
                           data=json.dumps(shift2),
                           content_type='application/json')
    assert response2.status_code == 400
    data = json.loads(response2.data)
    assert 'already scheduled' in data['error'].lower()

def test_required_day_off(client, sample_staff, sample_areas):
    staff_id = sample_staff[0]
    update_data = {'required_days_off': '["Wednesday"]'}
    client.put(f'/staff/{staff_id}',
               data=json.dumps(update_data),
               content_type='application/json')
    
    shift = {
        'staff_id': staff_id,
        'area_id': sample_areas[0],
        'date': '2025-10-29',  
        'start_time': '07:00',
        'end_time': '17:00'
    }
    response = client.post('/shifts',
                          data=json.dumps(shift),
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'wednesday' in data['error'].lower()