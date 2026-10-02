from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Subject, Exam
from .forms import SubjectForm, ExamForm
from accounts.decorators import admin_required, admin_or_teacher_required

@login_required
def exam_list_view(request):
    """
    Shows list of exams:
    - If student: shows active/available published exams.
    - If teacher/admin: shows exams with management actions (edit, delete, publish).
    """
    query = request.GET.get('q', '').strip()
    subject_id = request.GET.get('subject', '')
    status_filter = request.GET.get('status', '')

    subjects = Subject.objects.all()

    if request.user.is_student_user:
        exams_qs = Exam.objects.filter(is_published=True).select_related('subject', 'created_by')
    elif request.user.is_admin_user:
        exams_qs = Exam.objects.all().select_related('subject', 'created_by')
    else:  # Teacher
        exams_qs = Exam.objects.filter(created_by=request.user).select_related('subject', 'created_by')

    if query:
        exams_qs = exams_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(subject__name__icontains=query) |
            Q(subject__code__icontains=query)
        )

    if subject_id:
        exams_qs = exams_qs.filter(subject_id=subject_id)

    if status_filter == 'published':
        exams_qs = exams_qs.filter(is_published=True)
    elif status_filter == 'draft':
        exams_qs = exams_qs.filter(is_published=False)

    paginator = Paginator(exams_qs, 12)
    page_number = request.GET.get('page')
    exams = paginator.get_page(page_number)

    # If student, attach attempt status info to each exam
    if request.user.is_student_user:
        for exam in exams:
            attempts = exam.attempts.filter(student=request.user, status__in=['SUBMITTED', 'EXPIRED'])
            exam.user_attempts_count = attempts.count()
            exam.has_attempted = attempts.exists()
            exam.latest_attempt = attempts.order_by('-submitted_at').first()

    context = {
        'exams': exams,
        'subjects': subjects,
        'query': query,
        'selected_subject': subject_id,
        'status_filter': status_filter,
    }

    if request.user.is_student_user:
        return render(request, 'exams/student_exam_list.html', context)
    return render(request, 'exams/exam_list.html', context)


@admin_or_teacher_required
def exam_create_view(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            messages.success(request, f"Exam '{exam.title}' created successfully! Now add questions to it.")
            return redirect('questions:question_create', exam_id=exam.id)
        else:
            messages.error(request, "Please check the form errors.")
    else:
        # Pre-select subject if passed in query param
        initial_subject = request.GET.get('subject')
        form = ExamForm(initial={'subject': initial_subject} if initial_subject else None)

    return render(request, 'exams/exam_form.html', {'form': form, 'title': 'Create New Exam'})


@admin_or_teacher_required
def exam_edit_view(request, exam_id):
    if request.user.is_admin_user:
        exam = get_object_or_404(Exam, id=exam_id)
    else:
        exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)

    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, f"Exam '{exam.title}' updated successfully.")
            return redirect('exams:exam_detail', exam_id=exam.id)
        else:
            messages.error(request, "Please check the form errors.")
    else:
        form = ExamForm(instance=exam)

    return render(request, 'exams/exam_form.html', {'form': form, 'exam': exam, 'title': f'Edit Exam: {exam.title}'})


@admin_or_teacher_required
def exam_delete_view(request, exam_id):
    if request.user.is_admin_user:
        exam = get_object_or_404(Exam, id=exam_id)
    else:
        exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)

    if request.method == 'POST':
        title = exam.title
        exam.delete()
        messages.success(request, f"Exam '{title}' has been deleted permanently.")
        return redirect('exams:exam_list')

    return render(request, 'exams/exam_confirm_delete.html', {'exam': exam})


@admin_or_teacher_required
def exam_toggle_publish(request, exam_id):
    if request.user.is_admin_user:
        exam = get_object_or_404(Exam, id=exam_id)
    else:
        exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)

    if not exam.is_published and exam.questions.count() == 0:
        messages.warning(request, "Cannot publish an exam with zero questions. Please add questions first.")
        return redirect('exams:exam_detail', exam_id=exam.id)

    exam.is_published = not exam.is_published
    exam.save()
    status_text = "published and is now visible to students" if exam.is_published else "unpublished (saved as draft)"
    messages.success(request, f"Exam '{exam.title}' is now {status_text}.")
    return redirect('exams:exam_detail', exam_id=exam.id)


@login_required
def exam_detail_view(request, exam_id):
    exam = get_object_or_404(Exam.objects.select_related('subject', 'created_by').prefetch_related('questions'), id=exam_id)
    
    # If student, redirect to instructions view
    if request.user.is_student_user:
        return redirect('exams:exam_instructions', exam_id=exam.id)

    # Permission check for teachers
    if not request.user.is_admin_user and exam.created_by != request.user:
        messages.error(request, "You do not have permission to manage this exam.")
        return redirect('exams:exam_list')

    questions = exam.questions.prefetch_related('options').all()
    attempts = exam.attempts.filter(status__in=['SUBMITTED', 'EXPIRED']).select_related('student')
    
    attempts_count = attempts.count()
    passed_count = attempts.filter(is_passed=True).count()
    avg_score = attempts.aggregate(Avg('final_score'))['final_score__avg'] or 0
    avg_percentage = attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0

    context = {
        'exam': exam,
        'questions': questions,
        'attempts_count': attempts_count,
        'passed_count': passed_count,
        'avg_score': round(avg_score, 2),
        'avg_percentage': round(avg_percentage, 1),
        'pass_rate': round((passed_count / attempts_count * 100), 1) if attempts_count > 0 else 0,
    }
    return render(request, 'exams/exam_detail.html', context)


@login_required
def exam_instructions_view(request, exam_id):
    exam = get_object_or_404(Exam.objects.select_related('subject', 'created_by'), id=exam_id)
    
    can_attempt, reason = exam.can_student_attempt(request.user)
    past_attempts = exam.attempts.filter(student=request.user).order_by('-created_at')

    context = {
        'exam': exam,
        'can_attempt': can_attempt,
        'reason': reason,
        'past_attempts': past_attempts,
    }
    return render(request, 'exams/exam_instructions.html', context)


# --- Subject Management ---

@admin_or_teacher_required
def subject_list_view(request):
    subjects = Subject.objects.annotate(
        exam_count=Count('exams'),
        question_count=Count('exams__questions')
    ).order_by('name')
    return render(request, 'exams/subject_list.html', {'subjects': subjects})


@admin_or_teacher_required
def subject_create_view(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.created_by = request.user
            subject.save()
            messages.success(request, f"Subject '{subject.name}' created successfully.")
            return redirect('exams:subject_list')
    else:
        form = SubjectForm()
    return render(request, 'exams/subject_form.html', {'form': form, 'title': 'Add New Subject'})


@admin_or_teacher_required
def subject_edit_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, f"Subject '{subject.name}' updated successfully.")
            return redirect('exams:subject_list')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'exams/subject_form.html', {'form': form, 'subject': subject, 'title': f'Edit Subject: {subject.name}'})


@admin_required
def subject_delete_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        name = subject.name
        subject.delete()
        messages.success(request, f"Subject '{name}' deleted.")
        return redirect('exams:subject_list')
    return render(request, 'exams/subject_confirm_delete.html', {'subject': subject})
