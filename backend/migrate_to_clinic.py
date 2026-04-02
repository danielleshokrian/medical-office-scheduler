"""
One-time migration: assign all existing NULL clinic_id records to the LICDH clinic.

Run AFTER applying the Alembic migration (flask db upgrade),
BEFORE running setup_licdh.py or setup_demo.py.

Usage: python migrate_to_clinic.py
"""

from app import app, db
from models import Staff, StaffArea, Shift, TimeOffRequest, AISuggestion, User, Clinic
from sqlalchemy import text


def migrate():
    with app.app_context():
        # 1. Create LICDH clinic if it doesn't exist
        clinic = Clinic.query.filter_by(invite_code='LICDH2026').first()
        if not clinic:
            clinic = Clinic(
                name='Long Island Center for Digestive Health',
                invite_code='LICDH2026'
            )
            db.session.add(clinic)
            db.session.commit()
            print(f"Created LICDH clinic: id={clinic.id}")
        else:
            print(f"Found existing LICDH clinic: id={clinic.id}")

        cid = clinic.id

        # 2. Back-fill all tables -- only rows where clinic_id IS NULL
        tables = [
            'staff',
            'staff_area',
            'shift',
            'time_off_request',
            'ai_suggestion',
            '"user"',  # quoted because user is a reserved word in PostgreSQL
        ]

        for table_name in tables:
            result = db.session.execute(
                text(f"UPDATE {table_name} SET clinic_id = :cid WHERE clinic_id IS NULL"),
                {'cid': cid}
            )
            print(f"  {table_name}: {result.rowcount} rows updated")

        db.session.commit()
        print("\nMigration complete.")
        print("You can now run: python setup_demo.py")


if __name__ == '__main__':
    migrate()
