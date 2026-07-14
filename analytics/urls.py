from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.view, name='view'),
    path('update-chart/', views.update_chart_ajax, name='update_chart'),
]
