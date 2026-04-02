from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_cors import CORS, cross_origin
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from flask_mail import Mail, Message
from models import Staff, StaffArea, Shift, TimeOffRequest, AISuggestion, User, Clinic
from db import db
import os
import json
import logging
import secrets
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
mail = Mail(app)

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://127.0.0.1"
]

cors_origins_env = os.getenv('CORS_ORIGINS', '')
if cors_origins_env:
    custom_origins = [origin.strip() for origin in cors_origins_env.split(',')]
    allowed_origins.extend(custom_origins)

CORS(app,
     resources={r"/*": {"origins": allowed_origins}},
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = RotatingFileHandler(
        'logs/scheduler.log',
        maxBytes=10240000,
        backupCount=10
    )

    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))

    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Medical Office Scheduler startup')


def get_authenticated_user():
    current_user_id = get_jwt_identity()
    if current_user_id is None:
        return None
    return User.query.get(int(current_user_id))


def require_roles(*allowed_roles):
    user = get_authenticated_user()
    if not user:
        return None, jsonify({'error': 'User not found'}), 404
    if user.role not in allowed_roles:
        return None, jsonify({'error': 'Forbidden'}), 403
    return user, None, None


def get_current_clinic_id():
    """Read clinic_id from the JWT claims (no DB query needed)."""
    claims = get_jwt()
    return claims.get('clinic_id')


@app.route('/auth/register', methods=['POST'])
def register():
    """Register a new nurse account using the clinic invite code"""
    try:
        data = request.get_json()

        required = ['name', 'email', 'password', 'invite_code']
        if not all(k in data for k in required):
            return jsonify({'error': 'name, email, password, and invite_code are required'}), 400

        clinic = Clinic.query.filter_by(invite_code=data['invite_code'].strip()).first()
        if not clinic:
            return jsonify({'error': 'Invalid invite code. Please contact your nurse administrator.'}), 403

        if len(data['password']) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400

        email = data['email'].strip().lower()

        if User.query.filter_by(clinic_id=clinic.id, email=email).first():
            return jsonify({'error': 'An account with this email already exists'}), 400

        base = data['name'].strip().lower().replace(' ', '.')
        username = base
        counter = 1
        while User.query.filter_by(clinic_id=clinic.id, username=username).first():
            username = f"{base}{counter}"
            counter += 1

        first_name = data['name'].strip().split()[0]
        matched_staff = Staff.query.filter(
            Staff.clinic_id == clinic.id,
            db.func.lower(Staff.name).like(db.func.lower(first_name) + '%')
        ).first()

        user = User(
            username=username,
            email=email,
            role='nurse',
            clinic_id=clinic.id,
            staff_id=matched_staff.id if matched_staff else None
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        return jsonify({'message': 'Account created successfully. You can now log in.'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    """Login with email and password"""
    try:
        data = request.get_json()

        if not all(k in data for k in ['email', 'password']):
            return jsonify({'error': 'Email and password are required'}), 400

        email = data['email'].strip().lower()
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': user.role, 'clinic_id': user.clinic_id}
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


@app.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Send a password reset email"""
    try:
        data = request.get_json()
        email = (data.get('email') or '').strip().lower()
        if not email:
            return jsonify({'error': 'Email is required'}), 400

        user = User.query.filter_by(email=email).first()

        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            frontend_url = app.config.get('FRONTEND_URL', 'http://localhost:3000')
            reset_link = f"{frontend_url}/reset-password?token={token}"

            try:
                msg = Message(
                    subject='Password Reset — Medical Office Scheduler',
                    recipients=[user.email]
                )
                msg.body = (
                    f"Hi {user.username},\n\n"
                    f"You requested a password reset. Click the link below to set a new password.\n"
                    f"This link expires in 1 hour.\n\n"
                    f"{reset_link}\n\n"
                    f"If you did not request this, you can ignore this email.\n"
                )
                mail.send(msg)
            except Exception as mail_err:
                app.logger.error(f"Failed to send reset email: {mail_err}")

        return jsonify({'message': 'If that email is registered, a reset link has been sent.'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password using a valid token"""
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        new_password = data.get('password', '')

        if not token or not new_password:
            return jsonify({'error': 'Token and new password are required'}), 400

        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400

        user = User.query.filter_by(reset_token=token).first()

        if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
            return jsonify({'error': 'Reset link is invalid or has expired'}), 400

        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        return jsonify({'message': 'Password updated successfully. You can now log in.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/auth/refresh', methods=['POST'])
def refresh():
    """Get new access token using refresh token"""
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))

    if not user:
        return jsonify({'error': 'User not found'}), 404

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role, 'clinic_id': user.clinic_id}
    )

    return jsonify({'access_token': access_token}), 200


@app.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    """Get current user info"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify(user.to_dict()), 200

    except Exception as e:
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
            'checks': {'database': 'ok'}
        }), 200
    except Exception as e:
        return jsonify({
            'ready': False,
            'checks': {'database': 'failed'},
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
        clinic_id = get_current_clinic_id()
        role = request.args.get('role')
        active_only = request.args.get('active', 'true').lower() == 'true'

        query = Staff.query.filter_by(clinic_id=clinic_id)
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
        clinic_id = get_current_clinic_id()
        staff = Staff.query.filter_by(id=id, clinic_id=clinic_id).first_or_404()
        return jsonify(staff.to_dict()), 200
    except Exception as e:
        return jsonify({'error': 'Staff member not found'}), 404


@app.route('/staff', methods=['POST'])
@jwt_required()
def create_staff():
    try:
        user, error_response, status = require_roles('nurse_admin')
        if error_response:
            return error_response, status

        data = request.get_json()

        start_time = None
        if data.get('start_time'):
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()

        new_staff = Staff(
            clinic_id=user.clinic_id,
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
        user, error_response, status = require_roles('nurse_admin')
        if error_response:
            return error_response, status

        staff = Staff.query.filter_by(id=id, clinic_id=user.clinic_id).first_or_404()
        data = request.get_json()

        if 'start_time' in data and data['start_time']:
            data['start_time'] = datetime.strptime(data['start_time'], '%H:%M').time()

        for key, value in data.items():
            if hasattr(staff, key) and key not in ('id', 'clinic_id'):
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
        user, error_response, status = require_roles('nurse_admin')
        if error_response:
            return error_response, status

        staff = Staff.query.filter_by(id=id, clinic_id=user.clinic_id).first_or_404()
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
        current_user, error_response, status = require_roles('nurse_admin', 'nurse')
        if error_response:
            return error_response, status

        if current_user.role == 'nurse' and current_user.staff_id != id:
            return jsonify({'error': 'Nurses can only view their own schedule'}), 403

        staff = Staff.query.filter_by(id=id, clinic_id=current_user.clinic_id).first_or_404()

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
        clinic_id = get_current_clinic_id()
        areas = StaffArea.query.filter_by(clinic_id=clinic_id).all()
        return jsonify([a.to_dict() for a in areas]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/areas/<int:id>', methods=['GET'])
@jwt_required()
def get_area_by_id(id):
    try:
        clinic_id = get_current_clinic_id()
        area = StaffArea.query.filter_by(id=id, clinic_id=clinic_id).first_or_404()
        return jsonify(area.to_dict()), 200
    except Exception as e:
        return jsonify({'error': 'Area not found'}), 404


@app.route('/areas', methods=['POST'])
@jwt_required()
def create_area():
    try:
        user, error_response, status = require_roles('nurse_admin')
        if error_response:
            return error_response, status

        data = request.get_json()
        new_area = StaffArea(
            clinic_id=user.clinic_id,
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
        clinic_id = get_current_clinic_id()
        date_param = request.args.get('date')
        staff_id = request.args.get('staff_id')
        area_id = request.args.get('area_id')

        query = Shift.query.options(
            joinedload(Shift.staff_member),
            joinedload(Shift.area)
        ).filter(Shift.clinic_id == clinic_id)

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
        user, error_response, status = require_roles('nurse_admin')
        if error_response:
            return error_response, status

        clinic_id = user.clinic_id
        data = request.get_json()

        if not all(k in data for k in ['staff_id', 'area_id', 'date', 'start_time', 'end_time']):
            return jsonify({'error': 'Missing required fields'}), 400

        staff_id = data['staff_id']
        area_id = data['area_id']
        shift_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()

        staff = Staff.query.filter_by(id=staff_id, clinic_id=clinic_id).first()
        if not staff:
            return jsonify({'error': 'Staff member not found'}), 404

        area = StaffArea.query.filter_by(id=area_id, clinic_id=clinic_id).first()
        if not area:
            return jsonify({'error': 'Area not found'}), 404

        day_of_week = shift_date.strftime('%A')
        required_days_off = json.loads(staff.required_days_off) if staff.required_days_off else []

        if day_of_week in required_days_off:
            return jsonify({
                'error': f'Cannot schedule {staff.name} on {day_of_week} - this is a required day off'
            }), 400

        time_off_conflict = TimeOffRequest.query.filter(
            TimeOffRequest.staff_id == staff_id,
            TimeOffRequest.clinic_id == clinic_id,
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
            Shift.date == shift_date,
            Shift.clinic_id == clinic_id
        ).first()

        if existing_shift:
            return jsonify({'error': f'{staff.name} is already scheduled on {shift_date}'}), 400

        new_shift = Shift(
            clinic_id=clinic_id,
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
        clinic_id = get_current_clinic_id()
        shift = Shift.query.filter_by(id=id, clinic_id=clinic_id).first_or_404()
        return jsonify(shift.to_dict()), 200
    except Exception as e:
        return jsonify({'error': 'Shift not found'}), 404


@app.route('/shifts/<int:id>', methods=['PUT'])
@jwt_required()
def update_shift(id):
    try:
        user, error_response, status = require_roles('nurse_admin')
        if error_response:
            return error_response, status

        shift = Shift.query.filter_by(id=id, clinic_id=user.clinic_id).first_or_404()
        data = request.get_json()

        staff_id = data.get('staff_id', shift.staff_id)
        area_id = data.get('area_id', shift.area_id)
        shift_date = datetime.strptime(data['date'], '%Y-%m-%d').date() if 'date' in data else shift.date
        start_time = datetime.strptime(data['start_time'], '%H:%M').time() if 'start_time' in data else shift.start_time
        end_time = datetime.strptime(data['end_time'], '%H:%M').time() if 'end_time' in data else shift.end_time
        override_validation = data.get('override_validation', False)

        if not override_validation:
            is_valid, error_message = validate_shift(staff_id, area_id, shift_date, start_time, end_time, shift_id=id)
            if not is_valid:
                return jsonify({'error': error_message}), 400

        shift.staff_id = staff_id
        shift.area_id = area_id
        shift.date = shift_date
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
        user, error_response, status = require_roles('nurse_admin')
        if error_response:
            return error_response, status

        shift = Shift.query.filter_by(id=id, clinic_id=user.clinic_id).first_or_404()
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
        current_user, error_response, status = require_roles('nurse_admin', 'nurse')
        if error_response:
            return error_response, status

        query = TimeOffRequest.query.options(
            joinedload(TimeOffRequest.staff_member)
        ).filter(TimeOffRequest.clinic_id == current_user.clinic_id)

        if current_user.role == 'nurse':
            query = query.filter(TimeOffRequest.staff_id == current_user.staff_id)

        requests = query.all()
        return jsonify([r.to_dict() for r in requests]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/time-off/<int:id>', methods=['GET'])
@jwt_required()
def get_time_off_request_by_id(id):
    current_user, error_response, status = require_roles('nurse_admin', 'nurse')
    if error_response:
        return error_response, status

    request_obj = TimeOffRequest.query.options(
        joinedload(TimeOffRequest.staff_member)
    ).filter_by(id=id, clinic_id=current_user.clinic_id).first_or_404()

    if current_user.role == 'nurse' and request_obj.staff_id != current_user.staff_id:
        return jsonify({'error': 'Forbidden'}), 403

    return jsonify(request_obj.to_dict()), 200


@app.route('/time-off', methods=['POST'])
@jwt_required()
def create_time_off_request():
    try:
        current_user, error_response, status = require_roles('nurse_admin', 'nurse')
        if error_response:
            return error_response, status

        clinic_id = current_user.clinic_id
        data = request.get_json()

        if current_user.role == 'nurse':
            if not current_user.staff_id:
                return jsonify({'error': 'Nurse account is not linked to a staff member'}), 400
            data['staff_id'] = current_user.staff_id

        if 'staff_id' not in data or data['staff_id'] == '' or data['staff_id'] is None:
            return jsonify({'error': 'staff_id is required'}), 400

        try:
            staff_id = int(data['staff_id'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid staff_id'}), 400

        if 'start_date' not in data:
            return jsonify({'error': 'start_date is required'}), 400
        if 'end_date' not in data:
            return jsonify({'error': 'end_date is required'}), 400

        staff = Staff.query.filter_by(id=staff_id, clinic_id=clinic_id).first()
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

        request_type = data.get('request_type', 'pto')
        if request_type not in ('pto', 'day_off'):
            return jsonify({'error': 'request_type must be pto or day_off'}), 400

        if request_type == 'day_off' and start_date != end_date:
            return jsonify({'error': 'Scheduled day off must be a single day'}), 400

        overlapping = TimeOffRequest.query.filter(
            TimeOffRequest.staff_id == staff_id,
            TimeOffRequest.clinic_id == clinic_id,
            TimeOffRequest.request_type == request_type,
            TimeOffRequest.status.in_(['pending', 'approved']),
            TimeOffRequest.start_date <= end_date,
            TimeOffRequest.end_date >= start_date
        ).first()

        if overlapping:
            label = 'scheduled day off' if request_type == 'day_off' else 'time-off request'
            return jsonify({'error': f'An overlapping {label} already exists for that date'}), 400

        # Admins auto-approve; nurses submit as pending
        initial_status = 'approved' if current_user.role == 'nurse_admin' else 'pending'

        new_request = TimeOffRequest(
            clinic_id=clinic_id,
            staff_id=staff_id,
            start_date=start_date,
            end_date=end_date,
            reason=data.get('reason', ''),
            status=initial_status,
            request_type=request_type
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
        user, error_response, status = require_roles('nurse_admin')
        if error_response:
            return error_response, status

        request_obj = TimeOffRequest.query.filter_by(id=id, clinic_id=user.clinic_id).first_or_404()
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
        current_user, error_response, status = require_roles('nurse_admin', 'nurse')
        if error_response:
            return error_response, status

        request_obj = TimeOffRequest.query.filter_by(
            id=id, clinic_id=current_user.clinic_id
        ).first_or_404()

        if current_user.role == 'nurse':
            if request_obj.staff_id != current_user.staff_id:
                return jsonify({'error': 'Forbidden'}), 403
            if request_obj.status != 'pending':
                return jsonify({'error': 'Only pending requests can be deleted'}), 400

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
        clinic_id = get_current_clinic_id()
        coverage_date = datetime.strptime(date, '%Y-%m-%d').date()

        area = StaffArea.query.filter_by(id=area_id, clinic_id=clinic_id).first_or_404()

        shifts = Shift.query.options(
            joinedload(Shift.staff_member)
        ).filter(
            Shift.area_id == area_id,
            Shift.clinic_id == clinic_id,
            Shift.date == coverage_date
        ).all()

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
        user, error_response, status = require_roles('nurse_admin')
        if error_response:
            return error_response, status

        clinic_id = user.clinic_id
        data = request.get_json()
        week_start = datetime.strptime(data['week_start_date'], '%Y-%m-%d').date()
        fill_empty_only = data.get('fill_empty_only', False)
        ai_instruction = (data.get('ai_instruction') or '').strip()
        active_rooms = data.get('active_rooms') or None

        existing_shifts = None
        if fill_empty_only:
            week_end = week_start + timedelta(days=4)
            existing_shifts = Shift.query.filter(
                Shift.clinic_id == clinic_id,
                Shift.date >= week_start,
                Shift.date <= week_end
            ).all()

        result = generate_weekly_schedule(
            week_start, fill_empty_only, existing_shifts,
            ai_instruction=ai_instruction or None,
            active_rooms=active_rooms,
            clinic_id=clinic_id
        )

        if not result['success']:
            return jsonify({'error': result['message']}), 500

        suggestion = AISuggestion(
            clinic_id=clinic_id,
            week_start_date=week_start,
            suggested_schedule=json.dumps(result['shifts']),
            reasoning='Generated schedule',
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
    """Apply generated schedule by creating actual shifts"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        user, error_response, status = require_roles('nurse_admin')
        if error_response:
            return error_response, status

        clinic_id = user.clinic_id
        data = request.get_json()
        shifts_data = data['shifts']
        clear_existing = data.get('clear_existing', False)
        week_start = datetime.strptime(data['week_start_date'], '%Y-%m-%d').date()

        if clear_existing:
            week_end = week_start + timedelta(days=4)
            Shift.query.filter(
                Shift.clinic_id == clinic_id,
                Shift.date >= week_start,
                Shift.date <= week_end
            ).delete()

        created_shifts = []
        for shift_data in shifts_data:
            new_shift = Shift(
                clinic_id=clinic_id,
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
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5001, debug=True)
