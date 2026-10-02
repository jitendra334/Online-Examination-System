import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from exams.models import Subject, Exam
from questions.models import Question, Option
from results.models import ExamAttempt, StudentAnswer
from decimal import Decimal
import json

User = get_user_model()

def run_system_verification():
    print("==================================================")
    print("RUNNING ONLINE EXAMINATION SYSTEM TEST SUITE")
    print("==================================================")
    
    client = Client()

    # 1. Test Login Page
    resp = client.get('/accounts/login/')
    assert resp.status_code == 200, f"Login page failed: {resp.status_code}"
    print("[PASS] 1. Login page renders successfully.")

    # 2. Test Student Login
    login_success = client.login(username='rahul_cse', password='student123')
    assert login_success, "Student login failed!"
    print("[PASS] 2. Student (rahul_cse) authenticated successfully.")

    # 3. Test Student Dashboard
    resp = client.get('/dashboard/')
    assert resp.status_code == 200, f"Student dashboard failed: {resp.status_code}"
    assert b"Student Assessment Dashboard" in resp.content or b"Rahul" in resp.content
    print("[PASS] 3. Student Dashboard loads with metrics and charts.")

    # 4. Test Student Available Exams
    resp = client.get('/exams/')
    assert resp.status_code == 200
    print("[PASS] 4. Available Exams list loaded.")

    # 5. Test Teacher Flow
    client.logout()
    login_success = client.login(username='prof_sharma', password='teacher123')
    assert login_success, "Teacher login failed!"
    resp = client.get('/dashboard/')
    assert resp.status_code == 200
    assert b"Faculty Portal" in resp.content or b"Sharma" in resp.content
    print("[PASS] 5. Faculty Dashboard & metrics rendered.")

    # 6. Test Admin Flow
    client.logout()
    login_success = client.login(username='admin', password='admin123')
    assert login_success, "Admin login failed!"
    resp = client.get('/dashboard/')
    assert resp.status_code == 200
    assert b"Administrative Overview" in resp.content
    print("[PASS] 6. Administrator Dashboard & analytics rendered.")

    # 7. Test Admin User List
    resp = client.get('/accounts/admin/users/')
    assert resp.status_code == 200
    print("[PASS] 7. Admin User Management directory rendered.")

    # 8. Test Live Examination Lifecycle with Student
    client.logout()
    test_student, _ = User.objects.get_or_create(
        username='test_student_eval',
        defaults={
            'email': 'eval.student@examportal.edu',
            'first_name': 'Test',
            'last_name': 'Candidate',
            'role': User.Role.STUDENT,
            'student_id': '22CSE999',
            'department': 'CSE'
        }
    )
    test_student.set_password('student123')
    test_student.save()
    
    client.login(username='test_student_eval', password='student123')

    # Find an exam
    exam = Exam.objects.filter(is_published=True, questions__isnull=False).first()
    assert exam is not None, "No published exam found for testing!"
    
    # Clear prior test attempts for this student if any
    ExamAttempt.objects.filter(student=test_student, exam=exam).delete()
    print(f"[INFO] Testing exam: '{exam.title}'")

    # Start exam
    resp = client.get(f'/results/start/{exam.id}/', follow=True)
    assert resp.status_code == 200
    print("[PASS] 8. Examination session initialized and started.")

    # Get the active attempt
    attempt = ExamAttempt.objects.filter(student=test_student, exam=exam, status=ExamAttempt.Status.IN_PROGRESS).first()
    assert attempt is not None, "Active attempt was not created!"

    # Test AJAX Answer Save
    first_q_id = attempt.question_ids[0]
    question = Question.objects.get(id=first_q_id)
    correct_opt = question.correct_option

    save_payload = {
        'question_id': question.id,
        'option_id': correct_opt.id,
        'is_marked_for_review': False
    }
    resp = client.post(
        f'/results/ajax-save/{attempt.id}/',
        data=json.dumps(save_payload),
        content_type='application/json'
    )
    assert resp.status_code == 200
    res_data = json.loads(resp.content)
    assert res_data['status'] == 'success'
    print("[PASS] 9. AJAX instant answer save executed successfully.")

    # Test AJAX Toggle Review
    review_payload = {
        'question_id': question.id,
        'is_marked_for_review': True
    }
    resp = client.post(
        f'/results/ajax-review/{attempt.id}/',
        data=json.dumps(review_payload),
        content_type='application/json'
    )
    assert resp.status_code == 200
    print("[PASS] 10. AJAX Mark for Review updated.")

    # Test Final Submit
    resp = client.post(f'/results/submit/{attempt.id}/', follow=True)
    assert resp.status_code == 200
    attempt.refresh_from_db()
    assert attempt.status == ExamAttempt.Status.SUBMITTED
    assert attempt.attempted_questions >= 1
    assert attempt.correct_answers >= 1
    print(f"[PASS] 11. Exam submitted. Final Score: {attempt.final_score}/{attempt.total_marks} ({attempt.percentage}%, Passed: {attempt.is_passed})")

    # Test Scorecard View
    resp = client.get(f'/results/detail/{attempt.id}/')
    assert resp.status_code == 200
    assert b"Official Examination Scorecard" in resp.content
    print("[PASS] 12. Detailed Result Scorecard & Solution Review rendered.")

    # Test PDF Scorecard Generation
    resp = client.get(f'/results/pdf/{attempt.id}/')
    assert resp.status_code == 200
    assert resp['Content-Type'] == 'application/pdf'
    assert len(resp.content) > 1000
    print(f"[PASS] 13. PDF Certificate generated ({len(resp.content)} bytes).")

    # Test Global & Exam Leaderboards
    resp = client.get('/results/leaderboard/')
    assert resp.status_code == 200
    resp = client.get(f'/results/leaderboard/{exam.id}/')
    assert resp.status_code == 200
    print("[PASS] 14. Academic Leaderboards rendered.")

    # Test Teacher CSV Export
    client.logout()
    client.login(username='admin', password='admin123')
    resp = client.get(f'/results/exam/{exam.id}/export-csv/')
    assert resp.status_code == 200
    assert resp['Content-Type'] == 'text/csv'
    print("[PASS] 15. Teacher Marksheet CSV Export generated.")

    print("==================================================")
    print("ALL 15 SYSTEM TESTS PASSED PERFECTLY!")
    print("==================================================")

if __name__ == '__main__':
    run_system_verification()
