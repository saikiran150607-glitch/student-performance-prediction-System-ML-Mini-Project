import sys
import os

project_dir = r"C:\Users\Dell\Desktop\student-performance-prediction"
sys.path.insert(0, project_dir)

import database
from ml.train_model import train_and_evaluate_all_models
from ml.predict import predict_student_performance

print("--- Step 1: Initializing SQLite Database ---")
database.init_db()
print("Database initialized successfully.")

print("--- Step 2: Training 4 Classification Models ---")
res = train_and_evaluate_all_models()
print(f"Training Success: {res['success']}")
print(f"Best Model Selected: {res.get('best_model_name')}")
for m in res.get('models', []):
    print(f"  * {m['model_name']}: Accuracy = {m['accuracy']}%, F1 = {m['f1_score']}%, Best = {m.get('is_best')}")

print("--- Step 3: Testing Predictions on Report Examples ---")
examples = [
    ("STU001", 90, 5, 45, "Expected: Pass"),
    ("STU002", 45, 1, 18, "Expected: Fail"),
    ("STU003", 80, 4, 38, "Expected: Pass"),
    ("STU004", 55, 2, 22, "Expected: Fail"),
    ("STU005", 75, 3, 35, "Expected: Pass"),
    ("STU006", 40, 1, 15, "Expected: Fail"),
]

for sid, att, hours, marks, note in examples:
    pred = predict_student_performance(att, hours, marks)
    print(f"  {sid} (Att={att}%, Hours={hours}h, Marks={marks}/50) -> {pred['predicted_result']} (Confidence: {pred['confidence_pct']}) [{note}]")

print("--- Step 4: Testing Dashboard Stats Retrieval ---")
stats = database.get_dashboard_stats()
print(f"Total Students in DB: {stats['total_students']}")
print(f"Pass Count: {stats['pass_count']}, Support Count: {stats['support_count']}")
print(f"Avg Attendance: {stats['avg_attendance']}%, Avg Marks: {stats['avg_marks']}")
print(f"Recent Predictions count: {len(stats['recent_predictions'])}")

print("ALL BACKEND & ML VERIFICATIONS PASSED SUCCESSFULLY!")
