from django.urls import path
from . import views

app_name = 'export'

urlpatterns = [
    path('', views.index, name='index'),
    path('dataset/csv/', views.export_dataset_csv, name='dataset_csv'),
    path('dataset/excel/', views.export_dataset_excel, name='dataset_excel'),
    path('complete/zip/', views.export_complete_zip, name='complete_zip'),
]
