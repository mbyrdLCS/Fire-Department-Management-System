"""
WSGI configuration for PythonAnywhere deployment
"""

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/Fire-Department-Management-System'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = os.path.join(project_home, '.env')
load_dotenv(env_path)

# Import Flask app
from flask_app.app import app as application

# Ensure the database directory exists
db_path = os.path.join(project_home, 'flask_app', 'database')
os.makedirs(db_path, exist_ok=True)
