import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import DBSCAN
from sklearn.neighbors import LocalOutlierFactor
from sklearn.covariance import EllipticEnvelope
from scipy import stats
from django.utils.timezone import now, timedelta
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
    """Extract comprehensive features from normalized data."""
    try:
        features = []
        
        if data_type == 'KEYBOARD':
            speed = normalized_data.get('keystrokes_per_minute', 0)
            duration = normalized_data.get('typing_duration', 0)
            
            # Basic features
            features.append(('keystroke_speed', speed))
            features.append(('typing_duration', duration))
            
            # Derived features
            if duration > 0:
                efficiency = speed / duration  # keystrokes per second
                features.append(('typing_efficiency', efficiency))
            
            # Stress indicators
            if speed > 100:  # High typing speed might indicate stress
                stress_indicator = min((speed - 100) / 50, 1.0)  # Normalize to 0-1
                features.append(('typing_stress_indicator', stress_indicator))
            
            # Consistency features
            features.append(('typing_consistency', 1.0 - abs(speed - 80) / 80))  # Assuming 80 is normal
            
        elif data_type == 'SCREEN_TIME':
            duration = normalized_data.get('duration', 0)
            application = normalized_data.get('application', '')
            
            # Basic features
            features.append(('screen_time_duration', duration))
            
            # Time-based features
            hours = duration / 3600 if duration > 0 else 0
            features.append(('screen_time_hours', hours))
            
            # Productivity indicators
            productivity_apps = ['excel', 'word', 'powerpoint', 'outlook', 'teams', 'slack', 'vscode', 'pycharm']
            is_productivity = any(app.lower() in application.lower() for app in productivity_apps) if application else False
            features.append(('productivity_time_ratio', 1.0 if is_productivity else 0.0))
            
            # Stress indicators
            if hours > 6:  # More than 6 hours might indicate stress
                stress_indicator = min((hours - 6) / 4, 1.0)  # Normalize to 0-1
                features.append(('screen_time_stress_indicator', stress_indicator))
            
            # Break pattern features
            features.append(('break_frequency', 1.0 / max(hours, 1)))  # Inverse relationship
            
        elif data_type == 'WEARABLE':
            heart_rate = normalized_data.get('heart_rate', 0)
            steps = normalized_data.get('steps', 0)
            
            # Basic features
            features.append(('heart_rate', heart_rate))
            features.append(('steps', steps))
            
            # Health indicators
            if heart_rate > 0:
                # Heart rate variability approximation
                hr_variability = 1.0 - abs(heart_rate - 70) / 70  # Assuming 70 BPM is normal
                features.append(('heart_rate_variability', hr_variability))
                
                # Stress indicators based on heart rate
                if heart_rate > 80:
                    stress_indicator = min((heart_rate - 80) / 40, 1.0)
                    features.append(('heart_rate_stress_indicator', stress_indicator))
                elif heart_rate < 60:
                    stress_indicator = min((60 - heart_rate) / 20, 1.0)
                    features.append(('heart_rate_stress_indicator', stress_indicator))
                else:
                    features.append(('heart_rate_stress_indicator', 0.0))
            
            # Activity level features
            if steps > 0:
                activity_level = min(steps / 10000, 1.0)  # Normalize to 0-1 (10k steps = 1.0)
                features.append(('activity_level', activity_level))
                
                # Sedentary behavior indicator
                if steps < 5000:
                    sedentary_indicator = 1.0 - (steps / 5000)
                    features.append(('sedentary_indicator', sedentary_indicator))
                else:
                    features.append(('sedentary_indicator', 0.0))
            
            # Combined health score
            health_score = 0.0
            if heart_rate > 0 and steps > 0:
                hr_score = 1.0 - abs(heart_rate - 70) / 70
                step_score = min(steps / 10000, 1.0)
                health_score = (hr_score + step_score) / 2
            features.append(('overall_health_score', health_score))
            
        elif data_type == 'APP_USAGE':
            app_name = normalized_data.get('app_name', '')
            usage_duration = normalized_data.get('usage_duration', 0)
            
            # Basic features
            features.append(('app_usage_duration', usage_duration))
            
            # App category features
            work_apps = ['excel', 'word', 'powerpoint', 'outlook', 'teams', 'slack']
            social_apps = ['facebook', 'instagram', 'twitter', 'linkedin', 'whatsapp']
            entertainment_apps = ['youtube', 'netflix', 'spotify', 'games']
            
            if any(app in app_name.lower() for app in work_apps):
                features.append(('work_app_usage', 1.0))
                features.append(('social_app_usage', 0.0))
                features.append(('entertainment_app_usage', 0.0))
            elif any(app in app_name.lower() for app in social_apps):
                features.append(('work_app_usage', 0.0))
                features.append(('social_app_usage', 1.0))
                features.append(('entertainment_app_usage', 0.0))
            elif any(app in app_name.lower() for app in entertainment_apps):
                features.append(('work_app_usage', 0.0))
                features.append(('social_app_usage', 0.0))
                features.append(('entertainment_app_usage', 1.0))
            else:
                features.append(('work_app_usage', 0.0))
                features.append(('social_app_usage', 0.0))
                features.append(('entertainment_app_usage', 0.0))
            
        elif data_type == 'VOICE':
            stress_level = normalized_data.get('stress_level', 0)
            
            # Basic features
            features.append(('voice_stress_level', stress_level))
            
            # Voice pattern features
            if stress_level > 0.5:
                features.append(('voice_stress_indicator', stress_level))
            else:
                features.append(('voice_stress_indicator', 0.0))
            
            # Voice quality indicators
            features.append(('voice_clarity', 1.0 - stress_level))
            features.append(('voice_stability', 1.0 - abs(stress_level - 0.5) * 2))
        
        # Add metadata features
        features.append(('data_quality_score', 1.0))  # Assuming good quality
        features.append(('feature_extraction_timestamp', now().timestamp()))
        
        logger.info(f"Extracted {len(features)} features for {data_type} data")
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
    """Comprehensive anomaly detection using multiple algorithms."""
    try:
        feature_values = [f[1] for f in features]
        if not feature_values:
            return None
        
        X = np.array(feature_values).reshape(-1, 1)
        anomalies_detected = 0
        
        # 1. Statistical Anomaly Detection (Z-Score)
        anomalies_detected += detect_statistical_anomalies(features, user, processed_data, X)
        
        # 2. Isolation Forest Anomaly Detection
        anomalies_detected += detect_isolation_forest_anomalies(features, user, processed_data, X)
        
        # 3. Local Outlier Factor (LOF) Detection
        anomalies_detected += detect_lof_anomalies(features, user, processed_data, X)
        
        # 4. DBSCAN Clustering Anomaly Detection
        anomalies_detected += detect_dbscan_anomalies(features, user, processed_data, X)
        
        # 5. Elliptic Envelope Detection
        anomalies_detected += detect_elliptic_envelope_anomalies(features, user, processed_data, X)
        
        # 6. Pattern-based Anomaly Detection
        anomalies_detected += detect_pattern_anomalies(features, user, processed_data)
        
        # 7. Temporal Anomaly Detection
        anomalies_detected += detect_temporal_anomalies(user, processed_data)
        
        logger.info(f"Total anomalies detected for user {user.email_id}: {anomalies_detected}")
        return anomalies_detected
        
    except Exception as e:
        logger.error(f"Error in comprehensive anomaly detection: {str(e)}")
        return 0

def detect_statistical_anomalies(features, user, processed_data, X):
    """Detect anomalies using statistical methods (Z-score, IQR)."""
    try:
        anomalies_count = 0
        for i, (feature_type, feature_value) in enumerate(features):
            # Z-score method
            z_score = abs(stats.zscore(X)[i][0]) if len(X) > 1 else 0
            
            # IQR method
            q1, q3 = np.percentile(X, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            is_outlier = False
            severity = 'LOW'
            
            if z_score > 3.0 or feature_value < lower_bound or feature_value > upper_bound:
                is_outlier = True
                if z_score > 4.0 or feature_value < (q1 - 3 * iqr) or feature_value > (q3 + 3 * iqr):
                    severity = 'HIGH'
                elif z_score > 3.5 or feature_value < (q1 - 2 * iqr) or feature_value > (q3 + 2 * iqr):
                    severity = 'MEDIUM'
            
            if is_outlier:
                Anomaly.objects.create(
                    user=user,
                    processed_data=processed_data,
                    feature=None,
                    anomaly_type=f"statistical_outlier_{feature_type}",
                    severity=severity,
                    description=f"Statistical anomaly detected in {feature_type} (Z-score: {z_score:.2f}, Value: {feature_value:.2f}). This value is statistically significant from the normal distribution."
                )
                anomalies_count += 1
        
        return anomalies_count
    except Exception as e:
        logger.error(f"Error in statistical anomaly detection: {str(e)}")
        return 0

def detect_isolation_forest_anomalies(features, user, processed_data, X):
    """Detect anomalies using Isolation Forest."""
    try:
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomalies = iso_forest.fit_predict(X)
        
        anomalies_count = 0
        for i, (feature_type, feature_value) in enumerate(features):
            if anomalies[i] == -1:
                severity = 'LOW'
                if abs(feature_value) > 2.0:
                    severity = 'HIGH'
                elif abs(feature_value) > 1.5:
                    severity = 'MEDIUM'
                
                Anomaly.objects.create(
                    user=user,
                    processed_data=processed_data,
                    feature=None,
                    anomaly_type=f"isolation_forest_{feature_type}",
                    severity=severity,
                    description=f"Isolation Forest detected anomaly in {feature_type} with value {feature_value:.2f}. This value appears isolated from normal data clusters."
                )
                anomalies_count += 1
        
        return anomalies_count
    except Exception as e:
        logger.error(f"Error in Isolation Forest detection: {str(e)}")
        return 0

def detect_lof_anomalies(features, user, processed_data, X):
    """Detect anomalies using Local Outlier Factor."""
    try:
        if len(X) < 5:  # LOF needs at least 5 samples
            return 0
            
        lof = LocalOutlierFactor(contamination=0.1, n_neighbors=min(5, len(X)-1))
        anomalies = lof.fit_predict(X)
        
        anomalies_count = 0
        for i, (feature_type, feature_value) in enumerate(features):
            if anomalies[i] == -1:
                severity = 'LOW'
                if abs(feature_value) > 2.0:
                    severity = 'HIGH'
                elif abs(feature_value) > 1.5:
                    severity = 'MEDIUM'
                
                Anomaly.objects.create(
                    user=user,
                    processed_data=processed_data,
                    feature=None,
                    anomaly_type=f"lof_{feature_type}",
                    severity=severity,
                    description=f"Local Outlier Factor detected anomaly in {feature_type} with value {feature_value:.2f}. This value has low local density compared to neighbors."
                )
                anomalies_count += 1
        
        return anomalies_count
    except Exception as e:
        logger.error(f"Error in LOF detection: {str(e)}")
        return 0

def detect_dbscan_anomalies(features, user, processed_data, X):
    """Detect anomalies using DBSCAN clustering."""
    try:
        if len(X) < 3:  # DBSCAN needs at least 3 samples
            return 0
            
        dbscan = DBSCAN(eps=0.5, min_samples=2)
        clusters = dbscan.fit_predict(X)
        
        anomalies_count = 0
        for i, (feature_type, feature_value) in enumerate(features):
            if clusters[i] == -1:  # -1 indicates noise/anomaly
                severity = 'LOW'
                if abs(feature_value) > 2.0:
                    severity = 'HIGH'
                elif abs(feature_value) > 1.5:
                    severity = 'MEDIUM'
                
                Anomaly.objects.create(
                    user=user,
                    processed_data=processed_data,
                    feature=None,
                    anomaly_type=f"dbscan_{feature_type}",
                    severity=severity,
                    description=f"DBSCAN clustering detected anomaly in {feature_type} with value {feature_value:.2f}. This value does not belong to any identified cluster."
                )
                anomalies_count += 1
        
        return anomalies_count
    except Exception as e:
        logger.error(f"Error in DBSCAN detection: {str(e)}")
        return 0

def detect_elliptic_envelope_anomalies(features, user, processed_data, X):
    """Detect anomalies using Elliptic Envelope."""
    try:
        if len(X) < 10:  # Elliptic Envelope needs more samples
            return 0
            
        envelope = EllipticEnvelope(contamination=0.1, random_state=42)
        anomalies = envelope.fit_predict(X)
        
        anomalies_count = 0
        for i, (feature_type, feature_value) in enumerate(features):
            if anomalies[i] == -1:
                severity = 'LOW'
                if abs(feature_value) > 2.0:
                    severity = 'HIGH'
                elif abs(feature_value) > 1.5:
                    severity = 'MEDIUM'
                
                Anomaly.objects.create(
                    user=user,
                    processed_data=processed_data,
                    feature=None,
                    anomaly_type=f"elliptic_envelope_{feature_type}",
                    severity=severity,
                    description=f"Elliptic Envelope detected anomaly in {feature_type} with value {feature_value:.2f}. This value falls outside the expected multivariate normal distribution."
                )
                anomalies_count += 1
        
        return anomalies_count
    except Exception as e:
        logger.error(f"Error in Elliptic Envelope detection: {str(e)}")
        return 0

def detect_pattern_anomalies(features, user, processed_data):
    """Detect anomalies based on behavioral patterns."""
    try:
        anomalies_count = 0
        
        # Check for extreme values in specific features
        for feature_type, feature_value in features:
            if feature_type == 'heart_rate':
                if feature_value > 100 or feature_value < 50:  # Abnormal heart rate
                    severity = 'HIGH' if feature_value > 120 or feature_value < 40 else 'MEDIUM'
                    Anomaly.objects.create(
                        user=user,
                        processed_data=processed_data,
                        feature=None,
                        anomaly_type=f"abnormal_heart_rate",
                        severity=severity,
                        description=f"Abnormal heart rate detected: {feature_value:.0f} BPM. Normal range is 50-100 BPM."
                    )
                    anomalies_count += 1
            
            elif feature_type == 'keystroke_speed':
                if feature_value > 200 or feature_value < 20:  # Abnormal typing speed
                    severity = 'MEDIUM'
                    Anomaly.objects.create(
                        user=user,
                        processed_data=processed_data,
                        feature=None,
                        anomaly_type=f"abnormal_typing_speed",
                        severity=severity,
                        description=f"Unusual typing speed detected: {feature_value:.0f} keystrokes/min. This may indicate stress or fatigue."
                    )
                    anomalies_count += 1
            
            elif feature_type == 'screen_time_duration':
                if feature_value > 8 * 3600:  # More than 8 hours
                    severity = 'MEDIUM'
                    Anomaly.objects.create(
                        user=user,
                        processed_data=processed_data,
                        feature=None,
                        anomaly_type=f"excessive_screen_time",
                        severity=severity,
                        description=f"Excessive screen time detected: {feature_value/3600:.1f} hours. Consider taking breaks."
                    )
                    anomalies_count += 1
        
        return anomalies_count
    except Exception as e:
        logger.error(f"Error in pattern anomaly detection: {str(e)}")
        return 0

def detect_temporal_anomalies(user, processed_data):
    """Detect anomalies based on temporal patterns."""
    try:
        anomalies_count = 0
        
        # Get recent data for temporal analysis
        recent_data = ProcessedData.objects.filter(
            user=user,
            processed_at__gte=now() - timedelta(days=7)
        ).order_by('processed_at')
        
        if recent_data.count() < 3:
            return 0
        
        # Check for unusual activity patterns
        data_types = recent_data.values_list('data_type', flat=True)
        type_counts = {}
        for data_type in data_types:
            type_counts[data_type] = type_counts.get(data_type, 0) + 1
        
        # Detect unusual frequency of data collection
        for data_type, count in type_counts.items():
            if count > 50:  # Unusually high frequency
                Anomaly.objects.create(
                    user=user,
                    processed_data=processed_data,
                    feature=None,
                    anomaly_type=f"high_frequency_{data_type.lower()}",
                    severity='MEDIUM',
                    description=f"Unusually high frequency of {data_type} data collection detected ({count} records in 7 days). This may indicate system issues or unusual behavior."
                )
                anomalies_count += 1
        
        return anomalies_count
    except Exception as e:
        logger.error(f"Error in temporal anomaly detection: {str(e)}")
        return 0