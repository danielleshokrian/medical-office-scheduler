import json
from datetime import date, timedelta

def test_create_time_off_request(client, sample_staff):
    today = date.today()
    request_data = {
        'staff_id': sample_staff[0],
        'start_date': str(today),
        'end_date': str(today + timedelta(days=2)),
        'reason': 'Vacation'
    }
    response = client.post('/time-off',
                          data=json.dumps(request_data),
                          content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['status'] == 'pending'
    assert data['reason'] == 'Vacation'

def test_approve_time_off(client, sample_staff):
    today = date.today()
    request_data = {
        'staff_id': sample_staff[0],
        'start_date': str(today),
        'end_date': str(today + timedelta(days=1)),
        'reason': 'Personal'
    }
    create_response = client.post('/time-off',
                                  data=json.dumps(request_data),
                                  content_type='application/json')
    request_id = json.loads(create_response.data)['id']
    
    response = client.put(f'/time-off/{request_id}',
                         data=json.dumps({'status': 'approved'}),
                         content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'approved'

def test_deny_time_off(client, sample_staff):
    today = date.today()
    request_data = {
        'staff_id': sample_staff[0],
        'start_date': str(today),
        'end_date': str(today + timedelta(days=1))
    }
    create_response = client.post('/time-off',
                                  data=json.dumps(request_data),
                                  content_type='application/json')
    request_id = json.loads(create_response.data)['id']
    
    response = client.put(f'/time-off/{request_id}',
                         data=json.dumps({'status': 'denied'}),
                         content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'denied'