from django.db import models
from decimal import Decimal
from exams.models import Exam

class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField(help_text="The question statement / problem")
    marks = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, help_text="Marks allocated for this question")
    negative_marks = models.DecimalField(max_digits=4, decimal_places=2, default=0.00, blank=True, null=True, help_text="Custom negative mark override (leave 0 to use exam default)")
    explanation = models.TextField(blank=True, help_text="Detailed explanation of the solution shown in results")
    order = models.PositiveIntegerField(default=0, blank=True, help_text="Display order in test")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Q{self.id}: {self.question_text[:60]}..."

    @property
    def correct_option(self):
        return self.options.filter(is_correct=True).first()

    @property
    def options_count(self):
        return self.options.count()

    def get_negative_penalty(self):
        if self.negative_marks is not None and self.negative_marks > 0:
            return self.negative_marks
        if self.exam.negative_marking_enabled:
            return self.exam.negative_marks_per_question
        return Decimal('0.00')

    def save(self, *args, **kwargs):
        if self.negative_marks is None:
            self.negative_marks = Decimal('0.00')
        if not self.order or self.order == 0:
            last_order = self.exam.questions.exclude(pk=self.pk).aggregate(models.Max('order'))['order__max']
            self.order = (last_order or 0) + 1
        super().save(*args, **kwargs)


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.TextField(help_text="Option content text")
    is_correct = models.BooleanField(default=False, help_text="Check if this is the correct answer")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        status = "[CORRECT]" if self.is_correct else ""
        return f"{self.option_text[:50]} {status}"

