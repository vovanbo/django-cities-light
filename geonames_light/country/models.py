import unicodedata

from django.utils.encoding import force_unicode
from django.db.models import signals
from django.db import models
from django.template import defaultfilters
from django.utils.translation import ugettext_lazy as _

import autoslug

__all__ = ['Base', 'Country', 'CONTINENT_CHOICES']

CONTINENT_CHOICES = (
    ('OC', _(u'Oceania')),
    ('EU', _(u'Europe')),
    ('AF', _(u'Africa')),
    ('NA', _(u'North America')),
    ('AN', _(u'Antarctica')),
    ('SA', _(u'South America')),
    ('AS', _(u'Asia')),
)

class Country(Base):
    code2 = models.CharField(max_length=2, null=True, blank=True, unique=True)
    code3 = models.CharField(max_length=3, null=True, blank=True, unique=True)
    continent = models.CharField(max_length=2, db_index=True, choices=CONTINENT_CHOICES)
    tld = models.CharField(max_length=5, blank=True, db_index=True)
    
    class Meta:
        verbose_name_plural = _(u'countries')
        ordering = ['name']

    def __unicode__(self):
        return self.name
signals.pre_save.connect(set_name_ascii, sender=Country)
