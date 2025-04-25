from rest_framework import serializers
from .models import ScreenTime

class ScreenTimeSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email_id', read_only=True)
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = ScreenTime
        fields = [
            'id', 'user_email', 'timestamp', 'start_time', 'end_time',
            'duration', 'duration_seconds', 'application', 'category', 'is_active'
        ]
        read_only_fields = ['timestamp', 'duration', 'user_email']

    def get_duration_seconds(self, obj):
        return obj.duration.total_seconds() if obj.duration else 0

    def validate(self, data):
        if data.get('is_active') and not data.get('start_time'):
            raise serializers.ValidationError("Start time is required for an active timer.")
        if data.get('end_time') and not data.get('start_time'):
            raise serializers.ValidationError("Start time must be provided if end time is set.")
        if data.get('end_time') and data.get('start_time') and data['end_time'] < data['start_time']:
            raise serializers.ValidationError("End time must be after start time.")
        return data