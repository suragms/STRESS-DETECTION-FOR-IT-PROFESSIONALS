import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from django.utils.timezone import now
import logging
from .models import ProcessedData, ExtractedFeature, StressPattern, Anomaly, MLPrediction, UsersRegister

logger = logging.getLogger(__name__)

def clean_data(raw_data, data_type):
    """Clean raw data by removing noise and invalid entries."""
    try:
        cleaned_data = {}
        if data_type == 'KEYBOARD':
            keystrokes = raw_data.get('keystrokes_per_minute', 0)
            duration = raw_data.get('typing_duration', 0)
            if isinstance(keystrokes, (int, float)) and keystrokes >= 0 and duration > 0:
                cleaned_data = {'keystrokes_per_minute': keystrokes, 'typing_duration': duration}
            else:
                return None, False
        elif data_type == 'SCREEN_TIME':
            duration = raw_data.get('duration', 0)
            application = raw_data.get('application', '')
            if isinstance(duration, (int, float)) and duration >= 0 and application:
                cleaned_data = {'duration': duration, 'application': application}
            else:
                return None, False
        elif data_type == 'WEARABLE':
            heart_rate = raw_data.get('heart_rate', None)
            steps = raw_data.get('steps', None)
            if heart_rate and steps and heart_rate > 0 and steps >= 0:
                cleaned_data = {'heart_rate': heart_rate, 'steps': steps}
            else:
                return None, False
        return cleaned_data, True
    except Exception as e:
        logger.error(f"Error cleaning {data_type} data: {str(e)}")
        return None, False

def normalize_data(cleaned_data, data_type):
    """Normalize cleaned data using StandardScaler."""
    try:
        if not cleaned_data:
            return None
        scaler = StandardScaler()
        if data_type == 'KEYBOARD':
            values = [[cleaned_data['keystrokes_per_minute'], cleaned_data['typing_duration']]]
            normalized = scaler.fit_transform(values)
            return {'keystrokes_per_minute': normalized[0][0], 'typing_duration': normalized[0][1]}
        elif data_type == 'SCREEN_TIME':
            values = [[cleaned_data['duration']]]
            normalized = scaler.fit_transform(values)
            return {'duration': normalized[0][0], 'application': cleaned_data['application']}
        elif data_type == 'WEARABLE':
            values = [[cleaned_data['heart_rate'], cleaned_data['steps']]]
            normalized = scaler.fit_transform(values)
            return {'heart_rate': normalized[0][0], 'steps': normalized[0][1]}
        return None
    except Exception as e:
        logger.error(f"Error normalizing {data_type} data: {str(e)}")
        return None

def extract_features(normalized_data, data_type):
    """Extract features from normalized data."""
    try:
        features = []
        if data_type == 'KEYBOARD':
            speed = normalized_data.get('keystrokes_per_minute', 0)
            duration = normalized_data.get('typing_duration', 0)
            features.append(('keystroke_speed', speed))
            features.append(('typing_duration', duration))
        elif data_type == 'SCREEN_TIME':
            duration = normalized_data.get('duration', 0)
            features.append(('screen_time_duration', duration))
        elif data_type == 'WEARABLE':
            heart_rate = normalized_data.get('heart_rate', 0)
            steps = normalized_data.get('steps', 0)
            features.append(('heart_rate', heart_rate))
            features.append(('steps', steps))
        return features
    except Exception as e:
        logger.error(f"Error extracting features for {data_type}: {str(e)}")
        return []

def recognize_patterns(features, user):
    """Recognize stress patterns based on extracted features."""
    try:
        feature_values = [f[1] for f in features]
        if not feature_values:
            return None
        # Simple rule-based pattern recognition (replace with ML model in production)
        avg_feature = np.mean(feature_values)
        pattern_type = 'high_stress' if avg_feature > 1.5 else 'low_stress'
        confidence = 0.8 if avg_feature > 1.5 else 0.6
        description = f"Detected {pattern_type} based on feature analysis."
        
        stress_pattern = StressPattern.objects.create(
            user=user,
            pattern_type=pattern_type,
            confidence_score=confidence,
            description=description
        )
        for feature_type, feature_value in features:
            extracted_feature = ExtractedFeature.objects.create(
                user=user,
                processed_data=ProcessedData.objects.filter(user=user).last(),
                feature_type=feature_type,
                feature_value=feature_value
            )
            stress_pattern.features.add(extracted_feature)
        return stress_pattern
    except Exception as e:
        logger.error(f"Error recognizing patterns: {str(e)}")
        return None

def ml_processing(stress_pattern, user):
    """Apply ML model to predict stress levels."""
    try:
        if not stress_pattern:
            return None
        # Dummy ML model (replace with actual model)
        model = LogisticRegression()
        feature_values = [f.feature_value for f in stress_pattern.features.all()]
        X = np.array(feature_values).reshape(1, -1)
        y_pred = np.random.uniform(0, 100)  # Simulate stress score
        confidence = 0.85
        
        prediction = MLPrediction.objects.create(
            user=user,
            stress_pattern=stress_pattern,
            prediction_type='stress_level',
            prediction_value=y_pred,
            confidence_score=confidence,
            model_version='v1.0'
        )
        return prediction
    except Exception as e:
        logger.error(f"Error in ML processing: {str(e)}")
        return None

def detect_anomalies(features, user, processed_data):
    """Detect anomalies using Isolation Forest."""
    try:
        feature_values = [f[1] for f in features]
        if not feature_values:
            return None
        iso_forest = IsolationForest(contamination=0.1)
        X = np.array(feature_values).reshape(-1, 1)
        anomalies = iso_forest.fit_predict(X)
        
        for i, (feature_type, feature_value) in enumerate(features):
            if anomalies[i] == -1:
                extracted_feature = ExtractedFeature.objects.filter(
                    user=user, feature_type=feature_type, feature_value=feature_value
                ).last()
                Anomaly.objects.create(
                    user=user,
                    processed_data=processed_data,
                    feature=extracted_feature,
                    anomaly_type=f"outlier_{feature_type}",
                    severity='MEDIUM',
                    description=f"Anomaly detected in {feature_type} with value {feature_value}"
                )
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")