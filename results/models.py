from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

from exams.models import Exam
from questions.models import Question, Option

class ExamAttempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        EXPIRED = 'EXPIRED', 'Time Expired (Auto-Submitted)'
        DISQUALIFIED = 'DISQUALIFIED', 'Disqualified'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_attempts')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS
    )
    
    # Store custom randomized question order (JSON array of question IDs)
    question_order_json = models.TextField(blank=True, default='[]', help_text="Serialized JSON list of question IDs for this attempt")
    
    # Metrics
    time_taken_seconds = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    attempted_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    wrong_answers = models.PositiveIntegerField(default=0)
    unanswered_questions = models.PositiveIntegerField(default=0)
    marked_for_review_count = models.PositiveIntegerField(default=0)
    
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    negative_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    final_score = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_passed = models.BooleanField(default=False)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at', '-created_at']

    def __str__(self):
        return f"{self.student.username} - {self.exam.title} ({self.get_status_display()})"

    @property
    def question_ids(self):
        try:
            return json.loads(self.question_order_json)
        except Exception:
            return []

    def get_time_limit_deadline(self):
        return self.start_time + timedelta(minutes=self.exam.duration_minutes)

    def remaining_seconds(self):
        deadline = self.get_time_limit_deadline()
        now = timezone.now()
        rem = (deadline - now).total_seconds()
        return max(0, int(rem))

    def is_time_expired(self):
        return self.remaining_seconds() <= 0

    def duration_formatted(self):
        mins = self.time_taken_seconds // 60
        secs = self.time_taken_seconds % 60
        return f"{mins}m {secs}s"

    def calculate_results(self, save=True, auto_expired=False):
        """
        Calculates all score metrics:
        - Total Questions, Attempted, Correct, Wrong, Unanswered
        - Total Marks possible
        - Marks Earned
        - Negative Marks deducted
        - Final Score & Percentage
        - Pass / Fail status
        """
        now = timezone.now()
        if not self.submitted_at:
            self.submitted_at = now
            self.end_time = now
            delta = (now - self.start_time).total_seconds()
            self.time_taken_seconds = min(int(delta), self.exam.duration_minutes * 60)
        
        if auto_expired:
            self.status = self.Status.EXPIRED
        else:
            self.status = self.Status.SUBMITTED

        # Fetch all questions for this exam
        questions = self.exam.questions.prefetch_related('options').all()
        total_q = questions.count()
        self.total_questions = total_q

        # Calculate max possible marks
        max_marks = Decimal('0.00')
        for q in questions:
            max_marks += q.marks
        if self.exam.total_marks > 0:
            self.total_marks = self.exam.total_marks
        else:
            self.total_marks = max_marks

        # Evaluate student answers
        answers_map = {ans.question_id: ans for ans in self.answers.select_related('selected_option').all()}
        
        correct_cnt = 0
        wrong_cnt = 0
        attempted_cnt = 0
        review_cnt = 0
        earned_marks = Decimal('0.00')
        neg_marks = Decimal('0.00')

        for q in questions:
            ans = answers_map.get(q.id)
            if ans and ans.selected_option:
                attempted_cnt += 1
                if ans.is_marked_for_review:
                    review_cnt += 1

                if ans.selected_option.is_correct:
                    correct_cnt += 1
                    ans.is_correct = True
                    ans.marks_obtained = q.marks
                    earned_marks += q.marks
                else:
                    wrong_cnt += 1
                    ans.is_correct = False
                    penalty = q.get_negative_penalty()
                    ans.marks_obtained = -Decimal(str(penalty))
                    neg_marks += Decimal(str(penalty))
                ans.save()
            elif ans and ans.is_marked_for_review:
                review_cnt += 1

        self.attempted_questions = attempted_cnt
        self.correct_answers = correct_cnt
        self.wrong_answers = wrong_cnt
        self.unanswered_questions = total_q - attempted_cnt
        self.marked_for_review_count = review_cnt
        self.negative_marks = neg_marks

        calculated_score = earned_marks - neg_marks
        # Don't let final score drop below zero if undesirable, or allow accurate calculation
        self.final_score = max(Decimal('0.00'), calculated_score)

        if self.total_marks > 0:
            self.percentage = round((self.final_score / self.total_marks) * 100, 2)
        else:
            self.percentage = Decimal('0.00')

        passing_threshold = self.exam.passing_marks
        if passing_threshold <= 0 and self.total_marks > 0:
            # Default pass threshold: 40%
            passing_threshold = self.total_marks * Decimal('0.40')
        
        self.is_passed = (self.final_score >= passing_threshold)

        if save:
            self.save()

        return self


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    selected_option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True, related_name='selected_by_students')
    is_correct = models.BooleanField(default=False)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_marked_for_review = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('attempt', 'question')
        ordering = ['question__order', 'id']

    def __str__(self):
        status = "Answered" if self.selected_option else "Unanswered"
        return f"{self.attempt.student.username} - Q{self.question_id}: {status}"
