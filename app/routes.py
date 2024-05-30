from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from models import db, User, Customer, AccessRequest, InternalAccess, UserInternalAccess, Role
from datetime import datetime

main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__)

@main_bp.route('/')
def index():
    if 'user' in session:
        user_id = session['user']['oid']
        pending_requests = AccessRequest.query.filter_by(user_id=user_id, approved=False).order_by(AccessRequest.customer_id, AccessRequest.request_timestamp).all()
        approved_requests = AccessRequest.query.filter_by(user_id=user_id, approved=True).order_by(AccessRequest.customer_id, AccessRequest.request_timestamp).all()

        # Group approved requests by customer
        grouped_approved_requests = {}
        for request in approved_requests:
            customer_name = request.customer.name
            if customer_name not in grouped_approved_requests:
                grouped_approved_requests[customer_name] = []
            grouped_approved_requests[customer_name].append(request)

        # Query internal accesses for the user
        internal_access_records = UserInternalAccess.query.filter_by(user_id=user_id, granted=True).all()
        internal_access = [access.access.name for access in internal_access_records]


        return render_template('dashboard.html', pending_requests=pending_requests, grouped_approved_requests=grouped_approved_requests, internal_access=internal_access)
    else:
        return render_template('index.html')
@main_bp.route('/request_access', methods=['GET', 'POST'])
def request_access():
    if request.method == 'POST':
        user_id = session.get('user').get('oid')
        customer_id = int(request.form['customer_id'])
        role = request.form['role']
        first_name = session.get('user').get('given_name')
        last_name = session.get('user').get('family_name')
        approver_username = session.get('user').get('preferred_username')
        approver_first_name = session.get('user').get('given_name')
        approver_last_name = session.get('user').get('family_name')

        print(f"User ID: {user_id}, Customer ID: {customer_id}, Role: {role}, Approver: {approver_username}")

        # Check if user exists, if not, create a new user
        user = User.query.get(user_id)
        if not user:
            name = session.get('user').get('name')
            email = session.get('user').get('preferred_username')
            user = User(id=user_id, name=name, email=email)
            db.session.add(user)
            db.session.commit()
            print("New user created")

        # Verify customer exists before creating the access request
        customer = Customer.query.get(customer_id)
        if customer:
            existing_request = AccessRequest.query.filter_by(user_id=user_id, customer_id=customer_id).first()
            if existing_request:
                # If the role is changed, reset approval status and timestamp
                if existing_request.role != role:
                    existing_request.role = role
                    existing_request.first_name = first_name
                    existing_request.last_name = last_name
                    existing_request.request_timestamp = datetime.utcnow()
                    existing_request.approved = False
                    existing_request.approval_timestamp = None
                    existing_request.approver_username = None
                    existing_request.approver_first_name = None
                    existing_request.approver_last_name = None
                    print("Role changed and approval reset")
                else:
                    print("Role not changed, no reset needed")
            else:
                access_request = AccessRequest(
                    user_id=user_id,
                    customer_id=customer_id,
                    role=role,
                    first_name=first_name,
                    last_name=last_name,
                    request_timestamp=datetime.utcnow(),
                    approver_username=approver_username,
                    approver_first_name=approver_first_name,
                    approver_last_name=approver_last_name
                )
                db.session.add(access_request)
                print("New access request created")
            db.session.commit()
            return redirect(url_for('main.index'))
        else:
            print("Customer not found")
            return redirect(url_for('main.index'))

    customers = Customer.query.all()
    roles = Role.query.all()
    return render_template('request_access.html', customers=customers, roles=roles)

@main_bp.route('/request_internal_access', methods=['GET', 'POST'])
def request_internal_access():
    user_id = session.get('user').get('oid')

    if request.method == 'POST':
        selected_internal_accesses = request.form.getlist('internal_accesses')
        approver_username = session['user']['preferred_username']
        approver_first_name = session.get('user').get('given_name')
        approver_last_name = session.get('user').get('family_name')

        # Check if user exists, if not, create a new user
        user = User.query.get(user_id)
        if not user:
            name = session.get('user').get('name')
            email = session.get('user').get('preferred_username')
            user = User(id=user_id, name=name, email=email)
            db.session.add(user)
            db.session.commit()

        # Handle internal accesses
        for access_id in selected_internal_accesses:
            internal_access = InternalAccess.query.get(access_id)
            if not internal_access:
                continue
            
            existing_request = AccessRequest.query.filter_by(user_id=user_id, customer_id=0, role=internal_access.name, is_internal_access=True).first()
            if existing_request:
                if not existing_request.approved:
                    existing_request.request_timestamp = datetime.utcnow()
                    existing_request.approver_username = None
                    existing_request.approver_first_name = None
                    existing_request.approver_last_name = None
                    existing_request.approved = False
                    existing_request.approval_timestamp = None
            else:
                access_request = AccessRequest(
                    user_id=user_id,
                    customer_id=0,  # Using customer_id as 0 for internal access
                    role=internal_access.name,
                    first_name=session['user'].get('given_name'),
                    last_name=session['user'].get('family_name'),
                    request_timestamp=datetime.utcnow(),
                    approver_username=approver_username,
                    approver_first_name=approver_first_name,
                    approver_last_name=approver_last_name,
                    is_internal_access=True
                )
                db.session.add(access_request)
        db.session.commit()

        return redirect(url_for('main.index'))

    internal_accesses = InternalAccess.query.all()
    user_internal_access_ids = {access.internal_access_id for access in UserInternalAccess.query.filter_by(user_id=user_id).all()}
    return render_template('request_internal_access.html', internal_accesses=internal_accesses, user_internal_access_ids=user_internal_access_ids)

@admin_bp.route('/')
def admin_dashboard():
    if not session.get('is_admin'):
        return abort(403)
    requests = AccessRequest.query.filter_by(approved=False, is_internal_access=False).all()
    internal_requests = AccessRequest.query.filter_by(approved=False, is_internal_access=True).all()
    return render_template('admin_dashboard.html', requests=requests, internal_requests=internal_requests)

@admin_bp.route('/approve/<int:request_id>')
def approve_request(request_id):
    if not session.get('is_admin'):
        return abort(403)
    access_request = AccessRequest.query.get(request_id)
    access_request.approved = True
    access_request.approval_timestamp = datetime.utcnow()
    access_request.approver_username = session.get('user')['preferred_username']
    access_request.approver_first_name = session.get('user')['given_name']
    access_request.approver_last_name = session.get('user')['family_name']
    db.session.commit()
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/generate_report', methods=['GET', 'POST'])
def generate_report():
    if not session.get('is_admin'):
        return abort(403)
    
    if request.method == 'POST':
        report_type = request.form['report_type']
        report_scope = request.form['report_scope']
        customer_id = request.form.get('customer_id')
        user_id = request.form.get('user_id')
        
        query = db.session.query(
            Customer.name.label('customer_name'),
            User.name.label('user_name'),
            AccessRequest.role,
            AccessRequest.request_timestamp,
            AccessRequest.approval_timestamp,
            AccessRequest.approved,
            AccessRequest.approver_first_name,
            AccessRequest.approver_last_name
        ).join(Customer, AccessRequest.customer_id == Customer.id)\
         .join(User, AccessRequest.user_id == User.id)
        
        if report_scope == 'specific_customer' and customer_id:
            query = query.filter(AccessRequest.customer_id == customer_id)
        elif report_scope == 'specific_user' and user_id:
            query = query.filter(AccessRequest.user_id == user_id)
        
        report_data = query.order_by(Customer.name, User.name).all()

        # Internal Accesses Reporting
        internal_access_query = db.session.query(
            User.name.label('user_name'),
            InternalAccess.name.label('access_name'),
            UserInternalAccess.granted
        ).join(User, UserInternalAccess.user_id == User.id)\
         .join(InternalAccess, UserInternalAccess.internal_access_id == InternalAccess.id)
        
        if report_scope == 'specific_user' and user_id:
            internal_access_query = internal_access_query.filter(UserInternalAccess.user_id == user_id)

        internal_access_report_data = internal_access_query.order_by(User.name, InternalAccess.name).all()

        return render_template('report.html', report_data=report_data, internal_access_report_data=internal_access_report_data, report_type=report_type)

    customers = Customer.query.all()
    users = User.query.all()
    return render_template('generate_report.html', customers=customers, users=users)

@admin_bp.route('/create_customer', methods=['GET', 'POST'])
def create_customer():
    if not session.get('is_admin'):
        return abort(403)
    if request.method == 'POST':
        name = request.form['name']
        
        new_customer = Customer(name=name)
        db.session.add(new_customer)
        db.session.commit()

        return redirect(url_for('admin.admin_dashboard'))

    return render_template('create_customer.html')