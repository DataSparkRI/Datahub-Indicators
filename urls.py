from django.conf.urls.defaults import *
from indicators import views

urlpatterns = patterns('',
    url(r'^list_hierarchy/default.xml$', views.default, name="indicators-default_hierarchy"),
    url(r'^list_hierarchy/(?P<indicator_list_slug>[\w-]+).xml$', views.list_hierarchy, name="indicators-list_hierarchy"),
)
