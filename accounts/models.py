from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        TEACHER = 'TEACHER', 'Teacher / Examiner'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text="Role of the user in the examination system"
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    student_id = models.CharField(max_length=50, blank=True, null=True, help_text="Roll Number / Registration Number for students")
    employee_id = models.CharField(max_length=50, blank=True, null=True, help_text="Faculty ID for Teachers")
    department = models.CharField(max_length=100, blank=True, null=True, help_text="Academic Department (e.g., CSE, IT, ECE)")
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_teacher_user(self):
        return self.role == self.Role.TEACHER

    @property
    def is_student_user(self):
        return self.role == self.Role.STUDENT

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.username

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
