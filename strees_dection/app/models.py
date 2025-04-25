from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User

# UsersRegister Model

class UsersRegister(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)  # Link to auth User
    first_name = models.CharField(max_length=100, null=True, help_text="User's first name")
    last_name = models.CharField(max_length=100, null=True, help_text="User's last name")
    email_id = models.EmailField(unique=True, null=True, blank=True, help_text="User's email address")
    password = models.CharField(max_length=255, null=True, blank=True, help_text="User's password")
    confirm_password = models.CharField(max_length=255, null=True, blank=True, help_text="Confirm user's password")
    image = models.ImageField(upload_to='media', null=True, blank=True, help_text="Profile picture of the user")
    department = models.CharField(max_length=100, null=True, blank=True, help_text="Department of the user (e.g., IT, HR, etc.)")
    years_of_experience = models.PositiveIntegerField(null=True, blank=True, help_text="Years of experience in the work role")
    work_role = models.CharField(max_length=100, null=True, blank=True, help_text="Work role or job title (e.g., Software Engineer, Manager)")
    confirm_password_token = models.CharField(max_length=200, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email_id}"
# StressAssessment Model
from django.db import models
from django.utils.timezone import now
import json

class StressAssessment(models.Model):
    user = models.ForeignKey('UsersRegister', on_delete=models.CASCADE)
    date = models.DateTimeField(default=now)
    responses = models.TextField()  # Keep this field as per your function
    stress_score = models.IntegerField()
    recommendations = models.TextField()
    # data = models.TextField(default='{}')  # Uncomment if you need this field

    def get_responses(self):
        return json.loads(self.responses) if self.responses else []

    def set_responses(self, responses):
        self.responses = json.dumps(responses)
        
# Feedback Model
class Feedback(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    assessment = models.ForeignKey(StressAssessment, on_delete=models.CASCADE)
    feedback_text = models.TextField()
    rating = models.IntegerField()
    date = models.DateTimeField(default=now)

    def __str__(self):
        return f"Feedback by {self.user.email_id} on {self.date}"

# Models for Data Collection Module

# Behavioral Data Collector Models
class KeyboardActivity(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=now)
    keystrokes_per_minute = models.IntegerField(help_text="Number of keystrokes per minute")
    typing_duration = models.DurationField(help_text="Duration of typing activity")

    def __str__(self):
        return f"Keyboard Activity for {self.user.email_id} at {self.timestamp}"
# In models.py
class ScreenTime(models.Model):
    CATEGORY_CHOICES = (
        ('WORK', 'Work'),
        ('SOCIAL', 'Social Media'),
        ('ENTERTAINMENT', 'Entertainment'),
        ('PRODUCTIVITY', 'Productivity'),
        ('COMMUNICATION', 'Communication'),
        ('OTHER', 'Other'),
    )

    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=now)
    start_time = models.DateTimeField(null=True, blank=True, help_text="Start time of the screen activity")
    end_time = models.DateTimeField(null=True, blank=True, help_text="End time of the screen activity")
    duration = models.DurationField(null=True, blank=True, help_text="Total screen time duration")
    application = models.CharField(max_length=100, null=True, blank=True, help_text="Application in focus")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER', help_text="Category of the screen activity")
    is_active = models.BooleanField(default=False, help_text="Indicates if the timer is currently active")

    def save(self, *args, **kwargs):
        # Automatically calculate duration if start_time and end_time are provided
        if self.start_time and self.end_time and not self.duration:
            self.duration = self.end_time - self.start_time
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Screen Time for {self.user.email_id} at {self.timestamp} ({self.category})"

class ApplicationUsage(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=now)
    app_name = models.CharField(max_length=100, help_text="Name of the application")
    usage_duration = models.DurationField(help_text="Duration of app usage")

    def __str__(self):
        return f"App Usage: {self.app_name} by {self.user.email_id} at {self.timestamp}"

class VoicePattern(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=now)
    audio_file = models.FileField(upload_to='voice_patterns/', null=True, blank=True, help_text="Recorded voice sample")
    stress_level = models.FloatField(null=True, blank=True, help_text="Estimated stress level from voice analysis")

    def __str__(self):
        return f"Voice Pattern for {self.user.email_id} at {self.timestamp}"

# Wearable Device Integration Model
class WearableData(models.Model):
    DEVICE_TYPES = (
        ('FITBIT', 'Fitbit'),
        ('APPLE_WATCH', 'Apple Watch'),
        ('OTHER', 'Other'),
    )
    
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, help_text="Type of wearable device")
    timestamp = models.DateTimeField(default=now)
    heart_rate = models.IntegerField(null=True, blank=True, help_text="Heart rate in beats per minute")
    steps = models.IntegerField(null=True, blank=True, help_text="Number of steps taken")
    sleep_duration = models.DurationField(null=True, blank=True, help_text="Sleep duration")
    stress_indicator = models.FloatField(null=True, blank=True, help_text="Stress indicator from wearable data")

    def __str__(self):
        return f"Wearable Data from {self.device_type} for {self.user.email_id} at {self.timestamp}"
# Recommendation sections

class Recommendation(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    stress_assessment = models.ForeignKey(StressAssessment, on_delete=models.CASCADE, null=True, blank=True)
    recommendation_text = models.TextField(help_text="Personalized recommendation content")
    category = models.CharField(max_length=50, choices=[
        ('BREAK', 'Take a Break'),
        ('EXERCISE', 'Exercise'),
        ('MINDFULNESS', 'Mindfulness'),
        ('SCHEDULE', 'Schedule Adjustment'),
        ('RESOURCE', 'Resource'),
    ])
    priority = models.IntegerField(default=1, help_text="Priority level (1-5)")
    created_at = models.DateTimeField(auto_now_add=True)  # Changed to auto_now_add
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.category} Recommendation for {self.user.email_id}"
    
class Alert(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    message = models.TextField(help_text="Alert message for high stress")
    threshold = models.IntegerField(help_text="Stress score threshold that triggered this alert")
    triggered_at = models.DateTimeField(auto_now_add=True)  # Changed to auto_now_add
    is_acknowledged = models.BooleanField(default=False)

    def __str__(self):
        return f"Alert for {self.user.email_id} at {self.triggered_at}"

class Resource(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('VIDEO', 'Video'),
        ('ARTICLE', 'Article'),
        ('AUDIO', 'Audio'),
        ('EXERCISE', 'Exercise'),
    ])
    url = models.URLField(null=True, blank=True)
    file = models.FileField(upload_to='resources/', null=True, blank=True)

    def __str__(self):
        return self.title
    
from django.db import models
from django.utils.timezone import now
import json

class ProcessedData(models.Model):
    DATA_TYPES = (
        ('KEYBOARD', 'Keyboard Activity'),
        ('SCREEN_TIME', 'Screen Time'),
        ('APP_USAGE', 'Application Usage'),
        ('VOICE', 'Voice Pattern'),
        ('WEARABLE', 'Wearable Data'),
    )
    user = models.ForeignKey('UsersRegister', on_delete=models.CASCADE)
    data_type = models.CharField(max_length=20, choices=DATA_TYPES)
    raw_data = models.TextField(default='{}', help_text="Raw data before processing (JSON string)")
    cleaned_data = models.TextField(default='{}', help_text="Cleaned and normalized data (JSON string)")
    processed_at = models.DateTimeField(default=now)
    is_valid = models.BooleanField(default=True, help_text="Indicates if data passed cleaning checks")

    def __str__(self):
        return f"{self.data_type} Processed for {self.user.email_id} at {self.processed_at}"

    def get_raw_data(self):
        return json.loads(self.raw_data)

    def set_raw_data(self, data):
        self.raw_data = json.dumps(data)

    def get_cleaned_data(self):
        return json.loads(self.cleaned_data)

    def set_cleaned_data(self, data):
        self.cleaned_data = json.dumps(data)

class ExtractedFeature(models.Model):
    user = models.ForeignKey('UsersRegister', on_delete=models.CASCADE)
    processed_data = models.ForeignKey('ProcessedData', on_delete=models.CASCADE)
    feature_type = models.CharField(max_length=100, help_text="Type of feature (e.g., keystroke_speed, heart_rate_variability)")
    feature_value = models.FloatField(help_text="Extracted feature value")
    extracted_at = models.DateTimeField(default=now)
    context = models.TextField(default='{}', help_text="Additional context for the feature (JSON string)")

    def __str__(self):
        return f"{self.feature_type} for {self.user.email_id} at {self.extracted_at}"

    def get_context(self):
        return json.loads(self.context)

    def set_context(self, data):
        self.context = json.dumps(data)

# Pattern Recognition Model
class StressPattern(models.Model):
    user = models.ForeignKey('UsersRegister', on_delete=models.CASCADE)
    features = models.ManyToManyField('ExtractedFeature', help_text="Features contributing to this pattern")
    pattern_type = models.CharField(max_length=100, help_text="Type of pattern (e.g., high_stress, low_stress)")
    confidence_score = models.FloatField(help_text="Confidence in pattern recognition (0-1)")
    recognized_at = models.DateTimeField(default=now)
    description = models.TextField(help_text="Description of the recognized pattern")

    def __str__(self):
        return f"{self.pattern_type} Pattern for {self.user.email_id} at {self.recognized_at}"

# Anomaly Detection Model
class Anomaly(models.Model):
    user = models.ForeignKey('UsersRegister', on_delete=models.CASCADE)
    processed_data = models.ForeignKey('ProcessedData', on_delete=models.CASCADE, null=True)
    feature = models.ForeignKey('ExtractedFeature', on_delete=models.CASCADE, null=True)
    anomaly_type = models.CharField(max_length=100, help_text="Type of anomaly (e.g., outlier_heart_rate, unusual_typing)")
    severity = models.CharField(max_length=20, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ])
    detected_at = models.DateTimeField(default=now)
    description = models.TextField(help_text="Description of the anomaly")
    is_reviewed = models.BooleanField(default=False, help_text="Indicates if anomaly has been reviewed")

    def __str__(self):
        return f"{self.anomaly_type} Anomaly for {self.user.email_id} at {self.detected_at}"

# ML Model Prediction
class MLPrediction(models.Model):
    user = models.ForeignKey('UsersRegister', on_delete=models.CASCADE)
    stress_pattern = models.ForeignKey('StressPattern', on_delete=models.CASCADE, null=True)
    prediction_type = models.CharField(max_length=100, help_text="Type of prediction (e.g., stress_level, burnout_risk)")
    prediction_value = models.FloatField(help_text="Predicted value (e.g., stress score)")
    confidence_score = models.FloatField(help_text="Confidence in prediction (0-1)")
    predicted_at = models.DateTimeField(default=now)
    model_version = models.CharField(max_length=50, help_text="Version of the ML model used")

    def __str__(self):
        return f"{self.prediction_type} Prediction for {self.user.email_id} at {self.predicted_at}"