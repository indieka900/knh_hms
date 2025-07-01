from django.contrib import admin
from medical_records.models import admin_model


for model in admin_model:
    admin.site.register(model)

# Register your models here.
