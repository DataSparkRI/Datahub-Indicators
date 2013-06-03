from django.conf.urls.defaults import *
from indicators import views

urlpatterns = patterns('',
    url(r'^list_hierarchy/default.xml$', views.default, name="indicators-default_hierarchy"),
    url(r'^list_hierarchy/(?P<indicator_list_slug>[\w-]+).xml$', views.list_hierarchy, name="indicators-list_hierarchy"),
    url(r'^indicator_list/(?P<indicator_list_slug>[\w-]+)/$', views.indicator_list, name="indicators-indicator_list"),
    #url(r'^admin/', views.admin, name="indicators-admin"),
    url(r'^download/(?P<indicator_slug>[\w-]+).csv$', views.indicator_csv, name="indicators-indicator_csv"),
    url(r'^get_datasource_name/$', views.get_datasource_name, name="indicators-get_datasource_name"),
    url(r'^actions/batch_create/$', 'indicators.admin_views.batch_create', name="indicators_batch_create"),
)
