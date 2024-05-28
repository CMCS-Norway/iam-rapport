from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    access_requests = db.relationship('AccessRequest', backref='user', lazy=True)
    internal_accesses = db.relationship('UserInternalAccess', backref='user', lazy=True)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    access_requests = db.relationship('AccessRequest', backref='customer', lazy=True)

class AccessRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    request_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    approval_timestamp = db.Column(db.DateTime)
    approved = db.Column(db.Boolean, default=False)
    approver_username = db.Column(db.String(50))

    @classmethod
    def change_role(cls, user_id, customer_id, new_role, approver_username):
        existing_request = cls.query.filter_by(user_id=user_id, customer_id=customer_id).first()
        if existing_request:
            existing_request.role = new_role
            existing_request.approval_timestamp = datetime.utcnow()
            existing_request.approver_username = approver_username
        else:
            new_request = cls(
                user_id=user_id,
                customer_id=customer_id,
                role=new_role,
                approval_timestamp=datetime.utcnow(),
                approver_username=approver_username
            )
            db.session.add(new_request)
        db.session.commit()

class InternalAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class UserInternalAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id'), nullable=False)
    internal_access_id = db.Column(db.Integer, db.ForeignKey('internal_access.id'), nullable=False)
    granted = db.Column(db.Boolean, default=False)
    access = db.relationship('InternalAccess', backref='user_accesses', lazy=True)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)    