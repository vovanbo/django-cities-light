# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django import forms
from django.db.models import get_model

Region = get_model('address', 'Region')
City = get_model('address', 'City')
PostalCode = get_model('address', 'PostalCode')


# class CountryForm(forms.ModelForm):
#     """
#     Country model form.
#     """
#     class Meta:
#         model = Country
#         fields = ('name', 'continent', 'alternate_names')


class RegionForm(forms.ModelForm):
    """
    Region model form.
    """
    class Meta:
        model = Region
        fields = ('name', 'country', 'alternate_names')


class CityForm(forms.ModelForm):
    """
    City model form.
    """
    class Meta:
        model = City
        fields = ('name', 'region', 'country', 'alternate_names')


class PostalCodeForm(forms.ModelForm):
    """
    PostalCode model form
    """
    class Meta:
        model = PostalCode
        fields = ('code', 'country', 'region', 'city')
