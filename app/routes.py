from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, User, Customer, AccessRequest
from datetime import datetime

main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__)

@main_bp.route('/')
def index():
    customers = Customer.query.all()
    return render_template('index.html', customers=customers)

@main_bp.route('/request_access', methods=['POST'])
def request_access():
    user_id = session.get('user').get('oid')
    customer_id = int(request.form['customer_id'])  # Ensure customer_id is an integer
    role = request.form['role']
    
    # Get first and last name from session
    first_name = session.get('user').get('given_name')
    last_name = session.get('user').get('family_name')
    
    # Verify customer exists before creating the access request
    customer = Customer.query.get(customer_id)
    
    if customer:
        access_request = AccessRequest(
            user_id=user_id, 
            customer_id=customer_id, 
            role=role, 
            first_name=first_name, 
            last_name=last_name
        )
        db.session.add(access_request)
        db.session.commit()
        return redirect(url_for('main.index'))
    else:
        # Handle the error appropriately (e.g., flash a message or render an error page)
        return redirect(url_for('main.index'))  # Simplified for brevity

@admin_bp.route('/')
def admin_dashboard():
    requests = AccessRequest.query.filter_by(approved=False).all()
    return render_template('admin.html', requests=requests)

@admin_bp.route('/approve/<int:request_id>')
def approve_request(request_id):
    access_request = AccessRequest.query.get(request_id)
    access_request.approved = True
    access_request.approval_timestamp = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('admin.admin_dashboard'))