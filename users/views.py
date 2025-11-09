from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, StaffProfile
from .forms import UserUpdateForm, StaffProfileForm


@login_required
def profile_view(request):
    """User profile view with safe profile handling"""
    # Get or create profile for the current user
    profile, created = StaffProfile.objects.get_or_create(user=request.user)
    if created:
        messages.info(request, 'Your staff profile has been created.')
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user, request=request)
        profile_form = StaffProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user, request=request)
        profile_form = StaffProfileForm(instance=profile)
    
    return render(request, 'users/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def staff_list(request):
    """List all staff members - only for admin"""
    if not request.user.is_administrator:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    staff_members = User.objects.filter(is_active=True).order_by('role', 'first_name')
    
    # Ensure all staff members have profiles
    for staff in staff_members:
        StaffProfile.objects.get_or_create(user=staff)
    
    return render(request, 'users/staff_list.html', {
        'staff_members': staff_members
    })

@login_required
def staff_detail(request, pk):
    """Staff member detail view - only for admin"""
    if not request.user.is_administrator:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    staff = get_object_or_404(User, pk=pk, is_active=True)
    profile, created = StaffProfile.objects.get_or_create(user=staff)
    
    return render(request, 'users/staff_detail.html', {
        'staff': staff,
        'profile': profile
    })

@login_required
def staff_edit(request, pk):
    """Edit staff member - only for admin"""
    if not request.user.is_administrator:
        messages.error(request, 'You do not have permission to edit staff members.')
        return redirect('dashboard')
    
    staff = get_object_or_404(User, pk=pk, is_active=True)
    profile, created = StaffProfile.objects.get_or_create(user=staff)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=staff)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, f'Staff member {staff.get_full_name()} updated successfully!')
            return redirect('staff_detail', pk=staff.pk)
    else:
        user_form = UserUpdateForm(instance=staff)
    
    return render(request, 'users/staff_form.html', {
        'form': user_form, 
        'title': 'Edit Staff', 
        'staff': staff
    })


@login_required
def user_profile(request):
    """User profile view"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = StaffProfileForm(request.POST, instance=request.user.staff_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('user_profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        # Get or create staff profile
        profile, created = StaffProfile.objects.get_or_create(user=request.user)
        profile_form = StaffProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'users/profile.html', context)