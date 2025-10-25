from db import db
from sqlalchemy.orm import validates
from datetime import datetime, time

class Staff(db.Model):
    __tablename__ = 'staff'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'RN', 'GI_Tech', 'Scope_Tech'
    shift_length = db.Column(db.Integer, nullable=False)  # 8 or 10 hours
    days_per_week = db.Column(db.Integer, nullable=False)  # 4 or 5 days
    start_time = db.Column(db.Time, nullable=True)
    is_per_diem = db.Column(db.Boolean, default=False)
    area_restrictions = db.Column(db.String(200), nullable=True)
    required_days_off = db.Column(db.String(100), nullable=True)
    flexible_days_off = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    shifts = db.relationship('Shift', back_populates='staff_member', cascade='all, delete-orphan')
    time_off_requests = db.relationship('TimeOffRequest', back_populates='staff_member', cascade='all, delete-orphan')
    
    @validates('name')
    def validate_name(self, key, value):
        if not value or not value.strip():
            raise ValueError("Name cannot be empty")
        return value
    
    @validates('role')
    def validate_role(self, key, value):
        valid_roles = ['RN', 'GI_Tech', 'Scope_Tech']
        if value not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return value
    
    @validates('shift_length')
    def validate_shift_length(self, key, value):
        if value not in [8, 10]:
            raise ValueError("Shift length must be 8 or 10 hours")
        return value
    
    @validates('days_per_week')
    def validate_days_per_week(self, key, value):
        if value not in [4, 5]:
            raise ValueError("Days per week must be 4 or 5")
        return value
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'shift_length': self.shift_length,
            'days_per_week': self.days_per_week,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'is_per_diem': self.is_per_diem,
            'area_restrictions': self.area_restrictions,
            'required_days_off': self.required_days_off,
            'flexible_days_off': self.flexible_days_off,
            'is_active': self.is_active
        }


class StaffArea(db.Model):
    __tablename__ = 'staff_area'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    required_rn_count = db.Column(db.Integer, default=0)
    required_tech_count = db.Column(db.Integer, default=0)
    required_scope_tech_count = db.Column(db.Integer, default=0)
    special_rules = db.Column(db.Text, nullable=True)
    
    shifts = db.relationship('Shift', back_populates='area', cascade='all, delete-orphan')
    
    @validates('name')
    def validate_name(self, key, value):
        if not value or not value.strip():
            raise ValueError("Area name cannot be empty")
        return value
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'required_rn_count': self.required_rn_count,
            'required_tech_count': self.required_tech_count,
            'required_scope_tech_count': self.required_scope_tech_count,
            'special_rules': self.special_rules
        }


class Shift(db.Model):
    __tablename__ = 'shift'
    
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('staff_area.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    staff_member = db.relationship('Staff', back_populates='shifts')
    area = db.relationship('StaffArea', back_populates='shifts')
    
    __table_args__ = (
        db.Index('idx_shift_date_staff', 'date', 'staff_id'),  
        db.Index('idx_shift_date_area', 'date', 'area_id'),   
    )

    @validates('date')
    def validate_date(self, key, value):
        from datetime import date
        if not isinstance(value, date):
            raise ValueError("date must be a datetime.date object")
        return value
    
    def to_dict(self):
        return {
            'id': self.id,
            'staff_id': self.staff_id,
            'staff_name': self.staff_member.name if self.staff_member else None,
            'staff_role': self.staff_member.role if self.staff_member else None,
            'area_id': self.area_id,
            'area_name': self.area.name if self.area else None,
            'date': self.date.strftime('%Y-%m-%d'),
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M')
        }


class TimeOffRequest(db.Model):
    __tablename__ = 'time_off_request'
    
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    reason = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='pending', index=True)  # 'pending', 'approved', 'denied'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    staff_member = db.relationship('Staff', back_populates='time_off_requests')
    
    @validates('status')
    def validate_status(self, key, value):
        valid_statuses = ['pending', 'approved', 'denied']
        if value not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value
    
    def to_dict(self):
        return {
            'id': self.id,
            'staff_id': self.staff_id,
            'staff_name': self.staff_member.name if self.staff_member else None,
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'reason': self.reason,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }


class AISuggestion(db.Model):
    __tablename__ = 'ai_suggestion'
    
    id = db.Column(db.Integer, primary_key=True)
    week_start_date = db.Column(db.Date, nullable=False)
    suggested_schedule = db.Column(db.Text, nullable=False)
    reasoning = db.Column(db.Text, nullable=True)
    constraints_met = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'week_start_date': self.week_start_date.strftime('%Y-%m-%d'),
            'suggested_schedule': self.suggested_schedule,
            'reasoning': self.reasoning,
            'constraints_met': self.constraints_met,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'accepted': self.accepted
        }