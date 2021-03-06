# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.contrib.custom.content.openstack_plus.tickets \
    import views

TICKET = r'^(?P<ticket_id>[^/]+)/%s$'

urlpatterns = patterns(
    '',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(TICKET % 'update', views.UpdateView.as_view(), name='update'),
    url(r'^detail/(?P<ticket_id>[^/]+)/$',
        views.DetailView.as_view(),
        name='detail'),
)
