from django.contrib import admin
from indicators.models import DataSource, IndicatorList, Indicator


admin.site.register(DataSource)
admin.site.register(IndicatorList)
admin.site.register(Indicator)
