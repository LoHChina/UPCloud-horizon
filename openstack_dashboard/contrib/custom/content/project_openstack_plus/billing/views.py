# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from django.utils.translation import ugettext_lazy as _

from horizon import messages
from horizon import tabs

from openstack_dashboard.contrib.custom.content.project_openstack_plus.billing \
    import tabs as project_tabs

from openstack_dashboard.views import splash


class IndexView(tabs.TabbedTableView):
    tab_group_class = project_tabs.SummaryAndQueryTabs
    template_name = 'project_openstack_plus/billing/index.html'

    def get(self, request, *args, **kwargs):
        enable_metering_feature = getattr(
            self.request, 'enable_metering_feature', False)
        if not enable_metering_feature:
            response = splash(request)
            msg = _('Oops,this feature had been disabled, please go to '
                    '"Global Settings" page to check the configuration')
            messages.warning(request, msg)
        else:
            response = super(IndexView, self).get(request, *args, **kwargs)
        return response
