from indicators.models import Indicator, IndicatorData
from haystack.indexes import *
from haystack import site


class IndicatorIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    display_name = CharField(model_attr='display_name', boost=1.8)
    short_definition = CharField(model_attr='short_definition', boost=0.9)
    datalevels = MultiValueField()
    datasources = MultiValueField()
    content_auto = EdgeNgramField(model_attr='display_name')

    def prepare_datasources(self, obj):
        sources = [ds.short for ds in obj.sorted_datasources()]
        if len(sources) > 1:
            sources.append('cross')
        return sources

    def prepare_datalevels(self, obj):
        return [dl['key_unit_type'] for dl in IndicatorData.objects.filter(indicator=obj).values('key_unit_type').distinct('key_unit_type')]

    def index_queryset(self, using=None):
        return Indicator.objects.filter(published=True)

site.register(Indicator, IndicatorIndex)
