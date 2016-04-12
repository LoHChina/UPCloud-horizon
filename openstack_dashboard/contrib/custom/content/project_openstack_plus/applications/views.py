# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django import http
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

import json

from horizon import forms
from horizon import messages
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.views import splash

from openstack_dashboard.dashboards.project.stacks import views

from openstack_dashboard.contrib.custom.content.project_openstack_plus.\
    applications import forms as project_forms
from openstack_dashboard.contrib.custom.content.project_openstack_plus.\
    applications import tabs as project_tabs
from openstack_dashboard.contrib.custom.db import api as db_api


class IndexView(tabs.TabbedTableView):
    tab_group_class = project_tabs.AppStoreTabs
    template_name = 'project_openstack_plus/applications/index.html'

    def get(self, request, *args, **kwargs):
        enable_app_store = getattr(
            self.request, 'enable_app_store', False)
        if not enable_app_store:
            response = splash(request)
            msg = _('Oops,this feature had been disabled, please go to '
                    '"Global Settings" page to check the configuration')
            messages.warning(request, msg)
        else:
            response = super(IndexView, self).get(request, *args, **kwargs)
        return response


class UploadApplicationTemplateView(forms.ModalFormView):
    form_class = project_forms.UploadApplicationTemplateForm
    template_name = \
        'project_openstack_plus/applications/upload_application.html'
    success_url = reverse_lazy(
        'horizon:project_openstack_plus:applications:index')


class CreateApplicationView(View):

    def get(self, request, **kwargs):
        application_id = self.kwargs['application_id']
        data = db_api.application_get_by_id(request, application_id)
        template_name = 'project_openstack_plus/applications/create.html'
        form_class = project_forms.CreateAppForm
        success_url = (
            "%s?tab=app_store_tabs__my_apps_tab" %
            reverse("horizon:project_openstack_plus:applications:index"))
        views.CreateStackView.success_url = success_url
        views.CreateStackView.template_name = template_name
        views.CreateStackView.form_class = form_class
        return views.CreateStackView.as_view()(request, **data.template_data)


class DetailView(views.DetailView):
    tab_group_class = project_tabs.AppDetailTabs
    template_name = 'project_openstack_plus/applications/detail.html'


class AppView(View):
    def get(self, request, *args, **kwargs):
        app_id = kwargs["app_id"]
        stack = api.heat.stack_get(request, app_id)
        return http.HttpResponse(json.dumps({"status": stack.status,
                                             "app_id": stack.id,
                                             "action": stack.action}),
                                 content_type="application/json")
