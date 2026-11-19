import os

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'student-performance-prediction-secret-key-2026')
    DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'student_performance.db')
    DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
    SAMPLE_DATASET_PATH = os.path.join(DATASET_DIR, 'sample_students.csv')
    UPLOADED_DATASET_PATH = os.path.join(DATASET_DIR, 'uploaded_dataset.csv')
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    BEST_MODEL_PATH = os.path.join(MODELS_DIR, 'best_model.joblib')
    MODEL_METADATA_PATH = os.path.join(MODELS_DIR, 'model_metadata.json')
    EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
    
    # Default credentials for faculty demonstration
    DEFAULT_ADMIN_USERNAME = 'admin'
    DEFAULT_ADMIN_PASSWORD = 'admin123'
    
    # Upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file upload
    ALLOWED_EXTENSIONS = {'csv'}
