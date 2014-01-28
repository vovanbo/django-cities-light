# -*- coding: utf-8 -*-

from django.db import models
from .utils import to_search


class ToSearchTextField(models.TextField):
    """
    Trivial TextField subclass that passes values through to_search
    automatically.
    """

    def get_prep_lookup(self, lookup_type, value):
        """
        Return the value passed through to_search().
        """
        value = super(ToSearchTextField, self).get_prep_lookup(
            lookup_type, value)
        return to_search(value)

    def south_field_triple(self):
        """
        Returns a suitable description of this field for South.
        """
        from south.modelsinspector import introspector
        field_class = self.__class__.__module__ + "." + self.__class__.__name__
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)
