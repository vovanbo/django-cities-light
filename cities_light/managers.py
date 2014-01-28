# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.signals import class_prepared
from .signals import (set_name_ascii_signal, set_display_name_signal,
                      city_country_signal, city_search_names_signal
                      )


class RegionManager(models.Manager):

    """
    Manager for abstract Region class.
    Connect necessary signals to inherited models.
    """

    def contribute_to_class(self, model, name):
        class_prepared.connect(set_name_ascii_signal, sender=model.__class__)
        class_prepared.connect(set_display_name_signal, sender=model.__class__)
        return super(RegionManager, self).contribute_to_class(model, name)


class CityManager(models.Manager):

    """
    Manager for abstract City class.
    Connect necessary signals to inherited models.
    """

    def contribute_to_class(self, model, name):
        class_prepared.connect(set_name_ascii_signal, sender=model.__class__)
        class_prepared.connect(set_display_name_signal, sender=model.__class__)
        class_prepared.connect(city_country_signal, sender=model.__class__)
        class_prepared.connect(
            city_search_names_signal, sender=model.__class__)
        return super(CityManager, self).contribute_to_class(model, name)
