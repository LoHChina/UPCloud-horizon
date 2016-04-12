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

import openstack_dashboard.dashboards.project.instances.views as views

from openstack_dashboard.contrib.custom.utils import common_utils
from openstack_dashboard.dashboards.project.instances.tables import *  # noqa

from django.core.urlresolvers import reverse
from django import shortcuts
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from openstack_dashboard.dashboards.project.instances.workflows \
    import ResizeInstance


from openstack_dashboard.contrib.custom.db import api as db_api

import json

TICKET_INDEX = "horizon:project_openstack_plus:project_tickets:index"


class ContribLaunchLink(LaunchLink):

    def allowed(self, request, datum):
        if common_utils.need_ticket(request):
            self.verbose_name = _("Apply Instance")
        try:
            limits = api.nova.tenant_absolute_limits(request, reserved=True)

            instances_available = limits['maxTotalInstances'] \
                - limits['totalInstancesUsed']
            cores_available = limits['maxTotalCores'] \
                - limits['totalCoresUsed']
            ram_available = limits['maxTotalRAMSize'] - limits['totalRAMUsed']

            if instances_available <= 0 or cores_available <= 0 \
                    or ram_available <= 0:
                if "disabled" not in self.classes:
                    self.classes = [c for c in self.classes] + ['disabled']
                    self.verbose_name = string_concat(self.verbose_name, ' ',
                                                      _("(Quota exceeded)"))
            else:
                self.verbose_name = self.verbose_name
                classes = [c for c in self.classes if c != "disabled"]
                self.classes = classes
        except Exception:
            LOG.exception("Failed to retrieve quota information")
            # If we can't get the quota information, leave it to the
            # API to check when launching
        return True  # The action should always be displayed


class ContribInstanceTable(InstancesTable):
    class Meta(InstancesTable.Meta):
        launch_actions = (ContribLaunchLink, )
        table_actions = launch_actions + (TerminateInstance,
                                          InstancesFilterAction)


class ContribResizeInstance(ResizeInstance):
    def _order_steps(self):
        steps = super(ContribResizeInstance, self)._order_steps()
        if common_utils.need_ticket(self.request):
            self.name = "Apply Resize Instance"
            self.finalize_button_name = "Apply"
            self.handle = self._handle
        return steps

    @sensitive_variables('context')
    def _handle(self, request, context):
        description = ""
        values = {'user_id': request.user.id,
                  'project_id': request.user.tenant_id,
                  'title': _("Resize Instance"),
                  'description': description,
                  'context': json.dumps(context),
                  'status': "new",
                  'type': 'resize_instance'}
        db_api.ticket_create(request, values)
        return shortcuts.redirect(reverse(TICKET_INDEX))


views.IndexView.table_class = ContribInstanceTable
views.ResizeView.workflow_class = ContribResizeInstance
