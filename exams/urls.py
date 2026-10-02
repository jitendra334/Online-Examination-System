from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('', views.exam_list_view, name='exam_list'),
    path('create/', views.exam_create_view, name='exam_create'),
    path('<int:exam_id>/', views.exam_detail_view, name='exam_detail'),
    path('<int:exam_id>/edit/', views.exam_edit_view, name='exam_edit'),
    path('<int:exam_id>/delete/', views.exam_delete_view, name='exam_delete'),
    path('<int:exam_id>/toggle-publish/', views.exam_toggle_publish, name='exam_toggle_publish'),
    path('<int:exam_id>/instructions/', views.exam_instructions_view, name='exam_instructions'),
    
    # Subject URLs
    path('subjects/', views.subject_list_view, name='subject_list'),
    path('subjects/create/', views.subject_create_view, name='subject_create'),
    path('subjects/<int:subject_id>/edit/', views.subject_edit_view, name='subject_edit'),
    path('subjects/<int:subject_id>/delete/', views.subject_delete_view, name='subject_delete'),
]
