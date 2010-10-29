from django.contrib import admin
from indicators.models import DataSource, IndicatorList, Indicator, IndicatorPregenPart


admin.site.register(DataSource)
admin.site.register(IndicatorList)

class IndicatorPregenPartInline(admin.TabularInline):
    extra = 10
    model = IndicatorPregenPart

class IndicatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'data_type', 'visible_in_all_lists', 'published', )
    list_editable = ('visible_in_all_lists', 'published',)
    list_filter = ('data_type', 'visible_in_all_lists', 'datasources')
    search_fields = ('name', 'datasources__short_name', 'short_definition',
        'long_definition', 'notes', )
    exclude = ('raw_tags', 'raw_datasources', 'years_available_display', 'years_available', )
    prepopulated_fields = {"slug": ("name",)}
    inlines = [
        IndicatorPregenPartInline,
    ]
    
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
            'suppresion_threshold',
            'datasources',
        )}),    
            
        ('Django Internals', { 'fields':(
            'published',
            'visible_in_all_lists',
            'slug',
            'tags',
        )}),
    )
    
    
admin.site.register(Indicator, IndicatorAdmin)
