from django.conf.urls.defaults import *
from indicators import views

urlpatterns = patterns('',
    url(r'^list_hierarchy/default.xml$', views.default, name="indicators-default_hierarchy"),
    url(r'^list_hierarchy/(?P<indicator_list_slug>[\w-]+).xml$', views.list_hierarchy, name="indicators-list_hierarchy"),
    url(r'^admin/', views.admin, name="indicators-admin"),
    url(r'^download/(?P<indicator_slug>[\w-]+).csv$', views.indicator_csv, name="indicators-indicator_csv"),
)
