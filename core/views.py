from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification
from patients.models import Visit,Patient
from laboratory.models import LabTestRequest
from pharmacy.models import Prescription


from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages


def custom_login(request):
    """Custom login view that uses your existing login template"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                
                # Redirect based on user role or to dashboard
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'account/login.html', {'form': form})

def custom_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return render(request, 'account/login.html')

def custom_signup(request):
    messages.info(request, 'Staff accounts are created by administrators.')
    return redirect('custom_login')


@login_required
def dashboard(request):
    """Main dashboard view"""
    from laboratory.models import LabTestRequest
    from pharmacy.models import Prescription
    from patients.models import Visit,Patient
    from core.models import Notification
    from datetime import date

    
    # Calculate unread notifications count
    unread_count = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()

    # get current date
    current_date = date.today()

    
    context = {
        'total_active_patients': Patient.objects.filter().count(),
        'pending_lab_requests': LabTestRequest.objects.filter(
            assigned_to=request.user, 
            status=LabTestRequest.Status.PAYMENT_COMPLETED
        ).count() if request.user.role == 'LAB_TECH' else 0,
        
        'pending_prescriptions': Prescription.objects.filter(
            status=Prescription.Status.PENDING
        ).count() if request.user.role == 'PHARMACIST' else 0,
        
        'active_visits': Visit.objects.exclude(
            status__in=[Visit.Status.COMPLETED, Visit.Status.COMPLETED]
        ).count() if request.user.role == 'RECEPTIONIST' else 0,
        
        'unread_notifications_count': unread_count,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def notifications(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'core/notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})