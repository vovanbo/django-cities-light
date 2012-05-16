import os.path

from django.conf import settings

from appconf import AppConf

class GeonamesLightConf(AppConf):
    COUNTRY_SOURCES = [
        'http://download.geonames.org/export/dump/countryInfo.txt',
    ]
    
    REGION_SOURCES = [
        'http://download.geonames.org/export/dump/admin1CodesASCII.txt',
    ]
    REGION_ENABLE = 'geonames_light.region' in settings.INSTALLED_APPS
    
    SUBREGION_SOURCES = [
        'http://download.geonames.org/export/dump/admin2Codes.txt',
    ]
    SUBREGION_ENABLE = 'geonames_light.subregion' in settings.INSTALLED_APPS

    CITY_SOURCES = [
        'http://download.geonames.org/export/dump/cities15000.zip',
    ]
    CITY_ENABLE = 'geonames_light.city' in settings.INSTALLED_APPS
    
    
    DISTRICT_SOURCES = [
        'http://download.geonames.org/export/dump/hierarchy.zip',
    ]
    DISTRICT_ENABLE = 'geonames_light.district' in settings.INSTALLED_APPS
    
    DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), 'data')))
    
    class Meta:
        proxy = True
        prefix = 'geonames_light'
