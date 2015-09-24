import datetime
import os
import time

from django.db import reset_queries
from django.conf import settings
from django.core import management
from django.db import transaction


try:
    from core.models import IndicatorResult
except ImportError:
    pass
from indicators.util import get_dynamic_indicator_def, generate_indicator_data
from indicators.models import Indicator, IndicatorData

import csv
from util import generate_weave


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
try:
    from celery.decorators import task
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
        # if indicator.indicatorpregenpart_set.count() > 0:
                # skip indicators that aren't "dynamic" indicators
                #continue
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
except ImportError:
    pass

# HUEY TASKS! NOT CELERY TASKS
try:
    from huey.djhuey import task
    from django.core.management import call_command

    @task()
    def generate_weave_task():
        from indicators.util import generate_weave
        generate_weave()
        return "Generated Weave"

    @task()
    def import_indicator_csv_task(file_name):
        import_indicator_csv(file_name)

    @task()
    def run_indicator_api(indicators):
        from indicators.api import save_api
        for indicator in indicators:
           save_api(indicator)

except ImportError:
    pass


def import_indicator_csv(file_name):
    count = 0
    f = open(file_name)
    reader = csv.DictReader(f)
    bool_fields = ['published', 'retired', 'visible_in_all_lists', 'load_pending']
    inds = []
    for row in reader:
        count += 1
        args = dict(row)

        # we need to clean up some of the fields
        try:
            del args['last_audited'] # this should be set manually
        except KeyError:
            pass
        try:
            del args['Column name']
        except KeyError:
            pass
        try:
            del args['id']
        except KeyError:
            pass
        try:
            del args['last_load_completed']
        except KeyError:
            pass

        # tags in csv is actuall raw_tags so we need to set that up in
        # args and clear out ['tags']
        try:
            args['raw_tags'] = ','.join(args['tags'].split('|'))
            del args['tags']
        except KeyError:
            args['raw_tags'] = ','.join(args['raw_tags'].split('|'))

        if args['min'] == '':
            args['min'] = None
        else:
            args['min'] = int(args['min'])

        if args['max'] == '':
            args['max'] = None
        else:
            args['max'] = int(args['max'])

        if args['suppression_numerator'] == '':
            args['suppression_numerator'] = None
        else:
            args['suppression_numerator'] = int(args['suppression_numerator'])

        if args['suppression_denominator'] == '':
            args['suppression_denominator'] = None
        else:
            args['suppression_denominator'] = int(args['suppression_denominator'])


        # ENCODE or Ignore description fields
        args["short_definition"] = args["short_definition"].decode("utf-8", "ingore")
        args["long_definition"] = args["long_definition"].decode("utf-8", "ignore")

        # Translate bools fields. If some form of True is not specified, we
        # default to False
        for bf in bool_fields:
            if args[bf] in ['t', 'true', 'True', 'TRUE', '1']:
                args[bf] = True
            else:
                args[bf] = False
        try:
            with transaction.commit_on_success():
                ind = Indicator(**args)
                ind.save()
                inds.append(ind)
        except Exception as err:
            print(err)

    for i in inds:
        i.parse_tags()

    f.close()
    return str(count) + "---" + file_name
