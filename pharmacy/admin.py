from django.contrib import admin
from pharmacy.models import admin_models

for model in admin_models:
    admin.site.register(model)

# Register your models here.
