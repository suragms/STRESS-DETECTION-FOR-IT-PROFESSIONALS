from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now, timedelta
from .models import UsersRegister, StressAssessment, Feedback, KeyboardActivity, ScreenTime, ApplicationUsage, VoicePattern, WearableData, Recommendation, Alert, Resource, ProcessedData, ExtractedFeature, StressPattern, Anomaly, MLPrediction
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
import uuid
from .helpers import send_forget_password_mail
import json
import csv
from django.db.models import Avg, Max, Min, Sum
from django.contrib.auth import logout
import logging

# Set up logging
logger = logging.getLogger(__name__)

def home(request):
    feedbacks = Feedback.objects.select_related('user').order_by('-date')[:3]
    return render(request, 'home.html', {'feedbacks': feedbacks})

from django.core.serializers import serialize

def usershome(request):
    if 'email' in request.session:
        mail = request.session['email']
        try:
            user = UsersRegister.objects.get(email_id=mail)
            # Fetch unacknowledged alerts for the user, ordered by most recent
            alerts = Alert.objects.filter(user=user, is_acknowledged=False).order_by('-triggered_at')
            # Serialize alerts to JSON
            alerts_json = serialize('json', alerts)
            # Parse JSON to ensure it's properly formatted for JavaScript
            alerts_data = json.loads(alerts_json)
            # Extract fields and format for JavaScript
            alerts_formatted = [
                {
                    'id': alert['pk'],
                    'title': f"High Stress Alert (Threshold: {alert['fields']['threshold']})",
                    'description': alert['fields']['message'],
                    'timestamp': alert['fields']['triggered_at'],
                    'read': alert['fields']['is_acknowledged']
                } for alert in alerts_data
            ]
            user_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.email_id,  # using email_id as username
                'is_authenticated': True,
            }
            return render(request, 'usershome.html', {
                'user': user,
                'alerts': json.dumps(alerts_formatted),  # Pass JSON string to template
                'user_data': user_data,
            })
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {mail} not found in usershome")
            request.session.flush()
            messages.error(request, "User not found. Please log in again.")
            return redirect('login')
    return redirect('login')


from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login

def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email_id = request.POST.get('email_id')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        image = request.FILES.get('image')
        department = request.POST.get('department')
        new_department = request.POST.get('new_department')
        years_of_experience = request.POST.get('years_of_experience')
        work_role = request.POST.get('work_role')

        # Check if email already exists
        if UsersRegister.objects.filter(email_id=email_id).exists() or User.objects.filter(email=email_id).exists():
            messages.error(request, 'Email ID already exists. Please log in.')
            return redirect('/login/')

        # Validate passwords
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'userregistration.html')

        # Handle department
        if department == 'add_new' and new_department:
            department = new_department

        try:
            # Create Django User
            user = User.objects.create_user(
                username=email_id,  # Using email as username for simplicity
                email=email_id,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create UsersRegister profile
            profile = UsersRegister(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email_id=email_id,
                password=password,  # Storing plaintext password (consider removing if not needed)
                confirm_password=confirm_password,
                image=image,
                department=department,
                years_of_experience=years_of_experience,
                work_role=work_role
            )
            profile.save()

            messages.success(request, 'Signup successful. Please log in.')
            return redirect('/login/')
        except Exception as e:
            logger.error(f"Error during signup for {email_id}: {str(e)}")
            messages.error(request, 'An error occurred during signup. Please try again.')
            return render(request, 'userregistration.html')
    return render(request, 'userregistration.html')


def login(request):
    if request.method == "POST":
        email = request.POST.get('email_id')
        password = request.POST.get('password')
        try:
            user = UsersRegister.objects.get(email_id=email, password=password)
            request.session['email'] = user.email_id
            logger.info(f"User {user.email_id} logged in successfully, session set")
            return redirect('/usershome/')
        except UsersRegister.DoesNotExist:
            logger.warning(f"Login failed for email {email}: Invalid credentials")
            msg = "Invalid user"
            return render(request, 'userlogin.html', {"msg": msg})
    return render(request, 'userlogin.html')
           

def userprofile(request):
    if 'email' in request.session:
        mail = request.session['email']
        try:
            user = UsersRegister.objects.get(email_id=mail)
            return render(request, 'userprofile.html', {'user': user})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {mail} not found in userprofile")
            request.session.flush()
            return redirect('login')
    return redirect('login')

def userprofile_edit(request, eid):
    edt = UsersRegister.objects.get(id=eid)
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email_id = request.POST.get('email_id')
        image = request.FILES.get('image')
        department = request.POST.get('department')
        years_of_experience = request.POST.get('years_of_experience')
        work_role = request.POST.get('work_role')

        edt.first_name = first_name
        edt.last_name = last_name
        edt.email_id = email_id
        edt.department = department
        edt.years_of_experience = years_of_experience
        edt.work_role = work_role
        if image is not None:
            edt.image = image
        edt.save()
        return redirect("userprofile")
    return render(request, 'edit_profile.html', {'edt': edt})

def get_departments(request):
    departments = UsersRegister.objects.values_list('department', flat=True).distinct()
    return JsonResponse({'departments': list(departments)})

def user_logout(request):
    logger.info(f"User {request.session.get('email')} logged out")
    request.session.flush()
    return redirect('home')

def create_sample_data_for_user(user):
    """Create sample data for demonstration purposes"""
    from datetime import timedelta
    
    # Create sample stress assessment
    if not StressAssessment.objects.filter(user=user).exists():
        StressAssessment.objects.create(
            user=user,
            stress_score=75,
            responses='{"question1": "Sometimes", "question2": "Often"}',
            recommendations='Take regular breaks and practice mindfulness'
        )
    
    # Create sample wearable data for the last 7 days
    for i in range(7):
        date = now() - timedelta(days=i)
        WearableData.objects.get_or_create(
            user=user,
            timestamp=date,
            defaults={
                'device_type': 'FITBIT',
                'heart_rate': 72 + (i * 2),
                'steps': 8000 + (i * 500),
                'sleep_duration': timedelta(hours=7.5 - (i * 0.2)),
                'stress_indicator': 0.6 + (i * 0.05)
            }
        )

def settings_view(request):
    if 'email' in request.session:
        mail = request.session['email']
        try:
            user = UsersRegister.objects.get(email_id=mail)
            
            # Uncomment the line below to create sample data for testing
            # create_sample_data_for_user(user)
            
            # Fetch data from models for stats
            context = {'user': user}
            
            # 1. Stress Level - Get latest stress assessment
            try:
                latest_stress = StressAssessment.objects.filter(user=user).order_by('-date').first()
                if latest_stress:
                    context['stress_level'] = latest_stress.stress_score
                else:
                    context['stress_level'] = None
            except Exception as e:
                logger.error(f"Error fetching stress level for user {user.email_id}: {str(e)}")
                context['stress_level'] = None
            
            # 2. Average Sleep - Get from wearable data
            try:
                # Get sleep data from the last 7 days
                week_ago = now() - timedelta(days=7)
                sleep_data = WearableData.objects.filter(
                    user=user,
                    sleep_duration__isnull=False,
                    timestamp__gte=week_ago
                ).aggregate(avg_sleep=Avg('sleep_duration'))
                
                if sleep_data['avg_sleep']:
                    # Convert timedelta to hours
                    total_seconds = sleep_data['avg_sleep'].total_seconds()
                    context['avg_sleep'] = round(total_seconds / 3600, 1)
                else:
                    context['avg_sleep'] = None
            except Exception as e:
                logger.error(f"Error fetching sleep data for user {user.email_id}: {str(e)}")
                context['avg_sleep'] = None
            
            # 3. Daily Steps - Get from wearable data
            try:
                # Get steps from today
                today = now().date()
                today_steps = WearableData.objects.filter(
                    user=user,
                    steps__isnull=False,
                    timestamp__date=today
                ).aggregate(total_steps=Sum('steps'))
                
                if today_steps['total_steps']:
                    context['daily_steps'] = today_steps['total_steps']
                else:
                    context['daily_steps'] = None
            except Exception as e:
                logger.error(f"Error fetching steps data for user {user.email_id}: {str(e)}")
                context['daily_steps'] = None
            
            # 4. Current Streak - Calculate from stress assessments or daily activities
            try:
                # Calculate streak based on consecutive days with stress assessments
                stress_dates = StressAssessment.objects.filter(
                    user=user
                ).values_list('date__date', flat=True).distinct().order_by('-date__date')
                
                if stress_dates:
                    current_date = now().date()
                    streak = 0
                    check_date = current_date
                    
                    for stress_date in stress_dates:
                        if stress_date == check_date:
                            streak += 1
                            check_date -= timedelta(days=1)
                        else:
                            break
                    
                    context['current_streak'] = streak if streak > 0 else None
                else:
                    context['current_streak'] = None
            except Exception as e:
                logger.error(f"Error calculating streak for user {user.email_id}: {str(e)}")
                context['current_streak'] = None
            
            return render(request, 'settings.html', context)
            
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {mail} not found in settings")
            request.session.flush()
            return redirect('login')
    return redirect('login')

def debug_user_data(request):
    """Debug endpoint to check user data (for development only)"""
    if 'email' in request.session:
        mail = request.session['email']
        try:
            user = UsersRegister.objects.get(email_id=mail)
            
            # Get all data for the user
            stress_assessments = StressAssessment.objects.filter(user=user).count()
            wearable_data = WearableData.objects.filter(user=user).count()
            keyboard_activity = KeyboardActivity.objects.filter(user=user).count()
            screen_time = ScreenTime.objects.filter(user=user).count()
            
            context = {
                'user': user,
                'stress_assessments_count': stress_assessments,
                'wearable_data_count': wearable_data,
                'keyboard_activity_count': keyboard_activity,
                'screen_time_count': screen_time,
                'latest_stress': StressAssessment.objects.filter(user=user).order_by('-date').first(),
                'latest_wearable': WearableData.objects.filter(user=user).order_by('-timestamp').first(),
            }
            
            return render(request, 'debug_data.html', context)
            
        except UsersRegister.DoesNotExist:
            return JsonResponse({'error': 'User not found'})
    
    return JsonResponse({'error': 'Not authenticated'})

def faq_view(request):
    return render(request, 'faq.html')

def account_privacy_view(request):
    if 'email' in request.session:
        mail = request.session['email']
        try:
            user = UsersRegister.objects.get(email_id=mail)
            stress_assessments = StressAssessment.objects.filter(user=user).order_by('-date')[:5]
            feedbacks = Feedback.objects.filter(user=user).order_by('-date')[:5]
            return render(request, 'account_privacy.html', {
                'user': user,
                'stress_assessments': stress_assessments,
                'feedbacks': feedbacks
            })
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {mail} not found in account_privacy_view")
            request.session.flush()
            return redirect('login')
    return redirect('login')

def solutions(request):
    return render(request, 'solution.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import UsersRegister
import uuid
import logging


def forget_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = UsersRegister.objects.get(email_id=email)
            print(user)
            token = str(uuid.uuid4())
            user.confirm_password_token = token
            user.save()
            send_forget_password_mail(user.email_id, token)
            messages.success(request, 'Password reset link has been sent to your email.')
            return redirect('/login/')
        except Exception as e:
            print(e)
            messages.error(request, 'No account found with that email.')
    return render(request, 'forget-password.html')

def change_password(request, token):
    try:
        user = UsersRegister.objects.filter(confirm_password_token=token).first()
        if not user:
            messages.error(request, 'Invalid or expired token.')
            return redirect('/forget-password/')
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return redirect(f'/change-password/{token}/')
            user.password = new_password
            user.confirm_password = new_password
        #    user.confirm_password_token = None
            user.save()
            messages.success(request, 'Password updated successfully. Please log in.')
            return redirect('/login/')
    except Exception as e:
        logger.error(f"Error in change_password: {str(e)}")
        messages.error(request, 'An error occurred.')
    return render(request, 'change-password.html')
import json
import logging
from django.shortcuts import render, redirect
from django.utils.timezone import now
from .models import StressAssessment, UsersRegister

def stress_assessment(request):
    if request.method == "POST":
        try:
            responses = request.POST.getlist('responses')
            stress_score = sum(map(int, responses))  # Convert responses to integers and sum
            recommendations = (
                "Take a break and practice relaxation techniques." 
                if stress_score > 10 
                else "You are doing well!"
            )
            
            email = request.session.get('email')
            if not email:
                logger.warning("No email in session, redirecting to login")
                return redirect('login')
            
            try:
                user = UsersRegister.objects.get(email_id=email)
            except UsersRegister.DoesNotExist:
                logger.error(f"No user found for email: {email}, clearing session")
                request.session.flush()
                return redirect('login')
            
            # Create the assessment with responses as a JSON string
            assessment = StressAssessment.objects.create(
                user=user,
                date=now(),
                responses=json.dumps(responses),  # Already serialized as string
                stress_score=stress_score,
                recommendations=recommendations
            )
            logger.info(f"Stress assessment created for user: {email}, ID: {assessment.id}")
            return redirect('stress_result', assessment_id=assessment.id)  # Named parameter for clarity
        except ValueError as e:
            logger.error(f"Invalid response data: {e}")
            return render(request, "stress_assessment.html", {'error': 'Please provide valid responses'})
        except Exception as e:
            logger.error(f"Error in stress_assessment: {e}")
            return render(request, "stress_assessment.html", {'error': 'An error occurred'})
    
    return render(request, "stress_assessment.html")

def stress_result(request, assessment_id):
    assessment = StressAssessment.objects.get(id=assessment_id)
    return render(request, "stress_result.html", {"assessment": assessment})

    
def dashboard(request):
    email = request.session.get('email')
    if not email:
        return redirect('login')
    try:
        user = UsersRegister.objects.get(email_id=email)
    except UsersRegister.DoesNotExist:
        logger.error(f"User with email {email} not found in dashboard")
        request.session.flush()
        return redirect('login')
    assessments = StressAssessment.objects.filter(user=user).order_by('date')
    latest_assessment = assessments.last()
    dates = [assessment.date.strftime("%Y-%m-%d") for assessment in assessments]
    scores = [assessment.stress_score for assessment in assessments]
    total_assessments = assessments.count()
    avg_stress_score = assessments.aggregate(Avg('stress_score'))['stress_score__avg'] or 0
    max_stress_score = assessments.aggregate(Max('stress_score'))['stress_score__max'] or 0
    min_stress_score = assessments.aggregate(Min('stress_score'))['stress_score__min'] or 0
    context = {
        'latest_assessment': latest_assessment,
        'dates': json.dumps(dates),
        'scores': json.dumps(scores),
        'total_assessments': total_assessments,
        'avg_stress_score': avg_stress_score,
        'max_stress_score': max_stress_score,
        'min_stress_score': min_stress_score
    }
    return render(request, 'dashboard.html', context)

def user_dashboard(request):
    email = request.session.get('email')
    if not email:
        logger.warning("No email in session, redirecting to login")
        return redirect('login')
    
    try:
        user = UsersRegister.objects.get(email_id=email)
        logger.info(f"User {user.email_id} accessed unified_dashboard")
    except UsersRegister.DoesNotExist:
        logger.error(f"No user found for email: {email}, clearing session and redirecting")
        request.session.flush()
        return redirect('login')
    
    # Data Collection Dashboard data
    keyboard_data = KeyboardActivity.objects.filter(user=user).order_by('-timestamp')[:5]
    screen_time_data = ScreenTime.objects.filter(user=user).order_by('-timestamp')[:5]
    app_usage_data = ApplicationUsage.objects.filter(user=user).order_by('-timestamp')[:5]
    voice_data = VoicePattern.objects.filter(user=user).order_by('-timestamp')[:5]
    wearable_data = WearableData.objects.filter(user=user).order_by('-timestamp')[:5]
    
    # Stress Assessment Dashboard data
    assessments = StressAssessment.objects.filter(user=user).order_by('date')
    latest_assessment = assessments.last()
    dates = [assessment.date.strftime("%Y-%m-%d") for assessment in assessments]
    scores = [assessment.stress_score for assessment in assessments]
    total_assessments = assessments.count()
    avg_stress_score = assessments.aggregate(Avg('stress_score'))['stress_score__avg'] or 0
    max_stress_score = assessments.aggregate(Max('stress_score'))['stress_score__max'] or 0
    min_stress_score = assessments.aggregate(Min('stress_score'))['stress_score__min'] or 0

    context = {
        'user': user,
        # Data Collection context
        'keyboard_data': keyboard_data,
        'screen_time_data': screen_time_data,
        'app_usage_data': app_usage_data,
        'voice_data': voice_data,
        'wearable_data': wearable_data,
        # Stress Assessment context
        'latest_assessment': latest_assessment,
        'dates': json.dumps(dates),
        'scores': json.dumps(scores),
        'total_assessments': total_assessments,
        'avg_stress_score': avg_stress_score,
        'max_stress_score': max_stress_score,
        'min_stress_score': min_stress_score
    }
    logger.debug(f"Rendering unified_dashboard for user: {user.email_id}")
    return render(request, 'user_dashboard.html', context)
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .models import UsersRegister, Feedback
from .forms import FeedbackForm
import logging

def submit_feedback(request):
    # Check if user is authenticated via session
    if 'email' not in request.session:
        logger.warning("No email in session, redirecting to login")
        messages.error(request, 'Please log in to submit feedback.')
        return redirect('login')

    # Validate user existence
    try:
        user = UsersRegister.objects.get(email_id=request.session['email'])
    except ObjectDoesNotExist:
        logger.error(f"No user found for email: {request.session['email']}, clearing session")
        request.session.flush()
        messages.error(request, 'User not found. Please log in again.')
        return redirect('login')

    # Rate limiting: Check if user submitted feedback recently (within 5 minutes)
    form = FeedbackForm(request.POST or None)
    recent_feedback = Feedback.objects.filter(
        user=user,
        date__gte=timezone.now() - timezone.timedelta(minutes=5)
    ).exists()
    if recent_feedback and request.method != "POST":
        logger.warning(f"User {user.email_id} is rate-limited, rendering page with error")
        messages.error(request, 'You can only submit feedback once every 5 minutes.')

    if request.method == "POST":
        if form.is_valid():
            if recent_feedback:
                logger.warning(f"User {user.email_id} attempted POST while rate-limited")
                messages.error(request, 'You can only submit feedback once every 5 minutes.')
            else:
                try:
                    feedback = form.save(commit=False)
                    feedback.user = user
                    feedback.rating = int(form.cleaned_data['rating'])  # Ensure rating is integer
                    feedback.save()
                    logger.info(
                        f"Feedback saved for user {user.email_id}: "
                        f"{feedback.feedback_text[:50]}..., rating {feedback.rating}"
                    )
                    messages.success(request, 'Feedback submitted successfully.')
                    return redirect('submit_feedback')
                except Exception as e:
                    logger.exception(f"Error saving feedback for user {user.email_id}: {str(e)}")
                    messages.error(request, 'An error occurred while saving feedback. Please try again.')
        else:
            logger.warning(f"Form validation failed for user {user.email_id}: {form.errors}")
            messages.error(request, 'Please correct the errors below.')

    # Filter messages to include only feedback-related ones
    feedback_related_messages = [
        'Feedback submitted successfully.',
        'You can only submit feedback once every 5 minutes.',
        'An error occurred while saving feedback. Please try again.',
        'Please correct the errors below.'
    ]
    
    # Get all messages and filter them
    storage = messages.get_messages(request)
    filtered_messages = [
        {'message': str(msg), 'level': msg.level, 'tags': msg.tags}
        for msg in storage
        if str(msg) in feedback_related_messages
    ]
    
    # Mark messages as used to prevent them from being displayed again
    storage.used = True

    logger.debug(f"Rendering submit_feedback page for user {user.email_id}")
    return render(request, 'submit_feedback.html', {
        'form': form,
        'user': user,
        'messages': filtered_messages  # Pass filtered messages to the template
    })
    
def view_feedback(request):
    if 'email' in request.session:
        user = UsersRegister.objects.get(email_id=request.session['email'])
        feedbacks = Feedback.objects.filter(user=user)
        return render(request, 'view_feedback.html', {'feedbacks': feedbacks})
    return redirect('login')

# admin login
def adminlogin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        e = 'admin2024@gmail.com'
        p = 'admin@123'
        if email == e and password == p:
            request.session['email'] = email  # Set session for admin
            return redirect('admin_dashboard')
        else:
            messages.warning(request, 'Incorrect email or password. Please try again.')
    return render(request, 'admin_login.html')

# admin logout
def admin_logout(request):
    logger.info(f"Admin {request.session.get('email')} logged out")
    request.session.flush()
    return redirect('admin_login')

# admin manage users
from django.shortcuts import render, redirect
from .models import UsersRegister

def admin_manage_users(request):
    # Session-based admin check
    if 'email' not in request.session or request.session['email'] != 'admin2024@gmail.com':
        return redirect('admin_login')

    # Fetch users with related data to reduce queries
    users = UsersRegister.objects.select_related('user').all()
    
    context = {
        'users': users,
    }
    return render(request, 'admin_manage_users.html', context)
# admin dashboard
from django.db.models import Avg, Sum, Max
from django.shortcuts import render, redirect
from .models import UsersRegister, StressAssessment, KeyboardActivity, Feedback, VoicePattern, ScreenTime

def admin_dashboard(request):
    # Session-based admin check
    if 'email' not in request.session or request.session['email'] != 'admin2024@gmail.com':
        return redirect('admin_login')

    # Fetch users with related data to reduce queries
    users = UsersRegister.objects.select_related('user').all()
    
    # Compute user-specific data
    user_data = []
    for user in users:
        stress_avg = StressAssessment.objects.filter(user=user).aggregate(Avg('stress_score'))['stress_score__avg'] or 0
        keystrokes_sum = KeyboardActivity.objects.filter(user=user).aggregate(Sum('keystrokes_per_minute'))['keystrokes_per_minute__sum'] or 0
        feedback_avg = Feedback.objects.filter(user=user).aggregate(Avg('rating'))['rating__avg'] or 0
        voice_avg = VoicePattern.objects.filter(user=user).aggregate(Avg('stress_level'))['stress_level__avg'] or 0
        screen_time_sum = ScreenTime.objects.filter(user=user).aggregate(Sum('duration'))['duration__sum'] or 0
        screen_time_hours = screen_time_sum.total_seconds() / 3600 if screen_time_sum else 0

        user_data.append({
            'user': user,
            'stress_trend': round(stress_avg, 2),
            'keyboard_review': keystrokes_sum,  # Consider changing to avg
            'feedback_details': round(feedback_avg, 2) if feedback_avg else 0,
            'voice_patterns': round(voice_avg, 2) if voice_avg else 0,
            'screen_time': round(screen_time_hours, 2),
        })

    # Aggregate statistics
    total_users = users.count()
    assessments = StressAssessment.objects.all().order_by('date')
    total_assessments = assessments.count()
    avg_stress_score = assessments.aggregate(avg_score=Avg('stress_score'))['avg_score'] or 0
    max_stress_score = assessments.aggregate(max_score=Max('stress_score'))['max_score'] or 0

    context = {
        'total_users': total_users,
        'avg_stress_score': round(avg_stress_score, 2),
        'max_stress_score': max_stress_score,
        'total_assessments': total_assessments,
        'user_data': user_data,
    }
    return render(request, 'admin_dashboard.html', context)

#admin delete user
def delete_user(request, user_id):
    user = get_object_or_404(UsersRegister, id=user_id)
    user.delete()
    return redirect('admin_manage_users')

# admin edit user
def edit_user(request, user_id):
    user = get_object_or_404(UsersRegister, id=user_id)
    if request.method == 'POST':
        user.first_name = request.POST['first_name']
        user.last_name = request.POST['last_name']
        user.email_id = request.POST['email_id']
        user.department = request.POST['department']
        user.years_of_experience = request.POST['years_of_experience']
        user.work_role = request.POST['work_role']
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password and confirm_password:
            if password == confirm_password:
                user.password = password
                user.confirm_password = confirm_password
            else:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'edit_user.html', {'user': user})
        if 'image' in request.FILES:
            user.image = request.FILES['image']
        user.save()
        messages.success(request, 'User details updated successfully.')
        return redirect('admin_manage_users')
    return render(request, 'edit_user.html', {'user': user})

def export_stress_reports(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stress_reports.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Stress Score', 'Recommendations'])
    assessments = StressAssessment.objects.all().values_list('date', 'stress_score', 'recommendations')
    for assessment in assessments:
        writer.writerow(assessment)
    return response

# Data Collection Views
def data_collection_dashboard(request):
    email = request.session.get('email')
    if not email:
        logger.warning("No email in session, redirecting to login")
        return redirect('login')
    
    try:
        user = UsersRegister.objects.get(email_id=email)
        logger.info(f"User {user.email_id} accessed data_collection_dashboard")
    except UsersRegister.DoesNotExist:
        logger.error(f"No user found for email: {email}, clearing session and redirecting")
        request.session.flush()
        return redirect('login')
    
    keyboard_data = KeyboardActivity.objects.filter(user=user).order_by('-timestamp')[:5]
    screen_time_data = ScreenTime.objects.filter(user=user).order_by('-timestamp')[:5]
    app_usage_data = ApplicationUsage.objects.filter(user=user).order_by('-timestamp')[:5]
    voice_data = VoicePattern.objects.filter(user=user).order_by('-timestamp')[:5]
    wearable_data = WearableData.objects.filter(user=user).order_by('-timestamp')[:5]
    
    context = {
        'user': user,
        'keyboard_data': keyboard_data,
        'screen_time_data': screen_time_data,
        'app_usage_data': app_usage_data,
        'voice_data': voice_data,
        'wearable_data': wearable_data,
    }
    logger.debug(f"Rendering data_collection_dashboard for user: {user.email_id}")
    return render(request, 'data_collection_dashboard.html', context)

def collect_keyboard_activity(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'User not logged in'})
        try:
            user = UsersRegister.objects.get(email_id=email)
            keystrokes = int(request.POST.get('keystrokes', 0))
            duration = timedelta(seconds=int(request.POST.get('duration', 0)))
            
            KeyboardActivity.objects.create(
                user=user,
                keystrokes_per_minute=keystrokes,
                typing_duration=duration
            )
            return JsonResponse({'status': 'success'})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in collect_keyboard_activity")
            request.session.flush()
            return JsonResponse({'status': 'error', 'message': 'User not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def collect_screen_time(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'User not logged in'})
        try:
            user = UsersRegister.objects.get(email_id=email)
            duration = timedelta(seconds=int(request.POST.get('duration', 0)))
            application = request.POST.get('application', '')
            
            ScreenTime.objects.create(
                user=user,
                duration=duration,
                application=application
            )
            return JsonResponse({'status': 'success'})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in collect_screen_time")
            request.session.flush()
            return JsonResponse({'status': 'error', 'message': 'User not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def collect_app_usage(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'User not logged in'})
        try:
            user = UsersRegister.objects.get(email_id=email)
            app_name = request.POST.get('app_name', '')
            duration = timedelta(seconds=int(request.POST.get('duration', 0)))
            
            ApplicationUsage.objects.create(
                user=user,
                app_name=app_name,
                usage_duration=duration
            )
            return JsonResponse({'status': 'success'})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in collect_app_usage")
            request.session.flush()
            return JsonResponse({'status': 'error', 'message': 'User not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def collect_voice_pattern(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'User not logged in'})
        try:
            user = UsersRegister.objects.get(email_id=email)
            audio_file = request.FILES.get('audio_file')
            stress_level = float(request.POST.get('stress_level', 0.0)) if request.POST.get('stress_level') else None
            
            VoicePattern.objects.create(
                user=user,
                audio_file=audio_file,
                stress_level=stress_level
            )
            return JsonResponse({'status': 'success'})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in collect_voice_pattern")
            request.session.flush()
            return JsonResponse({'status': 'error', 'message': 'User not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def collect_wearable_data(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'User not logged in'})
        try:
            user = UsersRegister.objects.get(email_id=email)
            device_type = request.POST.get('device_type')
            heart_rate = int(request.POST.get('heart_rate', 0)) if request.POST.get('heart_rate') else None
            steps = int(request.POST.get('steps', 0)) if request.POST.get('steps') else None
            sleep_duration = timedelta(seconds=int(request.POST.get('sleep_duration', 0))) if request.POST.get('sleep_duration') else None
            stress_indicator = float(request.POST.get('stress_indicator', 0.0)) if request.POST.get('stress_indicator') else None
            
            WearableData.objects.create(
                user=user,
                device_type=device_type,
                heart_rate=heart_rate,
                steps=steps,
                sleep_duration=sleep_duration,
                stress_indicator=stress_indicator
            )
            return JsonResponse({'status': 'success'})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in collect_wearable_data")
            request.session.flush()
            return JsonResponse({'status': 'error', 'message': 'User not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def post_keyboard_activity(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            messages.error(request, 'Please log in to post keyboard activity.')
            return redirect('login')
        try:
            user = UsersRegister.objects.get(email_id=email)
            keystrokes = int(request.POST.get('keystrokes', 0))
            duration = timedelta(seconds=int(request.POST.get('duration', 0)))
            
            KeyboardActivity.objects.create(
                user=user,
                keystrokes_per_minute=keystrokes,
                typing_duration=duration
            )
            messages.success(request, 'Keyboard activity posted successfully.')
            return redirect('data_collection_dashboard')
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in post_keyboard_activity")
            request.session.flush()
            return redirect('login')
    return render(request, 'post_keyboard_activity.html')

from django.utils.timezone import make_aware
from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ScreenTime, UsersRegister
from .serializers import ScreenTimeSerializer  # We'll create this next
from django.shortcuts import render, redirect
from django.utils.timezone import make_aware, is_naive
from datetime import datetime, timedelta
from django.contrib import messages
from django.db import transaction
from .models import ScreenTime, UsersRegister
import logging

logger = logging.getLogger(__name__)

def post_screen_time(request):
    if request.method == 'POST':
        # Log POST data for debugging
        logger.debug(f"POST data: {request.POST}")
        logger.debug(f"CSRF token: {request.POST.get('csrfmiddlewaretoken')}")

        email = request.session.get('email')
        if not email:
            messages.error(request, 'Please log in to post screen time.')
            return redirect('login')
        
        try:
            with transaction.atomic():  # Ensure database consistency
                user = UsersRegister.objects.get(email_id=email)
                
                # Validate duration
                duration_str = request.POST.get('duration', '0')
                if not duration_str or not duration_str.isdigit():
                    messages.error(request, 'Duration must be a valid number.')
                    return render(request, 'post_screen_time.html')
                duration_seconds = int(duration_str)
                if duration_seconds <= 0:
                    messages.error(request, 'Duration must be greater than 0 seconds.')
                    return render(request, 'post_screen_time.html')

                # Validate application and category
                application = request.POST.get('application', '')
                category = request.POST.get('category', 'OTHER')
                if not application:
                    messages.error(request, 'Please select an application.')
                    return render(request, 'post_screen_time.html')
                if not category:
                    messages.error(request, 'Please select a category.')
                    return render(request, 'post_screen_time.html')

                # Handle datetime fields
                start_time_str = request.POST.get('start_time', '')
                end_time_str = request.POST.get('end_time', '')
                start_time = None
                end_time = None
                if start_time_str:
                    try:
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        if is_naive(start_time):
                            start_time = make_aware(start_time)
                    except ValueError as e:
                        logger.error(f"Invalid start_time format: {start_time_str}, error: {e}")
                        messages.error(request, 'Invalid start time format.')
                        return render(request, 'post_screen_time.html')
                if end_time_str:
                    try:
                        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                        if is_naive(end_time):
                            end_time = make_aware(end_time)
                    except ValueError as e:
                        logger.error(f"Invalid end_time format: {end_time_str}, error: {e}")
                        messages.error(request, 'Invalid end time format.')
                        return render(request, 'post_screen_time.html')

                # Create and save ScreenTime record
                screen_time = ScreenTime(
                    user=user,
                    duration=timedelta(seconds=duration_seconds),
                    application=application,
                    category=category,
                    start_time=start_time,
                    end_time=end_time,
                    is_active=False
                )
                screen_time.save()
                logger.info(f"ScreenTime record created: {screen_time.id} for user {user.email_id}")

                messages.success(request, 'Screen time posted successfully.')
                return redirect('data_collection_dashboard')
        
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in post_screen_time")
            request.session.flush()
            messages.error(request, 'User not found. Please log in again.')
            return redirect('login')
        except Exception as e:
            logger.error(f"Failed to save ScreenTime record: {str(e)}", exc_info=True)
            messages.error(request, f'Failed to save screen time: {str(e)}')
            return render(request, 'post_screen_time.html')
    
    return render(request, 'post_screen_time.html')

# Updated collect_screen_time view (for API-based collection)
def collect_screen_time(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'User not logged in'})
        try:
            user = UsersRegister.objects.get(email_id=email)
            duration_seconds = int(request.POST.get('duration', 0))
            application = request.POST.get('application', '')
            category = request.POST.get('category', 'OTHER')
            start_time_str = request.POST.get('start_time')
            end_time_str = request.POST.get('end_time')
            is_active = request.POST.get('is_active', 'false').lower() == 'true'

            # Convert ISO format strings to datetime objects
            start_time = None
            end_time = None
            if start_time_str:
                start_time = make_aware(datetime.fromisoformat(start_time_str.replace('Z', '+00:00')))
            if end_time_str:
                end_time = make_aware(datetime.fromisoformat(end_time_str.replace('Z', '+00:00')))

            # Create ScreenTime record
            ScreenTime.objects.create(
                user=user,
                duration=timedelta(seconds=duration_seconds),
                application=application,
                category=category,
                start_time=start_time,
                end_time=end_time,
                is_active=is_active
            )
            return JsonResponse({'status': 'success'})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in collect_screen_time")
            request.session.flush()
            return JsonResponse({'status': 'error', 'message': 'User not found'})
        except ValueError as e:
            logger.error(f"Error in collect_screen_time: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Invalid data'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

# API ViewSet for ScreenTime
class ScreenTimeViewSet(viewsets.ModelViewSet):
    queryset = ScreenTime.objects.all()
    serializer_class = ScreenTimeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return screen time records for the authenticated user
        return ScreenTime.objects.filter(user__email_id=self.request.user.email_id)

    def perform_create(self, serializer):
        # Automatically set the user to the authenticated user
        serializer.save(user=UsersRegister.objects.get(email_id=self.request.user.email_id))

    @action(detail=True, methods=['post'])
    def start_timer(self, request, pk=None):
        screen_time = self.get_object()
        if screen_time.is_active:
            return Response({'status': 'error', 'message': 'Timer is already active'}, status=status.HTTP_400_BAD_REQUEST)
        
        screen_time.start_time = now()
        screen_time.is_active = True
        screen_time.save()
        serializer = self.get_serializer(screen_time)
        return Response({'status': 'success', 'data': serializer.data})

    @action(detail=True, methods=['post'])
    def stop_timer(self, request, pk=None):
        screen_time = self.get_object()
        if not screen_time.is_active:
            return Response({'status': 'error', 'message': 'Timer is not active'}, status=status.HTTP_400_BAD_REQUEST)
        
        screen_time.end_time = now()
        screen_time.duration = screen_time.end_time - screen_time.start_time
        screen_time.is_active = False
        screen_time.save()
        serializer = self.get_serializer(screen_time)
        return Response({'status': 'success', 'data': serializer.data})

    @action(detail=False, methods=['get'])
    def active_timer(self, request):
        # Return the active timer for the user, if any
        screen_time = ScreenTime.objects.filter(user__email_id=self.request.user.email_id, is_active=True).first()
        if not screen_time:
            return Response({'status': 'error', 'message': 'No active timer'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(screen_time)
        return Response({'status': 'success', 'data': serializer.data})

def post_application_usage(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            messages.error(request, 'Please log in to post application usage.')
            return redirect('login')
        try:
            user = UsersRegister.objects.get(email_id=email)
            app_name = request.POST.get('app_name', '')
            duration = timedelta(seconds=int(request.POST.get('duration', 0)))
            
            ApplicationUsage.objects.create(
                user=user,
                app_name=app_name,
                usage_duration=duration
            )
            messages.success(request, 'Application usage posted successfully.')
            return redirect('data_collection_dashboard')
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in post_application_usage")
            request.session.flush()
            return redirect('login')
    return render(request, 'post_application_usage.html')

def post_voice_pattern(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            messages.error(request, 'Please log in to post voice pattern.')
            return redirect('login')
        try:
            user = UsersRegister.objects.get(email_id=email)
            audio_file = request.FILES.get('audio_file')
            stress_level = float(request.POST.get('stress_level', 0.0)) if request.POST.get('stress_level') else None
            
            VoicePattern.objects.create(
                user=user,
                audio_file=audio_file,
                stress_level=stress_level
            )
            messages.success(request, 'Voice pattern posted successfully.')
            return redirect('data_collection_dashboard')
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in post_voice_pattern")
            request.session.flush()
            return redirect('login')
    return render(request, 'post_voice_pattern.html')

def post_wearable_data(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            messages.error(request, 'Please log in to post wearable data.')
            return redirect('login')
        try:
            user = UsersRegister.objects.get(email_id=email)
            device_type = request.POST.get('device_type')
            heart_rate = int(request.POST.get('heart_rate', 0)) if request.POST.get('heart_rate') else None
            steps = int(request.POST.get('steps', 0)) if request.POST.get('steps') else None
            sleep_duration = timedelta(seconds=int(request.POST.get('sleep_duration', 0))) if request.POST.get('sleep_duration') else None
            stress_indicator = float(request.POST.get('stress_indicator', 0.0)) if request.POST.get('stress_indicator') else None
            
            WearableData.objects.create(
                user=user,
                device_type=device_type,
                heart_rate=heart_rate,
                steps=steps,
                sleep_duration=sleep_duration,
                stress_indicator=stress_indicator
            )
            messages.success(request, 'Wearable data posted successfully.')
            return redirect('data_collection_dashboard')
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in post_wearable_data")
            request.session.flush()
            return redirect('login')
    return render(request, 'post_wearable_data.html')

def recommendation_dashboard(request):
    if 'email' not in request.session:
        logger.warning("No email in session, redirecting to login")
        messages.error(request, "Please log in to access the dashboard.")
        return redirect('login')
    
    try:
        user = UsersRegister.objects.get(email_id=request.session['email'])
        recommendations = Recommendation.objects.filter(
            user=user, is_completed=False
        ).order_by('-created_at')
        alerts = Alert.objects.filter(
            user=user, is_acknowledged=False
        ).order_by('-triggered_at')
        pending_alerts = alerts.count()
        resources = Resource.objects.all()[:5]
        
        latest_assessment = StressAssessment.objects.filter(user=user).order_by('-date').first()
        if latest_assessment and not Recommendation.objects.filter(
            stress_assessment=latest_assessment
        ).exists():
            logger.debug(f"Generating recommendations for user {user.email_id}, assessment {latest_assessment.id}")
            generate_recommendations(user, latest_assessment)
            recommendations = Recommendation.objects.filter(
                user=user, is_completed=False
            ).order_by('-created_at')
        
        context = {
            'user': user,
            'recommendations': recommendations,
            'alerts': alerts,
            'pending_alerts': pending_alerts,
            'resources': resources,
        }
        logger.debug(f"Rendering recommendation_dashboard for {user.email_id}: "
                    f"recommendations={recommendations.count()}, "
                    f"alerts={alerts.count()}, "
                    f"pending_alerts={pending_alerts}, "
                    f"resources={resources.count()}")
        return render(request, 'recommendation_dashboard.html', context)
    except UsersRegister.DoesNotExist:
        logger.error(f"User with email {request.session['email']} not found")
        request.session.flush()
        messages.error(request, "User not found. Please log in again.")
        return redirect('login')
   
def view_recommendations(request):
    if 'email' not in request.session:
        return redirect('login')
    
    try:
        user = UsersRegister.objects.get(email_id=request.session['email'])
        recommendations = Recommendation.objects.filter(user=user, is_completed=False).order_by('-created_at')
        alerts = Alert.objects.filter(user=user, is_acknowledged=False).order_by('-triggered_at')
        
        latest_assessment = StressAssessment.objects.filter(user=user).order_by('-date').first()
        if latest_assessment and not Recommendation.objects.filter(stress_assessment=latest_assessment).exists():
            generate_recommendations(user, latest_assessment)
        
        context = {
            'user': user,
            'recommendations': recommendations,
            'alerts': alerts,
        }
        return render(request, 'recommendation_view.html', context)
    except UsersRegister.DoesNotExist:
        logger.error(f"User with email {request.session['email']} not found")
        request.session.flush()
        return redirect('login')
def generate_recommendations(user, assessment):
    """Helper function to generate personalized recommendations and alerts"""
    stress_score = assessment.stress_score
    logger.debug(f"Generating recommendations for user {user.email_id}, stress_score: {stress_score}")
    
    if stress_score > 20:
        Recommendation.objects.create(
            user=user,
            stress_assessment=assessment,
            recommendation_text="Take a 15-minute break and try deep breathing exercises.",
            category='BREAK',
            priority=3
        )
        Recommendation.objects.create(
            user=user,
            stress_assessment=assessment,
            recommendation_text="Consider a short walk outside to reduce stress.",
            category='EXERCISE',
            priority=2
        )
        alert = Alert.objects.create(
            user=user,
            message="High stress level detected! Please take action.",
            threshold=20
        )
        logger.info(f"Alert created for user {user.email_id}: {alert.message}")
    elif stress_score > 10:
        Recommendation.objects.create(
            user=user,
            stress_assessment=assessment,
            recommendation_text="Try a 5-minute mindfulness meditation.",
            category='MINDFULNESS',
            priority=2
        )
        Recommendation.objects.create(
            user=user,
            stress_assessment=assessment,
            recommendation_text="Review your schedule and prioritize tasks.",
            category='SCHEDULE',
            priority=1
        )
    else:
        Recommendation.objects.create(
            user=user,
            stress_assessment=assessment,
            recommendation_text="Great job! Maintain your well-being with this guided relaxation audio.",
            category='RESOURCE',
            priority=1
        )


def mark_recommendation_complete(request, recommendation_id):
    if request.method == 'POST':
        recommendation = get_object_or_404(Recommendation, id=recommendation_id, user__email_id=request.session.get('email'))
        recommendation.is_completed = True
        recommendation.save()
        messages.success(request, 'Recommendation marked as completed.')
    return redirect('view_recommendations')

def acknowledge_alert(request, alert_id):
    if request.method == 'POST':
        alert = get_object_or_404(Alert, id=alert_id, user__email_id=request.session.get('email'))
        alert.is_acknowledged = True
        alert.save()
        messages.success(request, 'Alert acknowledged.')
    return redirect('view_recommendations')

def view_resources(request):
    resources = Resource.objects.all()
    return render(request, 'resources.html', {'resources': resources})

# admin manage rec
def admin_manage_recommendations(request):
    recommendations = Recommendation.objects.all().order_by('-created_at')
    return render(request, 'admin_manage_recommendations.html', {'recommendations': recommendations})

# admin manage res
def admin_manage_resources(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        url = request.POST.get('url', '')
        file = request.FILES.get('file')
        
        Resource.objects.create(
            title=title,
            description=description,
            category=category,
            url=url if url else None,
            file=file if file else None
        )
        messages.success(request, 'Resource added successfully.')
        return redirect('admin_manage_resources')
    
    resources = Resource.objects.all()
    return render(request, 'admin_manage_resources.html', {'resources': resources})

# views.py (add these new views)
from django.utils.timezone import now, timedelta
from django.db.models import Avg, Sum, Count
from django.shortcuts import render, redirect
from django.shortcuts import render, redirect
from django.db.models import Avg
from .models import UsersRegister, StressAssessment, ScreenTime, KeyboardActivity, Recommendation
from django.shortcuts import render, redirect
from django.db.models import Avg
from .models import UsersRegister, StressAssessment, ScreenTime, KeyboardActivity, Recommendation, Alert
def personal_dashboard(request):
    if 'email' not in request.session:
        logger.warning("No email in session, redirecting to login")
        return redirect('login')
    
    try:
        user = UsersRegister.objects.get(email_id=request.session['email'])
        
        # Metrics calculation
        stress_assessments = StressAssessment.objects.filter(user=user)
        avg_score = stress_assessments.aggregate(Avg('stress_score'))['stress_score__avg'] or 0
        recent_trend = "Stable"  # Replace with actual logic
        keyboard_activities = KeyboardActivity.objects.filter(user=user)
        keyboard_avg = keyboard_activities.aggregate(Avg('keystrokes_per_minute'))['keystrokes_per_minute__avg'] or 0
        screen_times = ScreenTime.objects.filter(user=user)
        screen_time_hours = sum(st.duration.total_seconds() for st in screen_times) / 3600 if screen_times else 0
        wearable_metrics = {"avg_heart_rate": 0, "total_steps": 0}  # Replace with actual data
        voice_stress_avg = 0  # Replace with actual data
        feedback_count = 0  # Replace with actual data
        
        # Fetch recommendations and alerts
        recommendations = Recommendation.objects.filter(user=user, is_completed=False).order_by('-created_at')
        alerts = Alert.objects.filter(user=user, is_acknowledged=False).order_by('-triggered_at')
        
        # Debug logging
        logger.debug(f"User: {user.email_id}")
        logger.debug(f"Recommendations: {list(recommendations)}")
        logger.debug(f"Alerts: {list(alerts)}")
        
        context = {
            'user': user,
            'avg_score': avg_score,
            'recent_trend': recent_trend,
            'keyboard_avg': keyboard_avg,
            'screen_time_hours': screen_time_hours,
            'wearable_metrics': wearable_metrics,
            'voice_stress_avg': voice_stress_avg,
            'feedback_count': feedback_count,
            'recommendations': recommendations,
            'alerts': alerts,
            'error_message': None,
        }
        
        return render(request, 'personal_dashboard.html', context)
    except UsersRegister.DoesNotExist:
        logger.error(f"User with email {request.session.get('email')} not found")
        request.session.flush()
        messages.error(request, 'User not found. Please log in again.')
        return redirect('login')
    except Exception as e:
        logger.error(f"Error in personal_dashboard: {str(e)}")
        context = {
            'error_message': 'An unexpected error occurred. Please try again later.'
        }
        return render(request, 'personal_dashboard.html', context)
    
from django.shortcuts import render, redirect
from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
import json

def management_dashboard(request):
    # Check if the user is authenticated as admin
    if 'email' not in request.session or request.session['email'] != 'admin2024@gmail.com':
        return redirect('admin_login')
    
    # Fetch all stress assessments
    assessments = StressAssessment.objects.all()

    # Calculate department-wise statistics
    departments = UsersRegister.objects.values('department').annotate(
        avg_stress=Avg('stressassessment__stress_score'),
        total_users=Count('id')
    ).order_by('department')

    # Calculate stress trend for the past 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_trends = (
        StressAssessment.objects
        .filter(date__gte=thirty_days_ago)
        .annotate(day=TruncDate('date'))  # Truncate to date
        .values('day')
        .annotate(avg_score=Avg('stress_score'))
        .order_by('day')
    )

    # Prepare trend data for Chart.js
    trend_dates = [trend['day'].strftime('%Y-%m-%d') for trend in daily_trends]
    trend_scores = [float(trend['avg_score'] or 0) for trend in daily_trends]

    # Prepare context for the template
    context = {
        'total_users': UsersRegister.objects.count(),
        'avg_stress': assessments.aggregate(Avg('stress_score'))['stress_score__avg'] or 0,
        'departments': departments,
        'trend_data': json.dumps({
            'dates': trend_dates,
            'scores': trend_scores
        })
    }
    return render(request, 'management_dashboard.html', context)
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.timezone import now
from datetime import datetime, timedelta
from .models import UsersRegister, StressAssessment
from django.db.models import Avg

def generate_report(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        try:
            # Parse dates with time zone awareness
            start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else (now() - timedelta(days=30)).date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else now().date()

            # Validate end_date is not in the future
            today = now().date()
            if end > today:
                logger.warning(f"Invalid end_date {end} selected, future dates not allowed")
                messages.error(request, 'End date cannot be in the future. Please select today or an earlier date.')
                return render(request, 'generate_report.html', {
                    'report_type': report_type,
                    'start_date': start_date,
                    'end_date': end_date,
                })

            # Fetch assessments based on user session
            if 'email' in request.session:
                try:
                    user = UsersRegister.objects.get(email_id=request.session['email'])
                    assessments = StressAssessment.objects.filter(user=user, date__range=[start, end + timedelta(days=1)])
                except UsersRegister.DoesNotExist:
                    logger.error(f"No user found for email: {request.session['email']}")
                    request.session.flush()
                    messages.error(request, 'User not found. Please log in again.')
                    return redirect('login')
            else:
                assessments = StressAssessment.objects.filter(date__range=[start, end + timedelta(days=1)])

            # Log successful report generation
            logger.info(f"Report generated: type={report_type}, start={start}, end={end}, assessments_count={assessments.count()}")

            context = {
                'report_type': report_type,
                'start_date': start.strftime('%Y-%m-%d'),
                'end_date': end.strftime('%Y-%m-%d'),
                'assessments': assessments,
                'avg_score': assessments.aggregate(Avg('stress_score'))['stress_score__avg'] or 0
            }
            return render(request, 'report_view.html', context)

        except ValueError as e:
            logger.error(f"Invalid date format: start_date={start_date}, end_date={end_date}, error={str(e)}")
            messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
            return render(request, 'generate_report.html', {
                'report_type': report_type,
                'start_date': start_date,
                'end_date': end_date,
            })

    return render(request, 'generate_report.html')
from django.http import JsonResponse
from django.utils.timezone import now, timedelta
from .models import UsersRegister, StressAssessment, ScreenTime, KeyboardActivity
import json

def visualization_data(request):
    if 'email' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    user = UsersRegister.objects.get(email_id=request.session['email'])
    metric = request.GET.get('metric', 'stress_score')
    
    # Initialize response data
    data = {
        'dates': [],
        'scores': [],
        'screen_times': [],
        'keystrokes': [],
    }
    
    if metric == 'stress_score':
        assessments = StressAssessment.objects.filter(user=user).order_by('date')  # Remove 7-day filter
        data['dates'] = [a.date.strftime('%Y-%m-%d') for a in assessments]
        data['scores'] = [float(a.stress_score) for a in assessments]  # Ensure float values
    elif metric == 'screen_time':
        screen_times = ScreenTime.objects.filter(user=user).order_by('timestamp')  # Remove 7-day filter
        data['dates'] = [st.timestamp.strftime('%Y-%m-%d') for st in screen_times]
        data['screen_times'] = [float(st.duration.total_seconds() / 3600) for st in screen_times]  # Convert to hours
    elif metric == 'keystrokes':
        keyboard_activities = KeyboardActivity.objects.filter(user=user).order_by('timestamp')  # Remove 7-day filter
        data['dates'] = [ka.timestamp.strftime('%Y-%m-%d') for ka in keyboard_activities]
        data['keystrokes'] = [float(ka.keystrokes_per_minute) for ka in keyboard_activities]
    
    # Fallback for empty data
    if not data['dates']:
        data['dates'] = [(now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
        data['scores'] = [0.0] * 7
        data['screen_times'] = [0.0] * 7
        data['keystrokes'] = [0.0] * 7
        data['message'] = "No data available for the selected metric."
    
    return JsonResponse(data)

def export_report(request, report_type):
    if 'email' not in request.session:
        return redirect('login')
        
    response = HttpResponse(content_type=f'text/{report_type}')
    response['Content-Disposition'] = f'attachment; filename="stress_report_{now().strftime("%Y%m%d")}.{report_type}"'
    
    user = UsersRegister.objects.get(email_id=request.session['email'])
    assessments = StressAssessment.objects.filter(user=user)
    
    if report_type == 'csv':
        writer = csv.writer(response)
        writer.writerow(['Date', 'Stress Score', 'Recommendations'])
        for a in assessments:
            writer.writerow([a.date, a.stress_score, a.recommendations])
            
    elif report_type == 'json':
        data = [{
            'date': str(a.date),
            'stress_score': a.stress_score,
            'recommendations': a.recommendations
        } for a in assessments]
        response.write(json.dumps(data))
        
    return response

# views.py (Add these new views at the end of your existing views.py)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import UsersRegister, Alert, Recommendation, StressAssessment

# Admin Manage Alerts and Recommendations
def admin_manage_alerts_recommendations(request):
    if 'email' not in request.session or request.session['email'] != 'admin2024@gmail.com':
        return redirect('admin_login')

    # Fetch all alerts and recommendations
    alerts = Alert.objects.all().order_by('-triggered_at')
    recommendations = Recommendation.objects.all().order_by('-created_at')
    users = UsersRegister.objects.all()  # For dropdown in forms

    context = {
        'alerts': alerts,
        'recommendations': recommendations,
        'users': users,
    }
    return render(request, 'admin_manage_alerts_recommendations.html', context)

# Create Alert
def admin_create_alert(request):
    if 'email' not in request.session or request.session['email'] != 'admin2024@gmail.com':
        return redirect('admin_login')

    if request.method == 'POST':
        user_id = request.POST.get('user')
        message = request.POST.get('message')
        threshold = request.POST.get('threshold')

        try:
            user = UsersRegister.objects.get(id=user_id)
            Alert.objects.create(
                user=user,
                message=message,
                threshold=int(threshold),
                is_acknowledged=False
            )
            messages.success(request, 'Alert created successfully.')
            return redirect('admin_manage_alerts_recommendations')
        except UsersRegister.DoesNotExist:
            messages.error(request, 'Selected user does not exist.')
        except ValueError:
            messages.error(request, 'Please provide a valid threshold value.')

    users = UsersRegister.objects.all()
    return render(request, 'admin_create_alert.html', {'users': users})

# Edit Alert
def admin_edit_alert(request, alert_id):
    if 'email' not in request.session or request.session['email'] != 'admin2024@gmail.com':
        return redirect('admin_login')

    alert = get_object_or_404(Alert, id=alert_id)
    if request.method == 'POST':
        message = request.POST.get('message')
        threshold = request.POST.get('threshold')
        is_acknowledged = request.POST.get('is_acknowledged') == 'on'

        try:
            alert.message = message
            alert.threshold = int(threshold)
            alert.is_acknowledged = is_acknowledged
            alert.save()
            messages.success(request, 'Alert updated successfully.')
            return redirect('admin_manage_alerts_recommendations')
        except ValueError:
            messages.error(request, 'Please provide a valid threshold value.')

    return render(request, 'admin_edit_alert.html', {'alert': alert})

# Delete Alert
def admin_delete_alert(request, alert_id):
    if 'email' not in request.session or request.session['email'] != 'admin2024@gmail.com':
        return redirect('admin_login')

    alert = get_object_or_404(Alert, id=alert_id)
    alert.delete()
    messages.success(request, 'Alert deleted successfully.')
    return redirect('admin_manage_alerts_recommendations')

# Create Recommendation
def admin_create_recommendation(request):
    if 'email' not in request.session or request.session['email'] != 'admin2024@gmail.com':
        return redirect('admin_login')

    if request.method == 'POST':
        user_id = request.POST.get('user')
        stress_assessment_id = request.POST.get('stress_assessment')
        recommendation_text = request.POST.get('recommendation_text')
        category = request.POST.get('category')
        priority = request.POST.get('priority')

        try:
            user = UsersRegister.objects.get(id=user_id)
            stress_assessment = None
            if stress_assessment_id:
                stress_assessment = StressAssessment.objects.get(id=stress_assessment_id, user=user)

            Recommendation.objects.create(
                user=user,
                stress_assessment=stress_assessment,
                recommendation_text=recommendation_text,
                category=category,
                priority=int(priority),
                is_completed=False
            )
            messages.success(request, 'Recommendation created successfully.')
            return redirect('admin_manage_alerts_recommendations')
        except UsersRegister.DoesNotExist:
            messages.error(request, 'Selected user does not exist.')
        except StressAssessment.DoesNotExist:
            messages.error(request, 'Selected stress assessment does not exist.')
        except ValueError:
            messages.error(request, 'Please provide a valid priority value.')

    users = UsersRegister.objects.all()
    stress_assessments = StressAssessment.objects.all()
    return render(request, 'admin_create_recommendation.html', {
        'users': users,
        'stress_assessments': stress_assessments,
        'categories': Recommendation._meta.get_field('category').choices
    })

# Edit Recommendation
def admin_edit_recommendation(request, recommendation_id):
    if 'email' not in request.session or request.session['email'] != 'admin2024@gmail.com':
        return redirect('admin_login')

    recommendation = get_object_or_404(Recommendation, id=recommendation_id)
    if request.method == 'POST':
        recommendation_text = request.POST.get('recommendation_text')
        category = request.POST.get('category')
        priority = request.POST.get('priority')
        is_completed = request.POST.get('is_completed') == 'on'

        try:
            recommendation.recommendation_text = recommendation_text
            recommendation.category = category
            recommendation.priority = int(priority)
            recommendation.is_completed = is_completed
            recommendation.save()
            messages.success(request, 'Recommendation updated successfully.')
            return redirect('admin_manage_alerts_recommendations')
        except ValueError:
            messages.error(request, 'Please provide a valid priority value.')

    return render(request, 'admin_edit_recommendation.html', {
        'recommendation': recommendation,
        'categories': Recommendation._meta.get_field('category').choices
    })

# Delete Recommendation
def admin_delete_recommendation(request, recommendation_id):
    if 'email' not in request.session or request.session['email'] != 'admin2024@gmail.com':
        return redirect('admin_login')

    recommendation = get_object_or_404(Recommendation, id=recommendation_id)
    recommendation.delete()
    messages.success(request, 'Recommendation deleted successfully.')
    return redirect('admin_manage_alerts_recommendations')


from .analytics import clean_data, normalize_data, extract_features, recognize_patterns, ml_processing, detect_anomalies
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
import json
from .models import UsersRegister, ProcessedData, ExtractedFeature, StressPattern, Anomaly, MLPrediction

# Process Raw Data View
def process_raw_data(request):
    if 'email' not in request.session:
        messages.error(request, 'Please log in to process data.')
        return redirect('login')
    
    try:
        user = UsersRegister.objects.get(email_id=request.session['email'])
        
        # Track if any data was processed
        data_processed = False
        
        for data_type in ['KEYBOARD', 'SCREEN_TIME', 'WEARABLE']:
            raw_data = None  # Initialize raw_data
            
            if data_type == 'KEYBOARD':
                recent_data = KeyboardActivity.objects.filter(user=user).last()
                if recent_data:
                    raw_data = {
                        'keystrokes_per_minute': recent_data.keystrokes_per_minute,
                        'typing_duration': recent_data.typing_duration.total_seconds()
                    }
            elif data_type == 'SCREEN_TIME':
                recent_data = ScreenTime.objects.filter(user=user).last()
                if recent_data:
                    raw_data = {
                        'duration': recent_data.duration.total_seconds(),
                        'application': recent_data.application
                    }
            elif data_type == 'WEARABLE':
                recent_data = WearableData.objects.filter(user=user).last()
                if recent_data:
                    raw_data = {
                        'heart_rate': recent_data.heart_rate,
                        'steps': recent_data.steps
                    }
            
            # Skip if no raw_data was assigned
            if raw_data is None:
                logger.info(f"No recent {data_type} data found for user {user.email_id}")
                continue
            
            # Clean and normalize data
            cleaned_data, is_valid = clean_data(raw_data, data_type)
            if not is_valid:
                logger.warning(f"Invalid {data_type} data for {user.email_id}")
                continue
            
            normalized_data = normalize_data(cleaned_data, data_type)
            if not normalized_data:
                logger.warning(f"Normalization failed for {data_type} data")
                continue
            
            # Save processed data
            processed_data = ProcessedData.objects.create(
                user=user,
                data_type=data_type,
                processed_at=now(),
                is_valid=is_valid
            )
            processed_data.set_raw_data(raw_data)
            processed_data.set_cleaned_data(normalized_data)
            processed_data.save()
            
            # Extract features
            features = extract_features(normalized_data, data_type)
            for feature_type, feature_value in features:
                feature = ExtractedFeature.objects.create(
                    user=user,
                    processed_data=processed_data,
                    feature_type=feature_type,
                    feature_value=feature_value
                )
                feature.set_context({})
                feature.save()
            
            # Recognize patterns
            stress_pattern = recognize_patterns(features, user)
            
            # ML processing
            prediction = ml_processing(stress_pattern, user)
            
            # Detect anomalies
            detect_anomalies(features, user, processed_data)
            
            data_processed = True
        
        if data_processed:
            messages.success(request, 'Data processed successfully.')
        else:
            messages.warning(request, 'No data available to process.')
        
        # For testing purposes, create a sample anomaly if none exist
        if not Anomaly.objects.filter(user=user).exists():
            try:
                Anomaly.objects.create(
                    user=user,
                    processed_data=ProcessedData.objects.filter(user=user).first(),
                    anomaly_type="test_anomaly",
                    severity="MEDIUM",
                    description="This is a test anomaly to verify the system is working correctly."
                )
                logger.info(f"Created test anomaly for user {user.email_id}")
            except Exception as e:
                logger.error(f"Error creating test anomaly: {str(e)}")
        
        return redirect('analytics_dashboard')
    except UsersRegister.DoesNotExist:
        logger.error(f"User with email {request.session.get('email')} not found")
        request.session.flush()
        messages.error(request, 'User not found. Please log in again.')
        return redirect('login')

# Analytics Dashboard View
def analytics_dashboard(request):
    if 'email' not in request.session:
        logger.warning("Analytics dashboard accessed without session email")
        return redirect('login')
    
    try:
        logger.info(f"Loading analytics dashboard for user: {request.session['email']}")
        user = UsersRegister.objects.get(email_id=request.session['email'])
        logger.info(f"User found: {user.email_id}")
        
        # Test database connectivity
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('app_processeddata', 'app_extractedfeature', 'app_stresspattern', 'app_anomaly', 'app_mlprediction')")
                tables = [row[0] for row in cursor.fetchall()]
                logger.info(f"Available tables: {tables}")
        except Exception as e:
            logger.error(f"Database connectivity test failed: {str(e)}")
        
        # Initialize empty data structures
        processed_data = []
        features = []
        patterns = []
        anomalies = []
        predictions = []
        total_features = 0
        feature_types = {}
        avg_keyboard = 0
        avg_screen = 0
        avg_wearable = 0
        total_anomalies = 0
        high_severity = 0
        medium_severity = 0
        low_severity = 0
        anomaly_types = {}
        
        # Fetch data with error handling
        try:
            logger.info("Fetching processed data...")
            processed_data = list(ProcessedData.objects.filter(user=user).order_by('-processed_at')[:10])
            logger.info(f"Found {len(processed_data)} processed data records")
        except Exception as e:
            logger.error(f"Error fetching processed data for user {user.email_id}: {str(e)}")
            logger.error(f"Processed data error type: {type(e).__name__}")
            processed_data = []
        
        try:
            logger.info("Fetching extracted features...")
            features = list(ExtractedFeature.objects.filter(user=user).order_by('-extracted_at')[:20])
            logger.info(f"Found {len(features)} features for user {user.email_id}")
            
            # Calculate feature statistics
            try:
                total_features = ExtractedFeature.objects.filter(user=user).count()
                logger.info(f"Total features count: {total_features}")
            except Exception as e:
                logger.error(f"Error counting total features: {str(e)}")
                total_features = len(features)
            
            # Feature type distribution
            try:
                feature_types = {}
                all_features = ExtractedFeature.objects.filter(user=user)
                for feature in all_features:
                    base_type = feature.feature_type.split('_')[0] if '_' in feature.feature_type else feature.feature_type
                    feature_types[base_type] = feature_types.get(base_type, 0) + 1
                logger.info(f"Feature types: {feature_types}")
            except Exception as e:
                logger.error(f"Error calculating feature types: {str(e)}")
                feature_types = {}
            
            # Average feature values by category
            try:
                keyboard_features = ExtractedFeature.objects.filter(user=user, feature_type__icontains='keystroke')
                screen_features = ExtractedFeature.objects.filter(user=user, feature_type__icontains='screen')
                wearable_features = ExtractedFeature.objects.filter(user=user, feature_type__icontains='heart')
                
                avg_keyboard = keyboard_features.aggregate(Avg('feature_value'))['feature_value__avg'] or 0
                avg_screen = screen_features.aggregate(Avg('feature_value'))['feature_value__avg'] or 0
                avg_wearable = wearable_features.aggregate(Avg('feature_value'))['feature_value__avg'] or 0
                logger.info(f"Averages - Keyboard: {avg_keyboard}, Screen: {avg_screen}, Wearable: {avg_wearable}")
            except Exception as e:
                logger.error(f"Error calculating averages: {str(e)}")
                avg_keyboard = 0
                avg_screen = 0
                avg_wearable = 0
            
        except Exception as e:
            logger.error(f"Error fetching features for user {user.email_id}: {str(e)}")
            features = []
            total_features = 0
            feature_types = {}
            avg_keyboard = 0
            avg_screen = 0
            avg_wearable = 0
        
        try:
            logger.info("Fetching stress patterns...")
            patterns = list(StressPattern.objects.filter(user=user).order_by('-recognized_at')[:5])
            logger.info(f"Found {len(patterns)} patterns")
        except Exception as e:
            logger.error(f"Error fetching patterns for user {user.email_id}: {str(e)}")
            patterns = []
        
        try:
            logger.info("Fetching anomalies...")
            anomalies = list(Anomaly.objects.filter(user=user, is_reviewed=False).order_by('-detected_at')[:10])
            logger.info(f"Found {len(anomalies)} anomalies for user {user.email_id}")
            
            # Calculate anomaly statistics
            try:
                total_anomalies = Anomaly.objects.filter(user=user).count()
                high_severity = Anomaly.objects.filter(user=user, severity='HIGH').count()
                medium_severity = Anomaly.objects.filter(user=user, severity='MEDIUM').count()
                low_severity = Anomaly.objects.filter(user=user, severity='LOW').count()
                logger.info(f"Anomaly stats - Total: {total_anomalies}, High: {high_severity}, Medium: {medium_severity}, Low: {low_severity}")
            except Exception as e:
                logger.error(f"Error calculating anomaly statistics: {str(e)}")
                total_anomalies = len(anomalies)
                high_severity = 0
                medium_severity = 0
                low_severity = 0
            
            # Get anomaly types distribution
            try:
                anomaly_types = {}
                all_anomalies = Anomaly.objects.filter(user=user)
                for anomaly in all_anomalies:
                    base_type = anomaly.anomaly_type.split('_')[0] if '_' in anomaly.anomaly_type else anomaly.anomaly_type
                    anomaly_types[base_type] = anomaly_types.get(base_type, 0) + 1
                logger.info(f"Anomaly types: {anomaly_types}")
            except Exception as e:
                logger.error(f"Error calculating anomaly types: {str(e)}")
                anomaly_types = {}
            
        except Exception as e:
            logger.error(f"Error fetching anomalies for user {user.email_id}: {str(e)}")
            anomalies = []
            total_anomalies = 0
            high_severity = 0
            medium_severity = 0
            low_severity = 0
            anomaly_types = {}
        
        try:
            logger.info("Fetching ML predictions...")
            predictions = list(MLPrediction.objects.filter(user=user).order_by('-predicted_at')[:5])
            logger.info(f"Found {len(predictions)} predictions")
        except Exception as e:
            logger.error(f"Error fetching predictions for user {user.email_id}: {str(e)}")
            predictions = []
        
        # Create sample data if none exists for testing
        if not processed_data and not features and not patterns and not anomalies:
            logger.info("No data found, creating sample data for testing")
            try:
                # Create sample processed data
                sample_processed = ProcessedData.objects.create(
                    user=user,
                    data_type='KEYBOARD',
                    processed_at=now(),
                    is_valid=True
                )
                sample_processed.set_raw_data({'keystrokes_per_minute': 85, 'typing_duration': 300})
                sample_processed.set_cleaned_data({'keystrokes_per_minute': 85, 'typing_duration': 300})
                sample_processed.save()
                
                # Create sample features
                sample_features = [
                    ('keystroke_speed', 85.0),
                    ('typing_duration', 300.0),
                    ('typing_efficiency', 0.283),
                    ('typing_stress_indicator', 0.0),
                    ('typing_consistency', 0.9375)
                ]
                
                for feature_type, feature_value in sample_features:
                    ExtractedFeature.objects.create(
                        user=user,
                        processed_data=sample_processed,
                        feature_type=feature_type,
                        feature_value=feature_value
                    )
                
                # Create sample anomaly
                Anomaly.objects.create(
                    user=user,
                    processed_data=sample_processed,
                    anomaly_type="test_anomaly",
                    severity="MEDIUM",
                    description="Sample anomaly for testing purposes."
                )
                
                # Refresh the data
                processed_data = ProcessedData.objects.filter(user=user).order_by('-processed_at')[:10]
                features = ExtractedFeature.objects.filter(user=user).order_by('-extracted_at')[:20]
                anomalies = Anomaly.objects.filter(user=user, is_reviewed=False).order_by('-detected_at')[:10]
                
                logger.info("Sample data created successfully")
                
            except Exception as e:
                logger.error(f"Error creating sample data: {str(e)}")
        
        # Ensure all context values are valid
        context = {
            'user': user,
            'processed_data': processed_data or [],
            'features': features or [],
            'patterns': patterns or [],
            'anomalies': anomalies or [],
            'predictions': predictions or [],
            'anomaly_stats': {
                'total': total_anomalies or 0,
                'high': high_severity or 0,
                'medium': medium_severity or 0,
                'low': low_severity or 0,
                'types': anomaly_types or {}
            },
            'feature_stats': {
                'total': total_features or 0,
                'types': feature_types or {},
                'avg_keyboard': avg_keyboard or 0,
                'avg_screen': avg_screen or 0,
                'avg_wearable': avg_wearable or 0
            }
        }
        
        logger.info(f"Rendering analytics dashboard with {len(features)} features, {len(anomalies)} anomalies")
        
        # Debug: Print context keys to ensure all data is available
        logger.info(f"Context keys: {list(context.keys())}")
        logger.info(f"Features count: {len(context['features'])}")
        logger.info(f"Anomalies count: {len(context['anomalies'])}")
        
        return render(request, 'analytics_dashboard.html', context)
    except UsersRegister.DoesNotExist:
        request.session.flush()
        return redirect('login')
    except Exception as e:
        logger.error(f"Unexpected error in analytics_dashboard for user {request.session.get('email')}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        messages.error(request, f'An error occurred while loading the analytics dashboard: {str(e)}')
        return redirect('usershome')

# Admin Analytics Management View
def admin_analytics_management(request):
    if 'email' not in request.session or request.session['email'] != 'admin2024@gmail.com':
        return redirect('admin_login')
    
    users = UsersRegister.objects.all()
    processed_data = ProcessedData.objects.all().order_by('-processed_at')[:20]
    anomalies = Anomaly.objects.filter(is_reviewed=False).order_by('-detected_at')[:20]
    
    context = {
        'users': users,
        'processed_data': processed_data,
        'anomalies': anomalies,
        'total_processed': ProcessedData.objects.count(),
        'total_anomalies': Anomaly.objects.count(),
        'total_predictions': MLPrediction.objects.count(),
    }
    return render(request, 'admin_analytics_management.html', context)

# Review Anomaly View
def review_anomaly(request, anomaly_id):
    if 'email' not in request.session or request.session['email'] != 'admin2024@gmail.com':
        return redirect('admin_login')
    
    anomaly = get_object_or_404(Anomaly, id=anomaly_id)
    if request.method == 'POST':
        anomaly.is_reviewed = True
        anomaly.save()
        messages.success(request, 'Anomaly marked as reviewed.')
        return redirect('admin_analytics_management')
    
    return render(request, 'review_anomaly.html', {'anomaly': anomaly})

# Test Analytics View
def test_analytics(request):
    """Simple test view to check if analytics components are working"""
    if 'email' not in request.session:
        return JsonResponse({'error': 'Not logged in'}, status=401)
    
    try:
        user = UsersRegister.objects.get(email_id=request.session['email'])
        
        # Check if models exist
        models_status = {
            'ProcessedData': ProcessedData.objects.filter(user=user).count(),
            'ExtractedFeature': ExtractedFeature.objects.filter(user=user).count(),
            'StressPattern': StressPattern.objects.filter(user=user).count(),
            'Anomaly': Anomaly.objects.filter(user=user).count(),
            'MLPrediction': MLPrediction.objects.filter(user=user).count(),
        }
        
        return JsonResponse({
            'status': 'success',
            'user': user.email_id,
            'models_status': models_status,
            'session_email': request.session.get('email')
        })
        
    except Exception as e:
        logger.error(f"Test analytics error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)