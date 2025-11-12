from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('', views.homepage, name='homepage'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    
    # Two Wheeler URLs
    path('two-wheeler-entry/', views.two_wheeler_entry, name='two_wheeler_entry'),
    path('two-wheeler-exit/', views.two_wheeler_exit_search, name='two_wheeler_exit_search'),
    path('two-wheeler-exit/<str:token_id>/', views.two_wheeler_exit, name='two_wheeler_exit'),
    
    # Four Wheeler URLs
    path('four-wheeler-entry/', views.four_wheeler_entry, name='four_wheeler_entry'),
    path('four-wheeler-exit/', views.four_wheeler_exit_search, name='four_wheeler_exit_search'),
    path('four-wheeler-exit/<str:token_id>/', views.four_wheeler_exit, name='four_wheeler_exit'),
    
    # Success pages
    path('entry-success/<str:token_id>/', views.entry_success, name='entry_success'),
    path('exit-success/<str:token_id>/', views.exit_success, name='exit_success'),
    
    # Password reset URLs
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
    
    # Reports & Analytics URLs - ADD THESE
    path('reports/', views.reports_analytics, name='reports_analytics'),
    path('reports/daily/', views.generate_daily_report, name='daily_report'),
    path('reports/weekly/', views.generate_weekly_report, name='weekly_report'),
    path('reports/monthly/', views.generate_monthly_report, name='monthly_report'),
    path('reports/export-excel/', views.export_to_excel, name='export_excel'),
]