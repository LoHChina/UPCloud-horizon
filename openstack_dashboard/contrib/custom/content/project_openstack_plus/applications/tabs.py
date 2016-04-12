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

import logging
import random
import string

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.contrib.custom.content.project_openstack_plus.\
    applications import constants
from openstack_dashboard.contrib.custom.content.project_openstack_plus.\
    applications import tables
from openstack_dashboard.contrib.custom.db import api as db_api
from openstack_dashboard.dashboards.project.stacks \
    import tabs as stack_tabs


constants.APPLICATION_CATEGORY.insert(0, ("all", _("All Applications")))
APPLICATION_CATEGORY = constants.APPLICATION_CATEGORY
LOG = logging.getLogger(__name__)


class AppTopologyTab(stack_tabs.StackTopologyTab):
    template_name = "project/applications/_detail_topology.html"


class AppOverviewTab(stack_tabs.StackOverviewTab):
    template_name = "project/applications/_detail_overview.html"


class AppDetailTabs(stack_tabs.StackDetailTabs):
    slug = "stack_details"
    tabs = (AppTopologyTab, AppOverviewTab)
    sticky = True


class AppStoreTab(tabs.TableTab):
    table_classes = (tables.AppStoreTable,)
    name = _("App Store")
    slug = "app_store_tab"
    template_name = ("horizon/common/_detail_table.html")

    def get_applications_data(self):
        category = self.request.GET.get("category")
        if category == "all":
            category = None
        applications = db_api.application_get_all(self.request, category)
        # For application tiny icon and formated time
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        for app in applications:
            app.created_at = app.created_at.strftime(fmt)
            if self.request.user.tenant_id == app.project_id:
                app.can_delete = True
            letters = list(string.ascii_lowercase)
            random.shuffle(letters)
            app.random = letters[0]
        return applications

    def get_context_data(self, request, **kwargs):
        context = super(AppStoreTab, self).get_context_data(request, **kwargs)
        current_category = request.GET.get("category") or "all"
        current_application_category = []
        for index, category in enumerate(APPLICATION_CATEGORY):
            if current_category == category[0]:
                context['table'].current_category = category
            else:
                current_application_category.append(category)
        context['table'].category = current_application_category
        return context


class MyAppsTab(tabs.TableTab):
    table_classes = (tables.MyAppsTable,)
    name = _("My Apps")
    slug = "my_apps_tab"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_my_apps_data(self):
        try:
            applications, _more, _prev = api.heat.stacks_list(self.request)
        except Exception:
            msg = _('Unable to retrieve application list.')
            exceptions.handle(self.request, msg)

        for app in applications:
            # For application tiny icon
            letters = list(string.ascii_lowercase)
            random.shuffle(letters)
            app.random = letters[0]

            try:
                app_identifier = '%s/%s' % (app.stack_name, app.id)
                resources = api.heat.resources_list(self.request,
                                                    app_identifier)
                for resource in resources:
                    if resource.resource_type == "OS::Nova::Server":
                        app.logo = "%s.png" % resource.resource_name
            except Exception:
                resources = []
                messages.error(self.request, _(
                    'Unable to get resources for application "%s".') %
                    app.stack_name)
        return applications


class AppStoreTabs(tabs.TabGroup):
    slug = "app_store_tabs"
    template_name = "horizon/common/_tab_group.html"
    tabs = (AppStoreTab, MyAppsTab)
