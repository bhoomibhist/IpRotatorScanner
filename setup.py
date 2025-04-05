#!/usr/bin/env python3
"""
URL Indexing Checker Setup Script
This script helps set up the URL Indexing Checker application by:
1. Creating required directories
2. Setting up environment variables
3. Creating database tables
"""

import os
import sys
import random
import string
import argparse

def generate_secret_key(length=32):
    """Generate a random secret key for Flask sessions."""
    characters = string.ascii_letters + string.digits + '!@#$%^&*()_-+=<>?'
    return ''.join(random.choice(characters) for _ in range(length))

def create_env_file(db_url=None):
    """Create a .env file with required environment variables."""
    if os.path.exists('.env'):
        print("INFO: .env file already exists, skipping creation")
        return
    
    # Use provided database URL or default
    if not db_url:
        db_url = os.environ.get("DATABASE_URL", "sqlite:///instance/indexing_checker.db")
    
    # Generate a secret key
    secret_key = generate_secret_key()
    
    # Create the .env file
    with open('.env', 'w') as f:
        f.write(f"DATABASE_URL={db_url}\n")
        f.write(f"SESSION_SECRET={secret_key}\n")
    
    print("INFO: Created .env file with environment variables")

def setup_database():
    """Initialize the database tables."""
    try:
        # Import the app to create tables
        from app import db, app
        with app.app_context():
            db.create_all()
            print("INFO: Successfully created database tables")
    except Exception as e:
        print(f"ERROR: Failed to create database tables: {str(e)}")
        return False
    
    return True

def main():
    """Main setup function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='URL Indexing Checker Setup')
    parser.add_argument('--db-url', help='Database URL (e.g., postgresql://user:pass@localhost/dbname)')
    args = parser.parse_args()
    
    print("=== URL Indexing Checker Setup ===")
    
    # Create .env file
    create_env_file(args.db_url)
    
    # Set up database
    if setup_database():
        print("\nSetup completed successfully!")
        print("\nYou can now run the application with:")
        print("    python main.py")
        print("or with Gunicorn:")
        print("    gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app")
    else:
        print("\nSetup encountered errors. Please check the messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()