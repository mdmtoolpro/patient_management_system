from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count
from django.db import transaction
from .models import Payment, Invoice
from .forms import PaymentForm, LabTestPaymentForm, MedicinePaymentForm, PaymentSearchForm
from laboratory.models import LabTestRequest
from pharmacy.models import Prescription
from core.models import Notification
from users.models import User
import random

@login_required
def process_lab_payment(request, request_id):
    """Cashier processes payment for lab test"""
    lab_request = get_object_or_404(LabTestRequest, request_id=request_id)
    
    if request.user.role not in ['CASHIER', 'RECEPTIONIST', 'ADMIN']:
        messages.error(request, "You don't have permission to process payments.")
        return redirect('lab_requests_list')
    
    if lab_request.status != LabTestRequest.Status.PAYMENT_PENDING:
        messages.warning(request, f"This lab request is already {lab_request.get_status_display().lower()}.")
        return redirect('lab_requests_list')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'CASH')
        
        try:
            with transaction.atomic():
                # Create payment record
                payment = Payment(
                    payment_id=f"PAY{timezone.now().strftime('%y%m%d')}{random.randint(1000, 9999)}",
                    patient=lab_request.visit.patient,
                    visit=lab_request.visit,
                    payment_type=Payment.PaymentType.LAB_TEST,
                    payment_method=payment_method,
                    amount=lab_request.test_type.price,
                    lab_request=lab_request,
                    processed_by=request.user,
                    status=Payment.Status.COMPLETED,
                    completed_at=timezone.now(),
                    receipt_number=f"RCP{timezone.now().strftime('%y%m%d')}{random.randint(1000, 9999)}"
                )
                payment.save()
                
                # Update lab request status
                lab_request.status = LabTestRequest.Status.PAYMENT_COMPLETED
                lab_request.payment_completed_at = timezone.now()
                lab_request.save()
                
                messages.success(request, f'Payment of {lab_request.test_type.price} ETB processed successfully. Lab test is ready for assignment.')
                return redirect('assign_lab_request', request_id=request_id)
                
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
    
    context = {
        'lab_request': lab_request,
    }
    return render(request, 'billing/process_lab_payment.html', context)

@login_required
def assign_lab_request(request, request_id):
    """Assign lab request to a technician"""
    lab_request = get_object_or_404(LabTestRequest, request_id=request_id)
    
    if request.user.role not in ['CASHIER', 'RECEPTIONIST', 'ADMIN', 'LAB_TECH']:
        messages.error(request, "You don't have permission to assign lab requests.")
        return redirect('lab_requests_list')
    
    if lab_request.status != LabTestRequest.Status.PAYMENT_COMPLETED:
        messages.warning(request, "This lab request is not ready for assignment.")
        return redirect('lab_requests_list')
    
    # Get available lab technicians
    lab_techs = User.objects.filter(role=User.Role.LAB_TECH, is_active=True)
    
    if request.method == 'POST':
        technician_id = request.POST.get('technician')
        
        if technician_id:
            technician = get_object_or_404(User, id=technician_id, role=User.Role.LAB_TECH)
            
            # Assign to technician
            lab_request.assigned_to = technician
            lab_request.status = LabTestRequest.Status.IN_PROGRESS
            lab_request.started_at = timezone.now()
            lab_request.save()
            
            # Notify the assigned technician
            Notification.objects.create(
                recipient=technician,
                notification_type=Notification.NotificationType.LAB_REQUEST,
                title='New Lab Test Assigned',
                message=f'New {lab_request.test_type.name} test assigned for patient {lab_request.visit.patient}',
                related_object_id=lab_request.request_id
            )
            
            messages.success(request, f'Lab test assigned to {technician.get_full_name()}.')
            return redirect('lab_requests_list')
        else:
            messages.error(request, 'Please select a lab technician.')
    
    context = {
        'lab_request': lab_request,
        'lab_techs': lab_techs,
    }
    return render(request, 'billing/assign_request.html', context)

@login_required
def process_medicine_payment(request, prescription_id):
    prescription = get_object_or_404(Prescription, prescription_id=prescription_id)
    
    if request.user.role not in ['CASHIER', 'RECEPTIONIST', 'ADMIN']:
        messages.error(request, "You don't have permission to process payments.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = MedicinePaymentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create payment
                    payment = Payment(
                        payment_id=f"PAY{timezone.now().strftime('%y%m%d')}{random.randint(1000, 9999)}",
                        patient=prescription.visit.patient,
                        visit=prescription.visit,
                        payment_type=Payment.PaymentType.MEDICINE,
                        payment_method=form.cleaned_data['payment_method'],
                        amount=prescription.total_cost,
                        prescription=prescription,
                        processed_by=request.user,
                        notes=form.cleaned_data['notes'],
                        status=Payment.Status.COMPLETED,
                        completed_at=timezone.now(),
                        receipt_number=f"RCP{timezone.now().strftime('%y%m%d')}{random.randint(1000, 9999)}"
                    )
                    payment.save()
                    
                    # Update prescription status
                    prescription.status = Prescription.Status.DISPENSED
                    prescription.dispensed_at = timezone.now()
                    prescription.save()
                    
                    # Update visit status
                    prescription.visit.status = Visit.Status.MEDICINE_DISPENSED
                    prescription.visit.save()
                    
                    messages.success(request, f'Payment of {prescription.total_cost} ETB processed successfully. Medicines dispensed.')
                    return redirect('payment_detail', payment_id=payment.payment_id)
                    
            except Exception as e:
                messages.error(request, f'Error processing payment: {str(e)}')
    else:
        form = MedicinePaymentForm()
    
    context = {
        'form': form,
        'prescription': prescription,
    }
    return render(request, 'billing/process_medicine_payment.html', context)

@login_required
def payment_list(request):
    form = PaymentSearchForm(request.GET or None)
    payments = Payment.objects.all().order_by('-created_at')
    if form.is_valid():
        if form.cleaned_data['patient_id']:
            payments = payments.filter(patient__patient_id__icontains=form.cleaned_data['patient_id'])
        if form.cleaned_data['payment_id']:
            payments = payments.filter(payment_id__icontains=form.cleaned_data['payment_id'])
        if form.cleaned_data['date_from']:
            payments = payments.filter(created_at__date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data['date_to']:
            payments = payments.filter(created_at__date__lte=form.cleaned_data['date_to'])

    total_pending = 0
    pay_pending = Payment.objects.filter(status='PENDING').values_list('amount', flat=True)
    for total_pend in pay_pending:
        total_pending = total_pending + total_pend
    total_paid = 0

    pay_complete = Payment.objects.filter(status='COMPLETED').values_list('amount', flat=True)
    for total_complete in pay_complete:
        total_paid = total_paid + total_complete

    context = {
        'payments': payments,
        'form': form,
        'total_paid': total_paid,
        'total_pending': total_pending,
    }
    return render(request, 'billing/payment_list.html', context)

@login_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, payment_id=payment_id)
    return render(request, 'billing/payment_detail.html', {'payment': payment})