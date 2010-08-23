from django.contrib import admin
from indicators.models import DataSource, IndicatorList


admin.site.register(DataSource)
admin.site.register(IndicatorList)

