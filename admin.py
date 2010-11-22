from django.contrib import admin
from indicators.models import DataSource, IndicatorList, Indicator, IndicatorPregenPart


admin.site.register(DataSource)
admin.site.register(IndicatorList)

def load_indicators(modeladmin, request, queryset):
    from indicators.load import DataImporter
    DataImporter().run_all(indicator_list=queryset)
load_indicators.short_description = "Load data for the selected Indicators"

def publish(modeladmin, request, queryset):
    queryset.update(published=True)
publish.short_description = "Publish selected indicators"

def unpublish(modeladmin, request, queryset):
    queryset.update(published=False)
unpublish.short_description = "Unpublish selected indicators"

class IndicatorPregenPartInline(admin.TabularInline):
    extra = 10
    model = IndicatorPregenPart

class IndicatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'data_type', 'visible_in_all_lists', 'published', 'load_pending', 'last_load_completed')
    list_editable = ('visible_in_all_lists', 'published',)
    list_filter = ('data_type', 'visible_in_all_lists', 'datasources', 'load_pending')
    search_fields = ('name', 'datasources__short_name', 'short_definition',
        'long_definition', 'notes', 'file_name')
    exclude = ('raw_tags', 'raw_datasources', 'years_available_display', 'years_available', )
    prepopulated_fields = {"slug": ("name",)}
    inlines = [
        IndicatorPregenPartInline,
    ]

    try:
        from indicators.load import DataImporter
        actions = [load_indicators, publish, unpublish]
    except ImportError:
        actions = [publish, unpublish]
    
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
            'visible_in_all_lists',
            'slug',
            'tags',
            'load_pending',
            'last_load_completed'
        )}),
    )
    
    
admin.site.register(Indicator, IndicatorAdmin)
