from django import forms
from .models import Subject, Exam

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description', 'icon', 'color_code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Data Structures & Algorithms'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CS-301'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description of subject'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. bi-cpu, bi-code-slash, bi-database'}),
            'color_code': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
        }


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'title', 'subject', 'description', 'duration_minutes',
            'total_marks', 'passing_marks', 'negative_marking_enabled',
            'negative_marks_per_question', 'is_published', 'random_question_order',
            'random_option_order', 'show_answers_after_submission', 'max_attempts',
            'start_time', 'end_time', 'instructions'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Midterm Online Examination'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Overview of syllabus covered'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'passing_marks': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'negative_marking_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'negMarkingCheckbox'}),
            'negative_marks_per_question': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'id': 'negMarkValInput'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'random_question_order': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'random_option_order': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_answers_after_submission': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
