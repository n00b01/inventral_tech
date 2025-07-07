import os
import re
from flask import Flask, render_template, request, session, redirect, flash, jsonify, url_for
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from flask import send_from_directory

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fd4e84f5644aa4a316746e8bf367f16d')

# Configure logging
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

# PostgreSQL Database configuration in the .env file which I can't share publicly
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT')
}

def get_db_connection():
    """Create and return a PostgreSQL database connection with dict cursor"""
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


# CORE ROUTES

@app.route('/')
def home():
    message = request.args.get('message')
    return render_template('index.html', 
                         message=message,
                         active_page='home')

@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('login'))
    return render_template('dashboard.html',
                         user_name=session.get('user_name'),
                         active_page='dashboard')

@app.route('/client')
def client():
    return render_template('client.html',
                         active_page='client')

@app.route('/join')
def join():
    return render_template('join.html',
                         active_page='join')

@app.route('/projects')
def projects():
    return render_template('projects.html',
                         active_page='projects')

@app.route('/service')
def service():
    return render_template('service.html',
                         active_page='service')

@app.route('/favicon.ico') 
def favicon():  
    return send_from_directory( 
        os.path.join(app.root_path, 'static'),  
        'favicon',
        mimetype='image/vnd.microsoft.icon'  
    )

@app.route('/api/ping')
def ping():
    return {"status": "ok"}

@app.route('/')
def index():
    return render_template("index.html")


# AUTHENTICATION ROUTES

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please enter both email and password', 'error')
            return render_template('login.html')

        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT fullname, email, password 
                        FROM signup_table 
                        WHERE email = %s
                    """, (email,))
                    user = cursor.fetchone()

                    if user and check_password_hash(user['password'], password):
                        session['user_email'] = user['email']
                        session['user_name'] = user['fullname']
                        flash('Login successful!', 'success')
                        return redirect(url_for('dashboard'))
                    
                    flash('Invalid email or password', 'error')
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            flash('Login failed. Please try again.', 'error')

    return render_template('login.html',
                         active_page='login')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        required_fields = ['fullname', 'email', 'password', 'password1']
        if not all(request.form.get(field) for field in required_fields):
            flash('All fields are required', 'error')
            return render_template('signup.html')

        email = request.form['email']
        password = request.form['password']

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email format', 'error')
            return render_template('signup.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('signup.html')

        if password != request.form['password1']:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT email FROM signup_table WHERE email = %s", (email,))
                    if cursor.fetchone():
                        flash('Email already registered', 'error')
                        return render_template('signup.html')

                    hashed_pw = generate_password_hash(password)
                    cursor.execute("""
                        INSERT INTO signup_table (fullname, email, password)
                        VALUES (%s, %s, %s)
                    """, (request.form['fullname'], email, hashed_pw))
                    conn.commit()

            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            app.logger.error(f"Signup error: {str(e)}")
            flash('Registration failed. Please try again.', 'error')

    return render_template('signup.html',
                         active_page='signup')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


# FORM HANDLING ROUTES

@app.route('/join_mission', methods=['POST'])
def join_mission():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        skills = request.form.get('skills')
        message = request.form.get('message')
        
        if not all([name, email, message]):
            flash('Please fill all required fields', 'error')
            return redirect(url_for('join'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email format', 'error')
            return redirect(url_for('join'))

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS join_applications (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100) NOT NULL,
                        skills TEXT,
                        message TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    INSERT INTO join_applications (name, email, skills, message)
                    VALUES (%s, %s, %s, %s)
                """, (name, email, skills, message))
                conn.commit()
        
        flash('Application submitted successfully!', 'success')
    except Exception as e:
        flash('Error submitting application', 'error')
        app.logger.error(f"Join mission error: {str(e)}")
    
    return redirect(url_for('join'))

@app.route('/request_service', methods=['POST'])
def request_service():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        service_type = request.form.get('service')
        budget = request.form.get('budget')
        message = request.form.get('message')
        
        if not all([name, email, service_type, message]):
            flash('Please fill all required fields', 'error')
            return redirect(url_for('client'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email format', 'error')
            return redirect(url_for('client'))

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS service_requests (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100) NOT NULL,
                        service_type VARCHAR(50) NOT NULL,
                        budget VARCHAR(50),
                        message TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    INSERT INTO service_requests (name, email, service_type, budget, message)
                    VALUES (%s, %s, %s, %s, %s)
                """, (name, email, service_type, budget, message))
                conn.commit()
        
        flash('Request submitted! We\'ll contact you soon.', 'success')
    except Exception as e:
        flash('Error submitting request', 'error')
        app.logger.error(f"Service request error: {str(e)}")
    
    return redirect(url_for('client'))


# ERROR HANDLERS



@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# APPLICATION LAUNCH

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '127.0.0.1'),
        port=int(os.getenv('FLASK_PORT', '5050')),
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )

# Updated by @n00b01 >>Github