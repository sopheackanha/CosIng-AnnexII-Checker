from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('analysis/<int:analysis_id>/', views.analysis_result, name='analysis_result'),
    path('api/analysis-status/<int:analysis_id>/', views.check_analysis_status, name='check_analysis_status'),
    path('history/', views.history, name='history'),
    path('delete/<int:analysis_id>/', views.delete_analysis, name='delete_analysis'),
]
