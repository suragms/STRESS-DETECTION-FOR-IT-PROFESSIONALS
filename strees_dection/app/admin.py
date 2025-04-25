from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponse
import csv
from django.contrib.auth.models import User
from .models import (
    UsersRegister, StressAssessment, Feedback,
    KeyboardActivity, ScreenTime, ApplicationUsage, VoicePattern, WearableData,
    Recommendation, Alert, Resource,
    ProcessedData, ExtractedFeature, StressPattern, Anomaly, MLPrediction
)

# Custom admin for UsersRegister
class UsersRegisterAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email_id', 'department', 'years_of_experience', 'work_role', 'profile_pic', 'django_user')
    search_fields = ('first_name', 'last_name', 'email_id', 'user__username', 'user__email')
    list_filter = ('department', 'years_of_experience')
    readonly_fields = ('user',)

    def profile_pic(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%"/>', obj.image.url)
        return "No Image"
    profile_pic.short_description = 'Profile Picture'

    def django_user(self, obj):
        if obj.user:
            return obj.user.username
        return "No Django User"
    django_user.short_description = 'Django User'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_register.csv"'
        writer = csv.writer(response)
        writer.writerow(['First Name', 'Last Name', 'Email', 'Department', 'Years of Experience', 'Work Role', 'Django User'])
        
        users = UsersRegister.objects.all().values_list(
            'first_name', 'last_name', 'email_id', 'department', 'years_of_experience', 'work_role', 'user__username'
        )
        for user in users:
            writer.writerow(user)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-users/', self.export_as_csv, name="export-users"),
        ]
        return custom_urls + urls

# Custom admin for StressAssessment
class StressAssessmentAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'date', 'stress_score', 'recommendations')
    search_fields = ('date', 'user__email_id', 'user__user__email')
    list_filter = ('stress_score',)

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="stress_assessments.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Date', 'Stress Score', 'Recommendations'])
        
        assessments = StressAssessment.objects.all().values_list('user__email_id', 'date', 'stress_score', 'recommendations')
        for assessment in assessments:
            writer.writerow(assessment)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-stress-reports/', self.export_as_csv, name="export-stress-reports"),
        ]
        return custom_urls + urls

# Custom admin for Feedback
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'assessment', 'rating', 'date')
    search_fields = ('user__email_id', 'feedback_text', 'user__user__email')
    list_filter = ('rating', 'date')

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="feedback.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Assessment ID', 'Rating', 'Date', 'Feedback Text'])
        
        feedbacks = Feedback.objects.all().values_list('user__email_id', 'assessment__id', 'rating', 'date', 'feedback_text')
        for feedback in feedbacks:
            writer.writerow(feedback)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-feedback/', self.export_as_csv, name="export-feedback"),
        ]
        return custom_urls + urls

# Custom admin for KeyboardActivity
class KeyboardActivityAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'timestamp', 'keystrokes_per_minute', 'typing_duration')
    search_fields = ('user__email_id', 'user__user__email')
    list_filter = ('timestamp',)

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="keyboard_activity.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Timestamp', 'Keystrokes/Minute', 'Typing Duration'])
        
        activities = KeyboardActivity.objects.all().values_list('user__email_id', 'timestamp', 'keystrokes_per_minute', 'typing_duration')
        for activity in activities:
            writer.writerow(activity)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-keyboard-activity/', self.export_as_csv, name="export-keyboard-activity"),
        ]
        return custom_urls + urls

# Custom admin for ScreenTime
class ScreenTimeAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'timestamp', 'duration', 'application', 'category', 'is_active')
    search_fields = ('user__email_id', 'application', 'user__user__email')
    list_filter = ('timestamp', 'category', 'is_active')

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="screen_time.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Timestamp', 'Duration', 'Application', 'Category', 'Is Active'])
        
        screen_times = ScreenTime.objects.all().values_list(
            'user__email_id', 'timestamp', 'duration', 'application', 'category', 'is_active'
        )
        for screen_time in screen_times:
            writer.writerow(screen_time)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-screen-time/', self.export_as_csv, name="export-screen-time"),
        ]
        return custom_urls + urls

# Custom admin for ApplicationUsage
class ApplicationUsageAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'timestamp', 'app_name', 'usage_duration')
    search_fields = ('user__email_id', 'app_name', 'user__user__email')
    list_filter = ('timestamp',)

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="application_usage.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Timestamp', 'App Name', 'Usage Duration'])
        
        usages = ApplicationUsage.objects.all().values_list('user__email_id', 'timestamp', 'app_name', 'usage_duration')
        for usage in usages:
            writer.writerow(usage)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-app-usage/', self.export_as_csv, name="export-app-usage"),
        ]
        return custom_urls + urls

# Custom admin for VoicePattern
class VoicePatternAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'timestamp', 'stress_level', 'audio_file_link')
    search_fields = ('user__email_id', 'user__user__email')
    list_filter = ('timestamp', 'stress_level')

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def audio_file_link(self, obj):
        if obj.audio_file:
            return format_html('<a href="{}">Download</a>', obj.audio_file.url)
        return "No File"
    audio_file_link.short_description = 'Audio File'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="voice_patterns.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Timestamp', 'Stress Level', 'Audio File URL'])
        
        patterns = VoicePattern.objects.all().values_list('user__email_id', 'timestamp', 'stress_level', 'audio_file')
        for pattern in patterns:
            audio_url = pattern[3].url if pattern[3] else 'N/A'
            writer.writerow([pattern[0], pattern[1], pattern[2], audio_url])
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-voice-patterns/', self.export_as_csv, name="export-voice-patterns"),
        ]
        return custom_urls + urls

# Custom admin for WearableData
class WearableDataAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'timestamp', 'device_type', 'heart_rate', 'steps', 'sleep_duration', 'stress_indicator')
    search_fields = ('user__email_id', 'device_type', 'user__user__email')
    list_filter = ('device_type', 'timestamp')

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="wearable_data.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Timestamp', 'Device Type', 'Heart Rate', 'Steps', 'Sleep Duration', 'Stress Indicator'])
        
        data = WearableData.objects.all().values_list(
            'user__email_id', 'timestamp', 'device_type', 'heart_rate', 'steps', 'sleep_duration', 'stress_indicator'
        )
        for entry in data:
            writer.writerow(entry)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-wearable-data/', self.export_as_csv, name="export-wearable-data"),
        ]
        return custom_urls + urls

# Custom admin for Recommendation
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'category', 'recommendation_text', 'priority', 'created_at', 'is_completed')
    search_fields = ('user__email_id', 'recommendation_text', 'category', 'user__user__email')
    list_filter = ('category', 'priority', 'is_completed', 'created_at')

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="recommendations.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Category', 'Recommendation Text', 'Priority', 'Created At', 'Completed'])
        
        recommendations = Recommendation.objects.all().values_list(
            'user__email_id', 'category', 'recommendation_text', 'priority', 'created_at', 'is_completed'
        )
        for recommendation in recommendations:
            writer.writerow(recommendation)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-recommendations/', self.export_as_csv, name="export-recommendations"),
        ]
        return custom_urls + urls

# Custom admin for Alert
class AlertAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'message', 'threshold', 'triggered_at', 'is_acknowledged')
    search_fields = ('user__email_id', 'message', 'user__user__email')
    list_filter = ('threshold', 'is_acknowledged', 'triggered_at')

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="alerts.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Message', 'Threshold', 'Triggered At', 'Acknowledged'])
        
        alerts = Alert.objects.all().values_list(
            'user__email_id', 'message', 'threshold', 'triggered_at', 'is_acknowledged'
        )
        for alert in alerts:
            writer.writerow(alert)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-alerts/', self.export_as_csv, name="export-alerts"),
        ]
        return custom_urls + urls

# Custom admin for Resource
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'description_preview', 'url_link', 'file_link')
    search_fields = ('title', 'description', 'category')
    list_filter = ('category',)

    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'

    def url_link(self, obj):
        if obj.url:
            return format_html('<a href="{}" target="_blank">Link</a>', obj.url)
        return "No URL"
    url_link.short_description = 'URL'

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.file.url)
        return "No File"
    file_link.short_description = 'File'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="resources.csv"'
        writer = csv.writer(response)
        writer.writerow(['Title', 'Category', 'Description', 'URL', 'File URL'])
        
        resources = Resource.objects.all().values_list('title', 'category', 'description', 'url', 'file')
        for resource in resources:
            file_url = resource[4].url if resource[4] else 'N/A'
            writer.writerow([resource[0], resource[1], resource[2], resource[3] or 'N/A', file_url])
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-resources/', self.export_as_csv, name="export-resources"),
        ]
        return custom_urls + urls

# Custom admin for ProcessedData
class ProcessedDataAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'data_type', 'processed_at', 'is_valid')
    search_fields = ('user__email_id', 'data_type')
    list_filter = ('data_type', 'processed_at', 'is_valid')

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="processed_data.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Data Type', 'Processed At', 'Is Valid'])
        
        data = ProcessedData.objects.all().values_list('user__email_id', 'data_type', 'processed_at', 'is_valid')
        for entry in data:
            writer.writerow(entry)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-processed-data/', self.export_as_csv, name="export-processed-data"),
        ]
        return custom_urls + urls

# Custom admin for ExtractedFeature
class ExtractedFeatureAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'feature_type', 'feature_value', 'extracted_at')
    search_fields = ('user__email_id', 'feature_type')
    list_filter = ('feature_type', 'extracted_at')

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="extracted_features.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Feature Type', 'Feature Value', 'Extracted At'])
        
        features = ExtractedFeature.objects.all().values_list('user__email_id', 'feature_type', 'feature_value', 'extracted_at')
        for feature in features:
            writer.writerow(feature)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-extracted-features/', self.export_as_csv, name="export-extracted-features"),
        ]
        return custom_urls + urls

# Custom admin for StressPattern
class StressPatternAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'pattern_type', 'confidence_score', 'description')
    search_fields = ('user__email_id', 'pattern_type', 'description')
    list_filter = ('pattern_type',)

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="stress_patterns.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Pattern Type', 'Confidence Score', 'Description'])
        
        patterns = StressPattern.objects.all().values_list('user__email_id', 'pattern_type', 'confidence_score', 'description')
        for pattern in patterns:
            writer.writerow(pattern)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-stress-patterns/', self.export_as_csv, name="export-stress-patterns"),
        ]
        return custom_urls + urls

# Custom admin for Anomaly
class AnomalyAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'anomaly_type', 'severity', 'description')
    search_fields = ('user__email_id', 'anomaly_type', 'description')
    list_filter = ('anomaly_type', 'severity')

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="anomalies.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Anomaly Type', 'Severity', 'Description'])
        
        anomalies = Anomaly.objects.all().values_list('user__email_id', 'anomaly_type', 'severity', 'description')
        for anomaly in anomalies:
            writer.writerow(anomaly)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-anomalies/', self.export_as_csv, name="export-anomalies"),
        ]
        return custom_urls + urls

# Custom admin for MLPrediction
class MLPredictionAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'prediction_type', 'prediction_value', 'confidence_score')
    search_fields = ('user__email_id', 'prediction_type')
    list_filter = ('prediction_type',)

    def user_email(self, obj):
        return obj.user.email_id if obj.user else "No User"
    user_email.short_description = 'User Email'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ml_predictions.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Prediction Type', 'Prediction Value', 'Confidence Score'])
        
        predictions = MLPrediction.objects.all().values_list('user__email_id', 'prediction_type', 'prediction_value', 'confidence_score')
        for prediction in predictions:
            writer.writerow(prediction)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-ml-predictions/', self.export_as_csv, name="export-ml-predictions"),
        ]
        return custom_urls + urls

# Register models in the admin panel
admin.site.register(UsersRegister, UsersRegisterAdmin)
admin.site.register(StressAssessment, StressAssessmentAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(KeyboardActivity, KeyboardActivityAdmin)
admin.site.register(ScreenTime, ScreenTimeAdmin)
admin.site.register(ApplicationUsage, ApplicationUsageAdmin)
admin.site.register(VoicePattern, VoicePatternAdmin)
admin.site.register(WearableData, WearableDataAdmin)
admin.site.register(Recommendation, RecommendationAdmin)
admin.site.register(Alert, AlertAdmin)
admin.site.register(Resource, ResourceAdmin)
admin.site.register(ProcessedData, ProcessedDataAdmin)
admin.site.register(ExtractedFeature, ExtractedFeatureAdmin)
admin.site.register(StressPattern, StressPatternAdmin)
admin.site.register(Anomaly, AnomalyAdmin)
admin.site.register(MLPrediction, MLPredictionAdmin)

# Customize admin site header
admin.site.site_header = "Stress Detection Admin"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome to the Stress Detection Admin Panel"