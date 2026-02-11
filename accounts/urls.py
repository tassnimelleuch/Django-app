"""URL configurations for the accounts application."""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Registration - GET for form, POST for submission (both allowed)
    path('register/', views.register, name='register'),
    
    # Login - GET for form, POST for submission (both allowed by default)
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    
    # Logout - POST only for security
    path('logout/', views.user_logout, name='logout'),
    
    # Dashboard - GET only
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Contact list - GET only
    path('contacts/', views.contact_list, name='contact_list'),
    
    # Add contact - GET for form, POST for submission
    path('contacts/add/', views.add_contact, name='add_contact'),
    
    # Contact detail - GET only
    path('contacts/<int:contact_id>/', views.contact_detail, name='contact_detail'),
    
    # Edit contact - GET for form, POST for submission
    path('contacts/<int:contact_id>/edit/', views.edit_contact, name='edit_contact'),
    
    # Delete contact - POST only (no GET confirmation page)
    path('contacts/<int:contact_id>/delete/', views.delete_contact, name='delete_contact'),
    
    # Add phone - GET for form, POST for submission
    path('contacts/<int:contact_id>/add-phone/', views.add_phone, name='add_phone'),
    
    # Edit phone - GET for form, POST for submission
    path('phone/<int:phone_id>/edit/', views.edit_phone, name='edit_phone'),
    
    # Delete phone - POST only (no GET confirmation page)
    path('phone/<int:phone_id>/delete/', views.delete_phone, name='delete_phone'),
]