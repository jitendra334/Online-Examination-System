from django.contrib import admin
from .models import Question, Option

class OptionInline(admin.TabularInline):
    model = Option
    extra = 4
    min_num = 2

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_text', 'exam', 'marks', 'negative_marks', 'options_count', 'created_at')
    list_filter = ('exam__subject', 'exam')
    search_fields = ('question_text', 'explanation', 'exam__title')
    inlines = [OptionInline]

    def short_text(self, obj):
        return obj.question_text[:60]
    short_text.short_description = "Question"

@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'option_text', 'is_correct', 'order')
    list_filter = ('is_correct', 'question__exam')
    search_fields = ('option_text', 'question__question_text')
