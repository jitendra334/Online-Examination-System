from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
def role_required(allowed_roles=None):
    """
    Decorator for views that checks that the user is logged in and has one of the allowed roles.
    allowed_roles: list or tuple of role strings, e.g. ['ADMIN', 'TEACHER']
    """
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in to access this page.")
                return redirect('accounts:login')
            
            # Superusers always have admin privileges
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
                
            if request.user.role not in allowed_roles:
                messages.error(request, "Access Denied: You do not have permission to view this page.")
                return redirect('dashboard:index')
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def admin_required(view_func):
    """Requires user to have ADMIN role."""
    return role_required(['ADMIN'])(view_func)

def teacher_required(view_func):
    """Requires user to have TEACHER role."""
    return role_required(['TEACHER', 'ADMIN'])(view_func)

def admin_or_teacher_required(view_func):
    """Requires user to have either ADMIN or TEACHER role."""
    return role_required(['ADMIN', 'TEACHER'])(view_func)

def student_required(view_func):
    """Requires user to have STUDENT role."""
    return role_required(['STUDENT', 'ADMIN'])(view_func)
