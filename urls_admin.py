from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^indicator_batches/$', 'indicators.admin_views.indicator_batch_list', name="indicators_admin_batch_list"),
    url(r'^indicator_batches/([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})$', 'indicators.admin_views.indicator_batch', name="indicators_admin_batch"),
)

