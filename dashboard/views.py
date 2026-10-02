from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Max, Sum, Q
from django.utils import timezone
from datetime import timedelta
import json

from accounts.models import User
from exams.models import Exam, Subject
from questions.models import Question
from results.models import ExamAttempt
from accounts.decorators import admin_required, teacher_required, student_required

@login_required
def index(request):
    """
    Dispatches to role-specific dashboard based on user role.
    """
    if request.user.is_admin_user:
        return admin_dashboard_view(request)
    elif request.user.is_teacher_user:
        return teacher_dashboard_view(request)
    else:
        return student_dashboard_view(request)


@login_required
def admin_dashboard_view(request):
    if not request.user.is_admin_user:
        return redirect('dashboard:index')

    # Core Stats
    total_students = User.objects.filter(role=User.Role.STUDENT).count()
    total_teachers = User.objects.filter(role=User.Role.TEACHER).count()
    total_exams = Exam.objects.count()
    total_questions = Question.objects.count()
    
    submitted_attempts = ExamAttempt.objects.filter(status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED])
    total_attempts = submitted_attempts.count()
    passed_attempts = submitted_attempts.filter(is_passed=True).count()
    failed_attempts = total_attempts - passed_attempts
    overall_pass_rate = round((passed_attempts / total_attempts * 100), 1) if total_attempts > 0 else 0
    avg_score_overall = submitted_attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0

    # Chart 1: Pass vs Fail Distribution
    pass_fail_chart = {
        'labels': ['Passed', 'Failed'],
        'data': [passed_attempts, failed_attempts],
        'colors': ['#10b981', '#ef4444']
    }

    # Chart 2: Subject-wise Exams & Questions
    subjects = Subject.objects.annotate(
        exam_cnt=Count('exams', distinct=True),
        question_cnt=Count('exams__questions', distinct=True)
    )
    subject_labels = [s.name for s in subjects[:7]]
    subject_exam_data = [s.exam_cnt for s in subjects[:7]]
    subject_q_data = [s.question_cnt for s in subjects[:7]]

    subject_chart = {
        'labels': subject_labels,
        'exams': subject_exam_data,
        'questions': subject_q_data,
    }

    # Chart 3: Top Exam Performance
    top_exams = Exam.objects.annotate(
        attempt_count=Count('attempts', filter=Q(attempts__status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED])),
        avg_perc=Avg('attempts__percentage', filter=Q(attempts__status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED]))
    ).filter(attempt_count__gt=0).order_by('-attempt_count')[:6]

    exam_labels = [e.title[:18] + '...' if len(e.title) > 18 else e.title for e in top_exams]
    exam_avg_scores = [round(float(e.avg_perc or 0), 1) for e in top_exams]
    exam_attempts_data = [int(e.attempt_count) for e in top_exams]

    exam_perf_chart = {
        'labels': exam_labels,
        'averages': exam_avg_scores,
        'attempts': exam_attempts_data,
    }

    # Recent Submissions Table
    recent_attempts = submitted_attempts.select_related('student', 'exam', 'exam__subject').order_by('-submitted_at')[:8]
    
    # Active/Recent Exams
    recent_exams = Exam.objects.select_related('subject', 'created_by').order_by('-created_at')[:6]

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_exams': total_exams,
        'total_questions': total_questions,
        'total_attempts': total_attempts,
        'overall_pass_rate': overall_pass_rate,
        'avg_score_overall': round(float(avg_score_overall or 0), 1),
        'pass_fail_chart_json': json.dumps(pass_fail_chart),
        'subject_chart_json': json.dumps(subject_chart),
        'exam_perf_chart_json': json.dumps(exam_perf_chart),
        'recent_attempts': recent_attempts,
        'recent_exams': recent_exams,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def teacher_dashboard_view(request):
    if not (request.user.is_teacher_user or request.user.is_admin_user):
        return redirect('dashboard:index')

    teacher_exams = Exam.objects.filter(created_by=request.user).select_related('subject')
    total_teacher_exams = teacher_exams.count()
    
    total_teacher_questions = Question.objects.filter(exam__created_by=request.user).count()

    teacher_attempts = ExamAttempt.objects.filter(
        exam__created_by=request.user,
        status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED]
    ).select_related('student', 'exam')
    
    total_evaluations = teacher_attempts.count()
    passed_cnt = teacher_attempts.filter(is_passed=True).count()
    failed_cnt = total_evaluations - passed_cnt
    pass_rate = round((passed_cnt / total_evaluations * 100), 1) if total_evaluations > 0 else 0
    avg_score = teacher_attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0

    # Chart: Exam-wise performance for teacher
    exam_stats = teacher_exams.annotate(
        att_cnt=Count('attempts', filter=Q(attempts__status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED])),
        avg_score=Avg('attempts__percentage', filter=Q(attempts__status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED])),
        pass_cnt=Count('attempts', filter=Q(attempts__status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED], attempts__is_passed=True))
    ).filter(att_cnt__gt=0)[:6]

    t_exam_labels = [e.title[:18] + '...' if len(e.title) > 18 else e.title for e in exam_stats]
    t_exam_avg = [round(float(e.avg_score or 0), 1) for e in exam_stats]
    t_exam_pass = [int(e.pass_cnt) for e in exam_stats]
    t_exam_attempts = [int(e.att_cnt) for e in exam_stats]

    teacher_chart = {
        'labels': t_exam_labels,
        'averages': t_exam_avg,
        'passes': t_exam_pass,
        'attempts': t_exam_attempts,
    }

    # Pass vs Fail Chart
    teacher_pass_fail = {
        'labels': ['Passed', 'Failed'],
        'data': [passed_cnt, failed_cnt],
        'colors': ['#10b981', '#ef4444']
    }

    recent_submissions = teacher_attempts.order_by('-submitted_at')[:8]

    context = {
        'total_exams': total_teacher_exams,
        'total_questions': total_teacher_questions,
        'total_evaluations': total_evaluations,
        'pass_rate': pass_rate,
        'avg_score': round(float(avg_score or 0), 1),
        'my_exams': teacher_exams.order_by('-created_at')[:6],
        'recent_submissions': recent_submissions,
        'teacher_chart_json': json.dumps(teacher_chart),
        'teacher_pass_fail_json': json.dumps(teacher_pass_fail),
    }
    return render(request, 'dashboard/teacher_dashboard.html', context)


@login_required
def student_dashboard_view(request):
    if not (request.user.is_student_user or request.user.is_admin_user):
        return redirect('dashboard:index')

    student_attempts = ExamAttempt.objects.filter(
        student=request.user,
        status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED]
    ).select_related('exam', 'exam__subject').order_by('-submitted_at')

    total_attempted = student_attempts.count()
    passed_attempts = student_attempts.filter(is_passed=True).count()
    avg_percentage = student_attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0
    highest_score = student_attempts.aggregate(Max('percentage'))['percentage__max'] or 0
    pass_rate = round((passed_attempts / total_attempted * 100), 1) if total_attempted > 0 else 0

    # Available Exams
    all_published_exams = Exam.objects.filter(is_published=True).select_related('subject', 'created_by').order_by('-created_at')
    
    # Check which exams can be attempted
    available_exams = []
    for ex in all_published_exams:
        attempts_done = ex.attempts.filter(student=request.user, status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED]).count()
        if attempts_done < ex.max_attempts and ex.is_currently_active:
            ex.attempts_done = attempts_done
            available_exams.append(ex)

    # Chart: Student Score Timeline
    chronological_attempts = list(student_attempts.order_by('submitted_at')[:10])
    timeline_labels = [a.exam.title[:15] + '...' if len(a.exam.title) > 15 else a.exam.title for a in chronological_attempts]
    timeline_scores = [float(a.percentage) for a in chronological_attempts]

    student_perf_chart = {
        'labels': timeline_labels,
        'scores': timeline_scores,
    }

    # Subject Mastery Breakdown
    subject_attempts = student_attempts.values('exam__subject__name').annotate(
        subject_avg=Avg('percentage'),
        subject_count=Count('id')
    ).order_by('-subject_avg')

    subject_labels = [s['exam__subject__name'] for s in subject_attempts]
    subject_scores = [round(float(s['subject_avg'] or 0), 1) for s in subject_attempts]

    subject_mastery_chart = {
        'labels': subject_labels,
        'scores': subject_scores,
    }

    context = {
        'total_attempted': total_attempted,
        'passed_attempts': passed_attempts,
        'pass_rate': pass_rate,
        'avg_percentage': round(float(avg_percentage or 0), 1),
        'highest_score': round(float(highest_score or 0), 1),
        'available_exams': available_exams[:6],
        'recent_attempts': student_attempts[:5],
        'student_perf_chart_json': json.dumps(student_perf_chart),
        'subject_mastery_chart_json': json.dumps(subject_mastery_chart),
    }
    return render(request, 'dashboard/student_dashboard.html', context)
