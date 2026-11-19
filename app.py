import os
import io
import csv
import json
from functools import wraps
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_file, send_from_directory, jsonify, Response
)
import pandas as pd
from werkzeug.utils import secure_filename

from config import Config
import database
from ml.train_model import train_and_evaluate_all_models, load_and_preprocess_data
from ml.predict import predict_student_performance

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Ensure required directories exist
os.makedirs(Config.DATASET_DIR, exist_ok=True)
os.makedirs(Config.MODELS_DIR, exist_ok=True)
os.makedirs(Config.EXPORTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)

# ----------------- AUTHENTICATION DECORATOR -----------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in with faculty credentials to access this system.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_global_data():
    """Inject active ML model name and year globally across all templates."""
    active_model = "Classification Pipeline"
    if os.path.exists(Config.MODEL_METADATA_PATH):
        try:
            with open(Config.MODEL_METADATA_PATH, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                active_model = meta.get('best_model_name', active_model)
        except Exception:
            pass
    return {
        'active_model_name': active_model,
        'current_year': datetime.now().year
    }

# ----------------- ROUTES: AUTHENTICATION -----------------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = database.verify_user(username, password)
        if user:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}! Faculty session started.', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('dashboard'))
        else:
            flash('Invalid username or password. Use demo account: admin / admin123', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been signed out successfully.', 'info')
    return redirect(url_for('login'))

# ----------------- ROUTE: PAGE 2 - DASHBOARD -----------------

@app.route('/dashboard')
@login_required
def dashboard():
    stats = database.get_dashboard_stats()
    return render_template('dashboard.html', stats=stats, active_page='dashboard')

# ----------------- ROUTE: PAGE 3 - PREDICTION -----------------

@app.route('/prediction', methods=['GET', 'POST'])
@login_required
def prediction():
    result = None
    form_data = {}

    # Pre-fill via GET params if coming from Student Management
    if request.method == 'GET':
        if 'student_id' in request.args:
            form_data = {
                'student_id': request.args.get('student_id', ''),
                'attendance': request.args.get('attendance', ''),
                'study_hours': request.args.get('study_hours', ''),
                'marks': request.args.get('marks', '')
            }

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip().upper()
        attendance = request.form.get('attendance', '').strip()
        study_hours = request.form.get('study_hours', '').strip()
        marks = request.form.get('marks', '').strip()

        form_data = {
            'student_id': student_id,
            'attendance': attendance,
            'study_hours': study_hours,
            'marks': marks
        }

        if not student_id or not attendance or not study_hours or not marks:
            flash('All input parameters (Student ID, Attendance, Study Hours, Marks) are required.', 'danger')
        else:
            prediction_output = predict_student_performance(attendance, study_hours, marks)
            if not prediction_output.get('success'):
                flash(prediction_output.get('error', 'Prediction could not be computed.'), 'danger')
            else:
                result = prediction_output
                # Save into SQLite predictions and update students table
                database.add_prediction(
                    student_id=student_id,
                    attendance=result['attendance'],
                    study_hours=result['study_hours'],
                    marks=result['marks'],
                    predicted_result=result['predicted_result'],
                    probability=result['probability'],
                    model_name=result['model_name']
                )
                flash(f"Prediction generated successfully for student {student_id}.", 'success')

    return render_template('prediction.html', result=result, form_data=form_data, active_page='prediction')

# ----------------- ROUTE: PAGE 4 - STUDENT MANAGEMENT -----------------

@app.route('/students')
@login_required
def students():
    search = request.args.get('search', '').strip()
    filter_cat = request.args.get('filter', 'all').strip()
    sort_by = request.args.get('sort', 'student_id').strip()

    student_list = database.get_all_students(
        search=search if search else None,
        filter_category=filter_cat if filter_cat != 'all' else None,
        sort_by=sort_by
    )

    return render_template(
        'students.html',
        students=student_list,
        current_search=search,
        current_filter=filter_cat,
        current_sort=sort_by,
        active_page='students'
    )

@app.route('/students/add', methods=['POST'])
@login_required
def add_student_route():
    student_id = request.form.get('student_id', '').strip().upper()
    attendance = request.form.get('attendance', '').strip()
    study_hours = request.form.get('study_hours', '').strip()
    marks = request.form.get('marks', '').strip()

    try:
        att = float(attendance)
        hours = float(study_hours)
        mks = float(marks)
        if not (0 <= att <= 100 and 0 <= hours <= 24 and 0 <= mks <= 50):
            flash('Values out of range: Attendance (0-100), Hours (0-24), Marks (0-50).', 'danger')
            return redirect(url_for('students'))
    except ValueError:
        flash('Attendance, study hours, and marks must be numeric.', 'danger')
        return redirect(url_for('students'))

    # Evaluate prediction right away for convenience
    pred_res = predict_student_performance(att, hours, mks)
    predicted_result = pred_res.get('predicted_result', 'Not Evaluated')

    success, msg = database.add_student(student_id, att, hours, mks, predicted_result)
    if success:
        flash(f'Student {student_id} added successfully.', 'success')
    else:
        flash(f'Error adding student: {msg}', 'danger')

    return redirect(url_for('students'))

@app.route('/students/edit/<student_id>', methods=['POST'])
@login_required
def edit_student_route(student_id):
    attendance = request.form.get('attendance', '').strip()
    study_hours = request.form.get('study_hours', '').strip()
    marks = request.form.get('marks', '').strip()

    try:
        att = float(attendance)
        hours = float(study_hours)
        mks = float(marks)
        if not (0 <= att <= 100 and 0 <= hours <= 24 and 0 <= mks <= 50):
            flash('Values out of range: Attendance (0-100), Hours (0-24), Marks (0-50).', 'danger')
            return redirect(url_for('students'))
    except ValueError:
        flash('Attendance, study hours, and marks must be numeric.', 'danger')
        return redirect(url_for('students'))

    pred_res = predict_student_performance(att, hours, mks)
    predicted_result = pred_res.get('predicted_result', 'Not Evaluated')

    success, msg = database.update_student(student_id, att, hours, mks, predicted_result)
    if success:
        flash(f'Student {student_id} updated successfully.', 'success')
    else:
        flash(f'Error updating student: {msg}', 'danger')

    return redirect(url_for('students'))

@app.route('/students/delete/<student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    success, msg = database.delete_student(student_id)
    if success:
        flash(f'Student {student_id} removed from database.', 'info')
    else:
        flash(f'Error deleting student: {msg}', 'danger')
    return redirect(url_for('students'))

# ----------------- ROUTE: PAGE 5 - DATASET MANAGEMENT -----------------

@app.route('/dataset')
@login_required
def dataset():
    active_dataset_path = Config.UPLOADED_DATASET_PATH if os.path.exists(Config.UPLOADED_DATASET_PATH) else Config.SAMPLE_DATASET_PATH
    dataset_report = None
    uploaded_info = {
        'is_custom': os.path.exists(Config.UPLOADED_DATASET_PATH),
        'filename': os.path.basename(active_dataset_path)
    }

    if os.path.exists(active_dataset_path):
        df_raw = None
        try:
            df_raw = pd.read_csv(active_dataset_path)
            total_rows = len(df_raw)
            missing_vals = int(df_raw.isnull().any(axis=1).sum())
            duplicate_rows = int(df_raw.duplicated(subset=['student_id']).sum()) if 'student_id' in df_raw.columns else 0
            
            # Numeric range checks
            clean_df, warnings = load_and_preprocess_data(active_dataset_path)
            clean_count = len(clean_df) if clean_df is not None else 0
            invalid_vals = total_rows - clean_count

            preview_records = []
            if clean_df is not None:
                for idx, r in clean_df.head(15).iterrows():
                    preview_records.append({
                        'student_id': r.get('student_id', f'STU{idx+1:03d}'),
                        'attendance': r['attendance'],
                        'study_hours': r['study_hours'],
                        'marks': r['marks'],
                        'result': r['result']
                    })

            dataset_report = {
                'filename': os.path.basename(active_dataset_path),
                'total_rows': total_rows,
                'missing_values': missing_vals,
                'duplicate_rows': duplicate_rows,
                'invalid_values': invalid_vals,
                'preview_rows': preview_records,
                'warnings': warnings
            }
        except Exception as e:
            flash(f"Error reading dataset: {e}", 'danger')

    return render_template(
        'dataset.html',
        dataset_report=dataset_report,
        uploaded_info=uploaded_info,
        active_page='dataset'
    )

@app.route('/dataset/upload', methods=['POST'])
@login_required
def upload_dataset():
    if 'dataset_file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('dataset'))

    file = request.files['dataset_file']
    if file.filename == '':
        flash('Please select a CSV file.', 'danger')
        return redirect(url_for('dataset'))

    if not file.filename.lower().endswith('.csv'):
        flash('Invalid file extension. Please upload a CSV file (.csv).', 'danger')
        return redirect(url_for('dataset'))

    # Save to upload path
    try:
        file.save(Config.UPLOADED_DATASET_PATH)
        # Validate uploaded CSV
        df, warnings = load_and_preprocess_data(Config.UPLOADED_DATASET_PATH)
        if df is None:
            if os.path.exists(Config.UPLOADED_DATASET_PATH):
                os.remove(Config.UPLOADED_DATASET_PATH)
            flash(f"CSV Validation Failed: {' '.join(warnings)}", 'danger')
            return redirect(url_for('dataset'))

        flash(f'Dataset uploaded successfully! Verified {len(df)} valid records.', 'success')
    except Exception as e:
        flash(f'Failed to process file upload: {str(e)}', 'danger')

    return redirect(url_for('dataset'))

@app.route('/dataset/sample-download')
@login_required
def download_sample_csv():
    if not os.path.exists(Config.SAMPLE_DATASET_PATH):
        flash('Sample dataset file not available.', 'danger')
        return redirect(url_for('dataset'))
    return send_from_directory(
        directory=Config.DATASET_DIR,
        path='sample_students.csv',
        as_attachment=True,
        download_name='sample_students_template.csv',
        mimetype='text/csv'
    )

@app.route('/dataset/reset-sample', methods=['POST'])
@login_required
def reset_sample_dataset():
    if os.path.exists(Config.UPLOADED_DATASET_PATH):
        try:
            os.remove(Config.UPLOADED_DATASET_PATH)
            # Re-train models with sample dataset
            train_and_evaluate_all_models(Config.SAMPLE_DATASET_PATH)
            flash('Reset to default illustrative sample dataset. Models updated.', 'info')
        except Exception as e:
            flash(f'Error resetting dataset: {e}', 'danger')
    return redirect(url_for('dataset'))

# ----------------- ROUTE: PAGE 6 - MODEL TRAINING -----------------

@app.route('/model-training', methods=['GET', 'POST'])
@login_required
def model_training():
    if request.method == 'POST':
        # Train all 4 models live
        dataset_source = Config.UPLOADED_DATASET_PATH if os.path.exists(Config.UPLOADED_DATASET_PATH) else Config.SAMPLE_DATASET_PATH
        train_res = train_and_evaluate_all_models(dataset_source)
        if train_res.get('success'):
            best_name = train_res.get('best_model_name')
            flash(f'Model training complete! All 4 classification algorithms trained and compared. Best model: {best_name}', 'success')
        else:
            errors = ' '.join(train_res.get('errors', ['Model training failed.']))
            flash(f'Training Error: {errors}', 'danger')
        return redirect(url_for('model_training'))

    # Load latest model comparison results
    model_results = database.get_latest_model_results()
    if not model_results:
        # Initial run if table is empty
        train_res = train_and_evaluate_all_models()
        model_results = database.get_latest_model_results()

    return render_template(
        'model_training.html',
        models=model_results,
        active_page='training'
    )

# ----------------- ROUTE: PAGE 7 - PREDICTION HISTORY -----------------

@app.route('/history')
@login_required
def history():
    search = request.args.get('search', '').strip()
    filter_result = request.args.get('filter', 'all').strip()
    sort_by = request.args.get('sort', 'prediction_date').strip()

    predictions = database.get_all_predictions(
        search=search if search else None,
        filter_result=filter_result if filter_result != 'all' else None,
        sort_by=sort_by
    )

    return render_template(
        'history.html',
        predictions=predictions,
        current_search=search,
        current_filter=filter_result,
        current_sort=sort_by,
        active_page='history'
    )

@app.route('/history/delete/<int:pred_id>', methods=['POST'])
@login_required
def delete_history_item(pred_id):
    success = database.delete_prediction(pred_id)
    if success:
        flash('Prediction record deleted.', 'info')
    else:
        flash('Error deleting record.', 'danger')
    return redirect(url_for('history'))

@app.route('/history/clear', methods=['POST'])
@login_required
def clear_history():
    database.clear_all_predictions()
    flash('Prediction history cleared successfully.', 'info')
    return redirect(url_for('history'))

# ----------------- ROUTE: PAGE 8 - REPORTS & ANALYTICS -----------------

@app.route('/reports')
@login_required
def reports():
    analytics = database.get_analytics_data()
    return render_template('reports.html', data=analytics, active_page='reports')

# ----------------- ROUTE: PAGE 9 - ABOUT PROJECT -----------------

@app.route('/about')
@login_required
def about():
    return render_template('about.html', active_page='about')

# ----------------- CSV EXPORT ROUTES -----------------

@app.route('/export/history')
@login_required
def export_history_csv():
    preds = database.get_all_predictions()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Student ID', 'Attendance (%)', 'Daily Study Hours', 'Internal Marks (/50)', 'Predicted Result', 'Model Confidence', 'Algorithm', 'Prediction Timestamp'])

    for p in preds:
        writer.writerow([
            p['id'],
            p['student_id'],
            p['attendance'],
            p['study_hours'],
            p['marks'],
            p['predicted_result'],
            p['probability'],
            p['model_name'],
            p['prediction_date']
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=prediction_history_export.csv"}
    )

@app.route('/export/students')
@login_required
def export_students_csv():
    students = database.get_all_students()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Student ID', 'Attendance (%)', 'Daily Study Hours', 'Internal Marks (/50)', 'Predicted Status', 'Date Added'])

    for s in students:
        writer.writerow([
            s['id'],
            s['student_id'],
            s['attendance'],
            s['study_hours'],
            s['marks'],
            s['predicted_result'],
            s['created_at']
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=student_registry_export.csv"}
    )

# ----------------- INITIALIZATION & EXECUTION -----------------

def bootstrap_application():
    """Ensure database is initialized and initial models are trained."""
    database.init_db()
    if not os.path.exists(Config.BEST_MODEL_PATH) or not database.get_latest_model_results():
        print("Bootstrapping: Training initial ML models...")
        train_and_evaluate_all_models()

# Initialize when module is loaded
bootstrap_application()

if __name__ == '__main__':
    print("=" * 70)
    print(" STUDENT PERFORMANCE PREDICTION SYSTEM")
    print(" A Real-Life Application Using Machine Learning Algorithms")
    print(" Developed by: P. Sree Sai Kiran & R. Harshavardhan")
    print("=" * 70)
    print(" Server running at: http://127.0.0.1:5000")
    print(" Faculty Demo Login: admin / admin123")
    print("=" * 70)
    app.run(host='127.0.0.1', port=5000, debug=True)
