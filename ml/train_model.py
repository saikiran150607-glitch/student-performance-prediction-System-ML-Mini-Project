import os
import sys
import json
import joblib

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier

from config import Config
from ml.evaluate import calculate_metrics
import database

def load_and_preprocess_data(csv_path):
    """
    Load CSV dataset and validate columns and value ranges.
    Returns: cleaned DataFrame, list of warnings/errors
    """
    warnings = []
    if not os.path.exists(csv_path):
        return None, [f"Dataset file not found at: {csv_path}"]

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return None, [f"Failed to read CSV file: {str(e)}"]

    # Normalize column names
    df.columns = [col.strip().lower() for col in df.columns]
    required_cols = {'attendance', 'study_hours', 'marks', 'result'}
    
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        return None, [f"Missing required columns in CSV: {', '.join(missing_cols)}. Expected: attendance, study_hours, marks, result (and optional student_id)"]

    initial_count = len(df)
    
    # Drop rows where required features are NaN
    df = df.dropna(subset=['attendance', 'study_hours', 'marks', 'result']).copy()
    dropped_na = initial_count - len(df)
    if dropped_na > 0:
        warnings.append(f"Dropped {dropped_na} rows with missing (NaN) values.")

    # Convert numeric fields
    try:
        df['attendance'] = pd.to_numeric(df['attendance'])
        df['study_hours'] = pd.to_numeric(df['study_hours'])
        df['marks'] = pd.to_numeric(df['marks'])
    except Exception as e:
        return None, [f"Numeric conversion error: {str(e)}"]

    # Filter value ranges
    invalid_mask = (
        (df['attendance'] < 0) | (df['attendance'] > 100) |
        (df['study_hours'] < 0) | (df['study_hours'] > 24) |
        (df['marks'] < 0) | (df['marks'] > 50)
    )
    invalid_count = invalid_mask.sum()
    if invalid_count > 0:
        df = df[~invalid_mask].copy()
        warnings.append(f"Excluded {invalid_count} rows with out-of-range values (Attendance: 0-100, Study Hours: 0-24, Marks: 0-50).")

    # Map target result: Pass -> 1, Fail -> 0
    def parse_result(val):
        s = str(val).strip().lower()
        if s in ['pass', '1', 'p', 'true', 'likely to pass']:
            return 1
        elif s in ['fail', '0', 'f', 'false', 'may need support']:
            return 0
        return -1

    df['target'] = df['result'].apply(parse_result)
    unknown_results = (df['target'] == -1).sum()
    if unknown_results > 0:
        df = df[df['target'] != -1].copy()
        warnings.append(f"Excluded {unknown_results} rows with unrecognizable result labels. Expected 'Pass' or 'Fail'.")

    if len(df) == 0:
        return None, ["Dataset contains no valid records after cleaning."]

    # Dataset size checks
    if len(df) < 10:
        warnings.append("WARNING: Dataset contains fewer than 10 records. In machine learning, very small sample sizes cannot yield statistically reliable performance metrics.")
    elif len(df) < 30:
        warnings.append("NOTE: Dataset size is relatively small (<30 records). Stratified split will be used with caution.")

    return df, warnings

def train_and_evaluate_all_models(csv_path=None):
    """
    Train and compare 4 algorithms:
    1. Logistic Regression
    2. Decision Tree Classifier
    3. Random Forest Classifier
    4. K-Nearest Neighbors (KNN)
    
    Evaluates them, selects the best model, saves it to disk via Joblib,
    and updates SQLite database.
    """
    if csv_path is None:
        csv_path = Config.UPLOADED_DATASET_PATH if os.path.exists(Config.UPLOADED_DATASET_PATH) else Config.SAMPLE_DATASET_PATH

    df, warnings = load_and_preprocess_data(csv_path)
    if df is None:
        return {'success': False, 'errors': warnings, 'models': []}

    features = ['attendance', 'study_hours', 'marks']
    X = df[features]
    y = df['target']

    total_records = len(df)
    class_counts = y.value_counts().to_dict()
    pass_samples = class_counts.get(1, 0)
    fail_samples = class_counts.get(0, 0)

    # Check class distribution
    if pass_samples == 0 or fail_samples == 0:
        return {
            'success': False,
            'errors': ["Dataset must contain both 'Pass' and 'Fail' classes to train classification models."],
            'models': []
        }

    # Decide test size and split method
    if total_records >= 20:
        test_size = 0.2
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
        except Exception:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
    else:
        # Small sample fallback: 80/20 without strict stratification if impossible
        split_idx = max(1, int(total_records * 0.8))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        warnings.append("Used standard index splitting due to minimal sample count.")

    # Determine KNN neighbors (must be < len(X_train))
    n_neighbors = min(5, max(1, len(X_train) - 1))

    # Define the 4 model pipelines
    pipelines = {
        'Logistic Regression': Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', LogisticRegression(random_state=42, max_iter=1000))
        ]),
        'Decision Tree Classifier': Pipeline([
            ('classifier', DecisionTreeClassifier(max_depth=5, min_samples_split=4, random_state=42))
        ]),
        'Random Forest Classifier': Pipeline([
            ('classifier', RandomForestClassifier(n_estimators=100, max_depth=6, min_samples_split=4, random_state=42))
        ]),
        'K-Nearest Neighbors (KNN)': Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', KNeighborsClassifier(n_neighbors=n_neighbors))
        ])
    }

    results = []
    trained_pipelines = {}

    for name, pipe in pipelines.items():
        try:
            # Fit pipeline on training set only (prevent data leakage)
            pipe.fit(X_train, y_train)
            trained_pipelines[name] = pipe

            # Predict on test set
            y_pred = pipe.predict(X_test)
            metrics = calculate_metrics(y_test, y_pred)
            metrics['model_name'] = name

            # 5-fold cross validation if sample size permits
            if len(X) >= 30 and min(pass_samples, fail_samples) >= 5:
                try:
                    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
                    cv_scores = cross_val_score(pipe, X, y, cv=cv, scoring='f1')
                    metrics['cv_f1_mean'] = round(float(np.mean(cv_scores)) * 100, 2)
                    metrics['cv_f1_std'] = round(float(np.std(cv_scores)) * 100, 2)
                except Exception:
                    metrics['cv_f1_mean'] = metrics['f1_score']
                    metrics['cv_f1_std'] = 0.0
            else:
                metrics['cv_f1_mean'] = metrics['f1_score']
                metrics['cv_f1_std'] = 0.0

            results.append(metrics)
        except Exception as e:
            warnings.append(f"Error training {name}: {str(e)}")

    if not results:
        return {'success': False, 'errors': warnings or ["No models could be successfully trained."], 'models': []}

    # Select best model dynamically based on evaluation metrics:
    # Primary: F1-Score; Secondary: Accuracy
    best_model_info = max(results, key=lambda m: (m['f1_score'], m['accuracy']))
    best_model_name = best_model_info['model_name']
    best_pipeline = trained_pipelines[best_model_name]

    # Mark is_best
    for r in results:
        r['is_best'] = (r['model_name'] == best_model_name)

    # Ensure models directory exists and save best model
    os.makedirs(Config.MODELS_DIR, exist_ok=True)
    joblib.dump(best_pipeline, Config.BEST_MODEL_PATH)

    # Save model metadata
    metadata = {
        'best_model_name': best_model_name,
        'trained_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'dataset_source': os.path.basename(csv_path),
        'total_samples': total_records,
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'pass_samples': pass_samples,
        'fail_samples': fail_samples,
        'features': features,
        'best_metrics': best_model_info,
        'all_models': results,
        'warnings': warnings
    }

    with open(Config.MODEL_METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)

    # Save model evaluation to SQLite database
    database.save_model_results(results)

    return {
        'success': True,
        'best_model_name': best_model_name,
        'models': results,
        'metadata': metadata,
        'warnings': warnings
    }

if __name__ == '__main__':
    print("Initiating standalone training pipeline test...")
    res = train_and_evaluate_all_models()
    print("Training result:")
    print(f"Success: {res['success']}")
    if res['success']:
        print(f"Best Model Selected: {res['best_model_name']}")
        for m in res['models']:
            print(f"- {m['model_name']}: Accuracy={m['accuracy']}%, F1={m['f1_score']}%, Best={m.get('is_best')}")
    else:
        print(f"Errors: {res.get('errors')}")
