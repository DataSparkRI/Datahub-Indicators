from django.core.management.base import BaseCommand, CommandError
from indicators.models import *
import re
from optparse import make_option
from django.conf import settings
import csv
class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--file',
                    dest='file',
                    help='a file with weave error output'
                    ),
    )

    def handle(self, *args, **options):
        try:
            MISSING_RAW = open(options.get('file'),'r')

            regex = re.compile("(?<=object_id=\")\d+")
            missing = [int(m) for m in regex.findall(MISSING_RAW.read())]
            for m in missing:
                try:
                    obj = Indicator.objects.get(pk=m)
                    if obj.pregenparts.count():
                        obj.last_load_completed = datetime.datetime.now()
                        obj.save()
                        new_data = []
                        for pregenpart in obj.pregenparts.all():
                            filename = settings.DATAHUB_PREGEN_CSV_FILE \
                                + pregenpart.file_name
                            try:
                                csv_file = open(filename, 'rb')
                            except IOError:
                                print 'Unable to open the file "'+ filename + '" for the pregen data. ' + 'Meta-data saved.  Indicator Data unchanged.'
                            reader = csv.reader(csv_file)
                            cols = reader.next()
                            if pregenpart.column_name in cols \
                                    and pregenpart.key_column in cols:
                                name_col = cols.index(pregenpart.column_name)
                                key_col = cols.index(pregenpart.key_column)
                                for row in reader:
                                    val = row[name_col]
                                    key_value = row[key_col]

                                    if obj.data_type == 'numeric':
                                        #check for blank values
                                        if val =="" or val==None or val==" ":
                                            val = None
                                        else:
                                            float(val)

                                        data_type = 'numeric'
                                        numeric = val
                                        string = None

                                    elif obj.data_type =='string':
                                        data_type = 'string'
                                        string = val
                                        numeric = None

                                    new_data.append({
                                        'time_type': pregenpart.time_type,
                                        'time_key': pregenpart.time_value,
                                        'key_unit_type': pregenpart.key_type,
                                        'key_value': key_value,
                                        'data_type': data_type,
                                        'numeric': numeric,
                                        'string': string
                                    })
                        if len(new_data):
                            IndicatorData.objects.filter(indicator=obj).delete()
                            for d in new_data:
                                IndicatorData.objects.create(
                                    indicator=obj,
                                    time_type=d['time_type'],
                                    time_key=d['time_key'],
                                    key_unit_type=d['key_unit_type'],
                                    key_value=d['key_value'],
                                    data_type=d['data_type'],
                                    numeric=d['numeric'],
                                    string=d['string']
                                )
                            print  obj.name, 'Cleared the Indicator Data and added '+ str(len(new_data)) +' Indicator Data records from the pregen csv file.'

                        obj.last_load_completed = datetime.datetime.now()
                        obj.published = True
                        obj.save()

                except Indicator.DoesNotExist:
                    pass

            MISSING_RAW.close()
            print "Done"
        except IOError:
            print "Couldnt Open File"
