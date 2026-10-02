from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'student_id', 'employee_id', 'department', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'department')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'student_id', 'employee_id')
    ordering = ('username',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Examination Attributes', {
            'fields': ('role', 'phone_number', 'student_id', 'employee_id', 'department', 'bio', 'profile_picture')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Examination Attributes', {
            'fields': ('role', 'email', 'first_name', 'last_name', 'phone_number', 'student_id', 'employee_id', 'department')
        }),
    )
