from django.contrib import admin
from app.user.models import Address
# Register your models here.

class AddressAdmin(admin.ModelAdmin):
    list_display = ['user','receiver','addr','phone','is_default']
admin.site.register(Address,AddressAdmin)