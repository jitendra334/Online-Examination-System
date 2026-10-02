from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('teacher/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('student/', views.student_dashboard_view, name='student_dashboard'),
]
