# 🎓 Student Performance Prediction System

### A Real-Life Application Using Machine Learning Algorithms

A machine learning-based web application that predicts student academic performance using attendance percentage, daily study hours, and internal assessment marks.

The system helps faculty identify students who may need additional academic support through machine learning predictions and interactive analytics.

---

## 👥 Project Contributors

| Name | Roll Number | Responsibility |
|---|---|---|
| P. Sree Sai Kiran | 25RBAIM0030 | ML Engineering & Backend Architecture |
| R. Harshavardhan | 25RBAIM0024 | UI/UX System Design & Data Analytics |

---

## 📌 Project Overview

The Student Performance Prediction System uses machine learning classification algorithms to analyze student academic information and predict whether a student is:

- **Likely to Pass**
- **May Need Support**

The system considers three important academic parameters:

1. Attendance Percentage
2. Daily Study Hours
3. Internal Assessment Marks (out of 50)

The application provides a teacher dashboard, student management, dataset uploading, model training, prediction history, and performance analytics.

Predictions are intended to support academic guidance and are not guaranteed examination outcomes.

---

## ✨ Key Features

- Secure faculty login and authentication.
- Interactive teacher dashboard.
- Student registration and management.
- Student performance prediction.
- CSV dataset upload and validation.
- Machine learning model training.
- Comparison of four classification algorithms.
- Prediction confidence display.
- Prediction history management.
- Performance analytics and charts.
- CSV report export.
- Printable analytics reports.

---

## 🧠 Machine Learning Algorithms

Four machine learning algorithms are implemented:

| Algorithm | Description |
|---|---|
| Logistic Regression | Classification using a logistic function |
| Decision Tree | Classification using decision rules |
| Random Forest | Ensemble learning using multiple decision trees |
| K-Nearest Neighbors (KNN) | Classification based on nearest data points |

### Model Evaluation Metrics

The models are evaluated using:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion Matrix
- Cross-validation

The best-performing model is selected based on actual evaluation results and saved using Joblib.

---

## 🛠️ Technology Stack

**Frontend**
- HTML5
- CSS3
- Bootstrap 5
- JavaScript
- Chart.js

**Backend**
- Python
- Flask

**Machine Learning & Data Processing**
- Scikit-learn
- Pandas
- NumPy

**Database**
- SQLite

**Model Storage**
- Joblib

---

## 📁 Project Structure

```text
student-performance-prediction/
│
├── app.py
├── config.py
├── database.py
├── train_model.py
├── predict.py
├── evaluate.py
├── requirements.txt
├── README.md
├── run.bat
├── sample_students.csv
│
├── models/
│   └── best_model.joblib
│
├── database/
│   └── student_performance.db
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── prediction.html
│   ├── students.html
│   ├── dataset.html
│   ├── model_training.html
│   ├── history.html
│   ├── reports.html
│   └── about.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── docs/
│   ├── PROJECT_REPORT.pdf
│   └── FINAL_PROJECT_AUDIT.md
│
├── presentation/
│   ├── Student_Performance_Prediction.pptx
│   └── Student_Performance_Prediction_Slides.pdf
│
└── demo/
    ├── Student_Performance_Demo.mp4
    └── screenshots/
```

---

## ⚙️ Installation and Setup

### Prerequisites

Make sure the following are installed:

- Python 3.10 or compatible version supported by the dependencies.
- Git.
- A modern web browser.

### Step 1: Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### Step 2: Navigate to the project directory

```bash
cd student-performance-prediction
```

### Step 3: Create a virtual environment

```bash
python -m venv venv
```

### Step 4: Activate the virtual environment

For Windows:

```bash
venv\Scripts\activate
```

### Step 5: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Run the application

```bash
python app.py
```

Alternatively, Windows users can double-click:

```text
run.bat
```

### Step 7: Open the application

Open your browser and navigate to:

http://127.0.0.1:5000

---

## 🔐 Login Credentials

For the demonstration setup:

| Field | Value |
|---|---|
| Username | admin |
| Password | admin123 |

**Security note:** Change the default password before any real deployment. Never publish real credentials or secret keys.

---

## 📊 Dataset Information

The project includes an illustrative sample dataset containing 150 synthetic student records.

Dataset columns:

| Column | Description |
|---|---|
| student_id | Unique student identifier |
| attendance | Attendance percentage |
| study_hours | Daily study hours |
| marks | Internal assessment marks out of 50 |
| result | Actual labelled outcome (Pass/Fail) |

The dataset is provided for demonstration and model development.

Synthetic data should not be considered representative of actual student populations. Real-world implementation requires authorized and representative institutional data.

---

## 🔄 Machine Learning Workflow

1. Load the student dataset.
2. Perform data validation and preprocessing.
3. Separate input features and target labels.
4. Split the dataset into training and testing sets.
5. Train four classification algorithms.
6. Evaluate models using appropriate performance metrics.
7. Compare model performance.
8. Select the best-performing model.
9. Save the trained model using Joblib.
10. Use the selected model to predict student performance.

---

## 📂 Project Documentation and Deliverables

### Project Report

[View Project Report (PDF)](docs/PROJECT_REPORT.pdf)

### Technical Documentation

[View Project Report (Markdown)](docs/PROJECT_REPORT.md)

[View Final Project Audit](docs/FINAL_PROJECT_AUDIT.md)

### PowerPoint Presentation

[View Project Presentation (PPTX)](presentation/Student_Performance_Prediction.pptx)

[View Presentation (PDF)](presentation/Student_Performance_Prediction_Slides.pdf)

### Demonstration Video

[Watch Project Demonstration](demo/Student_Performance_Demo.mp4)

If the video is hosted externally, replace the link above with your Google Drive or YouTube demonstration link.

---

## 🎥 Application Screenshots

Add your application screenshots inside:

```text
demo/screenshots/
```

You can display them here using relative Markdown links.

Example:

```markdown
![Dashboard](demo/screenshots/dashboard.png)
![Prediction](demo/screenshots/prediction.png)
```

---

## 🔮 Future Enhancements

- Integration with real institutional student databases.
- More academic performance indicators.
- Improved model validation using larger datasets.
- Student and parent dashboards.
- Email notifications for academic support.
- Advanced student performance analytics.

---

## ⚠️ Disclaimer

This system is developed as an academic mini project.

Predictions are estimates generated using machine learning models and available input data. They are not guarantees of examination results and should only be used as decision-support information for teachers.

Student privacy and responsible use of academic data must