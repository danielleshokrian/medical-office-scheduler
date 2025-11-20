"""

Configuration settings for different environments

"""

import os

from datetime import timedelta

 

 

class Config:

    """Base configuration"""

    # Database

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://localhost/medical_scheduler')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

 

    # Security

    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', os.getenv('SECRET_KEY', 'jwt-secret-key-change-in-production'))

 

    # JWT Configuration

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    JWT_TOKEN_LOCATION = ["headers"]

    JWT_HEADER_NAME = "Authorization"

    JWT_HEADER_TYPE = "Bearer"

 

    # SQLAlchemy Connection Pooling (important for production)

    SQLALCHEMY_ENGINE_OPTIONS = {

        'pool_size': 10,

        'pool_timeout': 30,

        'pool_recycle': 3600,

        'max_overflow': 20

    }

 

 

class DevelopmentConfig(Config):

    """Development configuration"""

    DEBUG = True

    TESTING = False

 

    # Allow all origins in development

    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']

 

 

class ProductionConfig(Config):

    """Production configuration"""

    DEBUG = False

    TESTING = False

 

    # Only allow your production domains

    # Update these with your actual domain(s)

    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else [

        'https://yourdomain.com',

        'https://www.yourdomain.com'

    ]

 

    # Require HTTPS in production

    SESSION_COOKIE_SECURE = True

    SESSION_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SAMESITE = 'Lax'

 

 

class TestingConfig(Config):

    """Testing configuration"""

    DEBUG = True

    TESTING = True

    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'postgresql://localhost/medical_scheduler_test')

 

 

# Configuration dictionary

config = {

    'development': DevelopmentConfig,

    'production': ProductionConfig,

    'testing': TestingConfig,

    'default': DevelopmentConfig

}

 

 

def get_config():

    """Get configuration based on FLASK_ENV"""

    env = os.getenv('FLASK_ENV', 'development')

    return config.get(env, config['default'])