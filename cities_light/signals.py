# -*- coding: utf-8 -*-

"""
Signals for this application.

city_items_pre_import
    Emited by city_import() in the cities_light command for each row parsed in
    the data file. If a signal reciever raises InvalidItems then it will be
    skipped.

    An example is worth 1000 words: if you want to import only cities from
    France, USA and Belgium you could do as such::

        import cities_light

        def filter_city_import(sender, items, **kwargs):
            if items[8] not in ('FR', 'US', 'BE'):
                raise cities_light.InvalidItems()

        cities_light.signals.city_items_pre_import.connect(filter_city_import)

    Note: this signal gets a list rather than a City instance for performance
    reasons.

region_items_pre_import
    Same as city_items_pre_import, for example::

        def filter_region_import(sender, items, **kwargs):
            if items[0].split('.')[0] not in ('FR', 'US', 'BE'):
                raise cities_light.InvalidItems()
        cities_light.signals.region_items_pre_import.connect(
            filter_region_import)

filter_non_cities()
    By default, this reciever is connected to city_items_pre_import, it raises
    InvalidItems if the row doesn't have PPL in its features (it's not a
    populated place).
"""

from __future__ import unicode_literals
import django.dispatch
from django.db.models.signals import pre_save

from .utils import to_ascii, to_search
from .exceptions import InvalidItems

__all__ = ['city_items_pre_import', 'region_items_pre_import',
           'filter_non_cities']

city_items_pre_import = django.dispatch.Signal(providing_args=['items'])
region_items_pre_import = django.dispatch.Signal(providing_args=['items'])
postal_code_items_pre_import = django.dispatch.Signal(providing_args=['items'])


def filter_non_cities(sender, items, **kwargs):
    """
    Reports non populated places as invalid.
    """
    if ('PPL' not in items[7]) or (items[7] == 'PPLX'):
        # PPLX - это всякие Коломенские, Бирюлёво, Жулебино и прочее
        raise InvalidItems()

city_items_pre_import.connect(filter_non_cities)


def set_name_ascii(sender, instance=None, **kwargs):
    """
    Signal reciever that sets instance.name_ascii from instance.name.

    Ascii versions of names are often useful for autocompletes and search.
    """
    name_ascii = to_ascii(instance.name)

    if not name_ascii.strip():
        return

    if name_ascii and not instance.name_ascii:
        instance.name_ascii = to_ascii(instance.name)


def set_name_ascii_signal(sender, **kwargs):
    pre_save.connect(set_name_ascii, sender=sender)


def set_display_name(sender, instance=None, **kwargs):
    """
    Set instance.display_name to instance.get_display_name(), avoid spawning
    queries during __str__().
    """
    instance.display_name = instance.get_display_name()


def set_display_name_signal(sender, **kwargs):
    pre_save.connect(set_display_name, sender=sender)


def city_country(sender, instance, **kwargs):
    if instance.region_id and not instance.country_id:
        instance.country_id = instance.region.country_id


def city_country_signal(sender, **kwargs):
    pre_save.connect(city_country, sender=sender)


def city_search_names(sender, instance, **kwargs):
    search_names = []

    country_names = [instance.country.name]
    if instance.country.alternate_names:
        country_names += instance.country.alternate_names.split(',')

    city_names = [instance.name]
    if instance.alternate_names:
        city_names += instance.alternate_names.split(',')

    if instance.region:
        region_names = [instance.region.name]
        if instance.region.alternate_names:
            region_names += instance.region.alternate_names.split(',')

    for city_name in city_names:
        for country_name in country_names:
            name = to_search(city_name + country_name)
            if name not in search_names:
                search_names.append(name)

            if instance.region_id:
                for region_name in region_names:
                    name = to_search(city_name + region_name + country_name)
                    if name not in search_names:
                        search_names.append(name)

    instance.search_names = ' '.join(search_names)


def city_search_names_signal(sender, **kwargs):
    pre_save.connect(city_search_names, sender=sender)
