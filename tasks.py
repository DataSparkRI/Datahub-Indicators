import datetime
import os
import time

from celery.decorators import task

from indicators.util import get_dynamic_indicator_def, generate_indicator_data
from indicators.models import Indicator

def _get_batch_logger(batch_dir):
    import logging

    logger = logging.getLogger("default_indicator_logger")
    fh = logging.FileHandler(os.path.join(batch_dir, 'batch.log'))
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # bypass the root logger
    logger.propagate = False

    return logger

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
    indicator.mark_load_complete()
    indicator.save()
    print "Inserted %d values for %s" % (count, indicator)

@task
def create_indicator_data(indicator, start_time=None):
    indicator.create()
    if start_time:
        import datetime
        print '%s finished in %d seconds' % (indicator, (datetime.datetime.now() - start_time).seconds)

@task
def indicator_debug_batch(indicators_to_run, batch_folder):
    from core.indicators import indicator_list
    
    # whip up a logger that outputs to the batch directory for the indicators
    logger = _get_batch_logger(batch_folder)
    [idef(debug=True,logger=logger).csv_output(idef.__name__,path=batch_folder)
        for idef in indicator_list() 
        if idef.__name__ in indicators_to_run]

    logger.debug('Batch Finished')

    # create a tar.gz of the batch directory
    os.system('tar -cvzf %s %s' % (
        os.path.join(batch_folder, 'batch.tar.gz'), batch_folder, )
    )

