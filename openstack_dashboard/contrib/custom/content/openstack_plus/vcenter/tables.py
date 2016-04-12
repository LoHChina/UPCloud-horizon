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

from django.core.urlresolvers import reverse
from django.utils.translation import npgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from horizon.templatetags import sizeformat

from openstack_dashboard.contrib.custom.content.openstack_plus.vcenter \
    import utils


class LaunchLink(tables.LinkAction):
    name = "launch"
    verbose_name = _("Launch Instance")
    url = "horizon:openstack_plus:vcenter:launch"
    classes = ("ajax-modal", "btn-launch")
    icon = "cloud-upload"
    policy_rules = (("compute", "compute:create"),)
    ajax = True

    def get_link_url(self, datum=None):
        vcenter_id = self.table.kwargs['vcenter_id']
        return reverse(self.url, args=(vcenter_id,))


class StartInstance(tables.BatchAction):
    name = "start"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Start Instance",
            u"Start Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Started Instance",
            u"Started Instances",
            count
        )

    def action(self, request, datum):
        si = utils.get_vmware_si(request,
                                 self.table.kwargs.get('vcenter_id'))
        utils.power_on(si, datum)


class StopInstance(tables.BatchAction):
    name = "stop"
    classes = ('btn-danger',)

    @staticmethod
    def action_present(count):
        return npgettext_lazy(
            "Action to perform (the instance is currently running)",
            u"Shut Off Instance",
            u"Shut Off Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return npgettext_lazy(
            "Past action (the instance is currently already Shut Off)",
            u"Shut Off Instance",
            u"Shut Off Instances",
            count
        )

    def action(self, request, datum):
        si = utils.get_vmware_si(request,
                                 self.table.kwargs.get('vcenter_id'))
        utils.power_off(si, datum)


class VCenterInstancesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Instance Name"))
    memory = tables.Column("memory",
                           verbose_name=_("Memory"),
                           filters=(sizeformat.mbformat,))
    cpu = tables.Column("cpu_num", verbose_name=_("CPU"))
    ip = tables.Column("ip", verbose_name=_("IP"))
    state = tables.Column("state", verbose_name=_("Status"))

    class Meta(object):
        name = "vcenter_instances"
        verbose_name = _("vCenter Instances")
        row_actions = (StartInstance, StopInstance,)
        table_actions = (LaunchLink,)
