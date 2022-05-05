from django.contrib import admin
from tastypie.models import ApiKey, ApiAccess
 
admin.site.unregister(ApiKey)
admin.site.unregister(ApiAccess)