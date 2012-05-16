import unicodedata

from django.utils.encoding import force_unicode

def set_name_ascii(sender, instance=None, **kwargs):
    if isinstance(instance.name, str):
        instance.name = force_unicode(instance.name)

    instance.name_ascii = unicodedata.normalize('NFKD', instance.name
        ).encode('ascii', 'ignore')

class Base(models.Model):
    name = models.CharField(max_length=200, unique=True)
    name_ascii = models.CharField(max_length=200, db_index=True)
    geoname_id = models.IntegerField(null=True, blank=True)

    class Meta:
        abstract = True


