import os
import csv
import sys

from django.utils.functional import memoize
from django.db import transaction

from core.models import *
from core.indicators import *
from indicators.models import *
from indicators.tasks import insert_dynamic_data
from indicators.util import clean_value, get_dynamic_indicator_def, new_generate_indicator_data

key_field_cache = {}
get_files_cache = {}
get_metadata_cache = {}

def safe_strip(val):
    if isinstance(val, str) or isinstance(val, unicode):
        return val.strip()
    return val

class DataImporter(object):
    def __init__(self):
        self.directory = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            'data'
        ))
    
    def get_files(self):
        def do_get_files():
            files = {}
            for path, subpaths, subfiles in os.walk(self.directory):
                for filename in subfiles:
                    files[filename] = os.path.join(path, filename)
            return files
        do_get_files = memoize(do_get_files, get_files_cache, 0)
        return do_get_files()

    def get_key_field(self, pregen_part):
        def do_get_key_field(pregen_part):
            print 'in do_get_key_field for %s' % pregen_part
            if pregen_part.key_column:
                return pregen_part.key_column
            file_path = self.find_file(pregen_part)
            reader = csv.reader(open(file_path, 'rU'))
            header = reader.next()
            return header[0]
        do_get_key_field = memoize(do_get_key_field, key_field_cache, 1)
        return do_get_key_field(pregen_part)
    
    def find_file(self, pregen_part):
        file_path = None
        for file, path in self.get_files().iteritems():
            if file.lower() == pregen_part.file_name.lower() or file.lower() == pregen_part.file_name.lower() + '.csv':
                file_path = path
        return file_path
        
    def update_metadata(self):
        for indicator in Indicator.objects.all():
            indicator.calculate_metadata()
            indicator.save()
    
    def create_indicator(self, indicator_def):
        return Indicator.objects.create(**indicator_def)
    
    def insert_pregen_data(self, indicator):
        """ Find all rows for the indicator, and insert each """
        count = 0
        for pregen_part in indicator.indicatorpregenpart_set.all():
            file_path = self.find_file(pregen_part)
            if not file_path:
                print "WARNING: Couldn't find a file for %s (searched for %s)" % (
                    indicator.name, pregen_part.file_name)
                return
            
            reader = csv.DictReader(open(file_path, 'rU'))
            found_column = False
            key_field = self.get_key_field(pregen_part)
            for row in reader:
                if row.has_key(pregen_part.column_name):
                    found_column = True
                    data_type = pregen_part.indicator.data_type
                    if not data_type or data_type == '':
                        # this will trigger auto-detection
                        data_type = None
                    print data_type
                    indicator_data = generate_indicator_data(
                        indicator,
                        pregen_part.key_type,
                        row[key_field],
                        pregen_part.time_type,
                        str(pregen_part.time_value).split('.')[0],
                        row[pregen_part.column_name],
                        data_type=indicator.data_type
                    )
                    indicator_data.save(force_insert=True)
                    count += 1
            if not found_column:
                print "WARNING: Couldn't find a column for %s in one or more rows" % indicator.name
        print "Inserted %d values for %s" % (count, indicator)
        return count
     
    def _run_all(self, indicator_list=None, ignore_celery=False):
        from django.db.utils import IntegrityError
        
        import copy
        
        if indicator_list:
            indicators_to_import = Indicator.objects.filter(name__in=indicator_list)
        else:
            indicators_to_import = Indicator.objects.all()


        for indicator in indicators_to_import:
            IndicatorData.objects.filter(indicator=indicator).delete()
            
            print 'Inserting pre-gen data for %s...' % indicator
            if self.insert_pregen_data(indicator) > 0:
                indicator.update_metadata()
                indicator.save()
            print 'Inserting dynamic data for %s...' % indicator
            if not ignore_celery:
                insert_dynamic_data.delay(indicator.id)
            else:
                insert_dynamic_data(indicator.id)

    @transaction.commit_manually
    def run_all(self, *args, **kwargs):
        try:
            self._run_all(*args, **kwargs)
            transaction.commit()
        except:
            print "Caught an exception:", sys.exc_info()[0]
            transaction.rollback()
            raise


def synchronize_pregen_parts_from_IBR(full_path):
    import xlrd
    crosswalk_file = "Indicators by Release.xls"
    IBR = xlrd.open_workbook(full_path)
    sheet = IBR.sheet_by_index(0)
    attr_map = [
        'element_name',
        'indicator_group',
        'display_name',
        'short_definition',
        'long_definition',
        'hub_programming',
        'query_level',
        '',
        'file_name',
        'key_type',
        'min_threshold',
        'min',
        'max',
        '',
        '',
        '',
        'universe',
        'limitations',
        '',
        'range_params',
        'routine_use',
        'datasources',
        'subagency',
        '',
        '',
        '',
        'time_key',
        'time_parameters_available',
        'time_type',
        'update_frequency',
        'purpose',
        '',
        '',
        '',
        '',
        'raw_tags',
        '',
        'data_type',
        'unit',
        '',
        '',
        ''
    ]
    metadata = []
    for row_num in range(1, sheet.nrows):
        row = map(safe_strip, sheet.row_values(row_num))
        metadata_dict = dict(zip(attr_map, row))
        metadata.append(metadata_dict)
    for row in [row for row in metadata if row['element_name'] != '']:
        try:
            indicator = Indicator.objects.get(name=row['indicator_group'])
            IndicatorPregenPart.objects.get_or_create(
                indicator = indicator,
                file_name = row['file_name'],
                column_name = row['element_name'],
                key_type = row['key_type'],
                time_type = row['time_type'],
                time_value = row['time_key']
            )
        except Indicator.DoesNotExist:
            print "Couldn't find %s" % row['indicator_group']
            continue

def assign_datasource_to_existing():
    for indicator_name, IndicatorDef in indicator_list():
        try:
            i = Indicator.objects.get(name=indicator_name)
            i_def = IndicatorDef()
            for data_source in i_def.data_sources():
                i.datasources.add(DataSource.objects.get(
                    short=data_source))
                i.save()
        except Indicator.DoesNotExist:
            pass

def test_celery_performance(indicator_def):
    """ Run an indicator three ways:

    1. By itself, without celery
    2. By itself, through celery
    3. By itself 4 times

    Calculate the slowdown incurred by each method, with #1 as a reference
    """
    import datetime
    from indicators.tasks import create_indicator_data
    i = indicator_def()
    
    start1 = datetime.datetime.now()
    i.create()
    end1 = datetime.datetime.now()

    start2 = datetime.datetime.now()
    result = create_indicator_data.delay(i)
    result.wait()
    end2 = datetime.datetime.now()
    
    start3 = datetime.datetime.now()
    create_indicator_data.delay(i,start_time=start3)
    create_indicator_data.delay(i,start_time=start3)
    create_indicator_data.delay(i,start_time=start3)
    create_indicator_data.delay(i,start_time=start3)
    print "no celery, single indicator: %d" % (end1 - start1).seconds
    print "celery, single indicator: %d" % (end2 - start2).seconds
