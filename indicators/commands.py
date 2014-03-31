# huey tasks! not celery tasks! http://huey.readthedocs.org/en/latest/getting-started.html#getting-started-django
#from huey.djhuey.decorators import queue_command
from huey.djhuey import task
import ucsv as csv
from models import Indicator
from util import generate_weave

@task()
def generate_weave_task():
    generate_weave()

@task()
def import_indicator_csv_task(file_name):
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

        # Translate bools fields. If some form of True is not specified, we
        # default to False
        for f in bool_fields:
            if args[f] in ['t', 'true', 'True', 'TRUE', '1']:
                args[f] = True
            else:
                args[f] = False
        try:
            ind = Indicator(**args)
            ind.save()
            inds.append(ind)
        except TypeError as err:
            # error in header, end request
            f.close()
            return "Could not import from csv. Please check csv header. Error:%s" % err

    for i in inds:
        i.parse_tags()

    f.close()

    return str(count) + "---" + file_name
