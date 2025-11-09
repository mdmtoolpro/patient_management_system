from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from .models import Patient, Visit, MedicalExamination
from .forms import PatientRegistrationForm, VisitForm, MedicalExaminationForm
from billing.models import Payment
from billing.forms import RegistrationPaymentForm
from users.models import User
import random
import string

def generate_patient_id():
    return f"PAT{timezone.now().strftime('%y%m%d')}{random.randint(1000, 9999)}"

def generate_visit_id():
    return f"VIS{timezone.now().strftime('%y%m%d')}{random.randint(1000, 9999)}"

@login_required
def register_patient(request):
    if request.user.role not in ['RECEPTIONIST', 'ADMIN']:
        messages.error(request, "You don't have permission to register patients.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        patient_form = PatientRegistrationForm(request.POST)
        payment_form = RegistrationPaymentForm(request.POST)
        
        if patient_form.is_valid() and payment_form.is_valid():
            try:
                with transaction.atomic():
                    # Save patient
                    patient = patient_form.save(commit=False)
                    patient.created_by = request.user
                    patient.patient_id = generate_patient_id()
                    patient.save()
                    
                    # Create registration payment (50 ETB)
                    payment = Payment(
                        payment_id=f"PAY{timezone.now().strftime('%y%m%d')}{random.randint(1000, 9999)}",
                        patient=patient,
                        payment_type=Payment.PaymentType.REGISTRATION,
                        payment_method=payment_form.cleaned_data['payment_method'],
                        amount=50.00,  # Fixed registration fee
                        processed_by=request.user,
                        notes=payment_form.cleaned_data['notes'],
                        status=Payment.Status.COMPLETED,
                        completed_at=timezone.now(),
                        receipt_number=f"RCP{timezone.now().strftime('%y%m%d')}{random.randint(1000, 9999)}"
                    )
                    payment.save()
                    
                    messages.success(request, f'Patient {patient} registered successfully! Registration fee of 50 ETB collected.')
                    return redirect('patient_detail', patient_id=patient.patient_id)
                    
            except Exception as e:
                messages.error(request, f'Error registering patient: {str(e)}')
    else:
        patient_form = PatientRegistrationForm()
        payment_form = RegistrationPaymentForm()
    
    context = {
        'patient_form': patient_form,
        'payment_form': payment_form,
        'registration_fee': 50.00
    }
    return render(request, 'patients/register_patient.html', context)

@login_required
def patient_list(request):
    patients = Patient.objects.all().order_by('-created_at')
    return render(request, 'patients/patient_list.html', {'patients': patients})

@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    visits = patient.visits.all().order_by('-created_at')
    return render(request, 'patients/patient_detail.html', {
        'patient': patient,
        'visits': visits
    })

@login_required
def create_visit(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    if request.method == 'POST':
        form = VisitForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.patient = patient
            visit.visit_id = generate_visit_id()
            visit.status = Visit.Status.WITH_DOCTOR
            visit.doctor_assigned_time = timezone.now()
            visit.save()
            
            # Create medical examination record automatically
            MedicalExamination.objects.create(
                visit=visit,
                created_by=request.user  # Set the receptionist as creator
            )
            
            messages.success(request, f'Visit created for {patient}. Patient sent to doctor.')
            return redirect('visit_detail', visit_id=visit.visit_id)
    else:
        form = VisitForm()
    
    context = {
        'form': form,
        'patient': patient,
    }
    return render(request, 'patients/create_visit.html', context)

@login_required
def visit_detail(request, visit_id):
    visit = get_object_or_404(Visit, visit_id=visit_id)
    examination, created = MedicalExamination.objects.get_or_create(visit=visit)
    
    if request.method == 'POST' and request.user.role == 'DOCTOR':
        exam_form = MedicalExaminationForm(request.POST, instance=examination)
        if exam_form.is_valid():
            exam = exam_form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            messages.success(request, 'Examination details saved successfully.')
            return redirect('visit_detail', visit_id=visit_id)
    else:
        exam_form = MedicalExaminationForm(instance=examination)
    
    context = {
        'visit': visit,
        'exam_form': exam_form,
        'lab_requests': visit.lab_requests.all(),
    }
    return render(request, 'patients/visit_detail.html', context)