from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.contrib.custom.content.project_openstack_plus.billing \
    import views

urlpatterns = patterns(
    '',
    url(r'^$', views.IndexView.as_view(), name='index'),
)
