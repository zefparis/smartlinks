#!/usr/bin/env python3
"""
Script to set up the PostgreSQL database and user for the SmartLinks Autopilot application.
Run this script with a PostgreSQL superuser account.
"""
import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def setup_database():
    # Database connection parameters (using default postgres database for setup)
    db_params = {
        'dbname': 'postgres',  # Connect to default database
        'user': 'postgres',    # Default superuser - change as needed
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'host': 'localhost',
        'port': '5432'
    }
    
    # Database and user details
    db_name = 'smartlinks'
    db_user = 'smartlinks_user'
    db_password = 'smartpass'  # In production, use a more secure password
    
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if not cursor.fetchone():
            print(f"Creating database: {db_name}")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(db_name))
            )
        
        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_user WHERE usename = %s", (db_user,))
        if not cursor.fetchone():
            print(f"Creating user: {db_user}")
            cursor.execute(sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                sql.Identifier(db_user)), [db_password]
            )
        
        # Grant privileges
        print("Granting privileges...")
        cursor.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
            sql.Identifier(db_name), sql.Identifier(db_user))
        )
        
        print("Database setup completed successfully!")
        print(f"\nConnection string for your .env file:")
        print(f"DATABASE_URL=postgresql+psycopg2://{db_user}:{db_password}@localhost:5432/{db_name}")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    print("Setting up PostgreSQL database for SmartLinks Autopilot...")
    setup_database()
