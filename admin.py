from django.contrib import admin
from indicators.models import DataSource, IndicatorList, Indicator


admin.site.register(DataSource)
admin.site.register(IndicatorList)

class IndicatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'data_type', 'visible_in_all_lists' )
    list_editable = ('visible_in_all_lists', )
    list_filter = ('type', 'data_type', 'visible_in_all_lists', 'datasources')
    exclude = ('raw_tags', 'raw_datasources', 'years_available_display', 'years_available', )
    prepopulated_fields = {"slug": ("name",)}
    
admin.site.register(Indicator, IndicatorAdmin)
