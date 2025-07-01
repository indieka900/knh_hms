from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .services import RoleManager
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')

    # ✅ Define only the fields you use — no username
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'date_of_birth', 'phone_number', 'address')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Other'), {'fields': ('role', 'profile_picture', 'is_active_user')}),
    )

    # ✅ Customize add view to exclude username
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )

    actions = ['promote_to_doctor', 'promote_to_billing_staff', 'demote_to_patient']

    def promote_to_doctor(self, request, queryset):
        self.message_user(request, "Use the RoleManager in views for role changes")
    promote_to_doctor.short_description = "Promote selected users to Doctor"
# Register your models here.
