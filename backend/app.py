from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from models import Staff, StaffArea, Shift, TimeOffRequest, AISuggestion
from db import db
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/medical_scheduler')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

db.init_app(app)
migrate = Migrate(app, db)
CORS(app)


@app.route('/')
def home():
    return "<h1>Medical Office Scheduler API</h1>", 200


# ========== STAFF ROUTES ==========

@app.route('/staff', methods=['GET'])
def get_staff():
    try:
        role = request.args.get('role')
        active_only = request.args.get('active', 'true').lower() == 'true'
        
        query = Staff.query
        if active_only:
            query = query.filter_by(is_active=True)
        if role:
            query = query.filter_by(role=role)
        
        staff_list = query.all()
        return jsonify([s.to_dict() for s in staff_list]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/staff/<int:id>', methods=['GET'])
def get_staff_by_id(id):
    try:
        staff = Staff.query.get_or_404(id)
        return jsonify(staff.to_dict()), 200
    except Exception as e:
        return jsonify({'error': 'Staff member not found'}), 404


@app.route('/staff', methods=['POST'])
def create_staff():
    try:
        data = request.get_json()
        
        start_time = None
        if data.get('start_time'):
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        
        new_staff = Staff(
            name=data['name'],
            role=data['role'],
            shift_length=data['shift_length'],
            days_per_week=data['days_per_week'],
            start_time=start_time,
            is_per_diem=data.get('is_per_diem', False),
            area_restrictions=data.get('area_restrictions'),
            required_day_off=data.get('required_day_off'),
            is_active=data.get('is_active', True)
        )
        db.session.add(new_staff)
        db.session.commit()
        return jsonify(new_staff.to_dict()), 201
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except KeyError as ke:
        return jsonify({'error': f'Missing required field: {str(ke)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/staff/<int:id>', methods=['PUT'])
def update_staff(id):
    try:
        staff = Staff.query.get_or_404(id)
        data = request.get_json()
        
        if 'start_time' in data and data['start_time']:
            data['start_time'] = datetime.strptime(data['start_time'], '%H:%M').time()
        
        for key, value in data.items():
            if hasattr(staff, key):
                setattr(staff, key, value)
        
        db.session.commit()
        return jsonify(staff.to_dict()), 200
    except ValueError as ve:
        db.session.rollback()
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/staff/<int:id>', methods=['DELETE'])
def delete_staff(id):
    try:
        staff = Staff.query.get_or_404(id)
        staff.is_active = False
        db.session.commit()
        return jsonify({'message': f'Staff member {staff.name} deactivated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/staff/<int:id>/schedule', methods=['GET'])
def get_staff_schedule(id):
    try:
        staff = Staff.query.get_or_404(id)
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        shifts = staff.shifts
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            shifts = [s for s in shifts if s.date >= start]
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            shifts = [s for s in shifts if s.date <= end]
        
        return jsonify({
            'staff': staff.to_dict(),
            'shifts': [s.to_dict() for s in shifts]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== STAFF AREA ROUTES ==========

@app.route('/areas', methods=['GET'])
def get_areas():
    try:
        areas = StaffArea.query.all()
        return jsonify([a.to_dict() for a in areas]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/areas/<int:id>', methods=['GET'])
def get_area_by_id(id):
    try:
        area = StaffArea.query.get_or_404(id)
        return jsonify(area.to_dict()), 200
    except Exception as e:
        return jsonify({'error': 'Area not found'}), 404


@app.route('/areas', methods=['POST'])
def create_area():
    try:
        data = request.get_json()
        new_area = StaffArea(
            name=data['name'],
            required_rn_count=data.get('required_rn_count', 0),
            required_tech_count=data.get('required_tech_count', 0),
            required_scope_tech_count=data.get('required_scope_tech_count', 0),
            special_rules=data.get('special_rules')
        )
        db.session.add(new_area)
        db.session.commit()
        return jsonify(new_area.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ========== SHIFT ROUTES ==========

@app.route('/shifts', methods=['GET'])
def get_shifts():
    try:
        date = request.args.get('date')
        staff_id = request.args.get('staff_id')
        area_id = request.args.get('area_id')
        
        query = Shift.query
        
        if date:
            query_date = datetime.strptime(date, '%Y-%m-%d').date()
            query = query.filter_by(date=query_date)
        if staff_id:
            query = query.filter_by(staff_id=staff_id)
        if area_id:
            query = query.filter_by(area_id=area_id)
        
        shifts = query.all()
        return jsonify([s.to_dict() for s in shifts]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/shifts/<int:id>', methods=['GET'])
def get_shift_by_id(id):
    try:
        shift = Shift.query.get_or_404(id)
        return jsonify(shift.to_dict()), 200
    except Exception as e:
        return jsonify({'error': 'Shift not found'}), 404


@app.route('/shifts', methods=['POST'])
def create_shift():
    try:
        data = request.get_json()
        
        new_shift = Shift(
            staff_id=data['staff_id'],
            area_id=data['area_id'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
            end_time=datetime.strptime(data['end_time'], '%H:%M').time()
        )
        db.session.add(new_shift)
        db.session.commit()
        return jsonify(new_shift.to_dict()), 201
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except KeyError as ke:
        return jsonify({'error': f'Missing required field: {str(ke)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/shifts/<int:id>', methods=['PUT'])
def update_shift(id):
    try:
        shift = Shift.query.get_or_404(id)
        data = request.get_json()
        
        if 'staff_id' in data:
            shift.staff_id = data['staff_id']
        if 'area_id' in data:
            shift.area_id = data['area_id']
        if 'date' in data:
            shift.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'start_time' in data:
            shift.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        if 'end_time' in data:
            shift.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        db.session.commit()
        return jsonify(shift.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/shifts/<int:id>', methods=['DELETE'])
def delete_shift(id):
    try:
        shift = Shift.query.get_or_404(id)
        db.session.delete(shift)
        db.session.commit()
        return jsonify({'message': 'Shift deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ========== TIME OFF REQUEST ROUTES ==========

@app.route('/time-off', methods=['GET'])
def get_time_off_requests():
    try:
        status = request.args.get('status')
        staff_id = request.args.get('staff_id')
        
        query = TimeOffRequest.query
        
        if status:
            query = query.filter_by(status=status)
        if staff_id:
            query = query.filter_by(staff_id=staff_id)
        
        requests = query.all()
        return jsonify([r.to_dict() for r in requests]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/time-off/<int:id>', methods=['GET'])
def get_time_off_request_by_id(id):
    try:
        request_obj = TimeOffRequest.query.get_or_404(id)
        return jsonify(request_obj.to_dict()), 200
    except Exception as e:
        return jsonify({'error': 'Time-off request not found'}), 404


@app.route('/time-off', methods=['POST'])
def create_time_off_request():
    try:
        data = request.get_json()
        
        new_request = TimeOffRequest(
            staff_id=data['staff_id'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
            reason=data.get('reason'),
            status='pending'
        )
        db.session.add(new_request)
        db.session.commit()
        return jsonify(new_request.to_dict()), 201
    except KeyError as ke:
        return jsonify({'error': f'Missing required field: {str(ke)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/time-off/<int:id>', methods=['PUT'])
def update_time_off_request(id):
    try:
        request_obj = TimeOffRequest.query.get_or_404(id)
        data = request.get_json()
        
        if 'status' in data:
            request_obj.status = data['status']
        if 'reason' in data:
            request_obj.reason = data['reason']
        
        db.session.commit()
        return jsonify(request_obj.to_dict()), 200
    except ValueError as ve:
        db.session.rollback()
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/time-off/<int:id>', methods=['DELETE'])
def delete_time_off_request(id):
    try:
        request_obj = TimeOffRequest.query.get_or_404(id)
        db.session.delete(request_obj)
        db.session.commit()
        return jsonify({'message': 'Time-off request deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)