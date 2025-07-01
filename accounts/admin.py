from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .services import RoleManager
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number', 'date_of_birth', 'address', 
                    'profile_picture', 'is_active_user')
        }),
    )
    
    actions = ['promote_to_doctor', 'promote_to_billing_staff', 'demote_to_patient']
    
    def promote_to_doctor(self, request, queryset):
        # This would open a form for additional doctor data
        # For now, just show message
        self.message_user(request, "Use the RoleManager in views for role changes")
    promote_to_doctor.short_description = "Promote selected users to Doctor"

# Register your models here.
