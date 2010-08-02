import os
import csv
import sys
from datahub.indicators.models import Indicator, IndicatorData
from django.utils.functional import memoize
from django.db import transaction

key_field_cache = {}
get_files_cache = {}
get_variables_cache = {}

def safe_strip(val):
    if isinstance(val, str):
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
        crosswalk_file = "WEAVE_DATA_CROSSWALK.xls"
        return xlrd.open_workbook(os.path.join(self.directory,crosswalk_file))
    
    def get_variables(self):
        def do_get_variables():
            book = self.open_xsl()
            sheet = book.sheet_by_index(0)
            attr_map = [
                'keep_or_drop',
                'display',
                'data_type',
                'min',
                'max',
                'name',
                'dataset_tag',
                'file_name',
                'icon',
                'source',
                'time_group',
                'year',
                'short_label_prefix',
                'short_label',
                'hover_label',
                'variable_definition',
                'case_restrictions',
                'category_one',
                'category_two',
                'category_three',
                'category_four',
            ]
        
            variables = []
            for row_num in range(1, sheet.nrows):
                row = map(safe_strip, sheet.row_values(row_num))
                var_dict = dict(zip(attr_map, row))
                
                variables.append(var_dict)
            return variables
        do_get_variables = memoize(do_get_variables, get_variables_cache, 0)
        return do_get_variables()

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

    def generate_indicator_data(self, variable, row):
        from webportal.indicators.models import IndicatorData
        import datahub.indicators.conversion as conversion
        value = row[variable['name']]
        key_field = self.get_key_field(variable['file_name'])
        
        indicator_data_kwargs = {
            'name': variable['name'],
            'data_type': variable['data_type'].lower()
        }
        
        value = self.clean_value(value)
        
        if variable['data_type'].upper() == 'NUMERIC':
            if value == '':
                value = None
            indicator_data_kwargs['numeric'] = value
        else:
            indicator_data_kwargs['string'] = value
        indicator_data_kwargs['key_unit_type'] = variable['dataset_tag']
        if variable['dataset_tag'].upper() == 'SCHOOLS':
            indicator_data_kwargs['key_value'] = row[key_field].rjust(5,'0')
        elif variable['dataset_tag'].upper() == 'DISTRICTS':
            indicator_data_kwargs['key_value'] = row[key_field].rjust(2,'0')
        else:
            indicator_data_kwargs['key_value'] = row[key_field]
        
        if variable['year'] != '':
            indicator_data_kwargs['time_type'] = 'School Year'
            try:
                indicator_data_kwargs['time_key'] = conversion.year_to_school_year(variable['year'].split('-')[0])
            except:
                indicator_data_kwargs['time_key'] = conversion.year_to_school_year(variable['year'])
        return IndicatorData(**indicator_data_kwargs)


    def insert_data_for_indicator(self, indicator):
        # find all `variable`s for this indicator
        indicator_vars = []
        for var in self.get_variables():
            if var['time_group'] == '' and var['name'] == indicator.name:
                indicator_vars.append(var)
            elif not var['time_group'] == '' and var['time_group'] == indicator.name:
                indicator_vars.append(var)
        for variable in indicator_vars:
            # find the file
            file_path = None
            for file, path in self.get_files().iteritems():
                if file.lower() == variable['file_name'].lower() + '.csv':
                    file_path = path
            if file_path:
                reader = csv.DictReader(open(file_path, 'rU'))
                found_column = True
                for row in reader:
                    if row.has_key(variable['name']):
                        indicator_data = self.generate_indicator_data(variable, row)
                        indicator_data.indicator = indicator
                        indicator_data.save(force_insert=True)
                    else:
                        found_column = False
                if not found_column:
                    print "WARNING: Couldn't find a column for %s in one or more rows" % indicator.name
                    
            else:
                print "WARNING: Couldn't find a file for %s" % indicator.name
    
    @transaction.commit_manually
    def run_all(self):
        try:
            self._run_all()
            transaction.commit()
        except:
            print "Caught an exception:", sys.exc_info()[0]
            transaction.rollback()
            raise

    def _run_all(self):
        variables = self.get_variables()
        
        Indicator.objects.all().delete()
        IndicatorData.objects.all().delete()
        
        import copy
        for variable in variables:
            # add indicators and variables
            def prep_indicator_definition(var):
                indicator_def = copy.deepcopy(var)
                indicator_def['data_type'] = indicator_def['data_type'].upper()
                del indicator_def['source']

                if isinstance(indicator_def['min'], str) and indicator_def['min'].strip() == '':
                    indicator_def['min'] = None
                if isinstance(indicator_def['max'], str) and indicator_def['max'].strip() == '':
                    indicator_def['max'] = None

                try:
                    indicator_def['year'] = indicator_def['year'].split('-')[0]
                except:
                    indicator_def['year'] = str(int(indicator_def['year']))
                del indicator_def['year']
                del indicator_def['time_group']
                
                return indicator_def
            
            
            indicator_def = prep_indicator_definition(variable)
            indicator_def['name'] = indicator_def['name'].strip()
            keep_drop = indicator_def.pop('keep_or_drop').upper()
            display = indicator_def.pop('display').upper()
            if keep_drop == "KEEP" and display == "YES" and indicator_def['file_name']:
                if variable['time_group'].strip() == '':
                    print 'creating %s...' % indicator_def['name']
                    
                    indicator_def['key_unit_type'] = variable['dataset_tag']
                    i = Indicator(**indicator_def)
                    i.save(force_insert=True)
                    self.insert_data_for_indicator(i)

                # if part of a time group, add the "time group" indicator
                # if the component years of a time group indicator should be
                # available, they should be split out in the spreadsheet. 
                # check for an existing time group indicator
                elif variable['time_group'].strip() and not Indicator.objects.filter(name=variable['time_group'].strip()).count():
                    print 'creating time group variable %s...' % variable['time_group'].strip()
                    indicator_def['name'] = variable['time_group'].strip()
                    indicator_def['key_unit_type'] = variable['dataset_tag']
                    i = Indicator(**indicator_def)
                    i.save(force_insert=True)
                    self.insert_data_for_indicator(i)
