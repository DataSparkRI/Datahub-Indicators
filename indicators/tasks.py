import datetime
import os
import time

from celery.decorators import task
from django.db import reset_queries
from django.conf import settings
from django.core import management

from indicators.util import get_dynamic_indicator_def, generate_indicator_data
from indicators.models import Indicator, IndicatorData


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

@task(ignore_result=True) # Nothing is returned, so we can safely ignore results
def insert_dynamic_data(indicator_def):
    """ Run the indicator, and create IndicatorData objects for the results """

    try:
        from core.models import IndicatorResult
    except ImportError:
        return

    class_name = indicator_def.__name__
    print "Start %s" % class_name

    count = 0
    if not indicator_def:
        return

    IndicatorResult.objects.filter(class_name=class_name).delete()
    results = indicator_def(debug=True).create()
    for key, value in results.iteritems():
        if not value is None:
            value = str(value)
        IndicatorResult.objects.create(
            time_type=key[1].time_type,
            time_key=key[1].time_key,
            key_unit_type=key[0].key_unit_type,
            key_value=key[0].key_value,
            class_name=class_name,
            value=value
        )
        count += 1
    reset_queries() # normally handled during a web request
    print "Inserted %d values for %s" % (count, class_name)

@task
def move_to_portal(indicator_defs, portal_name):
    if portal_name not in settings.DATABASES:
        raise Exception('%s is not a configured database' % portal_name)

    try:
        from core.models import IndicatorResult
    except ImportError:
        return

    for i_def in indicator_defs:
        indicator = Indicator.objects.get_for_def(i_def, using=portal_name)
        if indicator.indicatorpregenpart_set.count() > 0:
            # skip indicators that aren't "dynamic" indicators
            continue
        results = IndicatorResult.objects.filter(class_name=i_def.__name__)
        IndicatorData.objects.using(portal_name).filter(indicator=indicator).delete()
        for result in results:
            indicator_data = generate_indicator_data(
                indicator,
                result.key_unit_type,
                result.key_value,
                result.time_type,
                result.time_key,
                result.value,
                data_type='numeric'
            )
            indicator_data.save(force_insert=True,using=portal_name) 

    
@task
def create_indicator_data(indicator, start_time=None):
    indicator.create()
    if start_time:
        import datetime
        print '%s finished in %d seconds' % (indicator, (datetime.datetime.now() - start_time).seconds)

@task
def indicator_debug_output(indicator_def, output_folder):
    # whip up a logger that outputs to the batch directory for the indicators
    #logger = _get_batch_logger(output_folder)
    print output_folder
    indicator_def(debug=True).csv_output(indicator_def.__name__,path=output_folder)


@task
def indicator_debug_batch(indicators_to_run, batch_folder):
    try:
        from core.indicators import indicator_list
    except ImportError:
        return
    
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

@task
def pwd():
    print os.path.abspath('.')


@task
def regenerate_weave(portal_name='portal'):
    if portal_name not in settings.DATABASES:
        raise Exception('%s is not a configured database' % portal_name)

    try:
        from weave.models import AttributeColumn
    except ImportError:
        return

    # first delete all the attribute columns
    AttributeColumn.objects.using(portal_name).all().delete()
    management.call_command('load_weave', portal_name=portal_name)
