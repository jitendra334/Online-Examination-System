from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.db.models import Count, Avg, Max, Q
from django.core.paginator import Paginator
import json
import random
import csv
import io

from exams.models import Exam
from questions.models import Question, Option
from .models import ExamAttempt, StudentAnswer
from accounts.decorators import student_required, teacher_required, admin_or_teacher_required

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def start_exam_view(request, exam_id):
    exam = get_object_or_404(Exam.objects.prefetch_related('questions'), id=exam_id)

    # Check if there is an in-progress attempt already
    existing_in_progress = ExamAttempt.objects.filter(
        student=request.user,
        exam=exam,
        status=ExamAttempt.Status.IN_PROGRESS
    ).first()

    if existing_in_progress:
        # Check if time expired on existing attempt
        if existing_in_progress.is_time_expired():
            existing_in_progress.calculate_results(save=True, auto_expired=True)
            messages.warning(request, "Your previous attempt has timed out and has been submitted.")
            return redirect('results:result_detail', attempt_id=existing_in_progress.id)
        return redirect('results:take_exam', attempt_id=existing_in_progress.id)

    # Validate if student is permitted to attempt
    can_attempt, reason = exam.can_student_attempt(request.user)
    if not can_attempt:
        messages.error(request, reason)
        return redirect('exams:exam_instructions', exam_id=exam.id)

    questions = list(exam.questions.all())
    if not questions:
        messages.error(request, "This exam has no questions yet.")
        return redirect('exams:exam_list')

    # Prepare question order
    if exam.random_question_order:
        random.shuffle(questions)
    
    question_ids = [q.id for q in questions]

    # Create new attempt
    attempt = ExamAttempt.objects.create(
        student=request.user,
        exam=exam,
        start_time=timezone.now(),
        status=ExamAttempt.Status.IN_PROGRESS,
        question_order_json=json.dumps(question_ids),
        total_questions=len(questions),
        ip_address=get_client_ip(request)
    )

    # Initialize empty StudentAnswer records for all questions
    answers_to_create = []
    for q in questions:
        answers_to_create.append(
            StudentAnswer(attempt=attempt, question=q)
        )
    StudentAnswer.objects.bulk_create(answers_to_create)

    messages.info(request, "Examination started. Best of luck!")
    return redirect('results:take_exam', attempt_id=attempt.id)


@login_required
def take_exam_view(request, attempt_id):
    attempt = get_object_or_404(
        ExamAttempt.objects.select_related('exam', 'exam__subject', 'student'),
        id=attempt_id,
        student=request.user
    )

    # If already submitted or expired, redirect to result
    if attempt.status != ExamAttempt.Status.IN_PROGRESS:
        messages.info(request, "This examination has already been completed.")
        return redirect('results:result_detail', attempt_id=attempt.id)

    # Check server-side time expiration
    remaining_secs = attempt.remaining_seconds()
    if remaining_secs <= 0:
        attempt.calculate_results(save=True, auto_expired=True)
        messages.warning(request, "Time expired! Your exam has been automatically submitted.")
        return redirect('results:result_detail', attempt_id=attempt.id)

    # Retrieve questions in the stored randomized order
    question_ids = attempt.question_ids
    if not question_ids:
        questions = list(attempt.exam.questions.prefetch_related('options').all())
    else:
        # Preserve order from question_ids
        questions_dict = {q.id: q for q in attempt.exam.questions.prefetch_related('options').all()}
        questions = [questions_dict[qid] for qid in question_ids if qid in questions_dict]

    # If exam has random option order, shuffle options per question
    if attempt.exam.random_option_order:
        for q in questions:
            opts = list(q.options.all())
            random.shuffle(opts)
            q.shuffled_options = opts
    else:
        for q in questions:
            q.shuffled_options = list(q.options.all())

    # Map current student answers
    student_answers = {ans.question_id: ans for ans in attempt.answers.all()}

    # Format questions data structure for frontend
    questions_data = []
    for idx, q in enumerate(questions, start=1):
        ans = student_answers.get(q.id)
        selected_opt_id = ans.selected_option_id if ans and ans.selected_option_id else None
        is_review = ans.is_marked_for_review if ans else False

        options_payload = []
        for opt in q.shuffled_options:
            options_payload.append({
                'id': opt.id,
                'text': opt.option_text,
                'order': opt.order
            })

        questions_data.append({
            'index': idx,
            'id': q.id,
            'text': q.question_text,
            'marks': float(q.marks),
            'negative_marks': float(q.get_negative_penalty()),
            'options': options_payload,
            'selected_option_id': selected_opt_id,
            'is_marked_for_review': is_review,
        })

    context = {
        'attempt': attempt,
        'exam': attempt.exam,
        'remaining_seconds': remaining_secs,
        'duration_minutes': attempt.exam.duration_minutes,
        'questions_json': json.dumps(questions_data),
        'total_questions': len(questions_data),
    }
    return render(request, 'results/take_exam.html', context)


@login_required
@require_POST
def ajax_save_answer(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, student=request.user)

    if attempt.status != ExamAttempt.Status.IN_PROGRESS or attempt.is_time_expired():
        return JsonResponse({'status': 'expired', 'message': 'Exam time has expired.'}, status=403)

    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        option_id = data.get('option_id')
        is_marked = data.get('is_marked_for_review', False)

        question = get_object_or_404(Question, id=question_id, exam=attempt.exam)
        option = get_object_or_404(Option, id=option_id, question=question) if option_id else None

        student_answer, created = StudentAnswer.objects.get_or_create(
            attempt=attempt,
            question=question
        )
        student_answer.selected_option = option
        student_answer.is_marked_for_review = is_marked
        student_answer.save()

        return JsonResponse({
            'status': 'success',
            'remaining_seconds': attempt.remaining_seconds(),
            'question_id': question_id,
            'selected_option_id': option_id,
            'is_marked_for_review': is_marked
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def ajax_clear_answer(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, student=request.user)

    if attempt.status != ExamAttempt.Status.IN_PROGRESS or attempt.is_time_expired():
        return JsonResponse({'status': 'expired', 'message': 'Exam time has expired.'}, status=403)

    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        is_marked = data.get('is_marked_for_review', False)

        question = get_object_or_404(Question, id=question_id, exam=attempt.exam)

        student_answer, created = StudentAnswer.objects.get_or_create(
            attempt=attempt,
            question=question
        )
        student_answer.selected_option = None
        student_answer.is_marked_for_review = is_marked
        student_answer.save()

        return JsonResponse({
            'status': 'success',
            'remaining_seconds': attempt.remaining_seconds(),
            'question_id': question_id,
            'selected_option_id': None,
            'is_marked_for_review': is_marked
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def ajax_toggle_review(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, student=request.user)

    if attempt.status != ExamAttempt.Status.IN_PROGRESS or attempt.is_time_expired():
        return JsonResponse({'status': 'expired', 'message': 'Exam time has expired.'}, status=403)

    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        is_marked = data.get('is_marked_for_review', False)

        question = get_object_or_404(Question, id=question_id, exam=attempt.exam)

        student_answer, created = StudentAnswer.objects.get_or_create(
            attempt=attempt,
            question=question
        )
        student_answer.is_marked_for_review = is_marked
        student_answer.save()

        return JsonResponse({
            'status': 'success',
            'question_id': question_id,
            'is_marked_for_review': is_marked
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def submit_exam_view(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, student=request.user)

    if attempt.status == ExamAttempt.Status.IN_PROGRESS:
        is_expired = attempt.is_time_expired()
        attempt.calculate_results(save=True, auto_expired=is_expired)
        messages.success(request, "Your examination has been submitted and evaluated successfully!")

    return redirect('results:result_detail', attempt_id=attempt.id)


@login_required
def result_detail_view(request, attempt_id):
    attempt = get_object_or_404(
        ExamAttempt.objects.select_related('student', 'exam', 'exam__subject'),
        id=attempt_id
    )

    # Permission: Only the student who attempted or admin/exam creator teacher can view
    if not (request.user == attempt.student or request.user.is_admin_user or attempt.exam.created_by == request.user):
        messages.error(request, "Permission denied.")
        return redirect('dashboard:index')

    # If still in progress, redirect back to exam
    if attempt.status == ExamAttempt.Status.IN_PROGRESS:
        if not attempt.is_time_expired():
            return redirect('results:take_exam', attempt_id=attempt.id)
        else:
            attempt.calculate_results(save=True, auto_expired=True)

    # Compute Rank among submitted attempts for this exam
    higher_scores = ExamAttempt.objects.filter(
        exam=attempt.exam,
        status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED],
        final_score__gt=attempt.final_score
    ).count()
    total_participants = ExamAttempt.objects.filter(
        exam=attempt.exam,
        status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED]
    ).count()
    rank = higher_scores + 1

    # Prepare answers review if allowed
    can_view_answers = attempt.exam.show_answers_after_submission or request.user.is_admin_user or attempt.exam.created_by == request.user

    question_reviews = []
    if can_view_answers:
        # Load answers in attempt question order
        answers_map = {ans.question_id: ans for ans in attempt.answers.select_related('selected_option').all()}
        
        question_ids = attempt.question_ids
        if not question_ids:
            questions = list(attempt.exam.questions.prefetch_related('options').all())
        else:
            questions_dict = {q.id: q for q in attempt.exam.questions.prefetch_related('options').all()}
            questions = [questions_dict[qid] for qid in question_ids if qid in questions_dict]

        for idx, q in enumerate(questions, start=1):
            ans = answers_map.get(q.id)
            selected_opt = ans.selected_option if ans else None
            correct_opt = q.correct_option

            status_label = "Unanswered"
            badge_class = "secondary"
            if selected_opt:
                if selected_opt.is_correct:
                    status_label = "Correct"
                    badge_class = "success"
                else:
                    status_label = "Incorrect"
                    badge_class = "danger"

            question_reviews.append({
                'number': idx,
                'question': q,
                'options': q.options.all(),
                'selected_option': selected_opt,
                'correct_option': correct_opt,
                'status_label': status_label,
                'badge_class': badge_class,
                'marks_obtained': ans.marks_obtained if ans else 0.00,
                'is_review': ans.is_marked_for_review if ans else False,
            })

    context = {
        'attempt': attempt,
        'exam': attempt.exam,
        'rank': rank,
        'total_participants': total_participants,
        'can_view_answers': can_view_answers,
        'question_reviews': question_reviews,
    }
    return render(request, 'results/result_detail.html', context)


@login_required
def result_pdf_view(request, attempt_id):
    attempt = get_object_or_404(
        ExamAttempt.objects.select_related('student', 'exam', 'exam__subject'),
        id=attempt_id
    )

    if not (request.user == attempt.student or request.user.is_admin_user or attempt.exam.created_by == request.user):
        return HttpResponse("Unauthorized", status=403)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1e293b'),
        alignment=1, # Center
        fontName='Helvetica-Bold'
    )
    sub_title_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
        fontName='Helvetica'
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1e3a8a'),
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=6
    )
    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155')
    )
    bold_style = ParagraphStyle(
        'BoldText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0f172a')
    )

    # Header
    elements.append(Paragraph("ONLINE EXAMINATION SYSTEM", title_style))
    elements.append(Paragraph("OFFICIAL SCORECARD & PERFORMANCE TRANSCRIPT", sub_title_style))
    elements.append(Spacer(1, 15))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563eb'), spaceAfter=15))

    # Candidate & Exam Information Table
    student_name = attempt.student.full_name
    student_id = attempt.student.student_id or "N/A"
    dept = attempt.student.department or "CSE"
    exam_title = attempt.exam.title
    subject_info = f"{attempt.exam.subject.name} ({attempt.exam.subject.code})"
    date_str = attempt.submitted_at.strftime("%d %B %Y, %I:%M %p") if attempt.submitted_at else "N/A"

    info_data = [
        [Paragraph("Candidate Name:", bold_style), Paragraph(student_name, normal_style),
         Paragraph("Student / Roll ID:", bold_style), Paragraph(student_id, normal_style)],
        [Paragraph("Department:", bold_style), Paragraph(dept, normal_style),
         Paragraph("Date of Exam:", bold_style), Paragraph(date_str, normal_style)],
        [Paragraph("Exam Title:", bold_style), Paragraph(exam_title, normal_style),
         Paragraph("Subject:", bold_style), Paragraph(subject_info, normal_style)],
    ]

    info_table = Table(info_data, colWidths=[110, 150, 110, 150])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 15))

    # Performance Summary Section
    elements.append(Paragraph("Score & Performance Summary", section_heading))
    
    result_status_color = colors.HexColor('#16a34a') if attempt.is_passed else colors.HexColor('#dc2626')
    result_text = "PASSED" if attempt.is_passed else "FAILED"
    
    perf_data = [
        [Paragraph("Metric", bold_style), Paragraph("Score / Value", bold_style), Paragraph("Metric", bold_style), Paragraph("Score / Value", bold_style)],
        [Paragraph("Total Questions", normal_style), Paragraph(str(attempt.total_questions), normal_style),
         Paragraph("Total Maximum Marks", normal_style), Paragraph(f"{attempt.total_marks}", normal_style)],
        [Paragraph("Attempted Questions", normal_style), Paragraph(str(attempt.attempted_questions), normal_style),
         Paragraph("Passing Marks Threshold", normal_style), Paragraph(f"{attempt.exam.passing_marks}", normal_style)],
        [Paragraph("Correct Answers", normal_style), Paragraph(f"<font color='#16a34a'><b>{attempt.correct_answers}</b></font>", normal_style),
         Paragraph("Negative Marks Deducted", normal_style), Paragraph(f"<font color='#dc2626'>-{attempt.negative_marks}</font>", normal_style)],
        [Paragraph("Wrong Answers", normal_style), Paragraph(f"<font color='#dc2626'><b>{attempt.wrong_answers}</b></font>", normal_style),
         Paragraph("Final Score Obtained", bold_style), Paragraph(f"<b>{attempt.final_score} / {attempt.total_marks}</b>", bold_style)],
        [Paragraph("Unanswered Questions", normal_style), Paragraph(str(attempt.unanswered_questions), normal_style),
         Paragraph("Percentage Achieved", bold_style), Paragraph(f"<b>{attempt.percentage}%</b>", bold_style)],
        [Paragraph("Time Taken", normal_style), Paragraph(attempt.duration_formatted(), normal_style),
         Paragraph("Result Qualification", bold_style), Paragraph(f"<b><font color='{result_status_color.hexval()}'>{result_text}</font></b>", bold_style)],
    ]

    perf_table = Table(perf_data, colWidths=[130, 130, 130, 130])
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#93c5fd')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(perf_table)
    elements.append(Spacer(1, 25))

    # Verification Note and Signature
    footer_text = Paragraph(
        "<i>This is a computer-generated official grade sheet generated by the Online Examination System. "
        "No handwritten signature is required for validation.</i>",
        normal_style
    )
    elements.append(footer_text)
    elements.append(Spacer(1, 20))

    sig_data = [
        [Paragraph("Candidate Signature", bold_style), Paragraph("Controller of Examinations", bold_style)],
        [Spacer(1, 20), Spacer(1, 20)],
        [Paragraph("____________________________", normal_style), Paragraph("____________________________", normal_style)],
    ]
    sig_table = Table(sig_data, colWidths=[260, 260])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    buffer.seek(0)
    
    filename = f"Scorecard_{attempt.student.username}_{attempt.exam.id}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def leaderboard_view(request, exam_id=None):
    exams = Exam.objects.filter(is_published=True).order_by('title')
    selected_exam = None
    rankings = []

    if exam_id:
        selected_exam = get_object_or_404(Exam, id=exam_id)
        attempts = ExamAttempt.objects.filter(
            exam=selected_exam,
            status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED]
        ).select_related('student').order_by('-final_score', 'time_taken_seconds')

        for rank, att in enumerate(attempts, start=1):
            rankings.append({
                'rank': rank,
                'student': att.student,
                'score': att.final_score,
                'total_marks': att.total_marks,
                'percentage': att.percentage,
                'time_taken': att.duration_formatted(),
                'is_passed': att.is_passed,
                'date': att.submitted_at,
            })
    else:
        # Global leaderboard by average score & total exams passed
        from django.contrib.auth import get_user_model
        User = get_user_model()
        students = User.objects.filter(role=User.Role.STUDENT).annotate(
            attempts_count=Count('exam_attempts', filter=Q(exam_attempts__status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED])),
            avg_score=Avg('exam_attempts__percentage', filter=Q(exam_attempts__status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED])),
            passed_count=Count('exam_attempts', filter=Q(exam_attempts__is_passed=True))
        ).filter(attempts_count__gt=0).order_by('-avg_score', '-passed_count')

        for rank, st in enumerate(students[:50], start=1):
            rankings.append({
                'rank': rank,
                'student': st,
                'attempts_count': st.attempts_count,
                'avg_percentage': round(st.avg_score or 0, 2),
                'passed_count': st.passed_count,
            })

    context = {
        'exams': exams,
        'selected_exam': selected_exam,
        'rankings': rankings,
        'is_exam_specific': bool(selected_exam),
    }
    return render(request, 'results/leaderboard.html', context)


@student_required
def student_history_view(request):
    attempts_qs = ExamAttempt.objects.filter(
        student=request.user,
        status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED]
    ).select_related('exam', 'exam__subject').order_by('-submitted_at')

    paginator = Paginator(attempts_qs, 10)
    page_number = request.GET.get('page')
    attempts = paginator.get_page(page_number)

    # Aggregate stats
    total_attempts = attempts_qs.count()
    passed_attempts = attempts_qs.filter(is_passed=True).count()
    avg_score = attempts_qs.aggregate(Avg('percentage'))['percentage__avg'] or 0

    context = {
        'attempts': attempts,
        'total_attempts': total_attempts,
        'passed_attempts': passed_attempts,
        'avg_score': round(avg_score, 1),
    }
    return render(request, 'results/student_history.html', context)


@admin_or_teacher_required
def teacher_exam_results_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not (request.user.is_admin_user or exam.created_by == request.user):
        messages.error(request, "Permission denied.")
        return redirect('exams:exam_list')

    attempts_qs = ExamAttempt.objects.filter(
        exam=exam,
        status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED]
    ).select_related('student').order_by('-final_score', 'time_taken_seconds')

    status_filter = request.GET.get('status')
    if status_filter == 'passed':
        attempts_qs = attempts_qs.filter(is_passed=True)
    elif status_filter == 'failed':
        attempts_qs = attempts_qs.filter(is_passed=False)

    total_attempts = attempts_qs.count()
    passed_attempts = attempts_qs.filter(is_passed=True).count()
    avg_score = attempts_qs.aggregate(Avg('final_score'))['final_score__avg'] or 0
    max_score = attempts_qs.aggregate(Max('final_score'))['final_score__max'] or 0

    context = {
        'exam': exam,
        'attempts': attempts_qs,
        'total_attempts': total_attempts,
        'passed_attempts': passed_attempts,
        'avg_score': round(avg_score, 2),
        'max_score': round(max_score, 2),
        'pass_rate': round((passed_attempts / total_attempts * 100), 1) if total_attempts > 0 else 0,
        'status_filter': status_filter,
    }
    return render(request, 'results/teacher_exam_results.html', context)


@admin_or_teacher_required
def export_results_csv(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not (request.user.is_admin_user or exam.created_by == request.user):
        return HttpResponse("Unauthorized", status=403)

    attempts = ExamAttempt.objects.filter(
        exam=exam,
        status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.EXPIRED]
    ).select_related('student').order_by('-final_score')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="results_{exam.title.replace(" ", "_")}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Rank', 'Username', 'Student Name', 'Roll/ID', 'Email', 'Department', 'Attempted Qs', 'Correct', 'Wrong', 'Final Score', 'Total Marks', 'Percentage', 'Status', 'Date'])

    for rank, att in enumerate(attempts, start=1):
        writer.writerow([
            rank,
            att.student.username,
            att.student.full_name,
            att.student.student_id or 'N/A',
            att.student.email,
            att.student.department or 'N/A',
            att.attempted_questions,
            att.correct_answers,
            att.wrong_answers,
            att.final_score,
            att.total_marks,
            f"{att.percentage}%",
            "Passed" if att.is_passed else "Failed",
            att.submitted_at.strftime("%Y-%m-%d %H:%M") if att.submitted_at else 'N/A'
        ])

    return response
