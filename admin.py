from django.contrib import admin
from indicators.models import DataSource, IndicatorList, Indicator, IndicatorPregenPart


admin.site.register(DataSource)
admin.site.register(IndicatorList)

class IndicatorPregenPartInline(admin.TabularInline):
    extra = 10
    model = IndicatorPregenPart

class IndicatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'data_type', 'visible_in_all_lists' )
    list_editable = ('visible_in_all_lists', )
    list_filter = ('data_type', 'visible_in_all_lists', 'datasources')
    search_fields = ('name', 'datasources__short_name', 'short_definition',
        'long_definition', 'notes', )
    exclude = ('raw_tags', 'raw_datasources', 'years_available_display', 'years_available', )
    prepopulated_fields = {"slug": ("name",)}
    inlines = [
        IndicatorPregenPartInline,
    ]
    
    
admin.site.register(Indicator, IndicatorAdmin)
