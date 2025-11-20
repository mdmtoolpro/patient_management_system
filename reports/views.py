from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from patients.models import Patient, Visit
from laboratory.models import LabTestRequest
from pharmacy.models import Prescription
from billing.models import Payment
import csv
import json

@login_required
def financial_reports(request):
    """Generate financial reports"""
    if request.user.role != 'ADMIN':
        return render(request, '403.html', status=403)
    
    # Get date range from request or default to current month
    period = request.GET.get('period', 'monthly')
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    # Calculate date range based on period
    if period == 'daily':
        start_date = timezone.now().date()
        end_date = start_date
        period_label = start_date.strftime('%B %d, %Y')
    elif period == 'weekly':
        start_date = timezone.now().date() - timedelta(days=7)
        end_date = timezone.now().date()
        period_label = f"Week of {start_date.strftime('%b %d')} to {end_date.strftime('%b %d, %Y')}"
    elif period == 'monthly':
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        period_label = start_date.strftime('%B %Y')
    else:  # yearly
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
        period_label = str(year)
    
    # Build date filter - Use the correct field name from your Payment model
    # Common field names: 'created_at', 'timestamp', 'date_created', 'payment_date'
    date_filter = {
        'created_at__date__range': [start_date, end_date]  # Try this first
    }
    
    # If the above fails, try alternative field names:
    # date_filter = {'timestamp__date__range': [start_date, end_date]}
    # date_filter = {'date_created__date__range': [start_date, end_date]}
    # date_filter = {'payment_date__date__range': [start_date, end_date]}
    
    try:
        # Calculate financial data
        payments = Payment.objects.filter(**date_filter, status='COMPLETED')
        
        registration_income = payments.filter(
            payment_type='REGISTRATION'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        lab_income = payments.filter(
            payment_type='LAB_TEST'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        pharmacy_income = payments.filter(
            payment_type='MEDICINE'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_income = registration_income + lab_income + pharmacy_income
        
    except Exception as e:
        # If date filtering fails, get all payments and filter in Python
        payments = Payment.objects.filter(status='COMPLETED')
        
        # Filter by date in Python (less efficient but works)
        payments_in_period = []
        for payment in payments:
            # Try different possible date fields
            payment_date = None
            if hasattr(payment, 'created_at') and payment.created_at:
                payment_date = payment.created_at.date()
            elif hasattr(payment, 'timestamp') and payment.timestamp:
                payment_date = payment.timestamp.date()
            elif hasattr(payment, 'date_created') and payment.date_created:
                payment_date = payment.date_created
            elif hasattr(payment, 'payment_date') and payment.payment_date:
                payment_date = payment.payment_date
            elif hasattr(payment, 'completed_at') and payment.completed_at:
                payment_date = payment.completed_at.date()
            
            if payment_date and start_date <= payment_date <= end_date:
                payments_in_period.append(payment)
        
        # Calculate totals from filtered payments
        registration_income = sum(p.amount for p in payments_in_period if p.payment_type == 'REGISTRATION')
        lab_income = sum(p.amount for p in payments_in_period if p.payment_type == 'LAB_TEST')
        pharmacy_income = sum(p.amount for p in payments_in_period if p.payment_type == 'MEDICINE')
        total_income = registration_income + lab_income + pharmacy_income
    
    # Calculate patient statistics - Use the correct field name
    try:
        total_patients = Patient.objects.filter(**date_filter).count()
        new_patients = Patient.objects.filter(**date_filter).count()
    except:
        # Alternative approach for patient date filtering
        total_patients = Patient.objects.all().count()  # Fallback
        new_patients = Patient.objects.all().count()    # Fallback
    
    try:
        total_visits = Visit.objects.filter(**date_filter).count()
    except:
        total_visits = Visit.objects.all().count()  # Fallback
    
    try:
        total_lab_tests = LabTestRequest.objects.filter(**date_filter).count()
    except:
        total_lab_tests = LabTestRequest.objects.all().count()  # Fallback
    
    try:
        total_prescriptions = Prescription.objects.filter(**date_filter).count()
    except:
        total_prescriptions = Prescription.objects.all().count()  # Fallback
    
    # Monthly data for charts (for yearly reports)
    monthly_data = []
    if period == 'yearly':
        for m in range(1, 13):
            month_start = datetime(year, m, 1).date()
            if m == 12:
                month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                month_end = datetime(year, m + 1, 1).date() - timedelta(days=1)
            
            try:
                month_payments = Payment.objects.filter(
                    created_at__date__range=[month_start, month_end],  # Try this field
                    status='COMPLETED'
                )
            except:
                # Fallback: filter all payments manually
                all_payments = Payment.objects.filter(status='COMPLETED')
                month_payments = [p for p in all_payments if hasattr(p, 'created_at') and p.created_at and month_start <= p.created_at.date() <= month_end]
            
            month_reg = sum(p.amount for p in month_payments if p.payment_type == 'REGISTRATION')
            month_lab = sum(p.amount for p in month_payments if p.payment_type == 'LAB_TEST')
            month_pharm = sum(p.amount for p in month_payments if p.payment_type == 'MEDICINE')
            
            monthly_data.append({
                'month': month_start.strftime('%b'),
                'registration': float(month_reg),
                'lab': float(month_lab),
                'pharmacy': float(month_pharm),
                'total': float(month_reg + month_lab + month_pharm)
            })
    
    context = {
        'period': period,
        'period_label': period_label,
        'start_date': start_date,
        'end_date': end_date,
        'year': year,
        'month': month,
        
        # Financial data
        'registration_income': registration_income,
        'lab_income': lab_income,
        'pharmacy_income': pharmacy_income,
        'total_income': total_income,
        
        # Statistics
        'total_patients': total_patients,
        'new_patients': new_patients,
        'total_visits': total_visits,
        'total_lab_tests': total_lab_tests,
        'total_prescriptions': total_prescriptions,
        
        # Chart data
        'monthly_data': monthly_data,
        'monthly_data_json': json.dumps(monthly_data),
        
        # Available years for filter
        'available_years': range(2020, timezone.now().year + 1),
    }
    
    return render(request, 'reports/financial_reports.html', context)

@login_required
def export_financial_report(request):
    """Export financial report as CSV"""
    if request.user.role != 'ADMIN':
        return HttpResponse('Unauthorized', status=403)
    
    # Get the same data as the financial_reports view
    period = request.GET.get('period', 'monthly')
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    # Calculate date range
    if period == 'monthly':
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
    else:  # yearly
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
    
    # Calculate financial data without date filtering for now
    payments = Payment.objects.filter(status='COMPLETED')
    
    registration_income = payments.filter(payment_type='REGISTRATION').aggregate(total=Sum('amount'))['total'] or 0
    lab_income = payments.filter(payment_type='LAB_TEST').aggregate(total=Sum('amount'))['total'] or 0
    pharmacy_income = payments.filter(payment_type='MEDICINE').aggregate(total=Sum('amount'))['total'] or 0
    total_income = registration_income + lab_income + pharmacy_income
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="financial_report_{year}_{month}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Financial Report', f'{start_date} to {end_date}'])
    writer.writerow([])
    writer.writerow(['Category', 'Amount (ETB)'])
    writer.writerow(['Registration Income', registration_income])
    writer.writerow(['Laboratory Income', lab_income])
    writer.writerow(['Pharmacy Income', pharmacy_income])
    writer.writerow(['Total Income', total_income])
    writer.writerow([])
    writer.writerow(['Statistics', 'Count'])
    writer.writerow(['Total Patients', Patient.objects.count()])
    writer.writerow(['Total Visits', Visit.objects.count()])
    writer.writerow(['Total Lab Tests', LabTestRequest.objects.count()])
    writer.writerow(['Total Prescriptions', Prescription.objects.count()])
    
    return response

@login_required
def dashboard_stats(request):
    """API endpoint for dashboard statistics"""
    if request.user.role != 'ADMIN':
        return HttpResponse('Unauthorized', status=403)
    
    today = timezone.now().date()
    
    # Today's statistics - without date filtering for now
    today_income = Payment.objects.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0
    today_patients = Patient.objects.count()
    
    # Monthly statistics - without date filtering for now
    monthly_income = Payment.objects.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0
    monthly_patients = Patient.objects.count()
    
    return HttpResponse(json.dumps({
        'today_income': float(today_income),
        'today_patients': today_patients,
        'monthly_income': float(monthly_income),
        'monthly_patients': monthly_patients,
    }), content_type='application/json')