import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from exams.models import Subject, Exam
from questions.models import Question, Option
from decimal import Decimal

User = get_user_model()

def run_question_suite():
    print("==================================================")
    print("RUNNING QUESTION MANAGEMENT & SECURITY TEST SUITE")
    print("==================================================")
    
    # 1. Setup test users
    admin_user, _ = User.objects.get_or_create(
        username='q_admin',
        defaults={'role': User.Role.ADMIN, 'email': 'qadmin@test.com'}
    )
    admin_user.set_password('admin123')
    admin_user.role = User.Role.ADMIN
    admin_user.save()

    teacher1, _ = User.objects.get_or_create(
        username='q_teacher1',
        defaults={'role': User.Role.TEACHER, 'email': 't1@test.com'}
    )
    teacher1.set_password('teacher123')
    teacher1.role = User.Role.TEACHER
    teacher1.save()

    teacher2, _ = User.objects.get_or_create(
        username='q_teacher2',
        defaults={'role': User.Role.TEACHER, 'email': 't2@test.com'}
    )
    teacher2.set_password('teacher123')
    teacher2.role = User.Role.TEACHER
    teacher2.save()

    student_user, _ = User.objects.get_or_create(
        username='q_student',
        defaults={'role': User.Role.STUDENT, 'email': 'student@test.com'}
    )
    student_user.set_password('student123')
    student_user.role = User.Role.STUDENT
    student_user.save()

    subject, _ = Subject.objects.get_or_create(
        name='Database Systems',
        code='CS401',
        defaults={'created_by': admin_user}
    )

    # Exams
    exam_t1, _ = Exam.objects.get_or_create(
        title='T1 SQL Exam',
        subject=subject,
        created_by=teacher1,
        defaults={'duration_minutes': 30, 'total_marks': Decimal('10.00'), 'passing_marks': Decimal('4.00')}
    )
    exam_t2, _ = Exam.objects.get_or_create(
        title='T2 NoSQL Exam',
        subject=subject,
        created_by=teacher2,
        defaults={'duration_minutes': 30, 'total_marks': Decimal('10.00'), 'passing_marks': Decimal('4.00')}
    )

    # Clean existing questions in test exams
    exam_t1.questions.all().delete()
    exam_t2.questions.all().delete()

    client = Client()

    # TEST 1: Teacher 1 adds question with blank negative_marks and blank order
    client.login(username='q_teacher1', password='teacher123')
    resp = client.post(f'/questions/exam/{exam_t1.id}/create/', {
        'question_text': 'What does SQL stand for?',
        'marks': '2.00',
        'negative_marks': '',  # Test empty field handling
        'order': '',           # Test auto-order calculation
        'option_1': 'Structured Query Language',
        'option_2': 'Simple Question Language',
        'option_3': 'Standard Quick Logic',
        'option_4': 'Sequential Query List',
        'correct_option': '1',
        'explanation': 'SQL is Structured Query Language.'
    }, follow=True)
    assert resp.status_code == 200, f"Teacher create question failed with status {resp.status_code}"
    
    q1 = Question.objects.filter(exam=exam_t1, question_text__startswith='What does SQL').first()
    assert q1 is not None, "Question was not saved to DB!"
    assert q1.negative_marks == Decimal('0.00'), f"Default negative marks failed: {q1.negative_marks}"
    assert q1.options.count() == 4, f"Option count should be 4, got {q1.options.count()}"
    assert q1.correct_option.option_text == 'Structured Query Language'
    print("[PASS] 1. Teacher successfully created question with automatic default values and 4 options.")

    # TEST 2: Save and Add Another Question
    resp = client.post(f'/questions/exam/{exam_t1.id}/create/', {
        'question_text': 'Which command is used to retrieve data from a table?',
        'marks': '1.50',
        'negative_marks': '0.50',
        'order': '2',
        'option_1': 'INSERT',
        'option_2': 'SELECT',
        'option_3': 'UPDATE',
        'option_4': 'DELETE',
        'correct_option': '2',
        'explanation': 'SELECT retrieves rows from tables.',
        'save_and_add': '1'
    }, follow=True)
    assert resp.status_code == 200
    q2 = Question.objects.filter(exam=exam_t1, question_text__startswith='Which command').first()
    assert q2 is not None
    assert q2.correct_option.option_text == 'SELECT'
    print("[PASS] 2. 'Save & Add Another' saved question and redirected cleanly.")

    # TEST 3: Teacher 1 can edit their question
    resp = client.post(f'/questions/exam/{exam_t1.id}/{q1.id}/edit/', {
        'question_text': 'What does SQL stand for? (Updated)',
        'marks': '3.00',
        'negative_marks': '0.25',
        'order': '1',
        'option_1': 'Structured Query Language (ANSI)',
        'option_2': 'Simple Question Language',
        'option_3': 'Standard Quick Logic',
        'option_4': 'Sequential Query List',
        'correct_option': '1',
        'explanation': 'Updated explanation.'
    }, follow=True)
    assert resp.status_code == 200
    q1.refresh_from_db()
    assert 'Updated' in q1.question_text
    assert q1.marks == Decimal('3.00')
    assert q1.options.get(order=1).option_text == 'Structured Query Language (ANSI)'
    print("[PASS] 3. Teacher successfully edited question statement, marks, and option text.")

    # TEST 4: Authorization - Teacher 1 cannot add or edit questions in Teacher 2's exam
    resp = client.get(f'/questions/exam/{exam_t2.id}/')
    assert resp.status_code in [302, 403], "Teacher 1 should not view questions of Teacher 2!"
    
    resp = client.post(f'/questions/exam/{exam_t2.id}/create/', {
        'question_text': 'Unauthorized Question',
        'marks': '1.00',
        'option_1': 'A', 'option_2': 'B', 'option_3': 'C', 'option_4': 'D',
        'correct_option': '1'
    })
    assert resp.status_code in [302, 403], "Teacher 1 was able to post to Teacher 2 exam!"
    assert not Question.objects.filter(question_text='Unauthorized Question').exists()
    print("[PASS] 4. Teacher-Exam isolation enforced: Teacher 1 blocked from modifying Teacher 2 exam.")

    # TEST 5: Admin can manage any exam's questions (Teacher 1 and Teacher 2)
    client.logout()
    client.login(username='q_admin', password='admin123')
    resp = client.get(f'/questions/exam/{exam_t2.id}/')
    assert resp.status_code == 200
    
    resp = client.post(f'/questions/exam/{exam_t2.id}/create/', {
        'question_text': 'What is MongoDB?',
        'marks': '2.00',
        'negative_marks': '0.00',
        'order': '1',
        'option_1': 'Document-oriented database',
        'option_2': 'Relational DB',
        'option_3': 'Graph DB',
        'option_4': 'Assembly language',
        'correct_option': '1',
        'explanation': 'MongoDB is a document store.'
    }, follow=True)
    assert resp.status_code == 200
    q_admin_created = Question.objects.filter(exam=exam_t2, question_text='What is MongoDB?').first()
    assert q_admin_created is not None
    print("[PASS] 5. Admin has global authorization to manage questions across all exams.")

    # TEST 6: Student is forbidden from accessing Question Management views
    client.logout()
    client.login(username='q_student', password='student123')
    resp = client.get(f'/questions/exam/{exam_t1.id}/')
    assert resp.status_code in [302, 403], "Student accessed question list!"
    resp = client.get(f'/questions/exam/{exam_t1.id}/create/')
    assert resp.status_code in [302, 403], "Student accessed question create!"
    resp = client.get(f'/questions/exam/{exam_t1.id}/{q1.id}/edit/')
    assert resp.status_code in [302, 403], "Student accessed question edit!"
    resp = client.get(f'/questions/exam/{exam_t1.id}/{q1.id}/delete/')
    assert resp.status_code in [302, 403], "Student accessed question delete!"
    print("[PASS] 6. Student role strictly prohibited from all question CRUD endpoints.")

    # TEST 7: Delete Question with confirmation page (GET) and POST delete
    client.logout()
    client.login(username='q_teacher1', password='teacher123')
    # GET renders confirmation
    resp = client.get(f'/questions/exam/{exam_t1.id}/{q2.id}/delete/')
    assert resp.status_code == 200
    assert b"Delete Question" in resp.content or b"Confirm" in resp.content
    
    # POST deletes
    resp = client.post(f'/questions/exam/{exam_t1.id}/{q2.id}/delete/', follow=True)
    assert resp.status_code == 200
    assert not Question.objects.filter(id=q2.id).exists()
    print("[PASS] 7. Question deletion verified: GET shows confirmation page, POST performs safe deletion.")

    # TEST 8: Sample CSV Download
    resp = client.get('/questions/sample-csv/')
    assert resp.status_code == 200
    assert resp['Content-Type'] == 'text/csv'
    assert b'question_text,option_a,option_b' in resp.content
    print("[PASS] 8. Sample CSV template download functioning.")

    print("==================================================")
    print("ALL 8 QUESTION MANAGEMENT TESTS PASSED PERFECTLY!")
    print("==================================================")

if __name__ == '__main__':
    run_question_suite()
