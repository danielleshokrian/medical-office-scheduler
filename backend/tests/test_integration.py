import json
from datetime import date, timedelta

class TestSchedulingWorkflow:
    
    def test_complete_weekly_schedule_workflow(self, client, sample_staff, sample_areas):
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        
        week_start = next_monday.strftime('%Y-%m-%d')
        
        response = client.get('/staff')
        all_staff = json.loads(response.data)
        rn_staff = [s for s in all_staff if s['role'] == 'RN' and s['is_active']]
        
        if len(rn_staff) < 2:
            import pytest
            pytest.skip("Not enough RN staff for workflow test")
        
        staff_1_id = rn_staff[0]['id']
        staff_2_id = rn_staff[1]['id']
        
        response = client.post('/time-off', json={
            'staff_id': staff_1_id,
            'start_date': week_start,
            'end_date': (next_monday + timedelta(days=2)).strftime('%Y-%m-%d'),
            'reason': 'Vacation'
        })
        assert response.status_code == 201
        
        time_off_data = json.loads(response.data)
        response = client.put(f'/time-off/{time_off_data["id"]}', json={
            'status': 'approved'
        })
        assert response.status_code == 200
        
        response = client.post('/shifts', json={
            'staff_id': staff_2_id,  # Different staff member
            'area_id': sample_areas[0],
            'date': (next_monday + timedelta(days=3)).strftime('%Y-%m-%d'),
            'start_time': '07:00',
            'end_time': '17:00'
        })
        assert response.status_code == 201
        
        response = client.get(f'/coverage/{sample_areas[0]}/{week_start}')
        assert response.status_code == 200
        coverage = response.get_json()
        assert 'is_covered' in coverage
        
        response = client.post('/shifts', json={
            'staff_id': staff_1_id,  # Staff with time-off
            'area_id': sample_areas[0],
            'date': week_start,
            'start_time': '07:00',
            'end_time': '17:00'
        })
        assert response.status_code == 400
        
    def test_validation_prevents_conflicts(self, client, sample_staff, sample_areas):
        test_date = '2025-11-10'
        
        response = client.post('/shifts', json={
            'staff_id': sample_staff[0],
            'area_id': sample_areas[0],
            'date': test_date,
            'start_time': '07:00',
            'end_time': '17:00'
        })
        assert response.status_code == 201
        
        response = client.post('/shifts', json={
            'staff_id': sample_staff[0],  # Same staff
            'area_id': sample_areas[1],
            'date': test_date,  # Same date
            'start_time': '08:00',
            'end_time': '18:00'
        })
        assert response.status_code == 400
        error_data = json.loads(response.data)
        assert 'already scheduled' in error_data['error'].lower()
        
    def test_time_off_prevents_shift_creation(self, client, sample_staff, sample_areas):
        """Test that approved time-off prevents shift creation"""
        test_date = '2025-11-15'
        
        # 1. Create and approve time-off
        response = client.post('/time-off', json={
            'staff_id': sample_staff[0],
            'start_date': test_date,
            'end_date': test_date,
            'reason': 'Personal'
        })
        assert response.status_code == 201
        time_off_data = json.loads(response.data)
        time_off_id = time_off_data['id']
        
        print(f"\n Created time-off: {time_off_data}")
        
        response = client.put(f'/time-off/{time_off_id}', json={
            'status': 'approved'
        })
        assert response.status_code == 200
        approved_data = json.loads(response.data)
        print(f" Approved time-off: {approved_data}")
        
        response = client.get(f'/time-off/{time_off_id}')
        verified_data = json.loads(response.data)
        assert verified_data['status'] == 'approved'
        
        response = client.post('/shifts', json={
            'staff_id': sample_staff[0],
            'area_id': sample_areas[0],
            'date': test_date,
            'start_time': '07:00',
            'end_time': '17:00'
        })
        
        if response.status_code != 400:
            print(f" Expected 400, got {response.status_code}")
            print(f"Response: {json.loads(response.data)}")
        
        assert response.status_code == 400
        error_data = json.loads(response.data)
        assert 'time off' in error_data['error'].lower() or 'time-off' in error_data['error'].lower()
            
    def test_staff_deactivation_workflow(self, client, sample_staff, sample_areas):
        response = client.post('/shifts', json={
            'staff_id': sample_staff[0],
            'area_id': sample_areas[0],
            'date': '2025-11-20',
            'start_time': '07:00',
            'end_time': '17:00'
        })
        assert response.status_code == 201
        
        response = client.delete(f'/staff/{sample_staff[0]}')
        assert response.status_code == 200
        
        response = client.get(f'/staff/{sample_staff[0]}')
        assert response.status_code == 200
        staff_data = json.loads(response.data)
        assert staff_data['is_active'] == False
        
        response = client.post('/shifts', json={
            'staff_id': sample_staff[0],
            'area_id': sample_areas[0],
            'date': '2025-11-21',
            'start_time': '07:00',
            'end_time': '17:00'
        })
        
    def test_area_coverage_calculation(self, client, sample_staff, sample_areas):
        test_date = '2025-11-25'
        
        admitting_area_id = sample_areas[0]
        
        response = client.get(f'/coverage/{admitting_area_id}/{test_date}')
        assert response.status_code == 200
        coverage = json.loads(response.data)
        assert coverage['is_covered'] == False

        response = client.get('/staff')
        all_staff = json.loads(response.data)
        rn_staff = [s['id'] for s in all_staff if s['role'] == 'RN' and s['is_active']][:2]
        
        if len(rn_staff) < 2:
            import pytest
            pytest.skip("Not enough RN staff for coverage test")
        
        response = client.post('/shifts', json={
            'staff_id': rn_staff[0],
            'area_id': admitting_area_id,
            'date': test_date,
            'start_time': '06:15',
            'end_time': '16:15'
        })
        assert response.status_code == 201, f"Failed to create first shift: {response.data}"
        
        response = client.post('/shifts', json={
            'staff_id': rn_staff[1],
            'area_id': admitting_area_id,
            'date': test_date,
            'start_time': '06:30',
            'end_time': '16:30'
        })
        assert response.status_code == 201, f"Failed to create second shift: {response.data}"
        
        response = client.get(f'/coverage/{admitting_area_id}/{test_date}')
        assert response.status_code == 200
        coverage = json.loads(response.data)
        assert coverage['is_covered'] == True
