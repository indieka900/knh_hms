from .models import MODULE_CHOICES, RolePermission

def module_permissions(request):
    """
    Context processor that provides a dict of module permissions for the current user.
    Usage in templates:
        {% if user_module_perms.patients %}
            show patients menu
        {% endif %}
    """
    if not request.user.is_authenticated:
        return {}

    user = request.user

    # Build a dict like {'patients': True, 'pharmacy': False, ...}
    perms = {}
    for code, label in MODULE_CHOICES:
        if user.is_superuser or user.role == 'administrator':
            perms[code] = True
        else:
            perms[code] = RolePermission.objects.filter(
                role=user.role, module=code, can_view=True
            ).exists()

    return {
        'user_module_perms': perms,
        'all_modules': MODULE_CHOICES,  # useful for admin forms
    }
