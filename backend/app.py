from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_cors import CORS, cross_origin
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from models import Staff, StaffArea, Shift, TimeOffRequest, AISuggestion, User
from db import db
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from datetime import datetime, timedelta, date
from utils import validate_shift, check_area_coverage
from ai_scheduler import generate_weekly_schedule
from sqlalchemy.orm import joinedload
from sqlalchemy import text
from config import get_config

load_dotenv()

app = Flask(__name__)

app.config.from_object(get_config())

db.init_app(app)

migrate = Migrate(app, db)

jwt = JWTManager(app)

if os.getenv('FLASK_ENV') == 'production':
    allowed_origins = app.config.get('CORS_ORIGINS', ['https://yourdomain.com'])
    CORS(app,
         resources={r"/*": {"origins": allowed_origins}},
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         supports_credentials=True)

else:
        CORS(app,
         resources={r"/*": {"origins": [
             "http://localhost:3000",
             "http://127.0.0.1:3000",
             "http://localhost",
             "http://127.0.0.1"
         ]}},
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         supports_credentials=True)

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = RotatingFileHandler(
        'logs/scheduler.log',
        maxBytes=10240000,  # 10MB
        backupCount=10

    )

    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))

    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)

    app.logger.info('Medical Office Scheduler startup')

@app.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            role=data.get('role', 'user')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    """Login and get JWT tokens"""
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['username', 'password']):
            return jsonify({'error': 'Missing username or password'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': user.role}
        )
        refresh_token = create_refresh_token(identity=str(user.id))

        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/auth/refresh', methods=['POST'])
#@jwt_required(refresh=True)
def refresh():
    """Get new access token using refresh token"""
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role}
    )
    
    return jsonify({'access_token': access_token}), 200


@app.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    try:
        current_user_id = get_jwt_identity()
        print("Authorization header:", request.headers.get("Authorization"))
        print(f"Getting user with ID: {current_user_id}")  
        
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        print(f"Error in /auth/me: {str(e)}")  
        import traceback
        traceback.print_exc()  
        return jsonify({'error': str(e)}), 500
    
@app.route('/health', methods=['GET'])

def health_check():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'service': 'medical-office-scheduler',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        app.logger.error(f'Health check failed: {str(e)}')
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/ready', methods=['GET'])
def readiness_check():
    try:
        db.session.execute(text('SELECT 1'))

        return jsonify({
            'ready': True,
            'checks': {
                'database': 'ok'
            }
        }), 200
    except Exception as e:
        return jsonify({
            'ready': False,
            'checks': {
                'database': 'failed'
            },
            'error': str(e)
        }), 503

@app.route('/')
@jwt_required()
def home():
    return "<h1>Medical Office Scheduler API</h1>", 200


# ========== STAFF ROUTES ==========

@app.route('/staff', methods=['GET'])
@jwt_required()
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
@jwt_required()
def get_staff_by_id(id):
    try:
        staff = Staff.query.get_or_404(id)
        return jsonify(staff.to_dict()), 200
    except Exception as e:
        return jsonify({'error': 'Staff member not found'}), 404


@app.route('/staff', methods=['POST'])
@jwt_required()
def create_staff():
    try:
        data = request.get_json()
        
        start_time = None
        if data.get('start_time'):
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()

        required_days_off = data.get('required_days_off')
        flexible_days_off = data.get('flexible_days_off')
        
        new_staff = Staff(
            name=data['name'],
            role=data['role'],
            shift_length=data['shift_length'],
            days_per_week=data['days_per_week'],
            start_time=start_time,
            is_per_diem=data.get('is_per_diem', False),
            area_restrictions=data.get('area_restrictions'),
            required_days_off=data.get('required_days_off'),
            flexible_days_off=data.get('flexible_days_off'),
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
def get_areas():
    try:
        areas = StaffArea.query.all()
        return jsonify([a.to_dict() for a in areas]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/areas/<int:id>', methods=['GET'])
@jwt_required()
def get_area_by_id(id):
    try:
        area = StaffArea.query.get_or_404(id)
        return jsonify(area.to_dict()), 200
    except Exception as e:
        return jsonify({'error': 'Area not found'}), 404


@app.route('/areas', methods=['POST'])
@jwt_required()
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
@jwt_required()
def get_shifts():
    try:
        date_param = request.args.get('date')
        staff_id = request.args.get('staff_id')
        area_id = request.args.get('area_id')
        
        query = Shift.query.options(
        joinedload(Shift.staff_member),
        joinedload(Shift.area)
        )
        
        if date_param:
            query_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            query = query.filter_by(date=query_date)
        if staff_id:
            query = query.filter_by(staff_id=staff_id)
        if area_id:
            query = query.filter_by(area_id=area_id)
        
        shifts = query.all()
        return jsonify([s.to_dict() for s in shifts]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/shifts', methods=['POST'])
@jwt_required()
def create_shift():
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['staff_id', 'area_id', 'date', 'start_time', 'end_time']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        staff_id = data['staff_id']
        area_id = data['area_id']
        shift_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        staff = Staff.query.get(staff_id)
        if not staff:
            return jsonify({'error': 'Staff member not found'}), 404
        
        area = StaffArea.query.get(area_id)
        if not area:
            return jsonify({'error': 'Area not found'}), 404
        
        day_of_week = shift_date.strftime('%A')  # Monday, Tuesday, etc.
        required_days_off = json.loads(staff.required_days_off) if staff.required_days_off else []
        
        if day_of_week in required_days_off:
            return jsonify({
                'error': f'Cannot schedule {staff.name} on {day_of_week} - this is a required day off'
            }), 400
        
        time_off_conflict = TimeOffRequest.query.filter(
            TimeOffRequest.staff_id == staff_id,
            TimeOffRequest.status == 'approved',
            TimeOffRequest.start_date <= shift_date,
            TimeOffRequest.end_date >= shift_date
        ).first()
        
        if time_off_conflict:
            return jsonify({
                'error': f'Cannot create shift: {staff.name} has approved time-off from {time_off_conflict.start_date} to {time_off_conflict.end_date}'
            }), 400
        
        existing_shift = Shift.query.filter(
            Shift.staff_id == staff_id,
            Shift.date == shift_date
        ).first()
        
        if existing_shift:
            return jsonify({'error': f'{staff.name} is already scheduled on {shift_date}'}), 400
        
        new_shift = Shift(
            staff_id=staff_id,
            area_id=area_id,
            date=shift_date,
            start_time=start_time,
            end_time=end_time
        )
        
        db.session.add(new_shift)
        db.session.commit()
        
        return jsonify(new_shift.to_dict()), 201
        
    except ValueError as e:
        return jsonify({'error': f'Invalid date/time format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/shifts/<int:id>', methods=['GET'])
@jwt_required()
def get_shift_by_id(id):
    try:
        shift = Shift.query.get_or_404(id)
        return jsonify(shift.to_dict()), 200
    except Exception as e:
        return jsonify({'error': 'Shift not found'}), 404


@app.route('/shifts/<int:id>', methods=['PUT'])
@jwt_required()
def update_shift(id):
    try:
        shift = Shift.query.get_or_404(id)
        data = request.get_json()
        
        staff_id = data.get('staff_id', shift.staff_id)
        area_id = data.get('area_id', shift.area_id)
        date = datetime.strptime(data['date'], '%Y-%m-%d').date() if 'date' in data else shift.date
        start_time = datetime.strptime(data['start_time'], '%H:%M').time() if 'start_time' in data else shift.start_time
        end_time = datetime.strptime(data['end_time'], '%H:%M').time() if 'end_time' in data else shift.end_time
        override_validation = data.get('override_validation', False)
        
        # VALIDATE SHIFT (unless overridden)
        if not override_validation:
            is_valid, error_message = validate_shift(staff_id, area_id, date, start_time, end_time, shift_id=id)
            
            if not is_valid:
                return jsonify({'error': error_message}), 400
        
        shift.staff_id = staff_id
        shift.area_id = area_id
        shift.date = date
        shift.start_time = start_time
        shift.end_time = end_time
        
        db.session.commit()
        return jsonify(shift.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/shifts/<int:id>', methods=['DELETE'])
@jwt_required()
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
@jwt_required()
def get_time_off_requests():
    try:
        requests = TimeOffRequest.query.options(
            joinedload(TimeOffRequest.staff_member)
        ).all()
        return jsonify([r.to_dict() for r in requests]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/time-off/<int:id>', methods=['GET'])
@jwt_required()
def get_time_off_request_by_id(id):
    request_obj = TimeOffRequest.query.options(
        joinedload(TimeOffRequest.staff_member)
    ).get_or_404(id)
    return jsonify(request_obj.to_dict()), 200


@app.route('/time-off', methods=['POST'])
@jwt_required()
def create_time_off_request():
    try:
        data = request.get_json()
        
        if 'staff_id' not in data:
            return jsonify({'error': 'staff_id is required'}), 400
        if 'start_date' not in data:
            return jsonify({'error': 'start_date is required'}), 400
        if 'end_date' not in data:
            return jsonify({'error': 'end_date is required'}), 400
        
        staff = Staff.query.get(data['staff_id'])
        if not staff:
            return jsonify({'error': 'Staff member not found'}), 404
        
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        today = date.today()
        
        if end_date < start_date:
            return jsonify({'error': 'End date must be on or after start date'}), 400
        
        if start_date < today:
            return jsonify({'error': 'Cannot request time off for past dates'}), 400
        
        duration = (end_date - start_date).days + 1
        if duration > 30:
            return jsonify({'error': 'Time-off requests cannot exceed 30 days'}), 400
        
        overlapping = TimeOffRequest.query.filter(
            TimeOffRequest.staff_id == data['staff_id'],
            TimeOffRequest.status.in_(['pending', 'approved']),
            TimeOffRequest.start_date <= end_date,
            TimeOffRequest.end_date >= start_date
        ).first()
        
        if overlapping:
            return jsonify({'error': 'Overlapping time-off request already exists'}), 400
        
        new_request = TimeOffRequest(
            staff_id=data['staff_id'],
            start_date=start_date,
            end_date=end_date,
            reason=data.get('reason', ''),
            status='pending'
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        return jsonify(new_request.to_dict()), 201
        
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/time-off/<int:id>', methods=['PUT'])
@jwt_required()
def update_time_off_request(id):
    try:
        request_obj = TimeOffRequest.query.get_or_404(id)
        data = request.get_json()
        
        if 'status' in data:
            valid_statuses = ['pending', 'approved', 'denied']
            if data['status'] not in valid_statuses:
                return jsonify({'error': f'Status must be one of: {", ".join(valid_statuses)}'}), 400
        
            request_obj.status = data['status']

        if 'reason' in data:
            request_obj.reason = data['reason']
        
        db.session.commit()
        return jsonify(request_obj.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/time-off/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_time_off_request(id):
    try:
        request_obj = TimeOffRequest.query.get_or_404(id)
        db.session.delete(request_obj)
        db.session.commit()
        return jsonify({'message': 'Time-off request deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@app.route('/coverage/<int:area_id>/<string:date>', methods=['GET'])
@jwt_required()
def get_area_coverage(area_id, date):
    try:
        coverage_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        shifts = Shift.query.options(
            joinedload(Shift.staff_member)
        ).filter(
            Shift.area_id == area_id,
            Shift.date == coverage_date
        ).all()
        
        area = StaffArea.query.get_or_404(area_id)
        
        is_covered, warnings = check_area_coverage(area_id, coverage_date)
        
        return jsonify({
            'area_id': area_id,
            'area_name': area.name,
            'date': date,
            'is_covered': is_covered,
            'warnings': warnings,
            'shifts': [s.to_dict() for s in shifts]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/ai/generate-schedule', methods=['POST', 'OPTIONS'])
@jwt_required()
def ai_generate_schedule():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json()
        week_start = datetime.strptime(data['week_start_date'], '%Y-%m-%d').date()
        fill_empty_only = data.get('fill_empty_only', False)
        
        existing_shifts = None
        if fill_empty_only:
            week_end = week_start + timedelta(days=4)
            existing_shifts = Shift.query.filter(
                Shift.date >= week_start,
                Shift.date <= week_end
            ).all()
        
        result = generate_weekly_schedule(week_start, fill_empty_only, existing_shifts)
        
        if not result['success']:
            return jsonify({'error': result['message']}), 500
        
        suggestion = AISuggestion(
            week_start_date=week_start,
            suggested_schedule=json.dumps(result['shifts']),
            reasoning='AI-generated schedule',
            constraints_met='All constraints evaluated',
            accepted=False
        )
        db.session.add(suggestion)
        db.session.commit()
        
        return jsonify({
            'suggestion_id': suggestion.id,
            'shifts': result['shifts'],
            'message': result['message']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ai/apply-schedule', methods=['POST', 'OPTIONS'])
@jwt_required()
def apply_ai_schedule():
    """Apply AI suggestions by creating actual shifts"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        shifts_data = data['shifts']
        clear_existing = data.get('clear_existing', False)
        week_start = datetime.strptime(data['week_start_date'], '%Y-%m-%d').date()
        
        if clear_existing:
            week_end = week_start + timedelta(days=4)
            Shift.query.filter(
                Shift.date >= week_start,
                Shift.date <= week_end
            ).delete()
        
        created_shifts = []
        for shift_data in shifts_data:
            new_shift = Shift(
                staff_id=shift_data['staff_id'],
                area_id=shift_data['area_id'],
                date=datetime.strptime(shift_data['date'], '%Y-%m-%d').date(),
                start_time=datetime.strptime(shift_data['start_time'], '%H:%M').time(),
                end_time=datetime.strptime(shift_data['end_time'], '%H:%M').time()
            )
            db.session.add(new_shift)
            created_shifts.append(new_shift)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully created {len(created_shifts)} shifts',
            'shifts': [s.to_dict() for s in created_shifts]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error applying schedule: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5001, debug=True)

