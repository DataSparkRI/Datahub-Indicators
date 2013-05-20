import decimal
import logging
from indicators.models import Indicator, IndicatorData

try:
    from core.indicators import indicator_list
except ImportError:
    pass

# Get an instance of a logger
weave_logger = logging.getLogger('datahub.indicator')

def clean_value(val):
    if hasattr(val, 'strip') and callable(val.strip):
        val = val.strip()
        val = val.replace("%","")
        val = val.replace("#DIV/0!", '')
        val = val.replace("#NULL!", '')
    return val

def get_dynamic_indicator_def(indicator):
    try:
        return indicator.resolve_indicator_def()
    except Indicator.MultipleDefinitionsFoundException:
        print "Found multiple definitions for %s, skipping" % indicator.name
        return None

def generate_indicator_data(indicator, key_type, key_value,
        time_type, time_key, value, data_type=None):
    from indicators.models import IndicatorData
    import indicators.conversion as conversion
    indicator_data_kwargs = {}

    value = clean_value(value)
    if data_type and data_type.lower() == 'string':
        data_type = 'string'
    elif data_type and data_type.lower() == 'numeric':
        data_type = 'numeric'
    else:
        try:
            float(value)
            data_type = 'numeric'
        except ValueError:
            data_type = 'string'
    indicator_data_kwargs['data_type'] = data_type

    if data_type == 'string':
        indicator_data_kwargs['string'] = value

    if data_type == 'numeric':
        if value == '':
            value = None
        indicator_data_kwargs['numeric'] = round_value_for_unit(value, indicator.unit)

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

def round_value_for_unit(value, unit):
    if value is None:
        return value
    decimals = 0
    if unit in ('rate', 'other'):
        decimals = 2
    return decimal.Decimal(str(round(value, decimals)))

def generate_weave(verbose=False):
    """ Write weave tables into weave instance"""
    from weave.api import clear_generated_meta, get_or_create_data_table, insert_data_row
    from weave.models import DataFilter, WeaveMetaPublic
    # we need to delete all the hub create weave data
    print_v(verbose, "Clearing Existing Meta...")
    clear_generated_meta()
    table_keys = {}
    filter_keys = {}
    # generatate categories
    print_v(verbose, "Creating Categories...")
    for kut in IndicatorData.objects.only('key_unit_type').distinct('key_unit_type'):
        table_keys[kut.key_unit_type] = get_or_create_data_table(kut.key_unit_type)

    print_v(verbose, "Creating filters...")

    for f in DataFilter.objects.all():
        if f.key_unit_type not in filter_keys:
            filter_keys[f.key_unit_type] = []
        filter_keys[f.key_unit_type].append({'kut':f.key_unit_type,
                                             'name':f.name,
                                             'filter_id':f.id,
                                             'table_id':get_or_create_data_table("%s - %s" % (f.key_unit_type, f.name))
                                             })
    # generate data
    print_v(verbose, "Creating Data...")
    for ind in Indicator.objects.filter(published=True):
        min = ind.min
        max = ind.max
        for ind_data in IndicatorData.objects.filter(indicator=ind).distinct('time_key', 'key_unit_type'):
            #print ind.display_name, ind_data.key_unit_type
            if ind_data.key_unit_type == 'School' or ind_data.key_unit_type == 'District' :
                time = format_school_year(ind_data.time_key)
            else:
                time = ind_data.time_key

            parent_id = table_keys[ind_data.key_unit_type]
            title = "%s, %s" % (ind.display_name, time)

            sql = """SELECT "key_value", "{0}" FROM "public"."indicators_indicatordata" WHERE "indicator_id"='{1}' AND "key_unit_type"='{2}' AND "time_key"='{3}'""".\
                    format(ind.data_type, ind.id, ind_data.key_unit_type, ind_data.time_key)

            insert_data_row(parent_id, title, ind.display_name,  ind.data_type, sql, ind.id, time, ind_data.key_unit_type, min, max)

            # apply filters
            if ind_data.key_unit_type in filter_keys:
                # apply the filters available for this Key Unit Type
                for kut in filter_keys[ind_data.key_unit_type]:
                    #print_v(verbose, "Applying filter: %s... to %s %s" % (kut['name'], ind.display_name, ind_data.time_key))
                    parent_id = kut['table_id']
                    title = "%s, %s" % (ind.display_name, time)

                    sql = """SELECT "key_value", "{0}" FROM "public"."indicators_indicatordata" WHERE "indicator_id"='{1}' AND "key_unit_type"='{2}' AND "time_key"='{3}' AND key_value in (SELECT key_value FROM weave_datafilterkey WHERE data_filter_id={4}) """.\
                        format(ind.data_type, ind.id, ind_data.key_unit_type, ind_data.time_key, kut['filter_id'])

                    data_table_name = "%s - %s" % (ind_data.key_unit_type, kut['name'])

                    insert_data_row(parent_id, title, ind.display_name, ind.data_type, sql, ind.id, time, data_table_name, min, max)


def print_v(verbose, text):
    if verbose:
        weave_logger.debug(text)


def format_school_year(time_key):
    s = time_key.replace(' ','')
    s = s.split('-')
    try:
        return "SY%s-%s" % (s[0][2:], s[1][2:])
    except IndexError:
        return time_key



