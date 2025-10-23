import json

def test_get_all_staff(client, sample_staff):
    response = client.get('/staff')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) >= 2

def test_get_staff_by_id(client, sample_staff):
    staff_id = sample_staff[0]  
    response = client.get(f'/staff/{staff_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Test RN'
    assert data['role'] == 'RN'

def test_create_staff(client):
    new_staff = {
        'name': 'New Nurse',
        'role': 'RN',
        'shift_length': 10,
        'days_per_week': 4,
        'is_per_diem': False,
        'area_restrictions': '["Any"]'
    }
    response = client.post('/staff', 
                          data=json.dumps(new_staff),
                          content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'New Nurse'

def test_update_staff(client, sample_staff):
    staff_id = sample_staff[0]  
    update_data = {'name': 'Updated RN'}
    response = client.put(f'/staff/{staff_id}',
                         data=json.dumps(update_data),
                         content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Updated RN'

def test_deactivate_staff(client, sample_staff):
    staff_id = sample_staff[0]  
    response = client.delete(f'/staff/{staff_id}')
    assert response.status_code == 200
    
    get_response = client.get(f'/staff/{staff_id}')
    data = json.loads(get_response.data)
    assert data['is_active'] == False

def test_filter_staff_by_role(client, sample_staff):
    response = client.get('/staff?role=RN')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(s['role'] == 'RN' for s in data)