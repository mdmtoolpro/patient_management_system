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
    
    # Build date filter
    date_filter = {
        'created_at__date__range': [start_date, end_date]
    }
    
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
    
    # Calculate patient statistics
    total_patients = Patient.objects.filter(**date_filter).count()
    new_patients = Patient.objects.filter(**date_filter).count()
    total_visits = Visit.objects.filter(**date_filter).count()
    total_lab_tests = LabTestRequest.objects.filter(**date_filter).count()
    total_prescriptions = Prescription.objects.filter(**date_filter).count()
    
    # Monthly data for charts (for yearly reports)
    monthly_data = []
    if period == 'yearly':
        for m in range(1, 13):
            month_start = datetime(year, m, 1).date()
            if m == 12:
                month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                month_end = datetime(year, m + 1, 1).date() - timedelta(days=1)
            
            month_payments = Payment.objects.filter(
                created_at__date__range=[month_start, month_end],
                status='COMPLETED'
            )
            
            month_reg = month_payments.filter(payment_type='REGISTRATION').aggregate(total=Sum('amount'))['total'] or 0
            month_lab = month_payments.filter(payment_type='LAB_TEST').aggregate(total=Sum('amount'))['total'] or 0
            month_pharm = month_payments.filter(payment_type='MEDICINE').aggregate(total=Sum('amount'))['total'] or 0
            
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
    
    # Calculate date range (simplified for export)
    if period == 'monthly':
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
    else:  # yearly
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
    
    date_filter = {
        'created_at__date__range': [start_date, end_date]
    }
    
    # Calculate financial data
    payments = Payment.objects.filter(**date_filter, status='COMPLETED')
    
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
    writer.writerow(['Total Patients', Patient.objects.filter(**date_filter).count()])
    writer.writerow(['Total Visits', Visit.objects.filter(**date_filter).count()])
    writer.writerow(['Total Lab Tests', LabTestRequest.objects.filter(**date_filter).count()])
    writer.writerow(['Total Prescriptions', Prescription.objects.filter(**date_filter).count()])
    
    return response

@login_required
def dashboard_stats(request):
    """API endpoint for dashboard statistics"""
    if request.user.role != 'ADMIN':
        return HttpResponse('Unauthorized', status=403)
    
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # Today's statistics
    today_income = Payment.objects.filter(
        created_at__date=today,
        status='COMPLETED'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    today_patients = Patient.objects.filter(created_at__date=today).count()
    
    # Monthly statistics
    monthly_income = Payment.objects.filter(
        created_at__date__gte=month_start,
        status='COMPLETED'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_patients = Patient.objects.filter(created_at__date__gte=month_start).count()
    
    return HttpResponse(json.dumps({
        'today_income': float(today_income),
        'today_patients': today_patients,
        'monthly_income': float(monthly_income),
        'monthly_patients': monthly_patients,
    }), content_type='application/json')