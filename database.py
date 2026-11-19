import sqlite3
import os
import json
import csv
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

def get_db_connection():
    """Establish and return a connection to the SQLite database with row factory."""
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize all database tables and seed default admin user and initial students."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table 1: users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table 2: students
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            attendance REAL NOT NULL,
            study_hours REAL NOT NULL,
            marks REAL NOT NULL,
            predicted_result TEXT DEFAULT 'Not Evaluated',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table 3: predictions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            attendance REAL NOT NULL,
            study_hours REAL NOT NULL,
            marks REAL NOT NULL,
            predicted_result TEXT NOT NULL,
            probability REAL DEFAULT 0.0,
            model_name TEXT NOT NULL,
            prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table 4: model_results
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            accuracy REAL NOT NULL,
            precision REAL NOT NULL,
            recall REAL NOT NULL,
            f1_score REAL NOT NULL,
            confusion_matrix TEXT NOT NULL,
            is_best INTEGER DEFAULT 0,
            trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed Default Admin if not exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (Config.DEFAULT_ADMIN_USERNAME,))
    admin = cursor.fetchone()
    if not admin:
        hashed_pw = generate_password_hash(Config.DEFAULT_ADMIN_PASSWORD)
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (Config.DEFAULT_ADMIN_USERNAME, hashed_pw)
        )

    # Seed initial students from sample_students.csv if students table is empty
    cursor.execute("SELECT COUNT(*) as count FROM students")
    count_row = cursor.fetchone()
    if count_row['count'] == 0 and os.path.exists(Config.SAMPLE_DATASET_PATH):
        try:
            with open(Config.SAMPLE_DATASET_PATH, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                initial_records = []
                initial_predictions = []
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                for row in reader:
                    sid = row['student_id'].strip()
                    att = float(row['attendance'])
                    hours = float(row['study_hours'])
                    marks = float(row['marks'])
                    res = row['result'].strip()
                    pred_res = 'Likely to Pass' if res.lower() == 'pass' else 'May Need Support'
                    initial_records.append((sid, att, hours, marks, pred_res, now))
                    
                    # Also pre-populate prediction history for rich demonstration
                    initial_predictions.append((sid, att, hours, marks, pred_res, 0.85 if pred_res == 'Likely to Pass' else 0.82, 'Random Forest Classifier', now))
                
                cursor.executemany('''
                    INSERT OR IGNORE INTO students (student_id, attendance, study_hours, marks, predicted_result, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', initial_records)
                
                cursor.executemany('''
                    INSERT INTO predictions (student_id, attendance, study_hours, marks, predicted_result, probability, model_name, prediction_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', initial_predictions)
        except Exception as e:
            print(f"Notice: Initial students seeding from CSV skipped: {e}")

    conn.commit()
    conn.close()

# ----------------- USER AUTHENTICATION -----------------

def get_user_by_username(username):
    """Retrieve user record by username."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

def verify_user(username, password):
    """Verify user credentials with password hash."""
    user = get_user_by_username(username)
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None

# ----------------- STUDENT CRUD OPERATIONS -----------------

def add_student(student_id, attendance, study_hours, marks, predicted_result='Not Evaluated'):
    """Add a new student record."""
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO students (student_id, attendance, study_hours, marks, predicted_result)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_id.strip().upper(), float(attendance), float(study_hours), float(marks), predicted_result))
        conn.commit()
        return True, "Student added successfully."
    except sqlite3.IntegrityError:
        return False, f"Student ID '{student_id}' already exists."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_all_students(search=None, filter_category=None, sort_by='student_id', order='ASC'):
    """Retrieve students with optional search, filtering, and sorting."""
    conn = get_db_connection()
    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if search:
        query += " AND student_id LIKE ?"
        params.append(f"%{search.strip()}%")

    if filter_category and filter_category != 'all':
        query += " AND predicted_result = ?"
        params.append(filter_category)

    # Valid sorting columns to prevent SQL injection
    valid_cols = {'student_id': 'student_id', 'attendance': 'attendance', 'study_hours': 'study_hours', 'marks': 'marks', 'predicted_result': 'predicted_result', 'created_at': 'created_at'}
    order_col = valid_cols.get(sort_by, 'student_id')
    order_dir = 'DESC' if str(order).upper() == 'DESC' else 'ASC'

    query += f" ORDER BY {order_col} {order_dir}"

    students = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(s) for s in students]

def get_student_by_id(student_id):
    """Fetch a single student by student_id."""
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE student_id = ?", (student_id.strip().upper(),)).fetchone()
    conn.close()
    return dict(student) if student else None

def update_student(student_id, attendance, study_hours, marks, predicted_result=None):
    """Update student record."""
    conn = get_db_connection()
    try:
        if predicted_result:
            conn.execute('''
                UPDATE students
                SET attendance = ?, study_hours = ?, marks = ?, predicted_result = ?
                WHERE student_id = ?
            ''', (float(attendance), float(study_hours), float(marks), predicted_result, student_id.strip().upper()))
        else:
            conn.execute('''
                UPDATE students
                SET attendance = ?, study_hours = ?, marks = ?
                WHERE student_id = ?
            ''', (float(attendance), float(study_hours), float(marks), student_id.strip().upper()))
        conn.commit()
        return True, "Student updated successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_student(student_id):
    """Delete a student record."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM students WHERE student_id = ?", (student_id.strip().upper(),))
        conn.commit()
        return True, "Student deleted successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# ----------------- PREDICTIONS HISTORY -----------------

def add_prediction(student_id, attendance, study_hours, marks, predicted_result, probability, model_name):
    """Record a prediction in the predictions table and update the student's status."""
    conn = get_db_connection()
    try:
        # Add to predictions history
        conn.execute('''
            INSERT INTO predictions (student_id, attendance, study_hours, marks, predicted_result, probability, model_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_id.strip().upper(), float(attendance), float(study_hours), float(marks), predicted_result, float(probability), model_name))
        
        # Update or Insert into students table so student records stay up-to-date
        conn.execute('''
            INSERT INTO students (student_id, attendance, study_hours, marks, predicted_result)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET
                attendance = excluded.attendance,
                study_hours = excluded.study_hours,
                marks = excluded.marks,
                predicted_result = excluded.predicted_result
        ''', (student_id.strip().upper(), float(attendance), float(study_hours), float(marks), predicted_result))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving prediction: {e}")
        return False
    finally:
        conn.close()

def get_all_predictions(search=None, filter_result=None, sort_by='prediction_date', order='DESC', limit=None):
    """Retrieve prediction records with optional filtering and pagination limit."""
    conn = get_db_connection()
    query = "SELECT * FROM predictions WHERE 1=1"
    params = []

    if search:
        query += " AND student_id LIKE ?"
        params.append(f"%{search.strip()}%")

    if filter_result and filter_result != 'all':
        query += " AND predicted_result = ?"
        params.append(filter_result)

    valid_cols = {'student_id': 'student_id', 'attendance': 'attendance', 'study_hours': 'study_hours', 'marks': 'marks', 'predicted_result': 'predicted_result', 'prediction_date': 'prediction_date', 'probability': 'probability'}
    order_col = valid_cols.get(sort_by, 'prediction_date')
    order_dir = 'ASC' if str(order).upper() == 'ASC' else 'DESC'

    query += f" ORDER BY {order_col} {order_dir}"

    if limit:
        query += f" LIMIT {int(limit)}"

    predictions = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(p) for p in predictions]

def delete_prediction(prediction_id):
    """Delete a prediction record by its ID."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM predictions WHERE id = ?", (int(prediction_id),))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def clear_all_predictions():
    """Clear all records from prediction history."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM predictions")
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

# ----------------- MODEL RESULTS STORAGE -----------------

def save_model_results(results_list):
    """Save trained model evaluation results and mark the best model."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Find best model index based on F1-score (or accuracy if tied)
        best_f1 = -1
        best_idx = 0
        for i, res in enumerate(results_list):
            if res['f1_score'] > best_f1:
                best_f1 = res['f1_score']
                best_idx = i

        # Clear previous active records to present latest training results
        cursor.execute("DELETE FROM model_results")

        for i, res in enumerate(results_list):
            is_best = 1 if i == best_idx else 0
            cm_str = json.dumps(res.get('confusion_matrix', []))
            cursor.execute('''
                INSERT INTO model_results (model_name, accuracy, precision, recall, f1_score, confusion_matrix, is_best)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (res['model_name'], res['accuracy'], res['precision'], res['recall'], res['f1_score'], cm_str, is_best))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving model results: {e}")
        return False
    finally:
        conn.close()

def get_latest_model_results():
    """Retrieve the latest model comparison evaluation results."""
    conn = get_db_connection()
    results = conn.execute("SELECT * FROM model_results ORDER BY f1_score DESC").fetchall()
    conn.close()
    formatted = []
    for r in results:
        d = dict(r)
        try:
            d['confusion_matrix'] = json.loads(d['confusion_matrix'])
        except Exception:
            d['confusion_matrix'] = []
        formatted.append(d)
    return formatted

# ----------------- DASHBOARD & ANALYTICS QUERIES -----------------

def get_dashboard_stats():
    """Calculate and return key statistics for dashboard cards and charts."""
    conn = get_db_connection()
    
    # Total students
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    
    # Students likely to pass & needing support
    pass_count = conn.execute("SELECT COUNT(*) FROM students WHERE predicted_result = 'Likely to Pass'").fetchone()[0]
    support_count = conn.execute("SELECT COUNT(*) FROM students WHERE predicted_result = 'May Need Support'").fetchone()[0]
    unevaluated_count = conn.execute("SELECT COUNT(*) FROM students WHERE predicted_result NOT IN ('Likely to Pass', 'May Need Support')").fetchone()[0]
    
    # Averages
    avg_row = conn.execute("SELECT AVG(attendance) as avg_att, AVG(study_hours) as avg_hours, AVG(marks) as avg_marks FROM students").fetchone()
    avg_attendance = round(avg_row['avg_att'] or 0.0, 1)
    avg_study_hours = round(avg_row['avg_hours'] or 0.0, 1)
    avg_marks = round(avg_row['avg_marks'] or 0.0, 1)

    # Attendance distribution groups: <60%, 60-75%, 75-85%, >85%
    att_g1 = conn.execute("SELECT COUNT(*) FROM students WHERE attendance < 60").fetchone()[0]
    att_g2 = conn.execute("SELECT COUNT(*) FROM students WHERE attendance >= 60 AND attendance < 75").fetchone()[0]
    att_g3 = conn.execute("SELECT COUNT(*) FROM students WHERE attendance >= 75 AND attendance < 85").fetchone()[0]
    att_g4 = conn.execute("SELECT COUNT(*) FROM students WHERE attendance >= 85").fetchone()[0]

    # Marks distribution groups (out of 50): 0-19, 20-29, 30-39, 40-50
    marks_g1 = conn.execute("SELECT COUNT(*) FROM students WHERE marks < 20").fetchone()[0]
    marks_g2 = conn.execute("SELECT COUNT(*) FROM students WHERE marks >= 20 AND marks < 30").fetchone()[0]
    marks_g3 = conn.execute("SELECT COUNT(*) FROM students WHERE marks >= 30 AND marks < 40").fetchone()[0]
    marks_g4 = conn.execute("SELECT COUNT(*) FROM students WHERE marks >= 40").fetchone()[0]

    # Study hours groups: 0-2 hrs, 2-4 hrs, 4-6 hrs, 6+ hrs
    hours_g1 = conn.execute("SELECT COUNT(*) FROM students WHERE study_hours < 2").fetchone()[0]
    hours_g2 = conn.execute("SELECT COUNT(*) FROM students WHERE study_hours >= 2 AND study_hours < 4").fetchone()[0]
    hours_g3 = conn.execute("SELECT COUNT(*) FROM students WHERE study_hours >= 4 AND study_hours < 6").fetchone()[0]
    hours_g4 = conn.execute("SELECT COUNT(*) FROM students WHERE study_hours >= 6").fetchone()[0]

    # Recent predictions (last 6)
    recent_preds = conn.execute("SELECT * FROM predictions ORDER BY prediction_date DESC, id DESC LIMIT 6").fetchall()
    recent_preds_list = [dict(p) for p in recent_preds]

    conn.close()

    return {
        'total_students': total_students,
        'pass_count': pass_count,
        'support_count': support_count,
        'unevaluated_count': unevaluated_count,
        'avg_attendance': avg_attendance,
        'avg_study_hours': avg_study_hours,
        'avg_marks': avg_marks,
        'attendance_distribution': [att_g1, att_g2, att_g3, att_g4],
        'marks_distribution': [marks_g1, marks_g2, marks_g3, marks_g4],
        'hours_distribution': [hours_g1, hours_g2, hours_g3, hours_g4],
        'recent_predictions': recent_preds_list
    }

def get_analytics_data():
    """Retrieve full analytics datasets for reports and visualization."""
    stats = get_dashboard_stats()
    model_results = get_latest_model_results()
    
    # Calculate percentage rates
    total = stats['total_students']
    pass_pct = round((stats['pass_count'] / total * 100), 1) if total > 0 else 0
    support_pct = round((stats['support_count'] / total * 100), 1) if total > 0 else 0

    return {
        'stats': stats,
        'pass_pct': pass_pct,
        'support_pct': support_pct,
        'model_results': model_results
    }
