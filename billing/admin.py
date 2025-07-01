from django.contrib import admin
from billing.models import model_admin, BillingStaff


@admin.register(BillingStaff)
class BillingStaffAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'user', 'department')
    search_fields = ('staff_id', 'user__email', 'user__first_name', 'user__last_name')

for model in model_admin:
    admin.site.register(model)

