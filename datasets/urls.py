from django.urls import path
from . import views

app_name = 'datasets'

urlpatterns = [
    path('upload/', views.upload_view, name='upload'),
    path('activate/<int:pk>/', views.activate_dataset, name='activate'),
    path('delete/<int:pk>/', views.delete_dataset, name='delete'),
]
