from django.db import models
from django.conf import settings
from django.utils import timezone

class Subject(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=30, unique=True, help_text="Subject Code, e.g. CS501, IT302")
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-journal-code', help_text="Bootstrap Icon class name, e.g., bi-cpu, bi-database")
    color_code = models.CharField(max_length=20, default='#2563eb', help_text="Hex code for theme badge, e.g. #2563eb")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_subjects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def total_exams(self):
        return self.exams.count()

    @property
    def active_exams_count(self):
        return self.exams.filter(is_published=True).count()


class Exam(models.Model):
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams')
    description = models.TextField(blank=True, help_text="Brief summary or syllabus covered in this exam")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_exams')
    
    # Timing and Scoring
    duration_minutes = models.PositiveIntegerField(default=30, help_text="Duration in minutes (e.g. 30, 60)")
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, help_text="Total marks possible. If 0, automatically computed from questions.")
    passing_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, help_text="Minimum marks required to pass")
    
    # Negative Marking
    negative_marking_enabled = models.BooleanField(default=False, help_text="Enable penalty marks for wrong answers")
    negative_marks_per_question = models.DecimalField(max_digits=4, decimal_places=2, default=0.25, help_text="Marks deducted per wrong answer if negative marking is enabled")
    
    # Exam Control Flags
    is_published = models.BooleanField(default=False, help_text="Only published exams are visible to students")
    random_question_order = models.BooleanField(default=True, help_text="Shuffle question order per attempt")
    random_option_order = models.BooleanField(default=False, help_text="Shuffle options order per question")
    show_answers_after_submission = models.BooleanField(default=True, help_text="Allow students to view detailed solutions & explanations after submission")
    max_attempts = models.PositiveIntegerField(default=1, help_text="Maximum allowed attempts per student (default 1)")
    
    # Schedule
    start_time = models.DateTimeField(null=True, blank=True, help_text="Optional start date/time")
    end_time = models.DateTimeField(null=True, blank=True, help_text="Optional deadline date/time")
    
    instructions = models.TextField(
        blank=True,
        default="1. The countdown timer starts as soon as you begin the exam.\n"
                "2. Each question has 4 options with exactly one correct answer.\n"
                "3. You can navigate between questions using the Question Palette or Next/Previous buttons.\n"
                "4. You can change your answers anytime before final submission.\n"
                "5. The exam will automatically submit when the timer reaches 00:00:00.\n"
                "6. Do not refresh or close the browser window during the test."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.subject.code}"

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def computed_total_marks(self):
        if self.total_marks > 0:
            return self.total_marks
        total = self.questions.aggregate(models.Sum('marks'))['marks__sum']
        return total if total is not None else 0.00

    @property
    def is_currently_active(self):
        if not self.is_published:
            return False
        now = timezone.now()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True

    def student_attempt_count(self, user):
        return self.attempts.filter(student=user, status__in=['SUBMITTED', 'EXPIRED']).count()

    def can_student_attempt(self, user):
        if not self.is_currently_active:
            return False, "This exam is currently not active or published."
        completed = self.student_attempt_count(user)
        if completed >= self.max_attempts:
            return False, f"You have reached the maximum allowed attempts ({self.max_attempts}) for this exam."
        return True, "Allowed"
