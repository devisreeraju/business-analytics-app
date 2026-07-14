from django.urls import path
from . import views

app_name = 'ai_advisor'

urlpatterns = [
    path('', views.view_report, name='view_report'),
    path('download-pdf/', views.download_pdf, name='download_pdf'),
]
