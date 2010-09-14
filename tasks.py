from celery.decorators import task
import time

from indicators.util import get_dynamic_indicator_def, new_generate_indicator_data
from indicators.models import Indicator

@task
def insert_dynamic_data(indicator_id, metadata):
    """ Run the indicator, and create IndicatorData objects for the results """
    indicator = Indicator.objects.get(id=indicator_id)
    count = 0
    indicator_def = get_dynamic_indicator_def(metadata)
    if not indicator_def:
        print "WARNING: Couldn't match %s from the spreadsheet to a dynamic Indicator Definition" % metadata['indicator_group']
        return
    results = indicator_def().create()
    
    for key, value in results.iteritems():
        indicator_data = new_generate_indicator_data(
            Indicator.objects.get(id=indicator_id),
            key[0].key_unit_type,
            key[0].key_value,
            key[1].time_type,
            key[1].time_key,
            value,
            data_type='numeric'
        )
        indicator_data.save(force_insert=True)
        count += 1
    indicator.calculate_metadata()
    indicator.assign_datasources(metadata['datasources'])
    indicator.save()
    print "Inserted %d values for %s" % (count, indicator)

@task
def create_indicator_data(indicator, start_time=None):
    indicator.create()
    if start_time:
        import datetime
        print '%s finished in %d seconds' % (indicator, (datetime.datetime.now() - start_time).seconds)
