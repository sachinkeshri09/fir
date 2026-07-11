from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- YOUR ORIGINAL PATHS ---
    path('', views.dashboard_view, name='home'), 
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('fir/<int:fir_id>/', views.fir_detail_view, name='fir_detail'),
    path('generate-fir/', views.generate_fir_view, name='generate_fir'),
    path('fir/<int:fir_id>/delete/', views.delete_fir_record_view, name='delete_fir_record'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    
    # --- YOUR PASSWORD RESET PATHS ---
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='fir_app/password_reset_form.html'
    ), name='password_reset'),
    
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='fir_app/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='fir_app/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='fir_app/password_reset_complete.html'
    ), name='password_reset_complete'),
]