import os
import csv
import sys

from django.utils.functional import memoize
from django.db import transaction

from core.models import *
from core.indicators import *
from indicators.models import *

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

    
    def clean_value(self, val):
        if hasattr(val, 'strip') and callable(val.strip):
            val = val.strip()
            val = val.replace("%","")
            val = val.replace("#DIV/0!", '')
            val = val.replace("#NULL!", '')
        return val

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
    
    def new_generate_indicator_data(self, indicator, key_type, key_value, 
            time_type, time_key, value, data_type=None):
        from webportal.indicators.models import IndicatorData
        import datahub.indicators.conversion as conversion
        indicator_data_kwargs = {}
        
        value = self.clean_value(value)
        if data_type and data_type.lower() == 'text':
            data_type = 'text'
        elif data_type and data_type.lower() == 'numeric':
            data_type = 'numeric'
        else:
            try:
                float(value)
                data_type = 'numeric'
            except ValueError:
                data_type = 'text'
        indicator_data_kwargs['data_type'] = data_type
        
        if data_type == 'text':
            indicator_data_kwargs['string'] = value
        
        if data_type == 'numeric':
            if value == '':
                value = None
            indicator_data_kwargs['numeric'] = value
        
        indicator_data_kwargs['key_unit_type'] = key_type
        
        if key_type.upper() == 'SCHOOL':
            indicator_data_kwargs['key_value'] = key_value.rjust(5,'0')
        elif key_type.upper() == 'DISTRICT':
            indicator_data_kwargs['key_value'] = key_value.rjust(2,'0')
        else:
            indicator_data_kwargs['key_value'] = key_value
        
        indicator_data_kwargs['time_type'] = time_type
        indicator_data_kwargs['time_key'] = time_key
        indicator_data_kwargs['indicator'] = indicator
        return IndicatorData(**indicator_data_kwargs)
            
    def generate_indicator_data(self, metadata, row):
        from webportal.indicators.models import IndicatorData
        import datahub.indicators.conversion as conversion
        value = row[metadata['element_name']]
        key_field = self.get_key_field(metadata['file_name'])
        indicator_data_kwargs = {
            'data_type': metadata['data_type'].lower()
        }
        
        value = self.clean_value(value)
        
        resolved_type = None
        if metadata['data_type'].lower() == 'text':
            resolved_type = 'text'
        elif metadata['data_type'].lower() == 'numeric':
            resolved_type = 'numeric'
        else:
            try:
                float(value)
                resolved_type = 'numeric'
            except ValueError:
                resolved_type = 'text'
        indicator_data_kwargs['data_type'] = resolved_type
        
        if indicator_data_kwargs['data_type'] == 'text':
            indicator_data_kwargs['string'] = value
        
        if indicator_data_kwargs['data_type'] == 'numeric':
            if value == '':
                value = None
            indicator_data_kwargs['numeric'] = value
        
        indicator_data_kwargs['key_unit_type'] = metadata['key_type']
        if metadata['key_type'].upper() == 'SCHOOL':
            indicator_data_kwargs['key_value'] = row[key_field].rjust(5,'0')
        elif metadata['key_type'].upper() == 'DISTRICT':
            indicator_data_kwargs['key_value'] = row[key_field].rjust(2,'0')
        else:
            indicator_data_kwargs['key_value'] = row[key_field]
        
        indicator_data_kwargs['time_type'] = metadata['time_type']
        indicator_data_kwargs['time_key'] = str(metadata['time_key']).split('.')[0]
        return IndicatorData(**indicator_data_kwargs)

    def find_file(self, metadata):
        file_path = None
        for file, path in self.get_files().iteritems():
            if file.lower() == metadata['file_name'].lower() or file.lower() == metadata['file_name'].lower() + '.csv':
                file_path = path
        return file_path
        
    @transaction.commit_manually
    def run_all(self):
        try:
            self._run_all()
            transaction.commit()
        except:
            print "Caught an exception:", sys.exc_info()[0]
            transaction.rollback()
            raise

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
        if indicator['data_type'] == 'text':
            indicator['data_type'] = 'string'
        if indicator['data_type'] == '':
            indicator['data_type'] = 'numeric'
        indicator['raw_tags'] = metadata['raw_tags'].strip()
        indicator['unit'] = metadata['unit'].strip()
        indicator['purpose'] = metadata['purpose'].strip()
        
        return indicator

    def check_metadata(self):
        counts = {}
        for metadata in self.get_metadata():
            idef = self.prep_indicator_definition(metadata)
            if not metadata['element_name']:
                if not counts.has_key(idef['name']):
                    counts[idef['name']] = 1
                else:
                    counts[idef['name']] += 1

        for name, count in counts.iteritems():
            if count > 1:
                print "%s, %d" % (name, count)
    
    def update_metadata(self):
        from django.db.models import Q
        for metadata in self.get_metadata():
            if metadata['hub_programming'].lower() == 'y':
                indicator_def = self.prep_indicator_definition(metadata)
                print indicator_def
                print Indicator.objects.filter(name__in=[indicator_def['name'], indicator_def['name']+'Indicator'])
                Indicator.objects.filter(name__in=[indicator_def['name'], indicator_def['name']+'Indicator']).update(
                    **indicator_def
                )
        for indicator in Indicator.objects.all():
            indicator.calculate_metadata()
            indicator.save()
    
    def load_only_static(self):
        from django.db.utils import IntegrityError
        Indicator.objects.exclude(file_name='').delete()
        for metadata in self.get_metadata():
            if not self.find_file(metadata) or metadata['hub_programming'].lower() == 'y':
                continue
            # add indicators            
            i = None
            indicator_def = self.prep_indicator_definition(metadata)
            if metadata['indicator_group'].strip() == '':
                existing_count = Indicator.objects.filter(
                    name=indicator_def['name']
                ).count()
                if existing_count == 0:
                    print 'creating %s...' % indicator_def['name']
                    i = Indicator.objects.create(**indicator_def)
                    self.insert_data_for_indicator(i)
                    i.assign_datasources(metadata['datasources'])
                else:
                    print "Skipping dupe %s" % indicator_def['name']
            elif metadata['indicator_group'].strip():
                # if part of a time group, add the "time group" indicator
                # if the component years of a time group indicator should be
                # available, they should be split out in the spreadsheet. 
                # check for an existing time group indicator
                existing_count = Indicator.objects.filter(
                        name=metadata['indicator_group'].strip()).count()
                if existing_count == 0:
                    print 'creating time group variable %s...' % (
                        metadata['indicator_group'].strip(), )
                    i = Indicator.objects.create(**indicator_def)
                    self.insert_data_for_indicator(i)
                    i.assign_datasources(metadata['datasources'])
            if i:
                i.calculate_metadata()
                i.save()
    
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

    def insert_data_for_indicator(self, indicator):
        # find all metadata rows for this indicator
        indicator_metadata = []
        for metadata in self.get_metadata():
            if metadata['indicator_group'] == indicator.name:
                indicator_metadata.append(metadata)
        for metadata in indicator_metadata:
            # find the file
            file_path = self.find_file(metadata)
            if file_path:
                reader = csv.DictReader(open(file_path, 'rU'))
                found_column = False
                for row in reader:
                    if row.has_key(metadata['element_name']):
                        found_column = True
                        indicator_data = self.generate_indicator_data(metadata, row)
                        indicator_data.indicator = indicator
                        indicator_data.save(force_insert=True)
                if not found_column:
                    print "WARNING: Couldn't find a column for %s in one or more rows" % indicator.name
                    
            else:
                print "WARNING: Couldn't find a file for %s" % indicator.name

    
    def create_indicator(self, indicator_def):
        return Indicator.objects.create(**indicator_def)
    
    def get_dynamic_indicator_def(self, metadata):
        dyn_indicator_list = getattr(self, '_indicator_list', None)
        if not getattr(self, '_indicator_list', None):
            self._indicator_list = indicator_list()
        for indicator_pair in self._indicator_list:
            if indicator_pair[0] == metadata['indicator_group'] + 'Indicator':
                return indicator_pair[1]

    def insert_dynamic_data(self, indicator, metadata):
        """ Run the indicator, and create IndicatorData objects for the results """
        count = 0
        indicator_def = self.get_dynamic_indicator_def(metadata)
        if not indicator_def:
            print "WARNING: Couldn't match %s from the spreadsheet to a dynamic Indicator Definition" % metadata['indicator_group']
            return
        results = indicator_def().create()
        
        for key, value in results.iteritems():
            indicator_data = self.new_generate_indicator_data(
                indicator,
                key[0].key_unit_type,
                key[0].key_value,
                key[1].time_type,
                key[1].time_key,
                value,
                data_type='numeric'
            )
            indicator_data.save(force_insert=True)
            count += 1
        print "Inserted %d values for %s" % (count, indicator)        
       
    def insert_pregen_data(self, indicator):
        """ Find all rows for the indicator, and insert each """
        count = 0
        for metadata in [metadata for metadata in self.get_metadata() if (
                metadata['hub_programming'].lower != 'y' and metadata['indicator_group'] == indicator.name)]:
            file_path = self.find_file(metadata)
            if not file_path:
                print "WARNING: Couldn't find a file for %s (searched for %s)" % (
                    indicator.name, metadata['file_name'])
                return
            
            reader = csv.DictReader(open(file_path, 'rU'))
            found_column = False
            key_field = self.get_key_field(metadata['file_name'])
            for row in reader:
                if row.has_key(metadata['element_name']):
                    found_column = True
                    data_type = metadata['data_type']
                    if data_type == '':
                        # this will trigger auto-detection
                        data_type = None
                    indicator_data = self.new_generate_indicator_data(
                        indicator,
                        metadata['key_type'],
                        row[key_field],
                        metadata['time_type'],
                        str(metadata['time_key']).split('.')[0],
                        row[metadata['element_name']],
                        data_type=metadata['data_type']
                    )
                    indicator_data.save(force_insert=True)
                    count += 1
            if not found_column:
                print "WARNING: Couldn't find a column for %s in one or more rows" % indicator.name
        print "Inserted %d values for %s" % (count, indicator)
     
    def new_run_all(self):
        from django.db.utils import IntegrityError
        IndicatorData.objects.all().delete()
        seen_indicators = set() # to track which Indicators may be gone now
        
        import copy
        for metadata in [metadata for metadata in self.get_metadata() if metadata['indicator_group'] != '' and metadata['display_name'] != '']:
            indicator_def = self.prep_indicator_definition(metadata)
            try:
                indicator = Indicator.objects.get(name=indicator_def['name'])
                Indicator.objects.filter(id=indicator.id).update(**indicator_def)
            except Indicator.DoesNotExist:
                indicator = self.create_indicator(indicator_def)
            seen_indicators.add(indicator)
            
            print 'Inserting data for %s' % indicator
            if metadata['hub_programming'].lower() == 'y':
                self.insert_dynamic_data(indicator, metadata)
            else:
                self.insert_pregen_data(indicator)
            indicator.calculate_metadata()
            indicator.assign_datasources(metadata['datasources'])
            indicator.save()

        print 'Indicators not seen'
        print '-------------------'
        for indicator in Indicator.objects.all():
            if indicator not in seen_indicators:
                print indicator.name
        
    def _run_all(self):
        from django.db.utils import IntegrityError
        
        #Indicator.objects.all().delete()
        IndicatorData.objects.all().delete()
        
        # import pregen indicators
        import copy
        for metadata in self.get_metadata():
            # add indicators            
            indicator_def = self.prep_indicator_definition(metadata)
            if metadata['indicator_group'].strip() == '':
                existing_count = Indicator.objects.filter(
                    name=indicator_def['name']
                ).count()
                if existing_count == 0:
                    print 'creating %s...' % indicator_def['name']
                    i = Indicator.objects.create(**indicator_def)
                    self.insert_data_for_indicator(i)
                else:
                    print "Skipping dupe %s" % indicator_def['name']
            elif metadata['indicator_group'].strip():
                # if part of a time group, add the "time group" indicator
                # if the component years of a time group indicator should be
                # available, they should be split out in the spreadsheet. 
                # check for an existing time group indicator
                existing_count = Indicator.objects.filter(
                        name=metadata['indicator_group']).count()
                if existing_count == 0:
                    print 'creating time group variable %s...' % (
                        metadata['indicator_group'].strip(), )
                    i = Indicator.objects.create(**indicator_def)
                    self.insert_data_for_indicator(i)
        
            i.calculate_metadata()
            i.save()
        
        # import dynamic indicators
        output_file = open('errors.txt', 'w')
        for indicator_name, IndicatorDef in indicator_list():
            try:
                if indicator_name in excel_info.keys():
                    indicator_def = IndicatorDef()
                    excel_related_info = excel_info[indicator_name]
                    # find data sources
                    i = Indicator.objects.create(
                        name=indicator_name, 
                        short_label=excel_related_info[0]
                    ) #etc
                    for data_source in indicator_def.data_sources():
                        i.datasources.add(DataSource.objects.get(
                            short=data_source))
                    i.save()
                    results = indicator_def.create()
                    self.csv_output(results, indicator_name)
                    
                    for key, value in results.iteritems():
                        i_data = IndicatorData(
                            indicator=i,
                            time_type=key[1].time_type,
                            time_key = key[1].time_key,
                            key_unit_type = key[0].key_unit_type,
                            key_value = key[0].key_value,
                            data_type = 'numeric',
                            numeric = value
                        )
                        i_data.save()
                    i.calculate_metadata()
                    i.save()
            except:
                output_file.write(str(sys.exc_info()) + '\n')
                break 
        output_file.close()


class DynamicImporter():
    def __init__(self):
        self.directory = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            'data'
        ))
        
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
    
    def csv_output(self, results, name):
        columns = []
        rows = []
        data = {}
        for key, value in results.iteritems():
            col = key[1]
            row = key[0]
            if not col in columns:
                columns.append(col)
            if not row in rows:
                rows.append(row)
            
            if not col in data.keys():
                data[col] = {}
            data[col][row] = value
        
        out_file = open(name + '.csv', 'w')
        out_file.write(',' + ','.join(map(lambda c: str(c), columns)) + "\n")
        for row in rows:
            row_data = [str(row),]
            
            for column in columns:    
                row_data.append(str(data[column][row]))
            
            out_file.write(','.join(row_data) + "\n")
    
    
    def xls_check(self):
        output_file = open('errors.txt', 'w')
        output_file.write('Indicators not found in excel file: \n')
        excel_info = self.grab_xls_info()
        count = 0
        for pair in indicator_list():
            if pair[0] in excel_info.keys():
                continue
            else:
                count += 1
                output_file.write(str(pair[0]) + '\n')
        output_file.close()
        print str(count) + ' indicators not found in the excel file'
            
    def run_all(self):
        Indicator.objects.all().delete()
        excel_info = self.grab_xls_info()
        output_file = open('errors.txt', 'w')
        
        for indicator_name, IndicatorDef in indicator_list():
            try:
                if indicator_name in excel_info.keys():
                    indicator_def = IndicatorDef()
                    excel_related_info = excel_info[indicator_name]
                    # find data sources
                    i = Indicator.objects.create(
                        name=indicator_name, 
                        short_label=excel_related_info[0]
                    ) #etc
                    for data_source in indicator_def.data_sources():
                        i.datasources.add(DataSource.objects.get(
                            short=data_source))
                    i.save()
                    results = indicator_def.create()
                    self.csv_output(results, indicator_name)
                    
                    for key, value in results.iteritems():
                        i_data = IndicatorData(indicator=i, time_type=key[1].time_type, time_key = key[1].time_key, key_unit_type = key[0].key_unit_type, key_value = key[0].key_value, data_type = 'numeric', numeric = value)
                        i_data.save()
                    i.calculate_metadata()
                    i.save()
            except:
                output_file.write(str(sys.exc_info()) + '\n')
                break 
        output_file.close()

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
