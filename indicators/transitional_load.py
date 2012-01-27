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
        
        def open_xsl(self):
            import xlrd
            crosswalk_file = "Indicators by Release.xls"
            return xlrd.open_workbook(os.path.join(self.directory,crosswalk_file))
        
        def get_metadata(self):
            def do_get_metadata():
                book = self.open_xsl()
                sheet = book.sheet_by_index(0)
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
                return metadata
            do_get_metadata = memoize(do_get_metadata, get_metadata_cache, 0)
            return do_get_metadata()

        def get_files(self):
            def do_get_files():
                files = {}
                for path, subpaths, subfiles in os.walk(self.directory):
                    for filename in subfiles:
                        files[filename] = os.path.join(path, filename)
                return files
            do_get_files = memoize(do_get_files, get_files_cache, 0)
            return do_get_files()

        def get_key_field(self, table_name):
            def do_get_key_field(table_name):
                print 'in do_get_key_field for %s' % table_name
                files = self.get_files()
                for filename, path in files.iteritems():
                    if filename.startswith(table_name) and filename.endswith('csv'):
                        # assuming the first column is the key field
                        reader = csv.reader(open(path, 'rU'))
                        header = reader.next()
                        return header[0]
                print "WARNING: Couldn't find a key field for %s" % table_name
                return ''
            do_get_key_field = memoize(do_get_key_field, key_field_cache, 1)
            return do_get_key_field(table_name)
        
        def prep_indicator_definition(self, metadata):
            indicator = {}
            if metadata['indicator_group'] != '':
                indicator['name'] = metadata['indicator_group'].strip()
            else:
                indicator['name'] = metadata['element_name'].strip()
            indicator['display_name'] = metadata['display_name'].strip()
            indicator['short_definition'] = metadata['short_definition'].strip()
            indicator['long_definition'] = metadata['long_definition'].strip()
            indicator['file_name'] = metadata['file_name'].strip()
            if isinstance(metadata['min'], str) and metadata['min'] == '':
                indicator['min'] = None
            else:
                indicator['min'] = metadata['min']
            if isinstance(metadata['max'], str) and metadata['max'] == '':
                indicator['max'] = None
            else:
                indicator['max'] = metadata['max']
            indicator['data_type'] = metadata['data_type'].lower().strip()
            indicator['raw_tags'] = metadata['raw_tags'].strip()
            indicator['raw_datasources'] = metadata['datasources'].strip()
            indicator['unit'] = metadata['unit'].strip()
            indicator['purpose'] = metadata['purpose'].strip()
            
            return indicator

        
        def grab_xls_info(self):
            # pull indicators by release and store info from the excel sheet
            import xlrd
            ibr_file = "Indicators_by_Release.xls" #xlsx not supported?
            
            book = xlrd.open_workbook(os.path.join(self.directory, ibr_file))
            excel_data = {}
            for wave in range(0, book.nsheets): #assuming multiple sheets
                sheet = book.sheet_by_index(wave)
                for row_num in range(1, sheet.nrows):
                    #stores short and long definitions in a dict with indicator group as the key
                    ig = sheet.cell_value(row_num, 1)
                    ig += 'Indicator'
                    excel_data[ig] = map(safe_strip, sheet.row_values(row_num, start_colx=2, end_colx=4))
            return excel_data

        def create_indicator(self, indicator_def):
            return Indicator.objects.create(**indicator_def)
        
        def _load_metadata(self, indicator_list=None):
            from django.db.utils import IntegrityError
            seen_indicators = set() # to track which Indicators may be gone now
            created_indicators = set()
            updated_indicators = set()
            
            import copy
            metadata_to_import = [
                metadata for metadata in self.get_metadata() \
                if metadata['indicator_group'] != '' and metadata['display_name'] != '' \
                    and (indicator_list == None or metadata['indicator_group'] in indicator_list)]

            for metadata in metadata_to_import:
                indicator_def = self.prep_indicator_definition(metadata)
                try:
                    indicator = Indicator.objects.get(name=indicator_def['name'])
                    Indicator.objects.filter(id=indicator.id).update(**indicator_def)
                    updated_indicators.add(indicator)
                except Indicator.DoesNotExist:
                    indicator = self.create_indicator(indicator_def)
                    created_indicators.add(indicator)
                seen_indicators.add(indicator)
                try:
                    indicator.assign_datasources()
                except:
                    print "Error assigning datasource for %s" % indicator.name
            
            
            print 'Indicators Updated'
            print '__________________'
            for indicator in updated_indicators:
                print indicator.name

            print '\n\nIndicators not seen'
            print '-------------------'
            if indicator_list:
                all_indicators =  Indicator.objects.filter(name__in=indicator_list)
            else:
                all_indicators = Indicator.objects.all()
            for indicator in all_indicators:
                if indicator not in seen_indicators:
                    print indicator.name

            print '\n\nNewly Created Indicators'
            print '-------------------'
            for indicator in created_indicators:
                print indicator.name
        
        @transaction.commit_manually
        def load_metadata(self):
            try:
                self._load_metadata()
                transaction.commit()
            except:
                print "Caught an exception:", sys.exc_info()[0]
                transaction.rollback()
                raise

        def synchronize_pregen_parts_from_IBR(self):
            IndicatorPregenPart.objects.all().delete()
            for row in [row for row in self.get_metadata() if row['element_name'] != '']:
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
    pass
