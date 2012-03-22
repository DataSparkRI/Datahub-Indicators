try:
    import os
    import csv
    import sys

    from django.utils.functional import memoize
    from django.db import transaction

    from core.models import *
    from core.indicators import *
    from indicators.models import *
    from indicators.tasks import insert_dynamic_data
    from indicators.util import clean_value, get_dynamic_indicator_def, generate_indicator_data

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
            if not indicator_list:
                indicator_list = Indicator.objects.all()
            
            IndicatorData.objects.filter(indicator__in=indicator_list).delete()

            # instead of using mark_load_pending, which should be used in the
            # general case, do a bulk update here for speed
            indicator_list.update(load_pending=True)

            for indicator in indicator_list.iterator():
                print 'Inserting pre-gen data for %s...' % indicator
                if self.insert_pregen_data(indicator) > 0:
                    indicator.mark_load_complete()
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
        
        @transaction.commit_manually
        def run_pregen_only(self, *args, **kwargs):
            try:
                kwargs['indicator_list'] = Indicator.objects.exclude(file_name='')
                self._run_all(*args, **kwargs)
                transaction.commit()
            except:
                print "Caught an exception:", sys.exc_info()[0]
                transaction.rollback()
                raise

        @transaction.commit_manually
        def run_dynamic_only(self, *args, **kwargs):
            try:
                kwargs['indicator_list'] = Indicator.objects.filter(file_name='')
                self._run_all(*args, **kwargs)
                transaction.commit()
            except:
                print "Caught an exception:", sys.exc_info()[0]
                transaction.rollback()
                raise

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
except ImportError:
    import re
    from xml.sax.saxutils import quoteattr

    from django.db import IntegrityError  
    from django.contrib.contenttypes.models import ContentType

    from indicators.models import Indicator, IndicatorData
    from weave.models import AttributeColumn, DataFilter

    class WeaveExporter(object):
        def time_translations(self, input):
            if not input:
                return None
            
            # school years
            sy_re = re.compile(r'School Year [0-9]{2}(?P<start_year>[0-9]{2})-[0-9]{2}(?P<end_year>[0-9]{2})')
            
            sy_match = sy_re.match(input)
            if sy_match:
                return 'SY%s-%s' % (sy_match.group('start_year'), 
                    sy_match.group('end_year'))

            # Calendar Years
            cy_re = re.compile(r'Calendar Year (?P<year>[0-9]{4})')

            cy_match = cy_re.match(input)
            if cy_match:
                return '%s' % cy_match.group('year')
            
            # future conversions...

            return input

        def run(self, indicator_list_qs=Indicator.objects.all()):
            from django.conf import settings
            assert hasattr(settings, 'WEAVE')
            connection = settings.WEAVE.get('CONNECTION', '')
            indicator_ctype = ContentType.objects.get(app_label='indicators', model='indicator')
                    
            # create AttributeColumns
            for indicator in indicator_list_qs.iterator():
                AttributeColumn.objects.filter(content_type=indicator_ctype,object_id=indicator.id).delete()
                for indicator_data in indicator.indicatordata_set.values(
                        'key_unit_type', 'time_key', 'data_type', 'time_type').distinct():
                    try:
                        if indicator.data_type.upper() == 'NUMERIC':
                            data_type = 'number'
                            sql_type = 'numeric'
                        else:
                            data_type = 'text'
                            sql_type = 'string'

                        if indicator_data['time_type'] and indicator_data['time_key']:
                            time = "%s %s" % (indicator_data['time_type'], indicator_data['time_key'])
                        else:
                            time = indicator_data['time_key']
                        if not indicator_data['time_key'] or indicator_data['time_key'].strip() == '':
                            time_sql = 'indicators_indicatordata."time_key" is null'
                        else:
                            time_sql = 'indicators_indicatordata."time_key" = \'%s\' and indicators_indicatordata."time_type" = \'%s\'' % (indicator_data['time_key'], indicator_data['time_type'])
                        data_with_keys_query = """
                            SELECT key_value, %s from indicators_indicatordata WHERE indicators_indicatordata."indicator_id" = '%s' AND indicators_indicatordata."key_unit_type" like '%s' AND (%s)
                        """ % (
                            sql_type,
                            indicator.id,
                            indicator_data['key_unit_type'],
                            time_sql,
                        )
                        
                        attribute_column, created = AttributeColumn.objects.get_or_create(
                            content_type=indicator_ctype,
                            object_id=indicator.id,
                            connection=connection,
                            dataTable=indicator_data['key_unit_type'],
                            name=indicator.name,
                            display_name=indicator.weave_name(),
                            keyType=indicator_data['key_unit_type'],
                            year=self.time_translations(time) or '',
                            dataType=data_type,
                            sqlQuery=data_with_keys_query.strip(),
                            min=str(indicator.min) if indicator.min else '',
                            max=str(indicator.max) if indicator.max else ''
                        )
                    except IntegrityError:
                        print "Duplicate AttributeColumn detected for (%s, %s, %s). AttributeColumn NOT created." % (
                            indicator.name,
                            indicator.key_unit_type,
                            indicator_data['time_key']
                        )
            """    
            for data_table in DataTable.objects.all():
                key_unit_type = KeyUnitType.objects.get(name=data_table.key_unit_type)
                for data_filter in DataFilter.objects.filter(key_unit_type=key_unit_type):
                    filtered_data_table, created = DataTable.objects.get_or_create_for_filter(data_filter)
                    for attribute_column in data_table.attributecolumn_set.all():
                        attribute_column, created = AttributeColumn.objects.get_or_create(
                            content_type=attribute_column.content_type,
                            object_id=attribute_column.object_id,
                            data_table=filtered_data_table,
                            name=attribute_column.name,
                            display_name=attribute_column.display_name,
                            category=None,
                            key_unit_type=attribute_column.key_unit_type,
                            year=attribute_column.year,
                            data_type=attribute_column.data_type,
                            data_with_keys_query=data_filter.modify_query(attribute_column.data_with_keys_query),
                            min=attribute_column.min,
                            max=attribute_column.max
                        )
                             
            """

