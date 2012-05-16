from django.contrib import admin

from models import Country
from cities_light.settings import *

class CountryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code2',
        'code3',
        'continent',
        'tld',
    )
    search_fields = (
        'name',
        'name_ascii',
        'code2',
        'code3',
        'tld'
    )
    list_filter = (
        'continent',
    )
admin.site.register(Country, CountryAdmin)
