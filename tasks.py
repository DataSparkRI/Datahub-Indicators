from celery.decorators import task
import time

from indicators.util import get_dynamic_indicator_def, generate_indicator_data
from indicators.models import Indicator

@task
def insert_dynamic_data(indicator_id):
    """ Run the indicator, and create IndicatorData objects for the results """
    indicator = Indicator.objects.get(id=indicator_id)

    print "Start %s" % indicator

    count = 0
    indicator_def = get_dynamic_indicator_def(indicator)
    if not indicator_def:
        return
    results = indicator_def(debug=True).create()
    
    for key, value in results.iteritems():
        indicator_data = generate_indicator_data(
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
    indicator.update_metadata()
    indicator.save()
    print "Inserted %d values for %s" % (count, indicator)

@task
def create_indicator_data(indicator, start_time=None):
    indicator.create()
    if start_time:
        import datetime
        print '%s finished in %d seconds' % (indicator, (datetime.datetime.now() - start_time).seconds)
