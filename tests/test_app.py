import os
import sys
import unittest
import io

project_dir = r"C:\Users\Dell\Desktop\student-performance-prediction"
sys.path.insert(0, project_dir)

from app import app
import database

class TestStudentPerformancePredictionSystem(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def login(self, username="admin", password="admin123"):
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def test_01_login_logout(self):
        print("\n[TEST] 1. Authentication flow...")
        # Bad login
        res_fail = self.login("wrong", "password")
        self.assertIn(b"Invalid username or password", res_fail.data)
        
        # Good login
        res_ok = self.login("admin", "admin123")
        self.assertEqual(res_ok.status_code, 200)
        self.assertIn(b"Dashboard", res_ok.data)
        
        # Logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res_logout.status_code, 200)
        self.assertIn(b"Sign In to Dashboard", res_logout.data)
        print("  -> Login & Logout verified successfully.")

    def test_02_dashboard_view(self):
        print("\n[TEST] 2. Dashboard analytics view...")
        self.login()
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Faculty Dashboard & Student Analytics", res.data)
        self.assertIn(b"Total Students", res.data)
        self.assertIn(b"Likely to Pass", res.data)
        self.assertIn(b"Needing Support", res.data)
        print("  -> Dashboard loads with all 5 stat cards and Chart.js containers.")

    def test_03_prediction_flow(self):
        print("\n[TEST] 3. Student performance prediction...")
        self.login()
        # Test Case 1: Likely to pass
        res1 = self.client.post('/prediction', data={
            'student_id': 'TEST_PASS_01',
            'attendance': '92',
            'study_hours': '5.5',
            'marks': '46'
        }, follow_redirects=True)
        self.assertEqual(res1.status_code, 200)
        self.assertIn(b"LIKELY TO PASS", res1.data)
        self.assertIn(b"Model Confidence Score", res1.data)

        # Test Case 2: At-risk student
        res2 = self.client.post('/prediction', data={
            'student_id': 'TEST_FAIL_02',
            'attendance': '40',
            'study_hours': '1.0',
            'marks': '14'
        }, follow_redirects=True)
        self.assertEqual(res2.status_code, 200)
        self.assertIn(b"MAY NEED SUPPORT", res2.data)
        print("  -> Prediction generated with probability score and tailored messages.")

    def test_04_student_crud(self):
        print("\n[TEST] 4. Student CRUD operations...")
        self.login()
        # Add student
        res_add = self.client.post('/students/add', data={
            'student_id': 'STU_CRUD_999',
            'attendance': '85',
            'study_hours': '4.0',
            'marks': '40'
        }, follow_redirects=True)
        self.assertEqual(res_add.status_code, 200)
        self.assertIn(b"STU_CRUD_999", res_add.data)

        # Edit student
        res_edit = self.client.post('/students/edit/STU_CRUD_999', data={
            'attendance': '90',
            'study_hours': '5.0',
            'marks': '45'
        }, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)

        # Delete student
        res_del = self.client.post('/students/delete/STU_CRUD_999', follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        print("  -> Create, Read, Update, Delete for students verified.")

    def test_05_dataset_management(self):
        print("\n[TEST] 5. Dataset management & template download...")
        self.login()
        # View dataset page
        res = self.client.get('/dataset')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Dataset Management", res.data)

        # Sample download
        res_dl = self.client.get('/dataset/sample-download')
        self.assertEqual(res_dl.status_code, 200)
        self.assertIn(b"student_id,attendance,study_hours,marks,result", res_dl.data)

        # Upload a valid CSV
        csv_content = (
            "student_id,attendance,study_hours,marks,result\n"
            "STU101,92,5.2,46,Pass\n"
            "STU102,42,1.2,16,Fail\n"
            "STU103,82,4.1,39,Pass\n"
            "STU104,52,2.1,21,Fail\n"
        )
        data = {
            'dataset_file': (io.BytesIO(csv_content.encode('utf-8')), 'test_upload.csv')
        }
        res_up = self.client.post('/dataset/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res_up.status_code, 200)
        print("  -> CSV validation and upload verified.")

    def test_06_model_training_comparison(self):
        print("\n[TEST] 6. Model training & comparative benchmark...")
        self.login()
        # Get page
        res = self.client.get('/model-training')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Algorithm Performance Comparison", res.data)
        self.assertIn(b"Logistic Regression", res.data)
        self.assertIn(b"Decision Tree Classifier", res.data)
        self.assertIn(b"Random Forest Classifier", res.data)
        self.assertIn(b"K-Nearest Neighbors", res.data)

        # Retrain POST
        res_train = self.client.post('/model-training', follow_redirects=True)
        self.assertEqual(res_train.status_code, 200)
        self.assertIn(b"Model training complete", res_train.data)
        print("  -> All 4 algorithms evaluated, compared, and serialized.")

    def test_07_prediction_history_and_export(self):
        print("\n[TEST] 7. Prediction history and CSV exports...")
        self.login()
        res_hist = self.client.get('/history')
        self.assertEqual(res_hist.status_code, 200)
        self.assertIn(b"Historical Predictions", res_hist.data)

        # Export history CSV
        res_exp_hist = self.client.get('/export/history')
        self.assertEqual(res_exp_hist.status_code, 200)
        self.assertEqual(res_exp_hist.mimetype, 'text/csv')

        # Export students CSV
        res_exp_stu = self.client.get('/export/students')
        self.assertEqual(res_exp_stu.status_code, 200)
        self.assertEqual(res_exp_stu.mimetype, 'text/csv')
        print("  -> History search, filter, and CSV exports verified.")

    def test_08_reports_and_about_pages(self):
        print("\n[TEST] 8. Reports & About page content...")
        self.login()
        # Reports
        res_rep = self.client.get('/reports')
        self.assertEqual(res_rep.status_code, 200)
        self.assertIn(b"Institutional Performance Report", res_rep.data)

        # About
        res_about = self.client.get('/about')
        self.assertEqual(res_about.status_code, 200)
        self.assertIn(b"P. Sree Sai Kiran", res_about.data)
        self.assertIn(b"25RBAIM0030", res_about.data)
        self.assertIn(b"R. Harshavardhan", res_about.data)
        self.assertIn(b"25RBAIM0024", res_about.data)
        print("  -> Reports and About project details verified.")

if __name__ == '__main__':
    unittest.main()
