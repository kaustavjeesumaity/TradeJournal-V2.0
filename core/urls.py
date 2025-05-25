from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, TradeViewSet

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('accounts/create/', views.account_create_view, name='account_create'),
    path('trades/create/', views.trade_create_view, name='trade_create'),
    path('accounts/<int:pk>/edit/', views.account_edit_view, name='account_edit'),
    path('accounts/<int:pk>/delete/', views.account_delete_view, name='account_delete'),
    path('trades/<int:pk>/edit/', views.trade_edit_view, name='trade_edit'),
    path('trades/<int:pk>/delete/', views.trade_delete_view, name='trade_delete'),
    path('profile/', views.profile_view, name='profile'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    path('trades/export/', views.trade_export_csv, name='trade_export_csv'),
    path('trades/import/', views.trade_import_csv, name='trade_import_csv'),
    path('tools/position-size/', views.position_size_calculator, name='position_size_calculator'),
    path('trades/fetch-mt5/', views.fetch_mt5_trades, name='fetch_mt5_trades'),
]

router = DefaultRouter()
router.register(r'api/accounts', AccountViewSet, basename='api-accounts')
router.register(r'api/trades', TradeViewSet, basename='api-trades')

urlpatterns += router.urls
