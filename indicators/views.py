from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.views.decorators import staff_member_required

from indicators.models import IndicatorList, Indicator
from accounts.models import IndicatorListShare

def default(request):
    lists = []
    if request.user.is_authenticated():
        for list in request.user.indicatorlist_set.filter(visible_in_weave=True):
            if (list.name == 'Default - List of All Available Indicators'):
                user_i_count = list.indicators.all().count()
                i_count = Indicator.objects.filter(published=True).count()
                if (user_i_count != i_count):
                    list.indicators = Indicator.objects.filter(published=True)

            lists.append({
                'name': list.name,
                'attr_col_Q': list.attribute_column_Q
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

@staff_member_required
def indicator_csv(request, indicator_slug):
    import csv
    indicator = get_object_or_404(Indicator, slug=indicator_slug)

    columns = ['']
    rows = []
    data = {}
    for indicator_data in indicator.indicatordata_set.all().order_by('time_key'):
        col = ' '.join([indicator_data.time_type, indicator_data.time_key])
        row = ' '.join([indicator_data.key_unit_type, indicator_data.key_value])
        if not col in columns:
            columns.append(col)
        if not row in rows:
            rows.append(row)
        
        if not col in data.keys():
            data[col] = {}
        data[col][row] = indicator_data.value
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % indicator.slug
    writer = csv.writer(response)
    
    # Write headers to CSV file
    writer.writerow(columns)

    # Write data to CSV file
    for row in rows:
        row_data = [str(row),]
        
        for column in columns[1:]:
            row_data.append(str(data[column][row]))
        
        writer.writerow(row_data)
    
    return response

