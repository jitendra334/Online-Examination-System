from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json
import random
from decimal import Decimal

from exams.models import Subject, Exam
from questions.models import Question, Option
from results.models import ExamAttempt, StudentAnswer

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds sample database data with realistic users, subjects, exams, questions, and evaluated attempts.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Online Examination System data..."))

        # 1. Create Users
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@examportal.edu',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'department': 'Administration',
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()

        # Teachers
        teacher1, _ = User.objects.get_or_create(
            username='prof_sharma',
            defaults={
                'email': 'r.sharma@examportal.edu',
                'first_name': 'Dr. Rajesh',
                'last_name': 'Sharma',
                'role': User.Role.TEACHER,
                'employee_id': 'FAC-CS-101',
                'department': 'Computer Science & Engineering',
                'bio': 'Associate Professor specializing in Algorithms and Systems.'
            }
        )
        teacher1.set_password('teacher123')
        teacher1.save()

        teacher2, _ = User.objects.get_or_create(
            username='dr_anita',
            defaults={
                'email': 'anita.verma@examportal.edu',
                'first_name': 'Dr. Anita',
                'last_name': 'Verma',
                'role': User.Role.TEACHER,
                'employee_id': 'FAC-IT-204',
                'department': 'Information Technology',
                'bio': 'Professor specializing in Databases and Cloud Architecture.'
            }
        )
        teacher2.set_password('teacher123')
        teacher2.save()

        # Students
        student1, _ = User.objects.get_or_create(
            username='rahul_cse',
            defaults={
                'email': 'rahul.cse@examportal.edu',
                'first_name': 'Rahul',
                'last_name': 'Verma',
                'role': User.Role.STUDENT,
                'student_id': '21CS045',
                'department': 'Computer Science & Engineering',
            }
        )
        student1.set_password('student123')
        student1.save()

        student2, _ = User.objects.get_or_create(
            username='priya_it',
            defaults={
                'email': 'priya.it@examportal.edu',
                'first_name': 'Priya',
                'last_name': 'Singh',
                'role': User.Role.STUDENT,
                'student_id': '22IT018',
                'department': 'Information Technology',
            }
        )
        student2.set_password('student123')
        student2.save()

        student3, _ = User.objects.get_or_create(
            username='amit_kumar',
            defaults={
                'email': 'amit.kumar@examportal.edu',
                'first_name': 'Amit',
                'last_name': 'Kumar',
                'role': User.Role.STUDENT,
                'student_id': '21CS012',
                'department': 'Computer Science & Engineering',
            }
        )
        student3.set_password('student123')
        student3.save()

        student4, _ = User.objects.get_or_create(
            username='sneha_patel',
            defaults={
                'email': 'sneha.patel@examportal.edu',
                'first_name': 'Sneha',
                'last_name': 'Patel',
                'role': User.Role.STUDENT,
                'student_id': '22EC089',
                'department': 'Electronics & Communication',
            }
        )
        student4.set_password('student123')
        student4.save()

        self.stdout.write(self.style.SUCCESS("[OK] Users seeded: admin, prof_sharma, dr_anita, rahul_cse, priya_it, amit_kumar, sneha_patel"))

        # 2. Create Subjects
        dsa, _ = Subject.objects.get_or_create(
            code='CS301',
            defaults={
                'name': 'Data Structures & Algorithms',
                'description': 'Core fundamental structures: arrays, trees, graphs, hashing, sorting algorithms.',
                'icon': 'bi-diagram-3',
                'color_code': '#2563eb',
                'created_by': teacher1
            }
        )

        dbms, _ = Subject.objects.get_or_create(
            code='CS402',
            defaults={
                'name': 'Database Management Systems',
                'description': 'Relational algebra, SQL, normalization, ACID properties, transaction indexing.',
                'icon': 'bi-database',
                'color_code': '#059669',
                'created_by': teacher2
            }
        )

        cn, _ = Subject.objects.get_or_create(
            code='CS501',
            defaults={
                'name': 'Computer Networks',
                'description': 'OSI Model, TCP/IP, routing protocols, subnets, HTTP/HTTPS security.',
                'icon': 'bi-hdd-network',
                'color_code': '#7c3aed',
                'created_by': teacher1
            }
        )

        py_web, _ = Subject.objects.get_or_create(
            code='CS504',
            defaults={
                'name': 'Python & Web Frameworks',
                'description': 'Object-oriented Python, Django architecture, REST APIs, ORM design.',
                'icon': 'bi-code-slash',
                'color_code': '#d97706',
                'created_by': teacher2
            }
        )

        self.stdout.write(self.style.SUCCESS("[OK] Subjects seeded: CS301, CS402, CS501, CS504"))

        # 3. Create Exams & Questions
        # Exam 1: DSA Midterm
        exam1, _ = Exam.objects.get_or_create(
            title='DSA Comprehensive Midterm Assessment',
            subject=dsa,
            defaults={
                'description': 'Evaluation of Trees, Graphs, Sorting Complexities, and Dynamic Programming foundations.',
                'created_by': teacher1,
                'duration_minutes': 25,
                'total_marks': Decimal('10.00'),
                'passing_marks': Decimal('4.00'),
                'negative_marking_enabled': True,
                'negative_marks_per_question': Decimal('0.25'),
                'is_published': True,
                'random_question_order': True,
                'random_option_order': True,
                'show_answers_after_submission': True,
            }
        )

        dsa_questions = [
            {
                'text': 'Which data structure is primarily used in Breadth-First Search (BFS) graph traversal?',
                'marks': 1.0,
                'explanation': 'BFS visits vertices level by level, requiring a FIFO Queue to maintain traversal order.',
                'options': [
                    ('Stack', False),
                    ('Queue', True),
                    ('Priority Queue', False),
                    ('Binary Search Tree', False),
                ]
            },
            {
                'text': 'What is the average and worst-case time complexity of standard QuickSort with Lomuto partitioning?',
                'marks': 1.0,
                'explanation': 'Average time is O(n log n), but with worst-case unbalanced pivot selection, it degrades to O(n^2).',
                'options': [
                    ('Avg: O(n log n), Worst: O(n log n)', False),
                    ('Avg: O(n log n), Worst: O(n^2)', True),
                    ('Avg: O(n), Worst: O(n log n)', False),
                    ('Avg: O(n^2), Worst: O(n^2)', False),
                ]
            },
            {
                'text': 'In a Min-Heap with N elements, what is the time complexity to extract the minimum element?',
                'marks': 1.0,
                'explanation': 'Extracting the root takes O(1) to read, but requires heapify down of the replaced root taking O(log N).',
                'options': [
                    ('O(1)', False),
                    ('O(log N)', True),
                    ('O(N)', False),
                    ('O(N log N)', False),
                ]
            },
            {
                'text': 'Which algorithmic paradigm does Dijkstra\'s Single-Source Shortest Path algorithm follow?',
                'marks': 1.0,
                'explanation': 'Dijkstra repeatedly picks the closest unvisited vertex, which is a classic Greedy approach.',
                'options': [
                    ('Greedy Method', True),
                    ('Dynamic Programming', False),
                    ('Divide and Conquer', False),
                    ('Backtracking', False),
                ]
            },
            {
                'text': 'What is the maximum number of nodes on level L of a binary tree (root at level 0)?',
                'marks': 1.0,
                'explanation': 'Level 0 has 2^0 = 1 node; level 1 has 2^1 = 2; level L has 2^L nodes.',
                'options': [
                    ('2^L', True),
                    ('2^(L-1)', False),
                    ('2^(L+1) - 1', False),
                    ('L^2', False),
                ]
            },
            {
                'text': 'Which of the following sorting algorithms is inherently stable?',
                'marks': 1.0,
                'explanation': 'MergeSort preserves the relative order of duplicate elements, making it a stable sort.',
                'options': [
                    ('HeapSort', False),
                    ('QuickSort', False),
                    ('MergeSort', True),
                    ('SelectionSort', False),
                ]
            },
            {
                'text': 'What is the optimal auxiliary space complexity of standard DFS on a tree with height H?',
                'marks': 1.0,
                'explanation': 'The recursion stack in DFS stores at most H frames corresponding to the height of the tree.',
                'options': [
                    ('O(1)', False),
                    ('O(H)', True),
                    ('O(N^2)', False),
                    ('O(N log N)', False),
                ]
            },
            {
                'text': 'Which collision resolution technique in Hash Tables uses a linked list at each index?',
                'marks': 1.0,
                'explanation': 'Separate Chaining resolves collisions by maintaining a chain/linked list of records at each bucket.',
                'options': [
                    ('Linear Probing', False),
                    ('Separate Chaining', True),
                    ('Quadratic Probing', False),
                    ('Double Hashing', False),
                ]
            },
            {
                'text': 'What is the height of a balanced AVL tree having N nodes?',
                'marks': 1.0,
                'explanation': 'AVL trees enforce a strict balance factor condition, guaranteeing a height bounded by O(log N).',
                'options': [
                    ('O(log N)', True),
                    ('O(N)', False),
                    ('O(N^(1/2))', False),
                    ('O(1)', False),
                ]
            },
            {
                'text': 'In Dynamic Programming, which property indicates that optimal solution of a problem incorporates optimal solutions of subproblems?',
                'marks': 1.0,
                'explanation': 'Optimal Substructure means optimal solutions to subproblems combine to give the optimal overall solution.',
                'options': [
                    ('Overlapping Subproblems', False),
                    ('Optimal Substructure', True),
                    ('Greedy Choice Property', False),
                    ('Memoization Property', False),
                ]
            }
        ]

        if exam1.questions.count() == 0:
            for idx, q_data in enumerate(dsa_questions, 1):
                q = Question.objects.create(
                    exam=exam1,
                    question_text=q_data['text'],
                    marks=q_data['marks'],
                    explanation=q_data['explanation'],
                    order=idx
                )
                for opt_idx, (opt_text, is_corr) in enumerate(q_data['options'], 1):
                    Option.objects.create(
                        question=q,
                        option_text=opt_text,
                        is_correct=is_corr,
                        order=opt_idx
                    )

        # Exam 2: DBMS Final Quiz
        exam2, _ = Exam.objects.get_or_create(
            title='DBMS & SQL Placement Readiness Quiz',
            subject=dbms,
            defaults={
                'description': 'ACID Properties, Normal Forms (1NF to BCNF), Joins, and Indexing architectures.',
                'created_by': teacher2,
                'duration_minutes': 20,
                'total_marks': Decimal('5.00'),
                'passing_marks': Decimal('2.00'),
                'negative_marking_enabled': True,
                'negative_marks_per_question': Decimal('0.33'),
                'is_published': True,
                'random_question_order': True,
                'random_option_order': True,
                'show_answers_after_submission': True,
            }
        )

        dbms_questions = [
            {
                'text': 'Which ACID property ensures that either all database modifications take effect or none do?',
                'marks': 1.0,
                'explanation': 'Atomicity guarantees the "all or nothing" execution rule for database transactions.',
                'options': [
                    ('Atomicity', True),
                    ('Consistency', False),
                    ('Isolation', False),
                    ('Durability', False),
                ]
            },
            {
                'text': 'A relation is in 3NF if it is in 2NF and has no:',
                'marks': 1.0,
                'explanation': 'Third Normal Form (3NF) eliminates transitive functional dependencies for non-prime attributes.',
                'options': [
                    ('Partial Dependency', False),
                    ('Transitive Dependency', True),
                    ('Multivalued Dependency', False),
                    ('Join Dependency', False),
                ]
            },
            {
                'text': 'Which SQL clause is used to filter results returned by an aggregate GROUP BY query?',
                'marks': 1.0,
                'explanation': 'HAVING operates on aggregated grouped records, whereas WHERE filters individual rows prior to aggregation.',
                'options': [
                    ('WHERE', False),
                    ('ORDER BY', False),
                    ('HAVING', True),
                    ('FILTER BY', False),
                ]
            },
            {
                'text': 'What type of index organizes physical data records on disk in sorted order matching the index key?',
                'marks': 1.0,
                'explanation': 'A Clustered Index determines the physical arrangement of rows in the table.',
                'options': [
                    ('Non-Clustered Index', False),
                    ('Clustered Index', True),
                    ('Bitmap Index', False),
                    ('Sparse Index', False),
                ]
            },
            {
                'text': 'In SQL, which lock prevents other concurrent transactions from reading or writing a row?',
                'marks': 1.0,
                'explanation': 'An Exclusive Lock (X lock) restricts both concurrent reads and writes by other transactions.',
                'options': [
                    ('Shared Lock', False),
                    ('Exclusive Lock', True),
                    ('Intent Shared Lock', False),
                    ('Update Lock', False),
                ]
            }
        ]

        if exam2.questions.count() == 0:
            for idx, q_data in enumerate(dbms_questions, 1):
                q = Question.objects.create(
                    exam=exam2,
                    question_text=q_data['text'],
                    marks=q_data['marks'],
                    explanation=q_data['explanation'],
                    order=idx
                )
                for opt_idx, (opt_text, is_corr) in enumerate(q_data['options'], 1):
                    Option.objects.create(
                        question=q,
                        option_text=opt_text,
                        is_correct=is_corr,
                        order=opt_idx
                    )

        # Exam 3: Python Web Quiz (Unpublished Draft)
        exam3, _ = Exam.objects.get_or_create(
            title='Django & Python Full-Stack Mastery',
            subject=py_web,
            defaults={
                'description': 'MVT pattern, middleware flow, Django ORM query optimization, and REST API authentication.',
                'created_by': teacher2,
                'duration_minutes': 30,
                'total_marks': Decimal('5.00'),
                'passing_marks': Decimal('2.50'),
                'negative_marking_enabled': False,
                'is_published': True,
                'random_question_order': True,
                'random_option_order': False,
                'show_answers_after_submission': True,
            }
        )

        py_questions = [
            {
                'text': 'In Django architecture, what does MVT stand for?',
                'marks': 1.0,
                'explanation': 'Django uses Model-View-Template pattern to handle data, presentation, and logic.',
                'options': [
                    ('Model-View-Template', True),
                    ('Model-Variable-Test', False),
                    ('Module-View-Thread', False),
                    ('Main-Variable-Type', False),
                ]
            },
            {
                'text': 'Which Django ORM method helps prevent the N+1 queries problem when traversing foreign key relationships?',
                'marks': 1.0,
                'explanation': 'select_related does SQL JOINs to eagerly load single-valued related foreign keys.',
                'options': [
                    ('filter()', False),
                    ('select_related()', True),
                    ('defer()', False),
                    ('only()', False),
                ]
            },
            {
                'text': 'What is the purpose of Django CSRF token middleware?',
                'marks': 1.0,
                'explanation': 'It protects against Cross-Site Request Forgery attacks on POST, PUT, and DELETE forms.',
                'options': [
                    ('Prevents Cross-Site Request Forgery attacks', True),
                    ('Encrypts database passwords', False),
                    ('Accelerates static media caching', False),
                    ('Manages user session cookies', False),
                ]
            },
            {
                'text': 'In Python, what is the output type of a generator function using the "yield" keyword?',
                'marks': 1.0,
                'explanation': 'Yielding values produces an iterator/generator object evaluated lazily.',
                'options': [
                    ('List', False),
                    ('Generator Iterator', True),
                    ('Tuple', False),
                    ('Dictionary', False),
                ]
            },
            {
                'text': 'Which command creates new database migration files in Django based on changes in models.py?',
                'marks': 1.0,
                'explanation': 'python manage.py makemigrations scans model definitions and writes migration files.',
                'options': [
                    ('python manage.py migrate', False),
                    ('python manage.py makemigrations', True),
                    ('python manage.py sqlmigrate', False),
                    ('python manage.py showmigrations', False),
                ]
            }
        ]

        if exam3.questions.count() == 0:
            for idx, q_data in enumerate(py_questions, 1):
                q = Question.objects.create(
                    exam=exam3,
                    question_text=q_data['text'],
                    marks=q_data['marks'],
                    explanation=q_data['explanation'],
                    order=idx
                )
                for opt_idx, (opt_text, is_corr) in enumerate(q_data['options'], 1):
                    Option.objects.create(
                        question=q,
                        option_text=opt_text,
                        is_correct=is_corr,
                        order=opt_idx
                    )

        self.stdout.write(self.style.SUCCESS("[OK] Exams and 20+ Questions with options seeded"))

        # 4. Create Simulated Completed Attempts with full answers for Charts & Leaderboards
        # Student 1 (Rahul) takes Exam 1
        self.create_simulated_attempt(student1, exam1, target_score_perc=90, delta_mins=18)
        # Student 2 (Priya) takes Exam 1
        self.create_simulated_attempt(student2, exam1, target_score_perc=100, delta_mins=14)
        # Student 3 (Amit) takes Exam 1
        self.create_simulated_attempt(student3, exam1, target_score_perc=70, delta_mins=22)
        # Student 4 (Sneha) takes Exam 1
        self.create_simulated_attempt(student4, exam1, target_score_perc=40, delta_mins=24)

        # Student 1 (Rahul) takes Exam 2
        self.create_simulated_attempt(student1, exam2, target_score_perc=80, delta_mins=12)
        # Student 2 (Priya) takes Exam 2
        self.create_simulated_attempt(student2, exam2, target_score_perc=100, delta_mins=10)

        self.stdout.write(self.style.SUCCESS("[OK] Pre-evaluated test attempts and leaderboards seeded!"))
        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully."))

    def create_simulated_attempt(self, student, exam, target_score_perc, delta_mins):
        if ExamAttempt.objects.filter(student=student, exam=exam).exists():
            return

        questions = list(exam.questions.prefetch_related('options').all())
        if not questions:
            return

        start_t = timezone.now() - timedelta(hours=random.randint(2, 48), minutes=delta_mins)
        submit_t = start_t + timedelta(minutes=delta_mins)

        attempt = ExamAttempt.objects.create(
            student=student,
            exam=exam,
            start_time=start_t,
            submitted_at=submit_t,
            end_time=submit_t,
            status=ExamAttempt.Status.SUBMITTED,
            time_taken_seconds=delta_mins * 60,
            question_order_json=json.dumps([q.id for q in questions]),
            total_questions=len(questions),
            ip_address="127.0.0.1"
        )

        total_q = len(questions)
        correct_needed = int(round((target_score_perc / 100.0) * total_q))

        for idx, q in enumerate(questions):
            options = list(q.options.all())
            correct_opt = q.correct_option
            wrong_opts = [o for o in options if not o.is_correct]

            if idx < correct_needed:
                selected = correct_opt
            elif wrong_opts:
                selected = random.choice(wrong_opts)
            else:
                selected = None

            StudentAnswer.objects.create(
                attempt=attempt,
                question=q,
                selected_option=selected,
                is_marked_for_review=(idx == 2)
            )

        attempt.calculate_results(save=True)
