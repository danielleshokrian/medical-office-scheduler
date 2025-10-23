import pytest
import os
import sys
from app import app as flask_app
from db import db
from models import Staff, StaffArea, Shift, TimeOffRequest
from datetime import datetime, date, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture
def app():
    """Create application for testing"""
    from app import app as flask_app
    from db import db
    
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/medical_scheduler_test'
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def _db(app):
    from db import db
    return db

@pytest.fixture
def sample_areas(app, _db):
    from models import StaffArea
    
    with app.app_context():
        areas = [
            StaffArea(name='Admitting', required_rn_count=2),
            StaffArea(name='Recovery', required_rn_count=2),
            StaffArea(name='Procedure Room 2', required_tech_count=2)
        ]
        _db.session.add_all(areas)
        _db.session.commit()
        
        area_ids = [a.id for a in areas]
        _db.session.expunge_all()
        return area_ids

@pytest.fixture
def sample_staff(app, _db, sample_areas):
    from models import Staff
    
    with app.app_context():
        staff_members = [
            Staff(
                name='Test RN', 
                role='RN', 
                shift_length=10, 
                days_per_week=4, 
                is_active=True, 
                area_restrictions='["Any"]'
            ),
            Staff(
                name='Test Tech', 
                role='GI_Tech', 
                shift_length=8, 
                days_per_week=4, 
                is_active=True, 
                area_restrictions='["Any"]'
            )
        ]
        _db.session.add_all(staff_members)
        _db.session.commit()
        
        staff_ids = [s.id for s in staff_members]
        _db.session.expunge_all()
        return staff_ids