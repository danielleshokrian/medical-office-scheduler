from flask import Flask
from flask_cors import CORS
from config import Config
from models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    CORS(app)
    
    from routes.staff import staff_bp
    from routes.shifts import shifts_bp
    from routes.time_off import time_off_bp
    from routes.ai_suggestions import ai_bp
    
    app.register_blueprint(staff_bp, url_prefix='/api/staff')
    app.register_blueprint(shifts_bp, url_prefix='/api/shifts')
    app.register_blueprint(time_off_bp, url_prefix='/api/time-off')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)