from django.contrib import admin
from .models import Subject, Exam

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_by', 'total_exams', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('created_at',)

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'created_by', 'duration_minutes', 'total_marks', 'passing_marks', 'negative_marking_enabled', 'is_published', 'created_at')
    list_filter = ('is_published', 'negative_marking_enabled', 'subject')
    search_fields = ('title', 'description', 'subject__name', 'created_by__username')
    actions = ['publish_exams', 'unpublish_exams']

    def publish_exams(self, request, queryset):
        queryset.update(is_published=True)
    publish_exams.short_description = "Publish selected exams"

    def unpublish_exams(self, request, queryset):
        queryset.update(is_published=False)
    unpublish_exams.short_description = "Unpublish selected exams"
