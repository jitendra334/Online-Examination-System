from django.urls import path
from . import views

app_name = 'results'

urlpatterns = [
    path('start/<int:exam_id>/', views.start_exam_view, name='start_exam'),
    path('take/<int:attempt_id>/', views.take_exam_view, name='take_exam'),
    path('ajax-save/<int:attempt_id>/', views.ajax_save_answer, name='ajax_save_answer'),
    path('ajax-clear/<int:attempt_id>/', views.ajax_clear_answer, name='ajax_clear_answer'),
    path('ajax-review/<int:attempt_id>/', views.ajax_toggle_review, name='ajax_toggle_review'),
    path('submit/<int:attempt_id>/', views.submit_exam_view, name='submit_exam'),
    path('detail/<int:attempt_id>/', views.result_detail_view, name='result_detail'),
    path('pdf/<int:attempt_id>/', views.result_pdf_view, name='result_pdf'),
    
    # Leaderboard & History
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('leaderboard/<int:exam_id>/', views.leaderboard_view, name='exam_leaderboard'),
    path('history/', views.student_history_view, name='student_history'),
    
    # Teacher Analytics
    path('exam/<int:exam_id>/attempts/', views.teacher_exam_results_view, name='teacher_exam_results'),
    path('exam/<int:exam_id>/export-csv/', views.export_results_csv, name='export_results_csv'),
]
