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

from openstack_dashboard.contrib.custom.content.openstack_plus.ceph_monitor\
    import views as ceph_views
from openstack_dashboard.contrib.custom.content.openstack_plus.log_analysis\
    import views as log_views
from openstack_dashboard.contrib.custom.content.openstack_plus.monitor\
    import views as monitor_views
from openstack_dashboard.contrib.custom.content.project.volumes.volumes\
    import views as volumes_views
from openstack_dashboard.contrib.custom import views

import horizon

horizon.site_urls.urlpatterns += patterns(
    '',
    url(r'^log/', log_views.LogView.as_view(), name='log'),
    url(r'^monitor/', monitor_views.MonitorView.as_view(), name='monitor'),
    url(r'^ceph_monitor/',
        ceph_views.CephMonitorView.as_view(), name='ceph_monitor'),
    url(r'^auto_backup/(?P<volume_id>[^/]+)/$',
        volumes_views.AutoBackupView.as_view(),
        name='auto_backup'),
    url(r'^check_ip/$', views.check_ip, name="check_ip"),
    url(r'^register/', views.RegisterView.as_view(), name='register'),
    url(r'^activate_account/', views.EnableView.as_view(),
        name='activate_account'),
    url(r'^register_success/(?P<username>[^/]+)/$',
        views.RegisterSuccessView.as_view(),
        name='register_success'),
    url(r'^forgot_pwd/', views.ForgetpwdView.as_view(), name='forgot_pwd'),
    url(r'^reset_forgot_pwd/(?P<user_id>[^/]+)/$',
        views.ResetpwdView.as_view(),
        name='reset_forgot_pwd'),
    url(r'^forgotpwd_email/(?P<username>[^/]+)/$',
        views.ForgetpwdEmailView.as_view(),
        name='forgotpwd_email'),
    url(r'^reset_pwd_success/(?P<username>[^/]+)/$',
        views.ResetSuccessView.as_view(),
        name='reset_pwd_success'),
)
