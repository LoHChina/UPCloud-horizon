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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon.utils import functions as utils

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.hypervisors \
    import tabs as project_tabs

from openstack_dashboard.contrib.custom.utils import common_utils

from openstack_dashboard.dashboards.admin.hypervisors.compute \
    import tabs as cmp_tabs
from openstack_dashboard.dashboards.admin.hypervisors \
    import tabs as hypervisors_tabs
from openstack_dashboard.dashboards.admin.hypervisors import views


class ContribHypervisorTab(project_tabs.HypervisorTab):

    def get_hypervisors_data(self):
        hypervisors = super(ContribHypervisorTab, self).get_hypervisors_data()
        common_utils.get_set_storage(hypervisors=hypervisors)
        enable_hypervisor_overcommit = getattr(
            self.request, 'enable_hypervisor_overcommit', False)
        if enable_hypervisor_overcommit:
            common_utils.get_overcommit_stats(hypervisors=hypervisors)

        return hypervisors


class AdminIndexView(tabs.TabbedTableView):
    tab_group_class = project_tabs.HypervisorHostTabs
    template_name = 'admin/hypervisors/index.html'
    page_title = _("All Hypervisors")

    def get_data(self):
        hypervisors = []
        try:
            hypervisors = api.nova.hypervisor_list(self.request)
            hypervisors.sort(key=utils.natural_sort('hypervisor_hostname'))
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve hypervisor information.'))

        return hypervisors

    def get_context_data(self, **kwargs):
        context = super(AdminIndexView, self).get_context_data(**kwargs)
        try:
            stats = api.nova.hypervisor_stats(self.request)
            common_utils.get_set_storage(stats=stats)
            enable_hypervisor_overcommit = getattr(
                self.request, 'enable_hypervisor_overcommit', False)
            if enable_hypervisor_overcommit:
                common_utils.get_overcommit_stats(stats=stats)
            context["stats"] = stats
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve hypervisor statistics.'))

        return context

hypervisors_tabs.HypervisorHostTabs.tabs = (ContribHypervisorTab,
                                            cmp_tabs.ComputeHostTab)
views.AdminIndexView = AdminIndexView
