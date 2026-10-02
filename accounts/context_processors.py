def user_roles(request):
    """
    Context processor to easily check user roles in any template.
    """
    if request.user.is_authenticated:
        return {
            'is_admin': request.user.is_admin_user,
            'is_teacher': request.user.is_teacher_user,
            'is_student': request.user.is_student_user,
            'current_user_role': request.user.role,
        }
    return {
        'is_admin': False,
        'is_teacher': False,
        'is_student': False,
        'current_user_role': None,
    }
