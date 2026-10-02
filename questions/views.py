from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.db import transaction
from decimal import Decimal
import csv
import json

from exams.models import Exam
from .models import Question, Option
from .forms import QuestionWith4OptionsForm, BulkUploadForm
from accounts.decorators import admin_or_teacher_required


def check_exam_permission(user, exam):
    """
    Checks whether the user is authorized to manage questions for the given exam.
    - Admin / Superuser: Full access to all exams.
    - Teacher: Access only to exams they created.
    - Student: No access (returns False).
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_admin_user:
        return True
    if user.is_teacher_user and exam.created_by == user:
        return True
    return False


@admin_or_teacher_required
def question_list_view(request, exam_id):
    exam = get_object_or_404(Exam.objects.select_related('subject', 'created_by'), id=exam_id)
    if not check_exam_permission(request.user, exam):
        messages.error(request, "Access Denied: You can only view and manage questions for exams you created.")
        return redirect('exams:exam_list')

    questions = exam.questions.prefetch_related('options').all()
    return render(request, 'questions/question_list.html', {
        'exam': exam,
        'questions': questions,
        'is_admin': request.user.is_admin_user
    })


@admin_or_teacher_required
def question_create_view(request, exam_id):
    exam = get_object_or_404(Exam.objects.select_related('subject', 'created_by'), id=exam_id)
    if not check_exam_permission(request.user, exam):
        messages.error(request, "Access Denied: You can only add questions to exams you created.")
        return redirect('exams:exam_list')

    next_order = exam.questions.count() + 1

    if request.method == 'POST':
        form = QuestionWith4OptionsForm(request.POST)
        if form.is_valid():
            try:
                question = form.save_question_and_options(exam=exam)
                
                # Check if user clicked "Save and Add Another"
                if 'save_and_add' in request.POST:
                    messages.success(request, f"Question #{question.order} added successfully! You can now add the next question.")
                    return redirect('questions:question_create', exam_id=exam.id)
                
                messages.success(request, f"Question #{question.order} added successfully to '{exam.title}'.")
                return redirect('questions:question_list', exam_id=exam.id)
            except Exception as e:
                messages.error(request, f"An error occurred while saving the question: {str(e)}")
        else:
            messages.error(request, "Failed to add question. Please correct the highlighted errors below.")
    else:
        form = QuestionWith4OptionsForm(initial={'order': next_order, 'marks': 1.00, 'correct_option': '1'})

    return render(request, 'questions/question_form.html', {
        'form': form,
        'exam': exam,
        'title': f'Add Question to {exam.title}',
        'is_edit': False
    })


@admin_or_teacher_required
def question_edit_view(request, exam_id, question_id):
    exam = get_object_or_404(Exam.objects.select_related('subject', 'created_by'), id=exam_id)
    if not check_exam_permission(request.user, exam):
        messages.error(request, "Access Denied: You can only edit questions for exams you created.")
        return redirect('exams:exam_list')

    question = get_object_or_404(Question, id=question_id, exam=exam)

    if request.method == 'POST':
        form = QuestionWith4OptionsForm(request.POST, instance=question)
        if form.is_valid():
            try:
                form.save_question_and_options(exam=exam)
                messages.success(request, f"Question #{question.order} updated successfully.")
                return redirect('questions:question_list', exam_id=exam.id)
            except Exception as e:
                messages.error(request, f"An error occurred while updating the question: {str(e)}")
        else:
            messages.error(request, "Failed to update question. Please correct the highlighted errors below.")
    else:
        form = QuestionWith4OptionsForm(instance=question)

    return render(request, 'questions/question_form.html', {
        'form': form,
        'exam': exam,
        'question': question,
        'title': f'Edit Question #{question.order}',
        'is_edit': True
    })


@admin_or_teacher_required
def question_delete_view(request, exam_id, question_id):
    exam = get_object_or_404(Exam.objects.select_related('subject', 'created_by'), id=exam_id)
    if not check_exam_permission(request.user, exam):
        messages.error(request, "Access Denied: You can only delete questions from exams you created.")
        return redirect('exams:exam_list')

    question = get_object_or_404(Question, id=question_id, exam=exam)

    if request.method == 'POST':
        q_order = question.order
        question.delete()
        messages.success(request, f"Question #{q_order} has been deleted successfully.")
        return redirect('questions:question_list', exam_id=exam.id)

    # GET displays the confirmation page
    return render(request, 'questions/question_confirm_delete.html', {
        'exam': exam,
        'question': question
    })


@admin_or_teacher_required
def question_bulk_upload_view(request, exam_id):
    exam = get_object_or_404(Exam.objects.select_related('subject', 'created_by'), id=exam_id)
    if not check_exam_permission(request.user, exam):
        messages.error(request, "Access Denied: You can only bulk upload questions to exams you created.")
        return redirect('exams:exam_list')

    if request.method == 'POST':
        form = BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            filename = uploaded_file.name.lower()
            created_count = 0

            try:
                with transaction.atomic():
                    if filename.endswith('.csv'):
                        decoded_file = uploaded_file.read().decode('utf-8-sig').splitlines()
                        reader = csv.DictReader(decoded_file)
                        current_order = exam.questions.count()

                        for row in reader:
                            q_text = row.get('question_text', '').strip()
                            opt_a = row.get('option_a', '').strip()
                            opt_b = row.get('option_b', '').strip()
                            opt_c = row.get('option_c', '').strip()
                            opt_d = row.get('option_d', '').strip()
                            correct_opt = row.get('correct_option', '1').strip()
                            explanation = row.get('explanation', '').strip()
                            
                            try:
                                raw_marks = row.get('marks', '1.0').strip()
                                marks = Decimal(raw_marks) if raw_marks else Decimal('1.00')
                            except Exception:
                                marks = Decimal('1.00')

                            if q_text and opt_a and opt_b and opt_c and opt_d:
                                current_order += 1
                                q = Question.objects.create(
                                    exam=exam,
                                    question_text=q_text,
                                    marks=marks,
                                    negative_marks=Decimal('0.00'),
                                    explanation=explanation,
                                    order=current_order
                                )
                                corr_num = int(correct_opt) if correct_opt.isdigit() and 1 <= int(correct_opt) <= 4 else 1
                                options = [opt_a, opt_b, opt_c, opt_d]
                                for i, text in enumerate(options):
                                    Option.objects.create(
                                        question=q,
                                        option_text=text,
                                        is_correct=(i + 1 == corr_num),
                                        order=i + 1
                                    )
                                created_count += 1

                    elif filename.endswith('.json'):
                        data = json.load(uploaded_file)
                        current_order = exam.questions.count()
                        for item in data:
                            q_text = item.get('question_text', '').strip()
                            options_list = item.get('options', [])
                            correct_idx = item.get('correct_option_index', 0)
                            try:
                                marks = Decimal(str(item.get('marks', 1.0)))
                            except Exception:
                                marks = Decimal('1.00')
                            explanation = item.get('explanation', '')

                            if q_text and len(options_list) >= 2:
                                current_order += 1
                                q = Question.objects.create(
                                    exam=exam,
                                    question_text=q_text,
                                    marks=marks,
                                    negative_marks=Decimal('0.00'),
                                    explanation=explanation,
                                    order=current_order
                                )
                                for idx, opt_text in enumerate(options_list):
                                    Option.objects.create(
                                        question=q,
                                        option_text=str(opt_text).strip(),
                                        is_correct=(idx == correct_idx),
                                        order=idx + 1
                                    )
                                created_count += 1

                if created_count > 0:
                    messages.success(request, f"Successfully imported {created_count} questions into '{exam.title}'!")
                    return redirect('questions:question_list', exam_id=exam.id)
                else:
                    messages.warning(request, "No valid questions were found in the uploaded file. Please check the file format.")

            except Exception as e:
                messages.error(request, f"Failed to parse uploaded file: {str(e)}")
        else:
            messages.error(request, "Invalid file submission. Please upload a valid CSV or JSON file.")
    else:
        form = BulkUploadForm()

    return render(request, 'questions/bulk_upload.html', {'form': form, 'exam': exam})


@login_required
def download_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_exam_questions.csv"'
    writer = csv.writer(response)
    writer.writerow(['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'marks', 'explanation'])
    writer.writerow([
        'Which data structure follows the LIFO (Last In First Out) principle?',
        'Queue',
        'Stack',
        'Linked List',
        'Binary Tree',
        '2',
        '1.0',
        'Stack operates on Last-In First-Out (LIFO) order.'
    ])
    writer.writerow([
        'What is the worst-case time complexity of QuickSort?',
        'O(n log n)',
        'O(n)',
        'O(n^2)',
        'O(log n)',
        '3',
        '1.0',
        'QuickSort exhibits O(n^2) time complexity when bad pivots are chosen consistently.'
    ])
    return response

