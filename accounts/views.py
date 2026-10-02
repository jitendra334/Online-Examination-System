from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import User
from .forms import (
    StudentRegisterForm,
    TeacherRegisterForm,
    UserLoginForm,
    UserProfileForm,
    AdminUserManagementForm
)
from .decorators import admin_required

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:index')
        else:
            messages.error(request, "Invalid username or password. Please check your credentials.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def register_student_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to the Examination Portal.")
            return redirect('dashboard:index')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentRegisterForm()

    return render(request, 'accounts/register_student.html', {'form': form})


def register_teacher_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = TeacherRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Faculty account registered successfully!")
            return redirect('dashboard:index')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = TeacherRegisterForm()

    return render(request, 'accounts/register_teacher.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out securely.")
    return redirect('accounts:login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors in the profile form.")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


# --- Admin User Management Views ---

@admin_required
def admin_users_list(request):
    role_filter = request.GET.get('role', '')
    query = request.GET.get('q', '').strip()

    users_qs = User.objects.all().order_by('-date_joined')

    if role_filter:
        users_qs = users_qs.filter(role=role_filter)

    if query:
        users_qs = users_qs.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(student_id__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(department__icontains=query)
        )

    paginator = Paginator(users_qs, 15)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)

    context = {
        'users': users,
        'role_filter': role_filter,
        'query': query,
        'total_count': users_qs.count(),
        'roles': User.Role.choices,
    }
    return render(request, 'accounts/admin/user_list.html', context)


@admin_required
def admin_user_create(request):
    if request.method == 'POST':
        form = AdminUserManagementForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} created successfully.")
            return redirect('accounts:admin_user_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = AdminUserManagementForm()

    return render(request, 'accounts/admin/user_form.html', {'form': form, 'title': 'Create New User'})


@admin_required
def admin_user_edit(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = AdminUserManagementForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user_obj.username} updated successfully.")
            return redirect('accounts:admin_user_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = AdminUserManagementForm(instance=user_obj)

    return render(request, 'accounts/admin/user_form.html', {'form': form, 'user_obj': user_obj, 'title': f'Edit User: {user_obj.username}'})


@admin_required
def admin_user_toggle_status(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if user_obj == request.user:
        messages.error(request, "You cannot deactivate your own administrative account.")
        return redirect('accounts:admin_user_list')
    
    user_obj.is_active = not user_obj.is_active
    user_obj.save()
    status_str = "activated" if user_obj.is_active else "deactivated"
    messages.success(request, f"User {user_obj.username} has been {status_str}.")
    return redirect('accounts:admin_user_list')


@admin_required
def admin_user_delete(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if user_obj == request.user:
        messages.error(request, "You cannot delete your own administrative account.")
        return redirect('accounts:admin_user_list')

    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f"User {username} deleted permanently.")
        return redirect('accounts:admin_user_list')

    return render(request, 'accounts/admin/user_confirm_delete.html', {'user_obj': user_obj})
