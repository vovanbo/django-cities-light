from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import signals

from cities_light.models import Base, set_name_ascii

import autoslug

class Region(Base):
    slug = autoslug.AutoSlugField(populate_from='name_ascii', 
        unique_with=('country__name',))
    
    country = models.ForeignKey('cities_light.country')
    
    class Meta:
        unique_together = (('country', 'name'),)
signals.pre_save.connect(set_name_ascii, sender=Region)
