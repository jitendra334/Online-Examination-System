from django.contrib import admin
from .models import ExamAttempt, StudentAnswer

class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    readonly_fields = ('question', 'selected_option', 'is_correct', 'marks_obtained', 'is_marked_for_review')
    can_delete = False

@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'student', 'exam', 'status', 'final_score', 'total_marks',
        'percentage', 'is_passed', 'attempted_questions', 'correct_answers', 'submitted_at'
    )
    list_filter = ('status', 'is_passed', 'exam__subject', 'exam')
    search_fields = ('student__username', 'student__email', 'student__student_id', 'exam__title')
    readonly_fields = (
        'student', 'exam', 'start_time', 'end_time', 'submitted_at',
        'time_taken_seconds', 'total_questions', 'attempted_questions',
        'correct_answers', 'wrong_answers', 'unanswered_questions',
        'marked_for_review_count', 'total_marks', 'negative_marks',
        'final_score', 'percentage', 'is_passed', 'ip_address'
    )
    inlines = [StudentAnswerInline]

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'question', 'selected_option', 'is_correct', 'marks_obtained', 'is_marked_for_review')
    list_filter = ('is_correct', 'is_marked_for_review')
    search_fields = ('attempt__student__username', 'question__question_text')
