from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import signals

from cities_light.models import Base, set_name_ascii
from cities_light.settings import *

import autoslug

class City(Base):
    slug = autoslug.AutoSlugField(populate_from='name_ascii', 
        unique_with=('country__name',))

    if ENABLE_SUBREGION:
        subregion = models.ForeignKey('subregion.subregion')
    elif ENABLE_REGION:
        region = models.ForeignKey('regions.region')
    else:
        country = models.ForeignKey('cities_light.country')

    class Meta:
        if ENABLE_SUBREGION:
            unique_together = (('subregion', 'name'),)
        elif ENABLE_REGION:
            unique_together = (('region', 'name'),)
        else:
            unique_together = (('country', 'name'),)
        verbose_name_plural = _(u'cities')
        ordering = ['name']
signals.pre_save.connect(set_name_ascii, sender=City)
