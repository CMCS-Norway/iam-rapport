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
        email = session.get('user').get('preferred_username')
        name = session.get('user').get('name')
        customer_id = int(request.form['customer_id'])  # Ensure customer_id is an integer
        role = request.form['role']
        
        # Get first and last name from session
        first_name = session.get('user').get('given_name')
        last_name = session.get('user').get('family_name')

        # Get selected systems
        selected_systems = request.form.getlist('systems')

        # Check if user exists, if not, create a new user
        user = User.query.get(user_id)
        if not user:
            user = User(id=user_id, name=name, email=email)
            db.session.add(user)
            db.session.commit()

        # Verify customer exists before creating the access request
        customer = Customer.query.get(customer_id)
        if customer:
            approver_username = session['user']['preferred_username']
            existing_request = AccessRequest.query.filter_by(user_id=user_id, customer_id=customer_id).first()
            if existing_request:
                # Update existing role
                existing_request.role = role
                existing_request.approval_timestamp = datetime.utcnow()
                existing_request.approver_username = approver_username
            else:
                # Create new access request
                for system in selected_systems:
                    access_request = AccessRequest(
                        user_id=user_id, 
                        customer_id=customer_id, 
                        role=role, 
                        first_name=first_name, 
                        last_name=last_name,
                        request_timestamp=datetime.utcnow(),
                        approver_username=approver_username
                    )
                    db.session.add(access_request)
            db.session.commit()

            return redirect(url_for('main.index'))
        else:
            # Handle the error appropriately (e.g., flash a message or render an error page)
            return redirect(url_for('main.index'))  # Simplified for brevity
    
    customers = Customer.query.all()
    roles = Role.query.all()
    return render_template('request_access.html', customers=customers, roles=roles)

@main_bp.route('/request_internal_access', methods=['GET', 'POST'])
def request_internal_access():
    user_id = session.get('user').get('oid')

    if request.method == 'POST':
        selected_internal_accesses = request.form.getlist('internal_accesses')

        # Check if user exists, if not, create a new user
        user = User.query.get(user_id)
        if not user:
            name = session.get('user').get('name')
            email = session.get('user').get('preferred_username')
            user = User(id=user_id, name=name, email=email)
            db.session.add(user)
            db.session.commit()

        # Handle internal accesses
        existing_accesses = {access.internal_access_id for access in UserInternalAccess.query.filter_by(user_id=user_id).all()}
        for access_id in selected_internal_accesses:
            access_id = int(access_id)
            if access_id not in existing_accesses:
                user_internal_access = UserInternalAccess(
                    user_id=user_id, 
                    internal_access_id=access_id, 
                    granted=True
                )
                db.session.add(user_internal_access)
        db.session.commit()

        return redirect(url_for('main.index'))

    internal_accesses = InternalAccess.query.all()
    user_internal_access_ids = {access.internal_access_id for access in UserInternalAccess.query.filter_by(user_id=user_id).all()}
    return render_template('request_internal_access.html', internal_accesses=internal_accesses, user_internal_access_ids=user_internal_access_ids)

@admin_bp.route('/')
def admin_dashboard():
    if not session.get('is_admin'):
        return abort(403)
    requests = AccessRequest.query.filter_by(approved=False).all()
    return render_template('admin.html', requests=requests)

@admin_bp.route('/approve/<int:request_id>')
def approve_request(request_id):
    if not session.get('is_admin'):
        return abort(403)
    access_request = AccessRequest.query.get(request_id)
    access_request.approved = True
    access_request.approval_timestamp = datetime.utcnow()
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
            AccessRequest.approved
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