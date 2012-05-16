from django.contrib import admin

from models import City
from cities_light.settings import *

class CityAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'country',
    )
    search_fields = (
        'name',
        'name_ascii',
    )
    list_filter = (
        'country__continent',
        'country',
    )

admin.site.register(City, CityAdmin)
