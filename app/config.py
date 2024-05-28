import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    AUTHORITY = os.getenv('AUTHORITY')
    REDIRECT_PATH = os.getenv('REDIRECT_PATH')
    SCOPE = ["User.Read"]
    SESSION_TYPE = "filesystem"
    REQUIRED_GROUPS = os.getenv('REQUIRED_GROUPS').split(',')
    ADMIN_GROUP_ID = os.getenv('ADMIN_GROUP_ID')  # Add this line