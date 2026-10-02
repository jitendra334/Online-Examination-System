from django import forms
from django.db import transaction, models
from decimal import Decimal
from .models import Question, Option
import json
import csv
import io

class QuestionWith4OptionsForm(forms.ModelForm):
    # 4 Option text fields
    option_1 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Option A'}),
        label="Option A",
        required=True
    )
    option_2 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Option B'}),
        label="Option B",
        required=True
    )
    option_3 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Option C'}),
        label="Option C",
        required=True
    )
    option_4 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Option D'}),
        label="Option D",
        required=True
    )
    correct_option = forms.ChoiceField(
        choices=[('1', 'Option A'), ('2', 'Option B'), ('3', 'Option C'), ('4', 'Option D')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Correct Answer",
        initial='1',
        required=True
    )

    class Meta:
        model = Question
        fields = ['question_text', 'marks', 'negative_marks', 'explanation', 'order']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Type your question problem statement here...'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0.5', 'placeholder': '1.00'}),
            'negative_marks': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0', 'placeholder': '0.00 (leave empty for exam default)'}),
            'explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Explain why the correct answer is right (shown to students in result review)'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Auto-calculated if empty'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['negative_marks'].required = False
        self.fields['order'].required = False
        self.fields['explanation'].required = False

        if self.instance and self.instance.pk:
            options = list(self.instance.options.all().order_by('order', 'id'))
            if len(options) >= 1:
                self.fields['option_1'].initial = options[0].option_text
            if len(options) >= 2:
                self.fields['option_2'].initial = options[1].option_text
            if len(options) >= 3:
                self.fields['option_3'].initial = options[2].option_text
            if len(options) >= 4:
                self.fields['option_4'].initial = options[3].option_text
            
            for idx, opt in enumerate(options[:4]):
                if opt.is_correct:
                    self.fields['correct_option'].initial = str(idx + 1)
                    break
        else:
            if not self.initial.get('correct_option'):
                self.initial['correct_option'] = '1'

    def clean_marks(self):
        marks = self.cleaned_data.get('marks')
        if marks is None or marks <= 0:
            raise forms.ValidationError("Marks must be greater than 0.")
        return marks

    def clean_negative_marks(self):
        neg = self.cleaned_data.get('negative_marks')
        if neg is None or neg == '':
            return Decimal('0.00')
        if neg < 0:
            raise forms.ValidationError("Negative penalty marks cannot be negative.")
        return neg

    def clean_order(self):
        order = self.cleaned_data.get('order')
        if order is None or order == '':
            return 0
        return order

    def save_question_and_options(self, exam, commit=True):
        question = self.save(commit=False)
        question.exam = exam

        if not question.negative_marks:
            question.negative_marks = Decimal('0.00')

        if not question.order or question.order == 0:
            last_order = exam.questions.exclude(pk=question.pk).aggregate(models.Max('order'))['order__max']
            question.order = (last_order or 0) + 1

        if commit:
            with transaction.atomic():
                question.save()

                opt_texts = [
                    self.cleaned_data['option_1'].strip(),
                    self.cleaned_data['option_2'].strip(),
                    self.cleaned_data['option_3'].strip(),
                    self.cleaned_data['option_4'].strip(),
                ]
                correct_choice = int(self.cleaned_data.get('correct_option', 1))

                existing_options = list(question.options.all().order_by('order', 'id'))
                if len(existing_options) == 4:
                    for idx, opt in enumerate(existing_options):
                        opt.option_text = opt_texts[idx]
                        opt.is_correct = (idx + 1 == correct_choice)
                        opt.order = idx + 1
                        opt.save()
                else:
                    question.options.all().delete()
                    for idx, text in enumerate(opt_texts):
                        Option.objects.create(
                            question=question,
                            option_text=text,
                            is_correct=(idx + 1 == correct_choice),
                            order=idx + 1
                        )
        return question


class BulkUploadForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.json'}),
        help_text="Upload a CSV or JSON file containing MCQ questions and 4 options."
    )

