from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('search/', views.search_results, name='search_results'),
    path('search/suggestions/', views.search_suggestions, name='search_suggestions'),
    path('app/<int:app_id>/', views.app_detail, name='app_detail'),
    path('supervisor/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/approve/<int:review_id>/', views.approve_review, name='approve_review'),
]