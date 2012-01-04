from optparse import make_option
import sys
import re
from xml.sax.saxutils import quoteattr

from django.db import IntegrityError  
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from indicators.models import Indicator, IndicatorData, DataFilter
from weave.models import AttributeColumn

class WeaveExporter(object):
    def time_translations(self, input):
        if not input:
            return None
        
        # school years
        sy_re = re.compile(r'School Year [0-9]{2}(?P<start_year>[0-9]{2})-[0-9]{2}(?P<end_year>[0-9]{2})')
        
        sy_match = sy_re.match(input)
        if sy_match:
            return 'SY%s-%s' % (sy_match.group('start_year'), 
                sy_match.group('end_year'))

        # Calendar Years
        cy_re = re.compile(r'Calendar Year (?P<year>[0-9]{4})')

        cy_match = cy_re.match(input)
        if cy_match:
            return '%s' % cy_match.group('year')
        
        # future conversions...

        return input

    def run(self, indicator_list_qs=Indicator.objects.all(), portal_name='portal'):
        from django.conf import settings
        assert hasattr(settings, 'WEAVE')
        connection = settings.WEAVE.get('CONNECTION', '')

        assert portal_name in settings.DATABASES

        indicator_ctype = ContentType.objects.get(
            app_label='indicators', model='indicator'
        )
                
        # create AttributeColumns
        for indicator in indicator_list_qs.iterator():
            AttributeColumn.objects \
                .using(portal_name) \
                .filter(content_type=indicator_ctype,object_id=indicator.id) \
                .delete()
            for indicator_data in indicator.indicatordata_set.values(
                    'key_unit_type', 'time_key', 'data_type', 'time_type').distinct():
                try:
                    if indicator.data_type.upper() == 'NUMERIC':
                        data_type = 'number'
                        sql_type = 'numeric'
                    else:
                        data_type = 'text'
                        sql_type = 'string'

                    if indicator_data['time_type'] and indicator_data['time_key']:
                        time = "%s %s" % (indicator_data['time_type'], indicator_data['time_key'])
                    else:
                        time = indicator_data['time_key']
                    if not indicator_data['time_key'] or indicator_data['time_key'].strip() == '':
                        time_sql = 'indicators_indicatordata."time_key" is null'
                    else:
                        time_sql = 'indicators_indicatordata."time_key" = \'%s\' and indicators_indicatordata."time_type" = \'%s\'' % (indicator_data['time_key'], indicator_data['time_type'])
                    data_with_keys_query = """
                        SELECT key_value, %s from indicators_indicatordata WHERE indicators_indicatordata."indicator_id" = '%s' AND indicators_indicatordata."key_unit_type" like '%s' AND (%s)
                    """ % (
                        sql_type,
                        indicator.id,
                        indicator_data['key_unit_type'],
                        time_sql,
                    )
                    
                    attribute_column, created = AttributeColumn.objects \
                        .using(portal_name) \
                        .get_or_create(
                        content_type=indicator_ctype,
                        object_id=indicator.id,
                        connection=connection,
                        dataTable=indicator_data['key_unit_type'],
                        name=indicator.weave_name(),
                        display_name=indicator.weave_name(),
                        keyType=indicator_data['key_unit_type'],
                        year=self.time_translations(time) or '',
                        dataType=data_type,
                        sqlQuery=data_with_keys_query.strip(),
                        min=str(indicator.min) if indicator.min else '',
                        max=str(indicator.max) if indicator.max else ''
                    )
                except IntegrityError:
                    print "Duplicate AttributeColumn detected for (%s, %s, %s). AttributeColumn NOT created." % (
                        indicator.name,
                        indicator.key_unit_type,
                        indicator_data['time_key']
                    )

        for data_filter in DataFilter.objects.all():
            keyType = data_filter.key_unit_type
            attribute_columns = AttributeColumn.objects \
                .using(portal_name) \
                .filter(keyType=keyType)
            table_name = data_filter.get_data_table_name()

            for ac in attribute_columns:
                AttributeColumn.objects.using(portal_name).get_or_create(
                    content_type=ac.content_type,
                    object_id=ac.object_id,
                    connection=ac.connection,
                    dataTable=table_name,
                    name=ac.name,
                    display_name=ac.display_name,
                    keyType=ac.keyType,
                    year=ac.year,
                    dataType=ac.dataType,
                    sqlQuery=data_filter.modify_query(ac.sqlQuery),
                    min=ac.min,
                    max=ac.max
                )


class Command(BaseCommand):
    option_list = BaseCommand.option_list# + (
    help = ''
    args = ''
  
    def handle(self, *args, **options):
        WeaveExporter().run()
