from flask import Blueprint, request, jsonify
from .models import User, db

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.as_dict() for user in users])

# Add more routes as needed