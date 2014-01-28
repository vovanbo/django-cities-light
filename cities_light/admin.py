# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from copy import copy

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList

from .forms import RegionForm
from .utils import to_search

from django.db.models import get_model

Region = get_model('address', 'Region')
City = get_model('address', 'City')


# class CountryAdmin(admin.ModelAdmin):
#     """
#     ModelAdmin for Country.
#     """

#     list_display = (
#         'name',
#         'code2',
#         'code3',
#         'continent',
#         'tld',
#     )
#     search_fields = (
#         'name',
#         'name_ascii',
#         'code2',
#         'code3',
#         'tld'
#     )
#     list_filter = (
#         'continent',
#     )
#     form = CountryForm
# admin.site.register(Country, CountryAdmin)


class RegionAdmin(admin.ModelAdmin):
    """
    ModelAdmin for Region.
    """
    list_filter = (
        # 'country__continent',
        'country',
    )
    search_fields = (
        'name',
        'name_ascii',
    )
    list_display = (
        'name',
        'country',
    )
    form = RegionForm

admin.site.register(Region, RegionAdmin)


class CityChangeList(ChangeList):

    def get_query_set(self, request):
        if 'q' in list(request.GET.keys()):
            request.GET = copy(request.GET)
            request.GET['q'] = to_search(request.GET['q'])
        return super(CityChangeList, self).get_query_set(request)


class CityAdmin(admin.ModelAdmin):
    """
    ModelAdmin for City.
    """
    list_display = (
        'name',
        'region',
        'country',
    )
    search_fields = (
        'search_names',
    )
    list_filter = (
        # 'country__continent',
        'country',
    )
    #form = CityForm

    def get_changelist(self, request, **kwargs):
        return CityChangeList

admin.site.register(City, CityAdmin)
