# -*- coding: utf-8 -*-

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
import autoslug

from .fields import ToSearchTextField
from .managers import RegionManager, CityManager
from .settings import INDEX_SEARCH_NAMES


CONTINENT_CHOICES = (
    ('OC', _('Oceania')),
    ('EU', _('Europe')),
    ('AF', _('Africa')),
    ('NA', _('North America')),
    ('AN', _('Antarctica')),
    ('SA', _('South America')),
    ('AS', _('Asia')),
)


@python_2_unicode_compatible
class Base(models.Model):
    """
    Base model with boilerplate for all models.
    """

    name_ascii = models.CharField(max_length=200, blank=True, db_index=True)
    slug = autoslug.AutoSlugField(populate_from='name_ascii')
    geoname_id = models.IntegerField(null=True, blank=True, unique=True)
    alternate_names = models.TextField(null=True, blank=True, default='')

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        display_name = getattr(self, 'display_name', None)
        if display_name:
            return display_name
        return self.name


# class Country(Base):
#     """
#     Country model.
#     """

#     name = models.CharField(max_length=200, unique=True)

#     code2 = models.CharField(max_length=2, null=True, blank=True, unique=True)
#     code3 = models.CharField(max_length=3, null=True, blank=True, unique=True)
#     continent = models.CharField(max_length=2, db_index=True,
#                                  choices=CONTINENT_CHOICES)
#     tld = models.CharField(max_length=5, blank=True, db_index=True)

#     class Meta(Base.Meta):
#         verbose_name_plural = _('countries')

# signals.pre_save.connect(set_name_ascii, sender=Country)


class AbstractRegion(Base):
    """
    Region/State model.
    """
    name = models.CharField(max_length=200, db_index=True)
    display_name = models.CharField(max_length=200)
    geoname_code = models.CharField(max_length=50, null=True, blank=True,
                                    db_index=True)
    country = models.ForeignKey('address.Country')

    objects = RegionManager()

    class Meta(Base.Meta):
        abstract = True
        unique_together = (('country', 'name'), )
        verbose_name = _('region/state')
        verbose_name_plural = _('regions/states')

    def get_display_name(self):
        return '%s, %s' % (self.name, self.country.printable_name)


class AbstractCity(Base):
    """
    Abstract City model.
    """
    name = models.CharField(max_length=200, db_index=True)
    display_name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=8, decimal_places=5,
                                   null=True, blank=True)
    longitude = models.DecimalField(max_digits=8, decimal_places=5,
                                    null=True, blank=True)
    region = models.ForeignKey('address.Region', blank=True, null=True)
    country = models.ForeignKey('address.Country')
    population = models.BigIntegerField(null=True, blank=True, db_index=True)
    feature_code = models.CharField(max_length=10, null=True, blank=True,
                                    db_index=True)
    search_names = ToSearchTextField(max_length=4000,
                                     db_index=INDEX_SEARCH_NAMES,
                                     blank=True, default='')

    objects = CityManager()

    class Meta(Base.Meta):
        abstract = True
        unique_together = (('region', 'name_ascii'),)
        verbose_name_plural = _('cities')

    def get_display_name(self):
        if self.region_id:
            return '%s, %s, %s' % (self.name, self.region.name,
                                   self.country.printable_name)
        else:
            return '%s, %s' % (self.name, self.country.name)
