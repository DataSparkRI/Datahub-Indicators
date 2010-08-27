from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from indicators.models import IndicatorList, Indicator

def default(request):
    lists = []
    if request.user.is_authenticated():
        for list in request.user.get_profile().indicator_lists.all():
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
