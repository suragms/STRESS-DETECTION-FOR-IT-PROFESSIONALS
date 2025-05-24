from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now, timedelta
from .models import UsersRegister, StressAssessment, Feedback, KeyboardActivity, ScreenTime, ApplicationUsage, VoicePattern, WearableData, Recommendation, Alert, Resource
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
            return render(request, 'usershome.html', {
                'user': user,
                'alerts': json.dumps(alerts_formatted)  # Pass JSON string to template
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
            messages.success(request, 'Login successful.')
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

def settings_view(request):
    if 'email' in request.session:
        mail = request.session['email']
        try:
            user = UsersRegister.objects.get(email_id=mail)
            return render(request, 'settings.html', {'user': user})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {mail} not found in userprofile")
            request.session.flush()
    return render(request, 'settings.html',{'user': user})

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
        
        return redirect('analytics_dashboard')
    except UsersRegister.DoesNotExist:
        logger.error(f"User with email {request.session.get('email')} not found")
        request.session.flush()
        messages.error(request, 'User not found. Please log in again.')
        return redirect('login')

# Analytics Dashboard View
def analytics_dashboard(request):
    if 'email' not in request.session:
        return redirect('login')
    
    try:
        user = UsersRegister.objects.get(email_id=request.session['email'])
        processed_data = ProcessedData.objects.filter(user=user).order_by('-processed_at')[:10]
        features = ExtractedFeature.objects.filter(user=user).order_by('-extracted_at')[:10]
        patterns = StressPattern.objects.filter(user=user).order_by('-recognized_at')[:5]
        anomalies = Anomaly.objects.filter(user=user, is_reviewed=False).order_by('-detected_at')[:5]
        predictions = MLPrediction.objects.filter(user=user).order_by('-predicted_at')[:5]
        
        context = {
            'user': user,
            'processed_data': processed_data,
            'features': features,
            'patterns': patterns,
            'anomalies': anomalies,
            'predictions': predictions,
        }
        return render(request, 'analytics_dashboard.html', context)
    except UsersRegister.DoesNotExist:
        request.session.flush()
        return redirect('login')

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