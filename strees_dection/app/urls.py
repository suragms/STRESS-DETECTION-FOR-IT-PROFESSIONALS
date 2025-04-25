
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register the ScreenTimeViewSet
router = DefaultRouter()
router.register(r'screen-time', views.ScreenTimeViewSet, basename='screen-time')

urlpatterns = [
    path('', views.home, name='home'),
    path('usershome/', views.usershome, name='usershome'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/faq/', views.faq_view, name='faq'),
    path('settings/account-privacy/', views.account_privacy_view, name='account_privacy'),
    path('settings/soluton/', views.solutions, name='solution'),
    path('submit_feedback/<int:assessment_id>/', views.submit_feedback, name='submit_feedback'),
    path('view_feedback/', views.view_feedback, name='view_feedback'),
    path('userprofile_edit/<int:eid>/', views.userprofile_edit, name='userprofile_edit'),
    path('userprofile/', views.userprofile, name='userprofile'),
    path('signup/', views.signup, name='signup'),
    path('get-departments/', views.get_departments, name='get_departments'),
    path('login/', views.login, name='login'),
    path('forget-password/', views.forget_password, name="forget_password"),
    path('change-password/<token>/', views.change_password, name="change_password"),
    path('stress_assessment/', views.stress_assessment, name='stress_assessment'),
    path('stress_result/<int:assessment_id>/', views.stress_result, name='stress_result'),
    path('admin-login/', views.adminlogin, name='admin_login'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-manage-users/', views.admin_manage_users, name='admin_manage_users'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('export-stress-reports/', views.export_stress_reports, name='export_stress_reports'),
    path('data_collection_dashboard/', views.data_collection_dashboard, name='data_collection_dashboard'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('collect_keyboard_activity/', views.collect_keyboard_activity, name='collect_keyboard_activity'),
    path('collect_screen_time/', views.collect_screen_time, name='collect_screen_time'),
    path('collect_app_usage/', views.collect_app_usage, name='collect_app_usage'),
    path('collect_voice_pattern/', views.collect_voice_pattern, name='collect_voice_pattern'),
    path('collect_wearable_data/', views.collect_wearable_data, name='collect_wearable_data'),
    path('post_keyboard_activity/', views.post_keyboard_activity, name='post_keyboard_activity'),
    path('post_screen_time/', views.post_screen_time, name='post_screen_time'),
    path('post_application_usage/', views.post_application_usage, name='post_application_usage'),
    path('post_voice_pattern/', views.post_voice_pattern, name='post_voice_pattern'),
    path('post_wearable_data/', views.post_wearable_data, name='post_wearable_data'),
    path('recommendation-dashboard/', views.recommendation_dashboard, name='recommendation_dashboard'),
    path('mark-recommendation-complete/<int:recommendation_id>/', views.mark_recommendation_complete, name='mark_recommendation_complete'),
    path('acknowledge-alert/<int:alert_id>/', views.acknowledge_alert, name='acknowledge_alert'),
    path('resources/', views.view_resources, name='view_resources'),
    path('admin-dashboard/manage-recommendations/', views.admin_manage_recommendations, name='admin_manage_recommendations'),
    path('admin-dashboard/manage-resources/', views.admin_manage_resources, name='admin_manage_resources'),
    path('recommendations/', views.view_recommendations, name='view_recommendations'),
    path('recommendations/mark_complete/<int:recommendation_id>/', views.mark_recommendation_complete, name='mark_recommendation_complete'),
    path('recommendations/acknowledge_alert/<int:alert_id>/', views.acknowledge_alert, name='acknowledge_alert'),
    path('personal-dashboard/', views.personal_dashboard, name='personal_dashboard'),
    path('management-dashboard/', views.management_dashboard, name='management_dashboard'),
    path('generate-report/', views.generate_report, name='generate_report'),
    path('visualization-data/', views.visualization_data, name='visualization_data'),
    path('export-report/<str:report_type>/', views.export_report, name='export_report'),
    path('admin_manage_alerts_recommendations/', views.admin_manage_alerts_recommendations, name='admin_manage_alerts_recommendations'),
    path('admin_create_alert/', views.admin_create_alert, name='admin_create_alert'),
    path('admin_edit_alert/<int:alert_id>/', views.admin_edit_alert, name='admin_edit_alert'),
    path('admin_delete_alert/<int:alert_id>/', views.admin_delete_alert, name='admin_delete_alert'),
    path('admin_create_recommendation/', views.admin_create_recommendation, name='admin_create_recommendation'),
    path('admin_edit_recommendation/<int:recommendation_id>/', views.admin_edit_recommendation, name='admin_edit_recommendation'),
    path('admin_delete_recommendation/<int:recommendation_id>/', views.admin_delete_recommendation, name='admin_delete_recommendation'),
    #path('control_screen_time_timer/', views.control_screen_time_timer, name='control_screen_time_timer'),
    # API endpoints
    path('api/', include(router.urls)),
    path('process-raw-data/', views.process_raw_data, name='process_raw_data'),
    path('analytics-dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
    path('admin-analytics-management/', views.admin_analytics_management, name='admin_analytics_management'),
    path('review-anomaly/<int:anomaly_id>/', views.review_anomaly, name='review_anomaly'),
]

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns += [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]