from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, TradeViewSet
from .models import Trade

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),    path('dashboard/', views.dashboard_view, name='dashboard'),    path('accounts/', views.account_list_view, name='account_list'),
    path('accounts/create/', views.account_create_view, name='account_create'),
    path('accounts/mt5/connect/', views.mt5_account_connect_view, name='mt5_account_connect'),
    path('accounts/mt5/refresh/', views.fetch_mt5_trades_view, name='fetch_mt5_trades'),
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
    path('trades/<int:pk>/', views.trade_detail_view, name='trade_detail'),
    path('attachments/<int:attachment_id>/delete/', views.delete_trade_attachment, name='delete_trade_attachment'),
    path('advanced-analytics/', views.advanced_analytics_view, name='advanced_analytics'),
    path('daily-checklist/', views.daily_checklist_view, name='daily_checklist'),
    path('weekly-checklist/', views.weekly_checklist_view, name='weekly_checklist'),
    path('monthly-checklist/', views.monthly_checklist_view, name='monthly_checklist'),
]

router = DefaultRouter()
router.register(r'api/accounts', AccountViewSet, basename='api-accounts')
router.register(r'api/trades', TradeViewSet, basename='api-trades')

urlpatterns += router.urls

from . import views

urlpatterns += [
    path('trade-plans/', views.trade_plan_list_view, name='trade_plan_list'),
    path('trade-plans/new/', views.trade_plan_create_view, name='trade_plan_create'),
    path('trade-plans/<int:pk>/', views.trade_plan_detail_view, name='trade_plan_detail'),
    path('trade-plans/<int:pk>/edit/', views.trade_plan_edit_view, name='trade_plan_edit'),
    path('trade-plans/<int:pk>/delete/', views.trade_plan_delete_view, name='trade_plan_delete'),
    path('trade-plans/<int:plan_id>/add-event/', views.trade_plan_event_add_view, name='trade_plan_event_add'),
    path('trade-plans/event/<int:event_id>/edit/', views.trade_plan_event_edit_view, name='trade_plan_event_edit'),
    path('trade-plans/event/<int:event_id>/delete/', views.trade_plan_event_delete_view, name='trade_plan_event_delete'),
    path('trade-plans/event/attachment/<int:attachment_id>/delete/', views.trade_plan_event_attachment_delete_view, name='trade_plan_event_attachment_delete'),
]

urlpatterns += [
    path('profile/edit/', views.profile_view, name='user_profile_edit'),
    path('milestones/', views.milestone_list_view, name='milestone_list'),
    path('milestones/new/', views.milestone_create_view, name='milestone_create'),
    path('milestones/<int:pk>/edit/', views.milestone_edit_view, name='milestone_edit'),
    path('milestones/<int:pk>/delete/', views.milestone_delete_view, name='milestone_delete'),
    path('lessons/', views.lesson_list_view, name='lesson_list'),
    path('lessons/new/', views.lesson_create_view, name='lesson_create'),
    path('lessons/<int:pk>/edit/', views.lesson_edit_view, name='lesson_edit'),
    path('lessons/<int:pk>/delete/', views.lesson_delete_view, name='lesson_delete'),
    path('achievements/', views.achievement_list_view, name='achievement_list'),
    path('achievements/new/', views.achievement_create_view, name='achievement_create'),
    path('achievements/<int:pk>/edit/', views.achievement_edit_view, name='achievement_edit'),
    path('achievements/<int:pk>/delete/', views.achievement_delete_view, name='achievement_delete'),
    path('reviews/', views.review_list_view, name='review_list'),
    path('reviews/new/', views.review_create_view, name='review_create'),
    path('reviews/<int:pk>/edit/', views.review_edit_view, name='review_edit'),
    path('reviews/<int:pk>/delete/', views.review_delete_view, name='review_delete'),
]

urlpatterns += [
    path('courses/', views.course_list_view, name='course_list'),
    path('courses/new/', views.course_create_view, name='course_create'),
    path('courses/<int:pk>/edit/', views.course_edit_view, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete_view, name='course_delete'),
    path('books/', views.book_list_view, name='book_list'),
    path('books/new/', views.book_create_view, name='book_create'),
    path('books/<int:pk>/edit/', views.book_edit_view, name='book_edit'),
    path('books/<int:pk>/delete/', views.book_delete_view, name='book_delete'),
    path('keylessons/', views.keylesson_list_view, name='keylesson_list'),
    path('keylessons/new/', views.keylesson_create_view, name='keylesson_create'),
    path('keylessons/<int:pk>/edit/', views.keylesson_edit_view, name='keylesson_edit'),
    path('keylessons/<int:pk>/delete/', views.keylesson_delete_view, name='keylesson_delete'),
    path('mistakes/', views.mistake_list_view, name='mistake_list'),
    path('mistakes/new/', views.mistake_create_view, name='mistake_create'),
    path('mistakes/<int:pk>/edit/', views.mistake_edit_view, name='mistake_edit'),
    path('mistakes/<int:pk>/delete/', views.mistake_delete_view, name='mistake_delete'),
]
