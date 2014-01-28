# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import datetime
import time
import os.path
import logging
import optparse
import sys
import progressbar

from django.db import transaction, reset_queries, IntegrityError
from django.db.models import get_model
from django.core.management.base import BaseCommand
from django.utils.encoding import force_text

from ...exceptions import InvalidItems
from ...signals import region_items_pre_import, city_items_pre_import
from ...geonames import Geonames
from ...utils import convert_bytes
from ...settings import (
    TRANSLATION_LANGUAGES, SOURCES, DATA_DIR,
    TRANSLATION_SOURCES, CITY_SOURCES, REGION_SOURCES
    )

if sys.platform != 'win32':
    import resource

try:
    import cPickle as pickle
except ImportError:
    import pickle

Country = get_model('address', 'Country')
Region = get_model('address', 'Region')
City = get_model('address', 'City')


class MemoryUsageWidget(progressbar.Widget):
    def update(self, pbar):
        if sys.platform != 'win32':
            return '%s' % convert_bytes(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            )
        return '?? kB'


class Command(BaseCommand):
    args = '''
[--force-all] [--force-import-all \\]
                              [--force-import countries.txt cities.txt ...] \\
                              [--force countries.txt cities.txt ...]
    '''.strip()
    help = '''
Download all files in CITIES_LIGHT_COUNTRY_SOURCES if they were updated or if
--force-all option was used.
Import country data if they were downloaded or if --force-import-all was used.

Same goes for CITIES_LIGHT_CITY_SOURCES.

It is possible to force the download of some files which have not been updated
on the server:

    manage.py --force cities15000 --force countryInfo

It is possible to force the import of files which weren't downloaded using the
--force-import option:

    manage.py --force-import cities15000 --force-import country
    '''.strip()

    logger = logging.getLogger('cities_light')

    option_list = BaseCommand.option_list + (
        optparse.make_option('--force-import-all', action='store_true',
                             default=False,
                             help='Import even if files are up-to-date.'
                             ),
        optparse.make_option('--force-all', action='store_true', default=False,
                             help='Download and import if files are up-to-date.'
                             ),
        optparse.make_option('--force-import', action='append', default=[],
                             help='Import even if files matching files are up-to-date'
                             ),
        optparse.make_option('--force', action='append', default=[],
                             help='Download and import even if matching files are up-to-date'
                             ),
        optparse.make_option('--noinsert', action='store_true',
                             default=False,
                             help='Update existing data only'
                             ),
        optparse.make_option('--hack-translations', action='store_true',
                             default=False,
                             help='Set this if you intend to import translations a lot'
                             ),
    )

    def _travis(self):
        if not os.environ.get('TRAVIS', False):
            return

        now = time.time()
        last_output = getattr(self, '_travis_last_output', None)

        if last_output is None or now - last_output >= 530:
            print('Do not kill me !')
            self._travis_last_output = now

    @transaction.commit_on_success
    def handle(self, *args, **options):
        if not os.path.exists(DATA_DIR):
            self.logger.info('Creating %s' % DATA_DIR)
            os.mkdir(DATA_DIR)

        install_file_path = os.path.join(DATA_DIR, 'install_datetime')
        translation_hack_path = os.path.join(DATA_DIR, 'translation_hack')

        self.noinsert = options.get('noinsert', False)
        self.widgets = [
            'RAM used: ',
            MemoryUsageWidget(),
            ' ',
            progressbar.ETA(),
            ' Done: ',
            progressbar.Percentage(),
            progressbar.Bar(),
        ]

        for url in SOURCES:
            destination_file_name = url.split('/')[-1]

            force = options.get('force_all', False)
            if not force:
                for f in options['force']:
                    if f in destination_file_name or f in url:
                        force = True

            geonames = Geonames(url, force=force)
            downloaded = geonames.downloaded

            force_import = options.get('force_import_all', False)

            if not force_import:
                for f in options['force_import']:
                    if f in destination_file_name or f in url:
                        force_import = True

            if not os.path.exists(install_file_path):
                self.logger.info('Forced import of %s because data do not seem'
                                 ' to have installed successfuly yet,'
                                 ' note that this is'
                                 ' equivalent to --force-import-all.' %
                                 destination_file_name)
                force_import = True

            if downloaded or force_import:
                self.logger.info('Importing %s' % destination_file_name)

                if url in TRANSLATION_SOURCES:
                    if options.get('hack_translations', False):
                        if os.path.exists(translation_hack_path):
                            self.logger.debug(
                                'Using translation parsed data: %s' %
                                translation_hack_path)
                            continue

                i = 0
                progress = progressbar.ProgressBar(
                    maxval=geonames.num_lines(),
                    widgets=self.widgets).start()

                for items in geonames.parse():
                    if url in CITY_SOURCES:
                        self.city_import(items)
                    elif url in REGION_SOURCES:
                        self.region_import(items)
                    # elif url in COUNTRY_SOURCES:
                    #     self.country_import(items)
                    elif url in TRANSLATION_SOURCES:
                        self.translation_parse(items)

                    reset_queries()

                    i += 1
                    progress.update(i)

                    self._travis()

                progress.finish()

                if url in TRANSLATION_SOURCES and options.get(
                        'hack_translations', False):
                    with open(translation_hack_path, 'w+') as f:
                        pickle.dump(self.translation_data, f)

        if options.get('hack_translations', False):
            with open(translation_hack_path, 'r') as f:
                self.translation_data = pickle.load(f)

        self.logger.info('Importing parsed translation in the database')
        self.translation_import()

        with open(install_file_path, 'wb+') as f:
            pickle.dump(datetime.datetime.now(), f)

    def _get_country(self, iso_3166_1_a2):
        '''
        Simple lazy identity map for iso_3166_1_a2->country
        '''
        if not hasattr(self, '_country_codes'):
            self._country_codes = {}

        if iso_3166_1_a2 not in self._country_codes.keys():
            self._country_codes[iso_3166_1_a2] = Country.objects.get(
                iso_3166_1_a2=iso_3166_1_a2).pk

        return self._country_codes[iso_3166_1_a2]

    def _get_region(self, iso_3166_1_a2, region_id):
        '''
        Simple lazy identity map for (iso_3166_1_a2, region_id)->region
        '''
        if not hasattr(self, '_region_codes'):
            self._region_codes = {}

        country_id = self._get_country(iso_3166_1_a2)
        if country_id not in self._region_codes:
            self._region_codes[country_id] = {}

        if region_id not in self._region_codes[country_id]:
            self._region_codes[country_id][region_id] = Region.objects.get(
                country_id=country_id, geoname_code=region_id).pk

        return self._region_codes[country_id][region_id]

    # def country_import(self, items):
    #     try:
    #         country = Country.objects.get(code2=items[0])
    #     except Country.DoesNotExist:
    #         if self.noinsert:
    #             return
    #         country = Country(code2=items[0])

    #     country.name = force_text(items[4])
    #     country.code3 = items[1]
    #     country.continent = items[8]
    # country.tld = items[9][1:]  # strip the leading dot
    #     if items[16]:
    #         country.geoname_id = items[16]

    #     self.save(country)

    def region_import(self, items):
        try:
            region_items_pre_import.send(sender=self, items=items)
        except InvalidItems:
            return

        items = [force_text(x) for x in items]

        (code,
         name,
         name_ascii,
         geoname_id
         ) = (items[i] for i in range(4))

        name = name if name else name_ascii
        iso_3166_1_a2, geoname_code = code.split('.')
        country = self._get_country(iso_3166_1_a2)

        if geoname_id:
            kwargs = dict(geoname_id=geoname_id)
        else:
            kwargs = dict(name=name, country_id=country)

        try:
            region = Region.objects.get(**kwargs)
        except Region.DoesNotExist:
            if self.noinsert:
                return
            region = Region(**kwargs)

        if not region.name:
            region.name = name

        if not region.country_id:
            region.country_id = country

        if not region.geoname_code:
            region.geoname_code = geoname_code

        if not region.name_ascii:
            region.name_ascii = name_ascii

        region.geoname_id = geoname_id
        self.save(region)

    def city_import(self, items):
        try:
            city_items_pre_import.send(sender=self, items=items)
        except InvalidItems:
            return

        # Docs here: http://download.geonames.org/export/dump/
        # Like a main 'geoname' table
        (geoname_id,
         name,
         name_ascii,
         alternate_names,
         latitude,
         longitude,
         feature_class,
         feature_code,
         country_code,
         cc2,
         admin1_code,
         admin2_code,
         admin3_code,
         admin4_code,
         population,
         elevation,
         dem,
         timezone,
         modification_date
         ) = (items[i] for i in range(19))

        # try:
        #     country = self._get_country(items[8])
        # except Country.DoesNotExist:
        #     if self.noinsert:
        #         return
        #     else:
        #         raise

        try:
            kwargs = dict(name=force_text(name),
                          country_id=self._get_country(country_code))
        except Country.DoesNotExist:
            if self.noinsert:
                return
            else:
                raise

        try:
            city = City.objects.get(**kwargs)
        except City.DoesNotExist:
            try:
                city = City.objects.get(geoname_id=geoname_id)
                city.name = force_text(name)
                city.country_id = self._get_country(country_code)
            except City.DoesNotExist:
                if self.noinsert:
                    return
                city = City(**kwargs)

        save = False

        if not city.region_id:
            try:
                city.region_id = self._get_region(country_code, admin1_code)
            except Region.DoesNotExist:
                pass
            else:
                save = True

        if not city.name_ascii:
            # useful for cities with chinese names
            city.name_ascii = name_ascii
            save = True

        if not city.latitude:
            city.latitude = latitude
            save = True

        if not city.longitude:
            city.longitude = longitude
            save = True

        if not city.population:
            city.population = population
            save = True

        if not city.feature_code:
            city.feature_code = feature_code
            save = True

        if not TRANSLATION_SOURCES and not city.alternate_names:
            city.alternate_names = force_text(alternate_names)
            save = True

        if not city.geoname_id:
            # city may have been added manually
            city.geoname_id = geoname_id
            save = True

        if save:
            self.save(city)

    def translation_parse(self, items):
        if not hasattr(self, 'translation_data'):
            # self.country_ids = Country.objects.values_list('geoname_id',
            #     flat=True)
            self.region_ids = Region.objects.values_list(
                'geoname_id', flat=True)
            self.city_ids = City.objects.values_list('geoname_id', flat=True)

            self.translation_data = {
                # Country: {},
                Region: {},
                City: {},
            }

        (alternate_name_id,
         geoname_id,
         iso_language,
         alternate_name,
         is_preferred_name,
         is_short_name,
         is_colloquial,
         is_historic
         ) = (items[i] for i in range(8))

        if len(items) > 5 and is_preferred_name is None:
        # avoid shortnames, colloquial, and historic
            return

        if iso_language not in TRANSLATION_LANGUAGES:
            return

        # arg optimisation code kills me !!!
        geoname_id = int(geoname_id)

        # if items[1] in self.country_ids:
        #     model_class = Country
        if geoname_id in self.region_ids:
            model_class = Region
        elif geoname_id in self.city_ids:
            model_class = City
        else:
            return

        if geoname_id not in self.translation_data[model_class]:
            self.translation_data[model_class][geoname_id] = {}

        if iso_language not in self.translation_data[model_class][geoname_id]:
            self.translation_data[model_class][geoname_id][iso_language] = []

        name_data = {
            'name': alternate_name,
            'is_preferred': bool(is_preferred_name),
            'is_short': bool(is_short_name)
        }
        self.translation_data[model_class][geoname_id][iso_language].append(name_data)

    def translation_import(self):
        data = getattr(self, 'translation_data', None)

        if not data:
            return

        max = 0
        for model_class, model_class_data in data.items():
            max += len(model_class_data.keys())

        i = 0
        progress = progressbar.ProgressBar(maxval=max,
                                           widgets=self.widgets).start()

        for model_class, model_class_data in data.items():

            for geoname_id, geoname_data in model_class_data.items():
                try:
                    model = model_class.objects.get(geoname_id=geoname_id)
                except model_class.DoesNotExist:
                    continue
                save = False

                if not model.alternate_names:
                    alternate_names = []
                else:
                    alternate_names = model.alternate_names.split(',')

                for lang, names_data in geoname_data.items():
                    if lang == 'post':
                        # we might want to save the postal codes somewhere
                        # here's where it will all start ...
                        continue

                    for name_data in names_data:
                        name = force_text(name_data['name'])
                        if name == model.name:
                            continue

                        if name not in alternate_names:
                            alternate_names.append(name)

                    if lang == TRANSLATION_LANGUAGES[0]:
                        selected = None
                        for idx, name_data in enumerate(names_data):
                            if name_data['is_preferred'] and not name_data['is_short']:
                                selected = idx
                                break
                            elif name_data['is_preferred'] and name_data['is_short']:
                                selected = idx
                                continue
                            elif selected is None:
                                selected = idx
                        if selected is not None:
                            model.name = force_text(names_data[selected]['name'].title())
                            save = True

                alternate_names = u','.join(alternate_names)
                if model.alternate_names != alternate_names:
                    model.alternate_names = alternate_names
                    save = True

                if save:
                    model.save()

                i += 1
                progress.update(i)

        progress.finish()

    def save(self, model):
        sid = transaction.savepoint()

        try:
            model.save()
        except IntegrityError as e:
            self.logger.warning('Saving %s failed: %s' % (model, e))
            transaction.savepoint_rollback(sid)
        else:
            transaction.savepoint_commit(sid)
