from django.urls import path
from . import views
from django.contrib.auth import views as auth_views 
urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', views.user_logout, name='logout'),  # Use our custom view
    path('dashboard/', views.dashboard, name='dashboard'),  # After login page
    path('contacts/', views.contact_list, name='contact_list'),
    path('contacts/add/', views.add_contact, name='add_contact'),
    path('contacts/<int:contact_id>/', views.contact_detail, name='contact_detail'),
    path('contacts/<int:contact_id>/edit/', views.edit_contact, name='edit_contact'),
    path('contacts/<int:contact_id>/delete/', views.delete_contact, name='delete_contact'),
    path('contacts/<int:contact_id>/add-phone/', views.add_phone, name='add_phone'),
    path('phone/<int:phone_id>/edit/', views.edit_phone, name='edit_phone'),
    path('phone/<int:phone_id>/delete/', views.delete_phone, name='delete_phone'),
]