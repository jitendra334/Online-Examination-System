from django.urls import path
from . import views

app_name = 'questions'

urlpatterns = [
    path('exam/<int:exam_id>/', views.question_list_view, name='question_list'),
    path('exam/<int:exam_id>/create/', views.question_create_view, name='question_create'),
    path('exam/<int:exam_id>/<int:question_id>/edit/', views.question_edit_view, name='question_edit'),
    path('exam/<int:exam_id>/<int:question_id>/delete/', views.question_delete_view, name='question_delete'),
    path('exam/<int:exam_id>/bulk-upload/', views.question_bulk_upload_view, name='question_bulk_upload'),
    path('sample-csv/', views.download_sample_csv, name='download_sample_csv'),
]
