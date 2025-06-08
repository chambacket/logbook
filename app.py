from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, make_response
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import json
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
import csv
from reportlab.platypus import Image
from io import StringIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from reportlab.platypus import Image

app = Flask(__name__)
app.secret_key = 'SUPA_SECRET_KEY'  # Change this to a random secret key
csrf = CSRFProtect(app)

UPLOAD_FOLDER = os.path.join('static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'equipment_returns.log')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Add logger to app
app.logger.setLevel(logging.INFO)
file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)


os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Add this near the top of your app.py, after creating the Flask app
@app.context_processor
def utility_processor():
    return {
        'min': min,
        'max': max
    }

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'fbls_db'
}

ADMIN_CREDENTIALS = {
    'email': 'admin@gmail.com',
    'username': 'admin',
    'password': generate_password_hash('admin123')
}

DEFAULT_DEPARTMENT = 'IECS'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
    return None

# Decorators
def faculty_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'faculty_id' not in session:
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated_function

# Add CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/auth', methods=['GET', 'POST'])
def auth():

    temp_message = None
    if 'temp_message' in session:
        temp_message = session.pop('temp_message')

    if request.method == 'POST':
        if 'name' in request.form:  # Registration
            return handle_registration()
        else:  # Login
            return handle_login()
    return render_template('auth.html', temp_message=temp_message)

def handle_registration():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    department = request.form.get('department', DEFAULT_DEPARTMENT)  # Set default to IECS
    
    if not all([name, email, password]):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': 'Name, email and password are required'
            })
        flash('Name, email and password are required', 'error')
        return redirect(url_for('auth'))
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT id FROM faculty WHERE email = %s", (email,))
            if cursor.fetchone():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': 'Email already exists'
                    })
                flash('Email already exists', 'error')
                return redirect(url_for('auth'))
            
            hashed_password = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO faculty (name, email, password, department) 
                VALUES (%s, %s, %s, %s)
            """, (name, email, hashed_password, department))
            
            connection.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'Registration successful! Please log in.'
                })
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth'))
            
        except Error as e:
            error_message = str(e)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': f'Registration failed: {error_message}'
                })
            flash(f'Registration failed: {error_message}', 'error')
            return redirect(url_for('auth'))
            
        finally:
            cursor.close()
            connection.close()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': False,
            'message': 'Database connection failed'
        })
    flash('Database connection failed', 'error')
    return redirect(url_for('auth'))

def handle_login():
    email = request.form['email']
    password = request.form['password']
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM faculty WHERE email = %s", (email,))
            faculty = cursor.fetchone()
            
            if faculty and check_password_hash(faculty['password'], password):
                session['faculty_id'] = faculty['id']
                session['faculty_name'] = faculty['name']
                session['temp_message'] = {
                    'type': 'success',
                    'text': 'Welcome back! You have successfully logged in.'
                }
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': True,
                        'redirect_url': url_for('dashboard'),
                        'message': 'Welcome back! You have successfully logged in.'
                    })
                return redirect(url_for('dashboard'))
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': 'Invalid email or password'
                    })
                flash('Invalid email or password', 'error')
                return redirect(url_for('auth'))
            
        finally:
            cursor.close()
            connection.close()
            
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': False,
            'message': 'Database connection failed'
        })
    flash('Database connection failed', 'error')
    return redirect(url_for('auth'))

@app.route('/dashboard')
@faculty_required
def dashboard():
    if session.pop('show_login_message', False):
        flash('Welcome back! You have successfully logged in.', 'success')
    
    borrowed_page = request.args.get('borrowed_page', 1, type=int)
    returned_page = request.args.get('returned_page', 1, type=int)
    items_per_page = 5
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get overall statistics
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM equipment) as total_items,
                    (SELECT COUNT(*) FROM borrowers WHERE status = 'approved' AND actual_return_date IS NULL) as issued_items,
                    (SELECT COUNT(*) FROM borrowers WHERE status = 'returned') as returned_items,
                    (SELECT COUNT(*) FROM faculty) as total_members
                FROM dual
            """)
            stats = cursor.fetchone()
            
            # Calculate percentages
            total = stats['total_items'] or 1  # Prevent division by zero
            stats['issued_percentage'] = round((stats['issued_items'] / total) * 100, 2)
            stats['returned_percentage'] = round((stats['returned_items'] / total) * 100, 2)
            
            # Get latest borrowed items with pagination
            cursor.execute("""
                SELECT 
                    b.id,
                    b.borrower_name as member_name,
                    b.borrow_date,
                    e.serial_number,
                    e.name as item_name
                FROM borrowers b
                JOIN equipment e ON b.equipment_id = e.id
                WHERE b.status = 'approved' 
                AND b.actual_return_date IS NULL
                ORDER BY b.borrow_date DESC
                LIMIT %s OFFSET %s
            """, (items_per_page, (borrowed_page - 1) * items_per_page))
            latest_borrowed = cursor.fetchall()
            
            # Get total count of borrowed items
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM borrowers
                WHERE status = 'approved' AND actual_return_date IS NULL
            """)
            total_borrowed = cursor.fetchone()['count']
            
            # Get latest returned items with pagination
            cursor.execute("""
                SELECT 
                    b.id,
                    b.borrower_name as member_name,
                    b.actual_return_date,
                    e.serial_number,
                    e.name as item_name
                FROM borrowers b
                JOIN equipment e ON b.equipment_id = e.id
                WHERE b.status = 'returned'
                ORDER BY b.actual_return_date DESC
                LIMIT %s OFFSET %s
            """, (items_per_page, (returned_page - 1) * items_per_page))
            latest_returned = cursor.fetchall()
            
            # Get total count of returned items
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM borrowers
                WHERE status = 'returned'
            """)
            total_returned = cursor.fetchone()['count']
            
            # Calculate pagination values
            borrowed_end = min(borrowed_page * items_per_page, total_borrowed)
            returned_end = min(returned_page * items_per_page, total_returned)
            borrowed_start = (borrowed_page - 1) * items_per_page + 1 if total_borrowed > 0 else 0
            returned_start = (returned_page - 1) * items_per_page + 1 if total_returned > 0 else 0

            # Fetch most borrowed items
            cursor.execute("""
                SELECT 
                    e.name,
                    COUNT(*) as borrow_count
                FROM borrowers b
                JOIN equipment e ON b.equipment_id = e.id
                GROUP BY e.id, e.name
                ORDER BY borrow_count DESC
                LIMIT 4
            """)
            most_borrowed = cursor.fetchall()

            # Get the maximum borrow count for percentage calculation
            most_borrowed_max = max([item['borrow_count'] for item in most_borrowed]) if most_borrowed else 1
            
            return render_template('dashboard.html',
                                total_items=stats['total_items'],
                                issued_items=stats['issued_items'],
                                returned_items=stats['returned_items'],
                                total_members=stats['total_members'],
                                issued_percentage=stats['issued_percentage'],
                                returned_percentage=stats['returned_percentage'],
                                latest_borrowed=latest_borrowed,
                                latest_returned=latest_returned,
                                borrowed_page=borrowed_page,
                                returned_page=returned_page,
                                page=borrowed_page,  # Add this line
                                items_per_page=items_per_page,
                                total_borrowed=total_borrowed,
                                total_returned=total_returned,
                                borrowed_start=borrowed_start,
                                borrowed_end=borrowed_end,
                                returned_start=returned_start,
                                returned_end=returned_end,
                                most_borrowed=most_borrowed,
                                most_borrowed_max=most_borrowed_max)
            
        except Error as e:
            print(f"Database error: {e}")  # Debug log
            flash(f'Error: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('dashboard.html', 
                         total_items=0,
                         issued_items=0,
                         returned_items=0,
                         total_members=0,
                         issued_percentage=0,
                         returned_percentage=0,
                         latest_borrowed=[],
                         latest_returned=[],
                         borrowed_page=1,
                         returned_page=1,
                         page=1, #added this line
                         items_per_page=5,
                         total_borrowed=0,
                         total_returned=0,
                         borrowed_start=0,
                         borrowed_end=0,
                         returned_start=0,
                         returned_end=0,
                         most_borrowed=[],
                         most_borrowed_max=1)

@app.route('/api/dashboard-data')
@faculty_required
def dashboard_data():
    try:
        table_type = request.args.get('type')
        page = request.args.get('page', 1, type=int)
        items_per_page = 5
        
        if not table_type:
            return jsonify({'error': 'Table type is required'}), 400
            
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
            
        try:
            cursor = connection.cursor(dictionary=True)
            
            if table_type == 'borrowed':
                # Get borrowed items with pagination
                cursor.execute("""
                    SELECT DISTINCT 
                        b.id,
                        b.borrower_name as member_name,
                        b.borrow_date as date,
                        e.serial_number,
                        e.name as item_name
                    FROM borrowers b
                    JOIN equipment e ON b.equipment_id = e.id
                    WHERE b.status = 'approved' 
                    AND b.actual_return_date IS NULL
                    ORDER BY b.borrow_date DESC, b.id DESC
                    LIMIT %s OFFSET %s
                """, (items_per_page, (page - 1) * items_per_page))
                items = cursor.fetchall()
                
                # Get total count
                cursor.execute("""
                    SELECT COUNT(DISTINCT b.id) as total 
                    FROM borrowers b 
                    WHERE b.status = 'approved' 
                    AND b.actual_return_date IS NULL
                """)
                total = cursor.fetchone()['total']
                
            else:  # returned
                # Get returned items with pagination
                cursor.execute("""
                    SELECT DISTINCT 
                        b.id,
                        b.borrower_name as member_name,
                        b.actual_return_date as date,
                        e.serial_number,
                        e.name as item_name
                    FROM borrowers b
                    JOIN equipment e ON b.equipment_id = e.id
                    WHERE b.status = 'returned'
                    ORDER BY b.actual_return_date DESC, b.id DESC
                    LIMIT %s OFFSET %s
                """, (items_per_page, (page - 1) * items_per_page))
                items = cursor.fetchall()
                
                # Get total count for returned items
                cursor.execute("""
                    SELECT COUNT(DISTINCT b.id) as total 
                    FROM borrowers b 
                    WHERE b.status = 'returned'
                """)
                total = cursor.fetchone()['total']
            
            # Calculate pagination values
            start = (page - 1) * items_per_page + 1 if total > 0 else 0
            end = min(page * items_per_page, total)
            
            # Convert datetime objects to string format
            for item in items:
                if isinstance(item['date'], datetime):
                    item['date'] = item['date'].strftime('%Y-%m-%d')
            
            return jsonify({
                'items': items,
                'total': total,
                'start': start,
                'end': end,
                'current_page': page,
                'has_more': end < total,
                'table_type': table_type  # Add table type to response
            })
            
        except Error as e:
            print(f"Database error in dashboard_data: {e}")
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            connection.close()
            
    except Exception as e:
        print(f"Unexpected error in dashboard_data: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
    
@app.route('/logout')
def logout():
    session.clear()
    # Store logout message in session
    session['temp_message'] = {
        'type': 'success',
        'text': 'You have been logged out successfully.'
    }
    return redirect(url_for('auth'))
    
@app.route('/equipment')
@faculty_required
def equipment():
    # Get temporary message if it exists and remove it from session
    temp_message = None
    if 'temp_message' in session:
        temp_message = session.pop('temp_message')
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM equipment ORDER BY name ASC")
            equipment = cursor.fetchall()
            return render_template('equipment.html', 
                                 equipment=equipment,
                                 temp_message=temp_message)
        finally:
            connection.close()
    return render_template('equipment.html', equipment=[], temp_message=temp_message)

@app.route('/equipment/add', methods=['POST'])
@csrf.exempt
@faculty_required
def add_equipment():
    try:
        name = request.form.get('name')
        category = request.form.get('category')
        serial_number = request.form.get('serial_number')
        condition_notes = request.form.get('condition_notes')
        image_path = None
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Check for duplicate serial number
            cursor.execute("SELECT id FROM equipment WHERE serial_number = %s", (serial_number,))
            if cursor.fetchone():
                return jsonify(success=False, 
                             message="Equipment with this serial number already exists!")
            
            # Process image if provided
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_path = f"images/{filename}"
            
            # Insert new equipment
            cursor.execute("""
                INSERT INTO equipment (name, category, serial_number, image_path, condition_notes, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, category, serial_number, image_path, condition_notes, 'available'))
            connection.commit()
            
            session['temp_message'] = {'type': 'success', 'text': 'Equipment added successfully!'}
            return jsonify(success=True)
            
    except Error as e:
        return jsonify(success=False, message=f"Database error: {str(e)}")
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/equipment/<int:id>', methods=['GET'])
@faculty_required
def get_equipment(id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM equipment WHERE id = %s", (id,))
            equipment = cursor.fetchone()
            if equipment:
                return jsonify(equipment)
            else:
                return jsonify({'error': 'Equipment not found'}), 404
        except Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()
    return jsonify({'error': 'Database connection failed'}), 500

@app.route('/equipment/update/<int:id>', methods=['POST'])
@faculty_required
def update_equipment(id):
    name = request.form.get('name')
    category = request.form.get('category')
    serial_number = request.form.get('serial_number')
    condition_notes = request.form.get('condition_notes')
    status = request.form.get('status')
    
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_path = f"images/{filename}"
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            if image_path:
                cursor.execute("""
                    UPDATE equipment 
                    SET name = %s, category = %s, serial_number = %s, image_path = %s, condition_notes = %s, status = %s
                    WHERE id = %s
                """, (name, category, serial_number, image_path, condition_notes, status, id))
            else:
                cursor.execute("""
                    UPDATE equipment 
                    SET name = %s, category = %s, serial_number = %s, condition_notes = %s, status = %s
                    WHERE id = %s
                """, (name, category, serial_number, condition_notes, status, id))
            connection.commit()
            flash("Equipment updated successfully!", "success")
            return jsonify(success=True, message="Equipment updated successfully!")
        except Error as e:
            flash(f"Error: {e}", "error")
            return jsonify(success=False, message=f"Error: {e}")
        finally:
            connection.close()
    return jsonify(success=False, message="Database connection failed")

@app.route('/equipment/delete/<int:id>', methods=['POST'])
@faculty_required
def delete_equipment(id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM equipment WHERE id = %s", (id,))
            connection.commit()
            flash("Equipment deleted successfully!", "success")
            return jsonify(success=True, message="Equipment deleted successfully!")
        except Error as e:
            flash(f"Error: {e}", "error")
            return jsonify(success=False, message=f"Error: {e}")
        finally:
            connection.close()
    return jsonify(success=False, message="Database connection failed")

@app.route('/borrow', methods=['GET', 'POST'])
@faculty_required
def borrow_equipment():
    if request.method == 'POST':
        try:
            equipment_id = request.form.get('equipment_id')
            borrower_name = request.form.get('borrower_name')
            room_number = request.form.get('room_number')
            contact_number = request.form.get('contact_number')
            expected_return_date = request.form.get('expected_return_date')
            
            if not all([equipment_id, borrower_name, room_number, contact_number, expected_return_date]):
                return jsonify({
                    'success': False,
                    'message': 'All fields are required'
                })
            
            connection = get_db_connection()
            if not connection:
                return jsonify({
                    'success': False,
                    'message': 'Database connection failed'
                })

            try:
                cursor = connection.cursor(dictionary=True)
                
                # Check if equipment is available
                cursor.execute("SELECT status FROM equipment WHERE id = %s", (equipment_id,))
                equipment = cursor.fetchone()
                
                if not equipment or equipment['status'] != 'available':
                    return jsonify({
                        'success': False,
                        'message': 'Equipment is not available for borrowing'
                    })
                
                # Insert new borrowing record
                cursor.execute("""
                    INSERT INTO borrowers 
                    (equipment_id, borrower_name, room_number, contact_number, 
                     expected_return_date, status, borrow_date)
                    VALUES (%s, %s, %s, %s, %s, 'approved', NOW())
                """, (equipment_id, borrower_name, room_number, contact_number, expected_return_date))
                
                # Update equipment status
                cursor.execute("UPDATE equipment SET status = 'borrowed' WHERE id = %s", (equipment_id,))
                
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Equipment borrowed successfully!'
                })
                
            except mysql.connector.Error as e:
                connection.rollback()
                return jsonify({
                    'success': False,
                    'message': f'Database error: {str(e)}'
                })
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            })
            
    if request.method == 'GET':
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # Get available equipment for the dropdown
            cursor.execute("""
                SELECT id, name 
                FROM equipment 
                WHERE status = 'available' 
                ORDER BY name ASC
            """)
            available_equipment = cursor.fetchall()

            page = request.args.get('page', 1, type=int)
            search = request.args.get('search', '')
            year = request.args.get('year', '')
            month = request.args.get('month', '')
            day = request.args.get('day', '')
            per_page = 10

            # Build WHERE clause
            where_conditions = ["1=1"]
            params = []
            
            if search:
                where_conditions.append("(b.borrower_name LIKE %s OR e.name LIKE %s)")
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            if year:
                where_conditions.append("YEAR(b.borrow_date) = %s")
                params.append(year)
            
            if month:
                where_conditions.append("MONTH(b.borrow_date) = %s")
                params.append(month)
            
            if day:
                where_conditions.append("DAY(b.borrow_date) = %s")
                params.append(day)
            
            where_clause = " AND ".join(where_conditions)

            # Get total count
            count_query = f"""
                SELECT COUNT(*) as total 
                FROM borrowers b
                JOIN equipment e ON b.equipment_id = e.id
                WHERE {where_clause}
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']

            # Calculate pagination
            offset = (page - 1) * per_page
            
            # Get paginated data
            query = f"""
                SELECT b.*, e.name as equipment_name
                FROM borrowers b
                JOIN equipment e ON b.equipment_id = e.id
                WHERE {where_clause}
                ORDER BY b.borrow_date DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, params + [per_page, offset])
            borrowers = cursor.fetchall()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'borrowers': borrowers,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'start': offset + 1,
                    'end': min(offset + per_page, total),
                    'has_more': (offset + per_page) < total
                })

            return render_template('borrow_form.html',
                                equipment=available_equipment,  # Add this line
                                borrowers=borrowers,
                                page=page,
                                per_page=per_page,
                                total_borrowers=total)

        except Exception as e:
            print(f"Error: {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': str(e)}), 500
        try:
            equipment_id = request.form.get('equipment_id')
            borrower_name = request.form.get('borrower_name')
            room_number = request.form.get('room_number')
            contact_number = request.form.get('contact_number')
            expected_return_date = request.form.get('expected_return_date')
            
            if not all([equipment_id, borrower_name, room_number, contact_number, expected_return_date]):
                return jsonify({
                    'success': False,
                    'message': 'All fields are required'
                })
            
            connection = get_db_connection()
            if connection:
                try:
                    cursor = connection.cursor(dictionary=True)
                    
                    # Check if equipment is available
                    cursor.execute("SELECT status FROM equipment WHERE id = %s", (equipment_id,))
                    equipment = cursor.fetchone()
                    
                    if not equipment or equipment['status'] != 'available':
                        return jsonify({
                            'success': False,
                            'message': 'Equipment is not available for borrowing.'
                        })
                    
                    # Insert new borrowing record
                    cursor.execute("""
                        INSERT INTO borrowers 
                        (equipment_id, borrower_name, room_number, contact_number, 
                         expected_return_date, status, borrow_date)
                        VALUES (%s, %s, %s, %s, %s, 'approved', NOW())
                    """, (equipment_id, borrower_name, room_number, contact_number, expected_return_date))
                    
                    # Update equipment status
                    cursor.execute("UPDATE equipment SET status = 'borrowed' WHERE id = %s", (equipment_id,))
                    
                    connection.commit()
                    
                    return jsonify({
                        'success': True,
                        'message': 'Equipment borrowed successfully!'
                    })
                    
                except Error as e:
                    return jsonify({
                        'success': False,
                        'message': f'Database error: {str(e)}'
                    })
                finally:
                    cursor.close()
                    connection.close()
        
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            })
    
    if request.method == 'GET':
        try:
            page = request.args.get('page', 1, type=int)
            search = request.args.get('search', '')
            year = request.args.get('year', '')
            month = request.args.get('month', '')
            day = request.args.get('day', '')
            per_page = 10

            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # Get available equipment for the form - Add this query
            cursor.execute("SELECT id, name FROM equipment WHERE status = 'available'")
            available_equipment = cursor.fetchall()

            # Build WHERE clause
            where_conditions = ["1=1"]
            params = []
            
            if search:
                where_conditions.append("""
                    (b.borrower_name LIKE %s 
                     OR b.student_id LIKE %s 
                     OR e.name LIKE %s)
                """)
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])
            
            if year:
                where_conditions.append("YEAR(b.borrow_date) = %s")
                params.append(int(year))
            
            if month:
                where_conditions.append("MONTH(b.borrow_date) = %s")
                params.append(int(month))
            
            if day:
                where_conditions.append("DAY(b.borrow_date) = %s")
                params.append(int(day))
            
            where_clause = " AND ".join(where_conditions)
            
            # Get total count
            count_query = f"""
                SELECT COUNT(*) as total 
                FROM borrowers b
                JOIN equipment e ON b.equipment_id = e.id
                WHERE {where_clause}
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            # Get paginated results
            offset = (page - 1) * per_page
            query = f"""
                SELECT b.*, e.name as equipment_name
                FROM borrowers b
                JOIN equipment e ON b.equipment_id = e.id
                WHERE {where_clause}
                ORDER BY b.borrow_date DESC
                LIMIT %s OFFSET %s
            """
            params.extend([per_page, offset])
            cursor.execute(query, params)
            borrowers = cursor.fetchall()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                formatted_borrowers = []
                for borrower in borrowers:
                    b = dict(borrower)
                    b['borrow_date'] = borrower['borrow_date'].strftime('%Y-%m-%d %H:%M:%S')
                    if borrower['expected_return_date']:
                        b['expected_return_date'] = borrower['expected_return_date'].strftime('%Y-%m-%d %H:%M:%S')
                    formatted_borrowers.append(b)

                return jsonify({
                    'borrowers': formatted_borrowers,
                    'total': total,
                    'page': page,
                    'start': offset + 1 if total > 0 else 0,
                    'end': min((page * per_page), total),
                    'has_more': (page * per_page) < total
                })

            return render_template('borrow_form.html',
                                equipment=available_equipment,  # Make sure to pass this
                                borrowers=borrowers,
                                page=page,
                                total_borrowers=total,
                                per_page=per_page)

        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': str(e)}), 500
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for('dashboard'))

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get available equipment for the form
            cursor.execute("SELECT id, name FROM equipment WHERE status = 'available'")
            available_equipment = cursor.fetchall()
            
            # Get total count of borrowers
            cursor.execute("SELECT COUNT(*) as total FROM borrowers")
            total_borrowers = cursor.fetchone()['total']
            
            # Calculate total pages
            total_pages = (total_borrowers + per_page - 1) // per_page
            
            # Get paginated borrowers list
            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT b.*, e.name as equipment_name
                FROM borrowers b
                JOIN equipment e ON b.equipment_id = e.id
                ORDER BY b.borrow_date DESC
                LIMIT %s OFFSET %s
            """, (per_page, offset))
            borrowers = cursor.fetchall()
            
            if request.method == 'POST':
                equipment_id = request.form.get('equipment_id')
                borrower_name = request.form.get('borrower_name')
                student_id = request.form.get('student_id')
                course = request.form.get('course')
                contact_number = request.form.get('contact_number')
                expected_return_date = request.form.get('expected_return_date')
                
                connection = get_db_connection()
                if connection:
                    try:
                        cursor = connection.cursor(dictionary=True)
                        
                        # Check if equipment is available
                        cursor.execute("SELECT status FROM equipment WHERE id = %s", (equipment_id,))
                        equipment = cursor.fetchone()
                        if not equipment or equipment['status'] != 'available':
                            flash("Equipment is not available for borrowing.", "error")
                            return redirect(url_for('borrow_equipment'))
                        
                        # Insert new borrowing record
                        cursor.execute("""
                            INSERT INTO borrowers 
                            (equipment_id, borrower_name, student_id, course, contact_number, expected_return_date, status)
                            VALUES (%s, %s, %s, %s, %s, %s, 'approved')
                        """, (equipment_id, borrower_name, student_id, course, contact_number, expected_return_date))
                        
                        # Update equipment status
                        cursor.execute("UPDATE equipment SET status = 'borrowed' WHERE id = %s", (equipment_id,))
                        
                        connection.commit()
                        flash("Equipment borrowed successfully!", "success")
                        return redirect(url_for('dashboard'))
                    except Error as e:
                        flash(f"An error occurred: {e}", "error")
                    finally:
                        cursor.close()
                        connection.close()
            
            return render_template('borrow_form.html',
                                equipment=available_equipment,
                                borrowers=borrowers,
                                page=page,
                                total_pages=total_pages,
                                total_borrowers=total_borrowers,
                                per_page=per_page)
                                
        finally:
            cursor.close()
            connection.close()
    
    flash("Unable to fetch data.", "error")
    return redirect(url_for('dashboard'))

@app.route('/borrowers')
@faculty_required
def borrowers_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get total count
            cursor.execute("SELECT COUNT(*) as total FROM borrowers")
            total_borrowers = cursor.fetchone()['total']
            
            # Calculate total pages
            total_pages = (total_borrowers + per_page - 1) // per_page
            
            # Get paginated results
            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT b.*, e.name as equipment_name
                FROM borrowers b
                JOIN equipment e ON b.equipment_id = e.id
                ORDER BY b.borrow_date DESC
                LIMIT %s OFFSET %s
            """, (per_page, offset))
            borrowers = cursor.fetchall()
            
            return render_template('borrowers_list.html',
                                borrowers=borrowers,
                                page=page,
                                total_pages=total_pages,
                                total_borrowers=total_borrowers,
                                per_page=per_page)
        finally:
            cursor.close()
            connection.close()
    
    flash("Unable to fetch borrowers list.", "error")
    return redirect(url_for('dashboard'))

@app.route('/return/<int:borrower_id>', methods=['POST'])
@faculty_required
def return_equipment(borrower_id):
    # Add logging
    app.logger.info(f"Attempting to return equipment for borrower ID: {borrower_id}")
    
    connection = None
    cursor = None
    try:
        # Validate input
        if not isinstance(borrower_id, int) or borrower_id <= 0:
            app.logger.warning(f"Invalid borrower ID: {borrower_id}")
            return jsonify({
                'success': False,
                'message': "Invalid borrower ID"
            }), 400

        # Establish database connection
        connection = get_db_connection()
        if not connection:
            app.logger.error("Failed to establish database connection")
            return jsonify({
                'success': False,
                'message': "Database connection failed"
            }), 500

        # Create cursor with dictionary support
        cursor = connection.cursor(dictionary=True)

        # Start a transaction
        connection.start_transaction()

        # Detailed query to get borrower and equipment details with locking
        cursor.execute("""
            SELECT 
                b.id, 
                b.equipment_id, 
                b.status, 
                e.name as equipment_name, 
                e.status as equipment_status
            FROM borrowers b
            JOIN equipment e ON b.equipment_id = e.id
            WHERE b.id = %s
            FOR UPDATE
        """, (borrower_id,))
        
        # Fetch the borrower record
        borrower = cursor.fetchone()
        
        # Check if borrower exists
        if not borrower:
            connection.rollback()
            app.logger.warning(f"No borrower found with ID: {borrower_id}")
            return jsonify({
                'success': False,
                'message': "Borrower record not found"
            }), 404
        
        # Check if already returned
        if borrower['status'] == 'returned':
            connection.rollback()
            app.logger.warning(f"Equipment already returned for borrower ID: {borrower_id}")
            return jsonify({
                'success': False,
                'message': "Equipment has already been returned"
            }), 400

        # Check equipment status
        if borrower['equipment_status'] != 'borrowed':
            connection.rollback()
            app.logger.warning(f"Invalid equipment status: {borrower['equipment_status']} for borrower ID: {borrower_id}")
            return jsonify({
                'success': False,
                'message': f"Cannot return {borrower['equipment_name']}. Current status is not 'borrowed'."
            }), 400

        # Update borrower record
        cursor.execute("""
            UPDATE borrowers 
            SET 
                status = 'returned',
                actual_return_date = NOW()
            WHERE id = %s
        """, (borrower_id,))
        
        # Verify borrower update
        if cursor.rowcount == 0:
            connection.rollback()
            app.logger.error(f"Failed to update borrower status for ID: {borrower_id}")
            return jsonify({
                'success': False,
                'message': "Failed to update borrower status"
            }), 500

        # Update equipment status
        cursor.execute("""
            UPDATE equipment 
            SET status = 'available'
            WHERE id = %s
        """, (borrower['equipment_id'],))
        
        # Verify equipment update
        if cursor.rowcount == 0:
            connection.rollback()
            app.logger.error(f"Failed to update equipment status for ID: {borrower['equipment_id']}")
            return jsonify({
                'success': False,
                'message': f"Failed to mark {borrower['equipment_name']} as available"
            }), 500

        # Commit the transaction
        connection.commit()
        
        app.logger.info(f"Successfully returned equipment for borrower ID: {borrower_id}")
        return jsonify({
            'success': True,
            'message': f"{borrower['equipment_name']} returned successfully!"
        })

    except mysql.connector.Error as db_error:
        # Detailed database error handling
        if connection and connection.in_transaction:
            connection.rollback()
        app.logger.error(f"Database error during return: {str(db_error)}")
        return jsonify({
            'success': False,
            'message': f"Database error: {str(db_error)}"
        }), 500

    except Exception as e:
        # Catch-all for unexpected errors
        if connection and connection.in_transaction:
            connection.rollback()
        app.logger.error(f"Unexpected error during equipment return: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': "An unexpected error occurred. Please try again."
        }), 500

    finally:
        # Ensure resources are always closed
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/generate_report', methods=['GET', 'POST'])
@faculty_required
def generate_report():
    try:
        search = request.args.get('search', '')
        year = request.args.get('year', '')
        month = request.args.get('month', '')
        day = request.args.get('day', '')

        connection = get_db_connection()
        if not connection:
            raise Exception("Database connection failed")

        cursor = connection.cursor(dictionary=True)

        # Build query with parameters
        query = """
            SELECT 
                b.borrower_name,
                e.name as equipment_name,
                b.room_number,
                b.contact_number,
                b.borrow_date,
                b.expected_return_date,
                b.actual_return_date,
                b.status
            FROM borrowers b
            JOIN equipment e ON b.equipment_id = e.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (b.borrower_name LIKE %s OR e.name LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        if year:
            query += " AND YEAR(b.borrow_date) = %s"
            params.append(year)
        if month:
            query += " AND MONTH(b.borrow_date) = %s"
            params.append(month)
        if day:
            query += " AND DAY(b.borrow_date) = %s"
            params.append(day)

        query += " ORDER BY b.borrow_date DESC"
        
        cursor.execute(query, params)
        borrowers = cursor.fetchall()

        if not borrowers:
            flash("No data available for the selected filters", "warning")
            return redirect(url_for('borrow_equipment'))

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        elements = []
        styles = getSampleStyleSheet()

        # Add title
        title = Paragraph(
            "Equipment Borrowing Report",
            ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1
            )
        )
        elements.append(title)
        elements.append(Spacer(1, 20))

        # Add metadata
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Paragraph(f"Total Records: {len(borrowers)}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Create table
        table_data = [['Borrower', 'Equipment', 'Room', 'Contact', 'Borrow Date', 'Expected Return', 'Status']]
        for borrower in borrowers:
            table_data.append([
                borrower['borrower_name'],
                borrower['equipment_name'],
                borrower['room_number'],
                borrower['contact_number'],
                borrower['borrow_date'].strftime('%Y-%m-%d'),
                borrower['expected_return_date'].strftime('%Y-%m-%d'),
                borrower['status'].upper()
            ])

        # Set column widths
        col_widths = [120, 120, 80, 80, 80, 80, 80]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Style the table
        table.setStyle(TableStyle([
            # Headers
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Row styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8)
        ]))

        elements.append(table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        # Return PDF file
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'borrowing_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )

    except Exception as e:
        print(f"Report generation error: {str(e)}")  # Debug print
        flash(f"Error generating report: {str(e)}", "error")
        return redirect(url_for('borrow_equipment'))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
            
@app.route('/bulk_borrow', methods=['POST'])
@faculty_required
def bulk_borrow():
    connection = None
    cursor = None
    try:
        borrower_name = request.form.get('borrower_name')
        room_number = request.form.get('room_number')
        contact_number = request.form.get('contact_number')
        expected_return_date = request.form.get('expected_return_date')
        equipment_ids = request.form.getlist('equipment_ids[]')

        if not all([borrower_name, room_number, contact_number, expected_return_date, equipment_ids]):
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            })

        connection = get_db_connection()
        if not connection:
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            })

        cursor = connection.cursor(dictionary=True)
        connection.start_transaction()

        # Verify all equipment is available
        cursor.execute("""
            SELECT id, name, status 
            FROM equipment 
            WHERE id IN (%s)
        """ % ','.join(['%s'] * len(equipment_ids)), equipment_ids)
        
        equipment_status = cursor.fetchall()
        unavailable = [e['name'] for e in equipment_status if e['status'] != 'available']
        
        if unavailable:
            connection.rollback()
            return jsonify({
                'success': False,
                'message': f"Following equipment not available: {', '.join(unavailable)}"
            })

        # Process each equipment
        for equipment_id in equipment_ids:
            # Create borrowing record
            cursor.execute("""
                INSERT INTO borrowers 
                (equipment_id, borrower_name, room_number, contact_number, 
                 expected_return_date, status, borrow_date)
                VALUES (%s, %s, %s, %s, %s, 'approved', NOW())
            """, (equipment_id, borrower_name, room_number, contact_number, expected_return_date))

            # Update equipment status
            cursor.execute("""
                UPDATE equipment 
                SET status = 'borrowed' 
                WHERE id = %s
            """, (equipment_id,))

        connection.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully borrowed {len(equipment_ids)} equipment items'
        })

    except Exception as e:
        if connection:
            connection.rollback()
        app.logger.error(f"Bulk borrow error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        })

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            
@app.route('/api/notifications/pending')
@faculty_required
def get_pending_notifications():
    """Get pending return notifications based on due dates"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database connection failed'})

        cursor = connection.cursor(dictionary=True)
        
        # Get borrowers with upcoming or overdue returns
        cursor.execute("""
            SELECT 
                b.id,
                b.borrower_name,
                b.room_number,
                b.contact_number,
                b.borrow_date,
                b.expected_return_date,
                e.name as equipment_name,
                e.serial_number,
                TIMESTAMPDIFF(HOUR, NOW(), b.expected_return_date) as hours_remaining,
                CASE 
                    WHEN b.expected_return_date < NOW() THEN 'overdue'
                    WHEN TIMESTAMPDIFF(HOUR, NOW(), b.expected_return_date) <= 1 THEN 'due_soon'
                    WHEN TIMESTAMPDIFF(HOUR, NOW(), b.expected_return_date) <= 24 THEN 'upcoming'
                    ELSE 'normal'
                END as status
            FROM borrowers b
            JOIN equipment e ON b.equipment_id = e.id
            WHERE b.status = 'approved' 
            AND b.actual_return_date IS NULL
            AND (
                b.expected_return_date < NOW() OR 
                TIMESTAMPDIFF(HOUR, NOW(), b.expected_return_date) <= 24
            )
            ORDER BY 
                CASE 
                    WHEN b.expected_return_date < NOW() THEN 1
                    WHEN TIMESTAMPDIFF(HOUR, NOW(), b.expected_return_date) <= 1 THEN 2
                    WHEN TIMESTAMPDIFF(HOUR, NOW(), b.expected_return_date) <= 24 THEN 3
                    ELSE 4
                END,
                b.expected_return_date ASC
        """)
        
        notifications = cursor.fetchall()
        
        # Add custom messages based on status
        for notification in notifications:
            hours = notification['hours_remaining']
            if notification['status'] == 'overdue':
                if hours <= -24:
                    days_overdue = abs(int(hours)) // 24
                    notification['message'] = f"OVERDUE by {days_overdue} day{'s' if days_overdue > 1 else ''}!"
                else:
                    notification['message'] = f"OVERDUE by {abs(int(hours))} hour{'s' if abs(int(hours)) > 1 else ''}!"
                notification['urgency_level'] = 'overdue'
            elif notification['status'] == 'due_soon':
                notification['message'] = "Due within 1 hour!"
                notification['urgency_level'] = 'critical'
            elif notification['status'] == 'upcoming':
                notification['message'] = f"Due in {max(1, int(hours))} hour{'s' if int(hours) > 1 else ''}"
                notification['urgency_level'] = 'warning'
            else:
                notification['message'] = "Due soon"
                notification['urgency_level'] = 'normal'
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })
        
    except Exception as e:
        app.logger.error(f"Error fetching notifications: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/api/notifications/mark_read', methods=['POST'])
@faculty_required
def mark_notifications_read():
    """Mark notifications as read (optional feature)"""
    try:
        # For now, we'll just return success since notifications are based on real-time data
        # You could extend this to track read status in a separate table if needed
        
        return jsonify({
            'success': True, 
            'message': 'Notifications marked as read',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error marking notifications as read: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/notifications/summary')
@faculty_required
def get_notification_summary():
    """Get summary of notification counts by urgency level"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database connection failed'})

        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN b.expected_return_date < NOW() THEN 1 ELSE 0 END) as overdue_count,
                SUM(CASE WHEN TIMESTAMPDIFF(HOUR, NOW(), b.expected_return_date) <= 1 
                    AND b.expected_return_date >= NOW() THEN 1 ELSE 0 END) as due_soon_count,
                SUM(CASE WHEN TIMESTAMPDIFF(HOUR, NOW(), b.expected_return_date) <= 24 
                    AND TIMESTAMPDIFF(HOUR, NOW(), b.expected_return_date) > 1 THEN 1 ELSE 0 END) as upcoming_count,
                COUNT(*) as total_active
            FROM borrowers b
            WHERE b.status = 'approved' 
            AND b.actual_return_date IS NULL
        """)
        
        summary = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        app.logger.error(f"Error fetching notification summary: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/api/notifications/test')
@faculty_required
def test_notifications():
    """Test endpoint to create sample overdue notifications (for development only)"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database connection failed'})

        cursor = connection.cursor(dictionary=True)
        
        # Create a test overdue entry (uncomment for testing)
        # cursor.execute("""
        #     INSERT INTO borrowers 
        #     (equipment_id, borrower_name, room_number, contact_number, 
        #      expected_return_date, status, borrow_date)
        #     SELECT 
        #         e.id, 
        #         'Test User', 
        #         'Test Room', 
        #         '1234567890',
        #         DATE_SUB(NOW(), INTERVAL 2 HOUR),
        #         'approved',
        #         DATE_SUB(NOW(), INTERVAL 1 DAY)
        #     FROM equipment e 
        #     WHERE e.status = 'available' 
        #     LIMIT 1
        # """)
        # connection.commit()
        
        # Get current notifications for testing
        cursor.execute("""
            SELECT COUNT(*) as total_notifications
            FROM borrowers b
            WHERE b.status = 'approved' 
            AND b.actual_return_date IS NULL
            AND (
                b.expected_return_date < NOW() OR 
                TIMESTAMPDIFF(HOUR, NOW(), b.expected_return_date) <= 24
            )
        """)
        
        result = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'message': 'Test completed',
            'current_notifications': result['total_notifications'],
            'test_time': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error in test notifications: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# Background task for logging overdue items
def check_and_log_overdue_items():
    """Background task to check for overdue items and log them"""
    try:
        connection = get_db_connection()
        if not connection:
            return

        cursor = connection.cursor(dictionary=True)
        
        # Get severely overdue items (more than 24 hours late)
        cursor.execute("""
            SELECT 
                b.id,
                b.borrower_name,
                b.contact_number,
                b.room_number,
                e.name as equipment_name,
                TIMESTAMPDIFF(HOUR, b.expected_return_date, NOW()) as hours_overdue
            FROM borrowers b
            JOIN equipment e ON b.equipment_id = e.id
            WHERE b.status = 'approved' 
            AND b.actual_return_date IS NULL
            AND b.expected_return_date < DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY hours_overdue DESC
        """)
        
        overdue_items = cursor.fetchall()
        
        # Log overdue items
        for item in overdue_items:
            app.logger.warning(
                f"OVERDUE ALERT: {item['borrower_name']} (Room: {item['room_number']}, "
                f"Contact: {item['contact_number']}) has {item['equipment_name']} "
                f"overdue by {item['hours_overdue']} hours"
            )
            
        if overdue_items:
            app.logger.info(f"Total overdue items: {len(overdue_items)}")
        
        return len(overdue_items)
        
    except Exception as e:
        app.logger.error(f"Error in overdue items check: {str(e)}")
        return 0
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# Optional: Add this to your existing routes or create a new one for manual checking
@app.route('/api/notifications/check_overdue')
@faculty_required
def manual_overdue_check():
    """Manual endpoint to check overdue items"""
    try:
        overdue_count = check_and_log_overdue_items()
        return jsonify({
            'success': True,
            'overdue_count': overdue_count,
            'message': f'Found {overdue_count} overdue items',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
            
if __name__ == '__main__':
    import socket
    from datetime import timedelta
    
    def get_local_ip():
        """Get the local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return socket.gethostbyname(socket.gethostname())

    # Get IP and port
    port = 5000
    local_ip = get_local_ip()

    # Print server information
    print("\n" + "="*60)
    print("🚀 Faculty Borrowing Logbook System - Development Server")
    print("="*60)
    print("\n✨ Server Status: Development Mode")
    print("\n📡 Access URLs:")
    print(f"   • Local:     http://localhost:{port}")
    print(f"   • Network:   http://{local_ip}:{port}")
    print("\n🛠️  Development Tools:")
    print("   • Debug Mode: Enabled")
    print("   • Auto Reload: Enabled")
    print("   • Error Reporting: Detailed")
    print("\n⚠️  Important Notes:")
    print("   • This is a development server only")
    print("   • Do not use it in a production environment")
    print("   • Press CTRL+C to stop the server")
    print("="*60 + "\n")

    # Basic security settings
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1)
    )
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True,
        threaded=True
    )