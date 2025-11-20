import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone
from django.db import transaction
from .models import Medicine, Prescription, PrescriptionItem, DispenseCart, CartItem
from core.models import Notification
from users.models import User
from billing.models import Payment
from patients.models import Patient, Visit
import random

@login_required
def pharmacy_dashboard(request):
    if request.user.role not in ['PHARMACIST', 'CASHIER', 'ADMIN']:
        return render(request, '403.html', status=403)
    
    # Get prescriptions based on user role
    if request.user.role == 'PHARMACIST':
        pending_prescriptions = Prescription.objects.filter(status=Prescription.Status.PENDING)
        ready_prescriptions = Prescription.objects.filter(status=Prescription.Status.READY)
    elif request.user.role == 'CASHIER':
        pending_prescriptions = Prescription.objects.none()  # Cashiers don't see pending
        ready_prescriptions = Prescription.objects.filter(status=Prescription.Status.READY)
    else:  # ADMIN
        pending_prescriptions = Prescription.objects.filter(status=Prescription.Status.PENDING)
        ready_prescriptions = Prescription.objects.filter(status=Prescription.Status.READY)
    
    active_carts = DispenseCart.objects.filter(pharmacist=request.user, is_active=True)

    prescriptions = Prescription.objects.filter(status=Prescription.Status.PENDING).order_by('-created_at')
    
    context = {
        'pending_prescriptions': pending_prescriptions,
        'ready_prescriptions': ready_prescriptions,
        'active_carts': active_carts,
        'prescriptions':prescriptions,
    }
    return render(request, 'pharmacy/dashboard.html', context)

@login_required
def prescription_list(request):
    prescriptions = Prescription.objects.all().order_by('-created_at')
    return render(request, 'pharmacy/prescription_list.html', {'prescriptions': prescriptions})

@login_required
def prescription_detail(request, prescription_id):
    prescription = get_object_or_404(Prescription, prescription_id=prescription_id)
    
    # Get the most recent active cart or create a new one
    try:
        # Try to get the most recent active cart
        cart = DispenseCart.objects.filter(
            pharmacist=request.user,
            prescription=prescription,
            is_active=True
        ).latest('created_at')
    except DispenseCart.DoesNotExist:
        # Create new cart if none exists
        cart = DispenseCart.objects.create(
            pharmacist=request.user,
            prescription=prescription,
            is_active=True
        )
    except DispenseCart.MultipleObjectsReturned:
        # Handle multiple active carts - get the most recent and deactivate others
        carts = DispenseCart.objects.filter(
            pharmacist=request.user,
            prescription=prescription,
            is_active=True
        ).order_by('-created_at')
        
        # Keep the most recent cart active, deactivate others
        cart = carts.first()
        carts.exclude(id=cart.id).update(is_active=False)
    
    context = {
        'prescription': prescription,
        'cart': cart,
    }
    return render(request, 'pharmacy/prescription_detail.html', context)


@login_required
def prescription_details(request, prescription_id):
    """View prescription details"""
    prescription = get_object_or_404(Prescription, prescription_id=prescription_id)
    prescription_items = prescription.items.all()
    
    context = {
        'prescription': prescription,
        'prescription_items': prescription_items,
        'patient': prescription.visit.patient,
        'visit': prescription.visit,
    }
    return render(request, 'pharmacy/prescription_details.html', context)
    
@login_required
@require_http_methods(["GET"])
def medicine_search(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'medicines': []})
    
    medicines = Medicine.objects.filter(
        Q(name__icontains=query) | 
        Q(generic_name__icontains=query) |
        Q(medicine_id__icontains=query)
    ).filter(
        quantity_in_stock__gt=0,
        is_active=True
    )[:10]  # Limit results
    
    results = []
    for medicine in medicines:
        results.append({
            'id': medicine.id,
            'medicine_id': medicine.medicine_id,
            'name': medicine.name,
            'generic_name': medicine.generic_name,
            'quantity_in_stock': medicine.quantity_in_stock,
            'unit_price': str(medicine.unit_price),
            'strength': medicine.strength,
            'dosage_form': medicine.dosage_form,
        })
    
    return JsonResponse({'medicines': results})

@login_required
@require_http_methods(["POST"])
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        prescription_id = data.get('prescription_id')
        medicine_id = data.get('medicine_id')
        quantity = int(data.get('quantity', 1))
        
        prescription = get_object_or_404(Prescription, prescription_id=prescription_id)
        medicine = get_object_or_404(Medicine, id=medicine_id)
        
        # Get or create cart
        cart, created = DispenseCart.objects.get_or_create(
            pharmacist=request.user,
            prescription=prescription,
            is_active=True
        )
        
        # Create prescription item if not exists
        prescription_item, created = PrescriptionItem.objects.get_or_create(
            prescription=prescription,
            medicine=medicine,
            defaults={
                'quantity': quantity,
                'dosage': data.get('dosage', ''),
                'duration': data.get('duration', ''),
                'instructions': data.get('instructions', ''),
                'unit_price': medicine.unit_price,
                'total_price': medicine.unit_price * quantity
            }
        )
        
        if not created:
            prescription_item.quantity += quantity
            prescription_item.total_price = prescription_item.unit_price * prescription_item.quantity
            prescription_item.save()
        
        # Add to cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            prescription_item=prescription_item,
            defaults={
                'quantity_to_dispense': quantity,
                'subtotal': medicine.unit_price * quantity
            }
        )
        
        if not created:
            cart_item.quantity_to_dispense += quantity
            cart_item.subtotal = prescription_item.unit_price * cart_item.quantity_to_dispense
            cart_item.save()
        
        # Update cart total
        cart.total_amount = sum(item.subtotal for item in cart.cartitem_set.all())
        cart.save()
        
        return JsonResponse({
            'status': 'success',
            'cart_total': str(cart.total_amount),
            'message': 'Medicine added to cart successfully'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def dispense_medicines(request, prescription_id):
    """Pharmacist dispenses medicines and creates payment record"""
    if request.user.role != 'PHARMACIST':
        return JsonResponse({'status': 'error', 'message': 'Only pharmacists can dispense medicines'})
    
    prescription = get_object_or_404(Prescription, prescription_id=prescription_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Calculate total cost from prescription items
                total_cost = sum(item.total_price for item in prescription.items.all())
                
                # Update prescription status to READY (waiting for payment)
                prescription.status = Prescription.Status.READY
                prescription.total_cost = total_cost
                prescription.reviewed_at = timezone.now()
                prescription.save()
                
                # Create pending payment record
                payment = Payment(
                    payment_id=f"PAY{timezone.now().strftime('%y%m%d')}{random.randint(1000, 9999)}",
                    patient=prescription.visit.patient,
                    visit=prescription.visit,
                    payment_type=Payment.PaymentType.MEDICINE,
                    payment_method=Payment.PaymentMethod.PENDING,  # Will be set by cashier
                    amount=total_cost,
                    prescription=prescription,
                    processed_by=request.user,  # Pharmacist who dispensed
                    status=Payment.Status.PENDING,  # Waiting for cashier
                    notes=f'Medicine payment for prescription {prescription.prescription_id}',
                    receipt_number=f"RCP{timezone.now().strftime('%y%m%d')}{random.randint(1000, 9999)}"
                )
                payment.save()
                
                # Update visit status
                prescription.visit.status = Visit.Status.PRESCRIPTION_READY
                prescription.visit.prescription_time = timezone.now()
                prescription.visit.save()
                
                # Create notification for cashier
                cashiers = User.objects.filter(role=User.Role.CASHIER, is_active=True)
                for cashier in cashiers:
                    Notification.objects.create(
                        recipient=cashier,
                        notification_type=Notification.NotificationType.PAYMENT,
                        title='Medicine Payment Required',
                        message=f'Patient {prescription.visit.patient} needs to pay ETB {total_cost} for medicines',
                        related_object_id=prescription.prescription_id
                    )
                
                # Deactivate cart
                DispenseCart.objects.filter(
                    pharmacist=request.user,
                    prescription=prescription,
                    is_active=True
                ).update(is_active=False)
                
                return JsonResponse({
                    'status': 'success', 
                    'message': f'Medicines dispensed successfully. Patient needs to pay ETB {total_cost}',
                    'total_cost': float(total_cost)
                })
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def update_cart(request):
    try:
        data = json.loads(request.body)
        cart_item_id = data.get('cart_item_id')
        new_quantity = int(data.get('quantity', 1))
        
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__pharmacist=request.user)
        
        if new_quantity <= 0:
            # If quantity is 0 or negative, remove the item
            cart_item.delete()
        else:
            cart_item.quantity_to_dispense = new_quantity
            cart_item.subtotal = cart_item.prescription_item.unit_price * new_quantity
            cart_item.save()
        
        # Update cart total
        cart = cart_item.cart
        cart.total_amount = sum(item.subtotal for item in cart.cartitem_set.all())
        cart.save()
        
        return JsonResponse({
            'status': 'success',
            'cart_total': str(cart.total_amount),
            'message': 'Cart updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@require_http_methods(["POST"])
def remove_from_cart(request):
    try:
        data = json.loads(request.body)
        cart_item_id = data.get('cart_item_id')
        
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__pharmacist=request.user)
        cart = cart_item.cart
        cart_item.delete()
        
        # Update cart total
        cart.total_amount = sum(item.subtotal for item in cart.cartitem_set.all())
        cart.save()
        
        return JsonResponse({
            'status': 'success',
            'cart_total': str(cart.total_amount),
            'message': 'Item removed from cart successfully'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})