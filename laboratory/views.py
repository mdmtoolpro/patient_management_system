from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import LabTestRequest, LabTestType, TestResult
from .forms import LabTestRequestForm, TestResultForm, LabTestAssignmentForm
from patients.models import Visit
from billing.models import Payment
from core.models import Notification
from users.models import User
from pharmacy.models import Prescription, PrescriptionItem, Medicine
from pharmacy.forms import PrescriptionForm, PrescriptionItemForm
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
    return render(request, 'laboratory/process_lab_payment.html', context)

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
def request_lab_test(request, visit_id):
    visit = get_object_or_404(Visit, visit_id=visit_id)
    
    if request.user.role != 'DOCTOR':
        messages.error(request, "Only doctors can request lab tests.")
        return redirect('visit_detail', visit_id=visit_id)
    
    if request.method == 'POST':
        form = LabTestRequestForm(request.POST)
        if form.is_valid():
            lab_request = form.save(commit=False)
            lab_request.visit = visit
            lab_request.requested_by = request.user
            lab_request.request_id = f"LAB{timezone.now().strftime('%y%m%d')}{random.randint(1000, 9999)}"
            lab_request.status = LabTestRequest.Status.PAYMENT_PENDING
            lab_request.save()
            
            # Update visit status
            visit.status = Visit.Status.LAB_REQUESTED
            visit.lab_request_time = timezone.now()
            visit.save()
            
            messages.success(request, f'Lab test {lab_request.test_type.name} requested. Patient sent to cashier for payment.')
            return redirect('visit_detail', visit_id=visit_id)
    else:
        form = LabTestRequestForm()
    
    context = {
        'form': form,
        'visit': visit,
    }
    return render(request, 'laboratory/lab_test_form.html', context)

@login_required
def lab_requests_list(request):
    if request.user.role == 'LAB_TECH':
        lab_requests = LabTestRequest.objects.filter(assigned_to=request.user)
    elif request.user.role == 'DOCTOR':
        lab_requests = LabTestRequest.objects.filter(requested_by=request.user)
    else:
        lab_requests = LabTestRequest.objects.all()
    
    lab_requests = lab_requests.order_by('-requested_at')
    payment_pending = LabTestRequest.objects.filter(status = 'PAYMENT_PENDING').count()
    payment_inprogress = LabTestRequest.objects.filter(status = 'IN_PROGRESS').count()
    payment_complete = LabTestRequest.objects.filter(status = 'COMPLETED').count()
    return render(request, 'laboratory/lab_requests_list.html', {'lab_requests': lab_requests,'payment_pending': payment_pending, 'payment_complete': payment_complete })

@login_required
def process_lab_test(request, request_id):
    lab_request = get_object_or_404(LabTestRequest, request_id=request_id)
    
    if request.user.role != 'LAB_TECH':
        messages.error(request, "Only lab technicians can process lab tests.")
        return redirect('lab_requests_list')
    
    if request.method == 'POST':
        form = TestResultForm(request.POST)
        if form.is_valid():
            test_result = form.save(commit=False)
            test_result.lab_request = lab_request
            test_result.performed_by = request.user
            test_result.save()
            
            # Update lab request status
            lab_request.status = LabTestRequest.Status.COMPLETED
            lab_request.completed_at = timezone.now()
            lab_request.save()
            
            # Update visit status
            lab_request.visit.status = Visit.Status.LAB_COMPLETED
            lab_request.visit.save()
            
            # Notify the doctor
            Notification.objects.create(
                recipient=lab_request.requested_by,
                notification_type=Notification.NotificationType.LAB_RESULT,
                title='Lab Test Results Ready',
                message=f'Results for {lab_request.test_type.name} are ready for patient {lab_request.visit.patient}',
                related_object_id=lab_request.request_id
            )
            
            messages.success(request, 'Lab test results submitted successfully. Doctor has been notified.')
            return redirect('lab_requests_list')
    else:
        form = TestResultForm()
    
    context = {
        'form': form,
        'lab_request': lab_request,
    }
    return render(request, 'laboratory/process_lab_test.html', context)

@login_required
def lab_result_detail(request, request_id):
    """View lab test results and allow prescription creation"""
    lab_request = get_object_or_404(LabTestRequest, request_id=request_id)
    
    # Check if user has permission to view this result
    if request.user.role not in ['DOCTOR', 'ADMIN'] and request.user != lab_request.requested_by:
        messages.error(request, "You don't have permission to view this lab result.")
        return redirect('dashboard')
    
    # Check if test has results
    try:
        test_result = lab_request.result
    except TestResult.DoesNotExist:
        messages.warning(request, "Lab test results are not yet available.")
        return redirect('visit_detail', visit_id=lab_request.visit.visit_id)
    
    # Check if prescription already exists
    try:
        prescription = Prescription.objects.get(visit=lab_request.visit)
    except Prescription.DoesNotExist:
        prescription = None
    
    # Prescription form
    if request.method == 'POST' and 'create_prescription' in request.POST:
        prescription_form = PrescriptionForm(request.POST)
        if prescription_form.is_valid():
            prescription = prescription_form.save(commit=False)
            prescription.visit = lab_request.visit
            prescription.prescribed_by = request.user
            prescription.prescription_id = f"PRES{timezone.now().strftime('%y%m%d')}{random.randint(1000, 9999)}"
            prescription.save()
            
            # Update visit status
            lab_request.visit.status = Visit.Status.PRESCRIPTION_READY
            lab_request.visit.prescription_time = timezone.now()
            lab_request.visit.save()
            
            # Notify pharmacists
            pharmacists = User.objects.filter(role=User.Role.PHARMACIST, is_active=True)
            for pharmacist in pharmacists:
                Notification.objects.create(
                    recipient=pharmacist,
                    notification_type=Notification.NotificationType.PRESCRIPTION,
                    title='New Prescription',
                    message=f'New prescription for {lab_request.visit.patient}',
                    related_object_id=prescription.prescription_id
                )
            
            messages.success(request, 'Prescription created successfully and sent to pharmacy.')
            return redirect('lab_result_detail', request_id=request_id)
    else:
        prescription_form = PrescriptionForm()
    
    context = {
        'lab_request': lab_request,
        'test_result': test_result,
        'prescription': prescription,
        'prescription_form': prescription_form,
    }
    return render(request, 'laboratory/lab_result_detail.html', context)