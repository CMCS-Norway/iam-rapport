import psycopg2
from psycopg2 import sql
from faker import Faker
import os
import time

# Initialize Faker
fake = Faker()

# Database connection parameters
DB_NAME = 'access_review'  # Changed from os.getenv('POSTGRES_DB') to 'access_review'
USER = os.getenv('POSTGRES_USER')
PASSWORD = os.getenv('POSTGRES_PASSWORD')

# Ensure the connection parameters are printed for debugging
if not all([DB_NAME, USER, PASSWORD]):
    print('Database connection parameters are missing!')
    print(f'DB_NAME: {DB_NAME}, USER: {USER}, PASSWORD: {PASSWORD}')

HOST = 'db'  # Ensure this points to the db service
PORT = '5432'

# Retry connection parameters
MAX_RETRIES = 5
RETRY_DELAY = 5

try:
    # Connect to the default postgres database to create the access_review database
    connection = psycopg2.connect(
        dbname='postgres',  # Connect to the default database first
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )

    cursor = connection.cursor()

    # Check if the database exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    exists = cursor.fetchone()

    # Close the connection to the default database
    cursor.close()
    connection.close()

    # Reconnect to the server to create the database
    connection = psycopg2.connect(
        dbname='postgres',  # Connect to the default database first
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )

    # Set autocommit mode to True
    connection.autocommit = True

    cursor = connection.cursor()

    if not exists:
        cursor.execute(sql.SQL("CREATE DATABASE {}; ").format(sql.Identifier(DB_NAME)))
        print(f'Database {DB_NAME} created successfully.')
    else:
        print(f'Database {DB_NAME} already exists.')

    # Close the connection to the default database
    cursor.close()
    connection.close()

    # Attempt to connect to the database with retries
    for attempt in range(MAX_RETRIES):
        try:
            connection = psycopg2.connect(
                dbname=DB_NAME,
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT
            )
            break  # Exit loop if connection is successful
        except psycopg2.OperationalError:
            print(f'Attempt {attempt + 1} of {MAX_RETRIES}: Database not ready, retrying in {RETRY_DELAY} seconds...')
            time.sleep(RETRY_DELAY)
    else:
        print('Failed to connect to the database after several attempts.')
        exit(1)

    cursor = connection.cursor()

    # Create a table for customer names
    cursor.execute("CREATE TABLE IF NOT EXISTS customers (id SERIAL PRIMARY KEY, name VARCHAR(100));")
    print('Table customers created successfully.')

    # Insert random customer names
    for _ in range(10):
        cursor.execute("INSERT INTO customers (name) VALUES (%s);", (fake.name(),))
    print('10 random customer names inserted successfully.')

except Exception as e:
    print(f'An error occurred: {e}')
finally:
    if 'connection' in locals() and connection:
        cursor.close()
        connection.close()
