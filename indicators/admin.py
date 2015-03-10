import csv, re
import logging
import os
import uuid
import datetime
from django.conf import settings
from django.contrib import admin, messages
from indicators.models import DataSource, SubDataSource, SubDataSourceDisclaimer, IndicatorList, DefaultIndicatorList, DefaultListSubscription, \
        Indicator, IndicatorPregenPart, IndicatorData, TypeIndicatorLookup, Permission,AnonymizedEnrollment
from django.utils.translation import ugettext_lazy as _
from indicators.fields import RoundingDecimalField, FileNameField

from radmin import console
console.register_to_all('Generate Weave','indicators.views.gen_weave', True)
from django.contrib.admin import SimpleListFilter

class upLoadType(SimpleListFilter):
    title = _('Data collected from')
    parameter_name = "collected"
    def lookups(self, request, model_admin):
        return (
            ('Hub', _('Hub generated')),
            ('Usr', _('CSV user uploaded')),
        )
    def queryset(self, request, queryset):
        from indicators.models import Indicator
        AI = Indicator.objects.all()
        Hub = []
        Usr = []
        for i in AI:
            list = IndicatorPregenPart.objects.filter(indicator__name=i)
            if len(list) == 0:
                Hub.append(i.id)
            else:
                Usr.append(i.id)
        if self.value() == 'Hub':
            return queryset.filter(id__in=Hub)
        elif self.value() == 'Usr':
            return queryset.filter(id__in=Usr)
        else:
            return AI

class subAgencyDataSourcesField(SimpleListFilter):
    title = _('Sub-Agency Data Sources')
    parameter_name = 'subDataSource'
    def lookups(self, request, model_admin):
        subDataSourceDisclaimer = SubDataSourceDisclaimer.objects.all();
        result = []
        for i in subDataSourceDisclaimer:
            result.append((i.id,_(i.name)))

        return tuple(result)
    def queryset(self, request, queryset):

        if self.value():
            v = self.value().split(" ")
            return queryset.filter(datasources__sub_datasources__disclaimer__id__in=v)
        else:
            return queryset


try:
    from django.contrib.admin.filterspecs import FilterSpec


    class IndicatorSourceListFilter(FilterSpec):

        """
        Add "By Indicator Source" filter option on the admin/indicators/indicators page.

        Ideally, there would be two filter values listed:
        1) PreGenCSV
        2) HUB-Core

        PreGenCSV=true if the indicator's FileName attribute is populated;
        else HUB-Core=true.
        """

        def test(cls, field):
            return field.null and isinstance(field, cls.fields) and not field._choices

        test = classmethod(test)

        def title(self):
            return "Indicator Source"

        def __init__(self, f, request, params, model, model_admin):
            super(IndicatorSourceListFilter, self).__init__(f, request, params, model, model_admin)

            self.file_exists_lookup_kwarg     = 'file_name__gt'
            self.file_not_exists_lookup_kwarg = 'file_name'
            self.file_exists_lookup_val       = request.GET.get(self.file_exists_lookup_kwarg, None)
            self.file_not_exists_lookup_val   = request.GET.get(self.file_not_exists_lookup_kwarg, None)

        def choices(self, cl):
            yield {
                    'selected'     : self.file_exists_lookup_val is None and self.file_not_exists_lookup_val is None,
                    'query_string' : cl.get_query_string({}, [self.file_exists_lookup_kwarg, self.file_not_exists_lookup_kwarg]),
                    'display'      : 'All',
            }
            yield {
                    'selected'     : self.file_exists_lookup_val is not None,
                    'query_string' : cl.get_query_string({self.file_exists_lookup_kwarg : ""}, [self.file_not_exists_lookup_kwarg]),
                    'display'      : 'PreGenCSV',
            }
            yield {
                    'selected'     : self.file_not_exists_lookup_val is not None,
                    'query_string' : cl.get_query_string({self.file_not_exists_lookup_kwarg : ""}, [self.file_exists_lookup_kwarg]),
                    'display'      : 'HUB-Core',
            }

    def _register_front(cls, test, factory):
        cls.filter_specs.insert(0, (test, factory))

    FilterSpec.register_front = classmethod(_register_front)
    FilterSpec.register_front(lambda f: isinstance(f, FileNameField), IndicatorSourceListFilter)
except ImportError:
    pass

# Actions available in Core
def batch_debug_indicators(modeladmin, request, queryset):
    """ Run selected indicators, and store output and a "debug" csv

    Each call to this view generates a view batch folder. The contents of the
    folder:

    - [indicator name].csv for each indicator selected
    - [indicator name]_debug.csv for each indicator selected
    - batch.log

    The indicator generation is scheduled in celery, and output is directed to
    batch.log.
    """
    try:
        from core.indicators import indicator_list
    except ImportError:
        return
    from indicators.tasks import indicator_debug_batch

    # create a directory to store the results of this debug batch
    batch_id = unicode(uuid.uuid1())
    batch_folder = os.path.join(settings.MEDIA_ROOT, 'batches', batch_id)
    os.makedirs(batch_folder)

    # map the queryset to names, for matching against definition classes
    indicators_to_run = [indicator.name for indicator in queryset]

    indicator_debug_batch(indicators_to_run, batch_folder)
batch_debug_indicators.short_description = \
    "Run a debug batch on the selected indicators"


def load_indicators(modeladmin, request, queryset):
    from indicators.load import DataImporter
    DataImporter().run_all(indicator_list=queryset)
load_indicators.short_description = "Load data for the selected Indicators"


# Actions available in Portal
def publish(modeladmin, request, queryset):
    queryset.update(published=True)
publish.short_description = "Publish selected indicators"


def unpublish(modeladmin, request, queryset):
    queryset.update(published=False)
unpublish.short_description = "Unpublish selected indicators"

def save_pregen_csv_data(modeladmin, request, queryset):
    mess = []
    names = []
    for obj in queryset:
            names.append(obj.name)
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
                        messages.add_message(
                            request, messages.ERROR,
                            'Unable to open the file "'
                            + filename + '" for the pregen data. '
                            'Meta-data saved.  Indicator Data unchanged.'
                        )
                        return obj
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
                    mess.append( obj.name + ': Cleared the Indicator Data and added '+ str(len(new_data)) + ' Indicator Data records from the pregen csv file')
                        
                    
                obj.last_load_completed = datetime.datetime.now()

    messages.add_message(
                            request, messages.INFO,
                            "Save PreGen CSV Data: "+ ', '.join([str(x) for x in names]) + "  "+'. '.join([str(x) for x in mess])
                        )
save_pregen_csv_data.short_description = "Save PreGen CSV Data"



def switch_load_pending(modeladmin, request, queryset):
    """ Flips load_pending on Indicators that are selected in queryset"""
    for obj in queryset:
        if obj.load_pending is False:
            obj.load_pending = True
        elif obj.load_pending is True:
            obj.load_pending = False
        obj.save()
switch_load_pending.short_description = "Toggle selected indicator's Load Pending status"

class IndicatorPregenPartInline(admin.TabularInline):
    extra = 10
    model = IndicatorPregenPart

class PermissionInline(admin.TabularInline):
    extra = 3
    model = Permission


class IndicatorAdmin(admin.ModelAdmin):
    class Media:
        css = {
            "all": ("stylesheets/extend_tag_textbox.css",
                    "stylesheets/extend_universe_textbox.css",)
        }
    list_display = ('name', 'data_type', 'visible_in_all_lists', 'published','retired', 'load_pending', 'last_load_completed', 'last_audited',)
    list_editable = ('visible_in_all_lists', 'published','retired',)
    list_filter = (upLoadType,'data_type', 'visible_in_all_lists', 'datasources', subAgencyDataSourcesField, 'load_pending', 'published','retired',  'last_audited')
    
    search_fields = ('name', 'datasources__short_name', 'short_definition',
                     'long_definition', 'notes', 'file_name')
    exclude = ('raw_tags', 'raw_datasources', 'years_available_display',
               'years_available', )
    prepopulated_fields = {"slug": ("name",)}
    inlines = [
        IndicatorPregenPartInline,
        PermissionInline,
    ]


    try:
        from indicators.load import DataImporter
        actions = [batch_debug_indicators, load_indicators, publish, unpublish]
    except ImportError:
        actions = [publish, unpublish, switch_load_pending, save_pregen_csv_data]

    fieldsets = (
        ('Basic Information', { 'fields':(
            'name',
            'file_name',
            'display_name',
            'short_definition',
            'long_definition',
            'purpose',
            'universe',
            'limitations',
            'routine_use',
            'last_audited',
        )}),

        ('Numerical/Addtional Information', { 'fields':(
            'min',
            'max',
            'unit',
            'data_type',
            'notes',
        )}),

        ('Metadata', { 'fields':(
            'data_levels_available',
            'query_level',
            'suppression_numerator',
            'suppression_denominator',
            'datasources',
        )}),

        ('Django Internals', { 'fields':(
            'published',
            'retired',
            'visible_in_all_lists',
            'slug',
            'tags',
            'load_pending',
            'last_load_completed'
        )}),
    )

    def response_add(self, request, new_obj):
        obj = self.handle_pregen_data(new_obj, request)
        return super(IndicatorAdmin, self).response_add(request, obj)

    def response_change(self, request, new_obj):
        obj = self.handle_pregen_data(new_obj, request)
        return super(IndicatorAdmin, self).response_add(request, obj)

    def handle_pregen_data(self, obj, request):
        if request.POST.get('updatePregenCSV') == 'on':
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
                        messages.add_message(
                            request, messages.ERROR,
                            'Unable to open the file "'
                            + filename + '" for the pregen data. '
                            'Meta-data saved.  Indicator Data unchanged.'
                        )
                        return obj
                    reader = csv.reader(csv_file)
                    cols = reader.next()
                    cols = [re.sub(r'[^\x00-\x7F]+','', y) for y in cols]
                    if (pregenpart.key_column in cols) == False and (pregenpart.column_name in cols) == False:
                       messages.add_message(
                            request, messages.ERROR,
                            "Bad column name (%s) and bad key column name (%s)."%(pregenpart.column_name, pregenpart.key_column)+
                            ' Meta-data "'+pregenpart.time_value+'" skiped.'
                        )
                    elif (pregenpart.key_column in cols) == False:
                       messages.add_message(
                            request, messages.ERROR,
                            "Good column name (%s) and bad key column name (%s)."%(pregenpart.column_name, pregenpart.key_column)+
                            ' Meta-data "'+pregenpart.time_value+'" skiped.'
                        )
                    elif (pregenpart.column_name in cols) == False:
                       messages.add_message(
                            request, messages.ERROR,
                            "Bad column name (%s) and good key column name (%s)."%(pregenpart.column_name, pregenpart.key_column)+
                            ' Meta-data "'+pregenpart.time_value+'" skiped.'
                        )
                    elif (pregenpart.key_column in cols) == True and (pregenpart.column_name in cols) == True:
                        messages.add_message(
                             request, messages.INFO,
                            "Good column name (%s) and good key column name (%s)."%(pregenpart.column_name, pregenpart.key_column)+
                            ' Meta-data "'+pregenpart.time_value+'" saved.'
                        )
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
                    messages.add_message(
                        request, messages.INFO,
                        'Cleared the Indicator Data and added '
                        + str(len(new_data)) +
                        ' Indicator Data records from the pregen csv file.'
                    )
                obj.last_load_completed = datetime.datetime.now()
        return obj


class DefaultListSubscriptionInline(admin.TabularInline):
    model = DefaultListSubscription

class DefaultIndicatorListAdmin(admin.ModelAdmin):
    #inlines = (DefaultListSubscriptionInline,)
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ['indicators']
    
class AnonymizedEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('school_year', 'SASID', 'distCode', 'grade','enroll_date', 'exit_date', 'exit_type')
    list_filter = ('school_year','exit_type')
   


admin.site.register(DataSource)
admin.site.register(SubDataSource)
admin.site.register(SubDataSourceDisclaimer)
admin.site.register(IndicatorList)
admin.site.register(DefaultIndicatorList, DefaultIndicatorListAdmin)
admin.site.register(Indicator, IndicatorAdmin)
admin.site.register(AnonymizedEnrollment, AnonymizedEnrollmentAdmin)
admin.site.register(TypeIndicatorLookup)
admin.site.register(Permission)
