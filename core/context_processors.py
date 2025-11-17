from .models import Notification
from laboratory.models import LabTestRequest
from pharmacy.models import Prescription

def clinic_info(request):
    """Provide clinic information to all templates"""
    unread_count = 0
    pending_lab_payments = 0
    pending_medicine_payments_count = 0
    pending_prescriptions = 0
    
    # Calculate statistics if user is authenticated
    if request.user.is_authenticated:
        try:
            unread_count = Notification.objects.filter(
                recipient=request.user, 
                is_read=False
            ).count()
            
            # Role-based counts for sidebar badges
            if request.user.role in ['CASHIER', 'RECEPTIONIST', 'ADMIN']:
                pending_lab_payments = LabTestRequest.objects.filter(
                    status=LabTestRequest.Status.PAYMENT_PENDING
                ).count()
                
                # Count pending medicine payments
                pending_medicine_payments_count = Prescription.objects.filter(
                    status=Prescription.Status.DISPENSED
                ).exclude(
                    visit__payment__payment_type='MEDICINE',
                    visit__payment__status='COMPLETED'
                ).count()
            
            if request.user.role in ['PHARMACIST', 'ADMIN']:
                pending_prescriptions = Prescription.objects.filter(
                    status=Prescription.Status.PENDING
                ).count()
                
        except:
            # If models aren't ready yet (during initial setup)
            unread_count = 0
            pending_lab_payments = 0
            pending_medicine_payments_count = 0
            pending_prescriptions = 0
    
    return {
        'clinic_name': "Dr. Gudeta Healthcare Clinic",
        'clinic_phone': "+251 XXX XXX XXX", 
        'clinic_email': "info@gudetaclinic.com",
        'clinic_address': "Addis Ababa, Ethiopia",
        'registration_fee': 50.00,
        'unread_notifications_count': unread_count,
        'pending_lab_payments': pending_lab_payments,
        'pending_medicine_payments_count': pending_medicine_payments_count,
        'pending_prescriptions': pending_prescriptions,
    }