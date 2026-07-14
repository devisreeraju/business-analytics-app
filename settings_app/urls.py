from django.urls import path
from . import views

app_name = 'settings_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
    path('test-connection/', views.test_mistral_connection, name='test_connection'),
]
