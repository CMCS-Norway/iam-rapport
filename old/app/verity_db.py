from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from models import User, Customer, AccessRequest, InternalAccess, UserInternalAccess

# Update the connection string with your database credentials
DATABASE_URL = "postgresql://myuser:mypassword@localhost/access_review"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Inspect the database
inspector = inspect(engine)

# Verify tables
tables = inspector.get_table_names()
print("Tables in the database:")
print(tables)

# Verify columns in each table
def print_columns(table_name):
    columns = inspector.get_columns(table_name)
    print(f"\nColumns in {table_name}:")
    for column in columns:
        print(f"{column['name']} - {column['type']}")

for table in tables:
    print_columns(table)

# Example query to check data
def example_query():
    print("\nExample query results:")
    # Fetch all users
    users = session.query(User).all()
    for user in users:
        print(f"User: {user.name}, Email: {user.email}")

    # Fetch all customers
    customers = session.query(Customer).all()
    for customer in customers:
        print(f"Customer: {customer.name}")

    # Fetch all access requests
    access_requests = session.query(AccessRequest).all()
    for request in access_requests:
        print(f"Access Request: User ID {request.user_id}, Customer ID {request.customer_id}, Role {request.role}")

    # Fetch all internal accesses
    internal_accesses = session.query(InternalAccess).all()
    for access in internal_accesses:
        print(f"Internal Access: {access.name}")

    # Fetch all user internal accesses
    user_internal_accesses = session.query(UserInternalAccess).all()
    for user_access in user_internal_accesses:
        print(f"User Internal Access: User ID {user_access.user_id}, Access ID {user_access.internal_access_id}, Granted {user_access.granted}")

example_query()