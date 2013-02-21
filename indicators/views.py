from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.views.decorators import staff_member_required
import re
from indicators.models import IndicatorList, Indicator, TypeIndicatorLookup, DataSource, IndicatorData, DefaultListSubscription
from accounts.models import IndicatorListShare
from bs4 import BeautifulSoup
import cStringIO as StringIO
from time import strftime
import csv

def default(request):
    lists = []
    if request.user.is_authenticated():
        for i_list in request.user.indicatorlist_set.filter(visible_in_weave=True):
            lists.append({
                'name': i_list.name,
                'attr_col_Q': i_list.attribute_column_Q
            })
        # get the default ones
        for subscription in DefaultListSubscription.objects.filter(user=request.user,visible_in_weave=True):
            lists.append({
                'name': subscription.ilist.name,
                'attr_col_Q': subscription.ilist.attribute_column_Q
            })

    else:
        lists.append({
            'name': 'All Indicators',
            'attr_col_Q': Q()
        })

    return render_to_response('indicators/default.xml',
        {
            'lists': lists
        },
        context_instance=RequestContext(request))

def list_hierarchy(request, indicator_list_slug):
    list = get_object_or_404(IndicatorList, slug=indicator_list_slug)
    indicator_ctype = ContentType.objects.get_for_model(Indicator)

    return render_to_response('indicators/indicator_list_hierarchy.xml',
        {'attribute_column_Q': list.attribute_column_Q, 'name': list.name},
        context_instance=RequestContext(request))

@staff_member_required
def admin(request):
    return render_to_response('indicators/admin.html',
        {'indicators': Indicator.objects.all().order_by('name')},
        context_instance=RequestContext(request))

def indicator_list(request, indicator_list_slug):
    """ The public landing page for an Indicator List. Can be used
    for sharing iLists
    """
    indicator_list = get_object_or_404(IndicatorList, slug=indicator_list_slug)

    is_owned_by_user = False
    is_shared_with_user = False

    if request.user.is_authenticated():
        is_owned_by_user = request.user == indicator_list.owner
        try:
            IndicatorListShare.objects.get(shared_with=request.user, ilist=indicator_list)
            is_shared_with_user = True
        except IndicatorListShare.DoesNotExist:
            is_shared_with_user = False
        default_list, created = IndicatorList.objects.get_or_create_default_for_user(
            request.user)
        ilists = IndicatorList.objects.filter(owner=request.user)
    else:
        default_list = None
        ilists = None

    return render_to_response('indicators/indicator_list.html',
        {
            'indicator_list': indicator_list,
            'is_owned_by_user': is_owned_by_user,
            'is_shared_with_user': is_shared_with_user,
            'default_indicator_list': default_list,
            'ilists': ilists
        },
        context_instance=RequestContext(request))

def gen_indicator_data(indicator):
    last_common_name_kut = ''
    last_common_name_indicator = Indicator

    for indicator_data in indicator.indicatordata_set.filter(Q(numeric__isnull=False) | Q(string__isnull=False)):
        if last_common_name_kut == indicator_data.key_unit_type:
            common_name_indicator = last_common_name_indicator
        else:
            common_name_id = TypeIndicatorLookup.objects.filter(name=indicator_data.key_unit_type).values_list('indicator_id')[0][0]
            common_name_indicator = Indicator.objects.get(id=common_name_id)
            last_common_name_indicator = common_name_indicator
            last_common_name_kut = indicator_data.key_unit_type

        common_names = IndicatorData.objects.filter(indicator=common_name_indicator).filter(key_value=indicator_data.key_value, time_key=indicator_data.time_key)
        for common_name in common_names:
            time_period = ' '.join([indicator_data.time_type, indicator_data.time_key])
            key_value = ' '.join([indicator_data.key_unit_type, indicator_data.key_value])
            source = [key_value, common_name.value]

            yield {
                'time_period': time_period,
                'key_value': key_value,
                'source': source,
                'value': indicator_data.value,
            }

def single_line(string):
    string = string.encode('ascii', 'ignore')
    string = ''.join(BeautifulSoup(string).findAll(text=True))
    string = re.sub('[\r\n]', '', string)
    return string

def indicator_csv(request, indicator_slug):
    indicator = get_object_or_404(Indicator, slug=indicator_slug)
    csv_file = StringIO.StringIO()
    writer = csv.writer(csv_file)
    columns = ['Key Value', 'Name'] #time period(s) are appended to this
    rows = []
    data = {}

    for indicator_data in gen_indicator_data(indicator):
        if not indicator_data['time_period'] in columns:
            columns.append(indicator_data['time_period'])
            data[indicator_data['time_period']] = {}

        if not indicator_data['source'] in rows: #this prevents source being written once per time period
            rows.append(indicator_data['source'])

        data[indicator_data['time_period']][indicator_data['key_value']] = indicator_data['value']

    # Write headers to CSV file
    writer.writerow(columns)

    # Write data to CSV file
    for row in rows:
        #note: row[n] = [key_value, common_name.string]
        row_data = [str(row[0]), str(row[1])]
        for time_period in columns[2:]:
            try:
                row_data.append(str(data[time_period][row[0]]))
            except KeyError:
                row_data.append('')

        writer.writerow(row_data)

    writer.writerow('')
    datasources = ''
    first = True
    for datasource in indicator.datasources.all():
        if first:
            datasources = datasource
            first = False
        else:
            datasources = "%s; %s" % (datasources, datasource)
    writer.writerow(["Name: %s" % indicator.display_name])
    writer.writerow(["Long Definition: %s" % single_line(indicator.long_definition)])
    writer.writerow(["Universe: %s" % single_line(indicator.universe)])
    writer.writerow(["Limitations: %s" % single_line(indicator.limitations)])
    writer.writerow(["Datasource(s): %s" % datasources])
    writer.writerow(["Downloaded: %s" % strftime("%a, %d %b %Y %H:%M:%S %Z")])
    writer.writerow(["Location: %s" % request.build_absolute_uri()])
    for datasource in indicator.datasources.all():
        for sub_datasource in datasource.sub_datasources.all():
            if sub_datasource.disclaimer:
                writer.writerow(["%s: %s" % (sub_datasource.disclaimer.title, single_line(sub_datasource.disclaimer.content))])

    response = HttpResponse(csv_file.getvalue(), mimetype="text/csv")
    response["Content-Disposition"] = "attachment; filename=%s.csv" % indicator.slug
    return response

def get_datasource_name(request):
    if request.is_ajax():
        if request.method == 'POST' and request.POST:
            short = request.POST.get('short')
            datasource = get_object_or_404(DataSource, short=short)
            return HttpResponse(datasource.name, content_type="text/plain")
    else:
        return HttpResponse(status=400)
