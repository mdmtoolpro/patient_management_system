from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta, datetime
from billing.models import Bill, Payment, BillItem
from patients.models import Patient, Visit
from laboratory.models import LabTest
from pharmacy.models import Medicine, Prescription

def revenue_report(start_date, end_date):
    """Generate revenue report by date range"""
    payments = Payment.objects.filter(
        payment_date__date__range=[start_date, end_date]
    )
    
    total_revenue = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    payment_methods = payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    daily_revenue = payments.extra(
        {'date': "date(payment_date)"}
    ).values('date').annotate(
        total=Sum('amount')
    ).order_by('date')
    
    return {
        'total_revenue': total_revenue,
        'payment_methods': payment_methods,
        'daily_revenue': daily_revenue,
        'payment_count': payments.count()
    }

def profit_analysis_report(start_date, end_date):
    """Generate profit analysis report"""
    bills = Bill.objects.filter(
        issue_date__range=[start_date, end_date],
        status__in=['paid', 'partially_paid']
    )
    
    total_income = bills.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_collected = bills.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    
    # Calculate costs (this would need actual cost data)
    # For now, we'll use estimated costs based on service types
    bill_items = BillItem.objects.filter(
        bill__issue_date__range=[start_date, end_date],
        bill__status__in=['paid', 'partially_paid']
    )
    
    service_costs = bill_items.values('item_type').annotate(
        revenue=Sum('total_price'),
        count=Count('id')
    )
    
    estimated_profit = total_income * 0.6  # Assuming 60% profit margin
    
    return {
        'total_income': total_income,
        'total_collected': total_collected,
        'estimated_profit': estimated_profit,
        'outstanding_revenue': total_income - total_collected,
        'service_costs': service_costs,
        'bill_count': bills.count()
    }

def patient_statistics_report(start_date, end_date):
    """Generate patient statistics report"""
    total_patients = Patient.objects.filter(is_active=True).count()
    new_patients = Patient.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).count()
    
    visits = Visit.objects.filter(
        visit_date__date__range=[start_date, end_date]
    )
    
    visit_stats = visits.values('doctor__first_name', 'doctor__last_name').annotate(
        visit_count=Count('id'),
        unique_patients=Count('patient', distinct=True)
    )
    
    patient_visits = visits.values('patient').annotate(
        visit_count=Count('id')
    ).order_by('-visit_count')[:10]  # Top 10 patients by visits
    
    return {
        'total_patients': total_patients,
        'new_patients': new_patients,
        'total_visits': visits.count(),
        'visit_stats': visit_stats,
        'patient_visits': patient_visits,
        'average_visits_per_patient': visits.count() / max(new_patients, 1)
    }

def medicine_sales_report(start_date, end_date):
    """Generate medicine sales report"""
    prescriptions = Prescription.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='dispensed'
    )
    
    medicine_sales = prescriptions.values(
        'items__medicine__name',
        'items__medicine__generic_name'
    ).annotate(
        total_quantity=Sum('items__quantity'),
        total_revenue=Sum('items__unit_price') * Sum('items__quantity'),
        prescription_count=Count('id', distinct=True)
    ).filter(items__medicine__isnull=False)
    
    low_stock_medicines = Medicine.objects.filter(
        stock_quantity__lte=models.F('min_stock_level'),
        is_active=True
    )
    
    return {
        'total_prescriptions': prescriptions.count(),
        'medicine_sales': medicine_sales,
        'low_stock_medicines': low_stock_medicines,
        'total_medicine_revenue': sum(item['total_revenue'] for item in medicine_sales if item['total_revenue'])
    }

def lab_test_analysis_report(start_date, end_date):
    """Generate lab test analysis report"""
    lab_tests = LabTest.objects.filter(
        order_date__date__range=[start_date, end_date]
    )
    
    test_stats = lab_tests.values('test_type__name').annotate(
        test_count=Count('id'),
        completed_count=Count('id', filter=Q(status='completed')),
        revenue=Sum('test_type__price')
    )
    
    status_distribution = lab_tests.values('status').annotate(
        count=Count('id')
    )
    
    doctor_orders = lab_tests.values('ordered_by__first_name', 'ordered_by__last_name').annotate(
        order_count=Count('id')
    ).order_by('-order_count')
    
    return {
        'total_tests': lab_tests.count(),
        'completed_tests': lab_tests.filter(status='completed').count(),
        'test_stats': test_stats,
        'status_distribution': status_distribution,
        'doctor_orders': doctor_orders,
        'total_revenue': sum(item['revenue'] for item in test_stats if item['revenue'])
    }

def comprehensive_report(start_date, end_date):
    """Generate comprehensive report combining all data"""
    revenue_data = revenue_report(start_date, end_date)
    profit_data = profit_analysis_report(start_date, end_date)
    patient_data = patient_statistics_report(start_date, end_date)
    medicine_data = medicine_sales_report(start_date, end_date)
    lab_data = lab_test_analysis_report(start_date, end_date)
    
    return {
        'period': f"{start_date} to {end_date}",
        'revenue': revenue_data,
        'profit': profit_data,
        'patients': patient_data,
        'medicines': medicine_data,
        'lab_tests': lab_data,
        'summary': {
            'total_revenue': revenue_data['total_revenue'],
            'estimated_profit': profit_data['estimated_profit'],
            'new_patients': patient_data['new_patients'],
            'total_visits': patient_data['total_visits'],
            'total_prescriptions': medicine_data['total_prescriptions'],
            'total_lab_tests': lab_data['total_tests']
        }
    }