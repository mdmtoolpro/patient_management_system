from django.db.models import Count
from core.models import Notification

def clinic_info(request):
    """Provide clinic information to all templates"""
    unread_count = 0
    pending_lab_payments = 0
    pending_prescriptions = 0
    
    # Calculate statistics if user is authenticated
    if request.user.is_authenticated:
        try:
            # Unread notifications count
            unread_count = Notification.objects.filter(
                recipient=request.user, 
                is_read=False
            ).count()
            
            # Role-based counts for sidebar badges
            if hasattr(request.user, 'role'):
                from laboratory.models import LabTestRequest
                from pharmacy.models import Prescription
                
                if request.user.role in ['CASHIER', 'RECEPTIONIST', 'ADMIN']:
                    pending_lab_payments = LabTestRequest.objects.filter(
                        status='PAYMENT_PENDING'
                    ).count()
                
                if request.user.role in ['PHARMACIST', 'ADMIN']:
                    pending_prescriptions = Prescription.objects.filter(
                        status='PENDING'
                    ).count()
                    
        except Exception as e:
            # If models aren't ready yet (during initial setup)
            print(f"Context processor error: {e}")
            unread_count = 0
            pending_lab_payments = 0
            pending_prescriptions = 0
    
    return {
        'clinic_name': "Dr. Gudeta Healthcare Clinic",
        'clinic_phone': "+251 XXX XXX XXX", 
        'clinic_email': "info@gudetaclinic.com",
        'clinic_address': "Addis Ababa, Ethiopia",
        'registration_fee': 50.00,
        'unread_notifications_count': unread_count,
        'pending_lab_payments': pending_lab_payments,
        'pending_prescriptions': pending_prescriptions,
    }