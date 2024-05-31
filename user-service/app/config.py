import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://user:password@db/user_service')
    SQLALCHEMY_TRACK_MODIFICATIONS = False