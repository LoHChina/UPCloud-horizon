# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

import uuid

from django.core.urlresolvers import reverse_lazy
from django.template.defaultfilters import capfirst  # noqa
from django.template.defaultfilters import floatformat  # noqa
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView  # noqa

from horizon import exceptions
from horizon.utils import csvbase
from horizon import workflows

from openstack_dashboard.contrib.custom.api import ceilometer
from openstack_dashboard.contrib.custom.content.project.overview \
    import workflows as quota_workflows

from openstack_dashboard.contrib.custom.content.project.usage \
    import base as contrib_base  # noqa

from openstack_dashboard.usage import tables as pro_tables  # noqa
from openstack_dashboard.usage import views as pro_views  # noqa

from openstack_dashboard.contrib.custom.db import api as db_api
from openstack_dashboard.contrib.custom.utils import timeutils

from openstack_dashboard import api


class ProjectUsageCsvRenderer(csvbase.BaseCsvResponse):

    columns = [_("Instance Name"), _("VCPUs"), _("RAM (MB)"),
               _("Disk (GB)"), _("Usage (Hours)"),
               _("Uptime (Seconds)"), _("State")]

    def get_row_data(self):

        for inst in self.context['usage'].get_instances():
            yield (inst['name'],
                   inst['vcpus'],
                   inst['memory_mb'],
                   inst['local_gb'],
                   floatformat(inst['hours'], 2),
                   inst['uptime'],
                   capfirst(inst['state']))

EVENT_TYPE = {
    "compute.instance.create.end": [_("Create Instance"), _("Instance")],
    "volume.detach.end": [_("Detach Volume"), _("Volume")],
    "volume.attach.end": [_("Attach Volume"), _("Volume")],
    "compute.instance.delete.end": [_("Terminate Instance"), _("Instance")],
    "compute.instance.shutdown.end": [_("Shutdown Instance"), _("Instance")],
    "volume.create.end": [_("Create Volume"), _("Volume")],
    "volume.delete.end": [_("Delete Volume"), _("Volume")],
    "compute.instance.power_on.end": [_("Start Instance"), _("Instance")],
    "snapshot.create.end": [_("Create Vomue Snapshot"), _("Volume Snapshot")],
    "snapshot.delete.end": [_("Delete Vomue Snapshot"), _("Volume Snapshot")],
    "compute.instance.snapshot.end": [_("Create Instance Snapshot"),
                                      _("Instance Snapshot")],
    "compute.instance.power_off.end": [_("Stop Instance"), _("Instance")],
    "compute.instance.rebuild.end": [_("Rebuild Instance"), _("Instance")],
    "compute.instance.reboot.end": [_("Reboot Instance"), _("Instance")],
    "compute.instance.resume": [_("Resume Instance"), _("Instance")],
    "compute.instance.suspend": [_("Suspend Instance"), _("Instance")],
    "network.create.end": [_("Create Network"), _("Network")],
    "network.delete.end": [_("Delete Network"), _("Network")],
    "router.create.end": [_("Create Router"), _("Router")],
    "router.delete.end": [_("Delete Router"), _("Router")],
    "floatingip.create.end": [_("Create Floating IP"), _("Floating IP")],
    "floatingip.delete.end": [_("Delete Floating IP"), _("Floating IP")],
}


class EventObj(object):
    def __init__(self, id, event_type, generated, display_name, type_name):
        self.id = id
        self.event_type = event_type
        self.generated = generated
        self.display_name = display_name
        self.type_name = type_name


class ProjectOverview(pro_views.UsageView):
    table_class = pro_tables.ProjectUsageTable
    usage_class = contrib_base.ProjectUsage
    template_name = 'project/overview/usage.html'
    csv_response_class = ProjectUsageCsvRenderer

    def _get_ticket_data(self):
        # Recieve the tickets
        try:
            tickets = db_api.ticket_get_all(self.request)
        except Exception:
            tickets = []
            msg = _('Ticket list can not be retrieved.')
            exceptions.handle(self.request, msg)

        tickets = filter(lambda x: x.user_id == self.request.user.id,
                         tickets)
        for ticket in tickets:
            ticket.status_code = ticket.status
            ticket.status = _(ticket.status.capitalize())  # noqa
            if not ticket.updated_at:
                ticket.updated_at = timeutils.format_time(ticket.created_at)
            else:
                ticket.updated_at = timeutils.format_time(ticket.updated_at)

        return tickets[:10]

    def get_context_data(self, **kwargs):
        context = super(ProjectOverview, self).get_context_data(**kwargs)
        context["tickets"] = self._get_ticket_data()
        # Check metering service
        if not api.base.is_service_enabled(self.request, "metering"):
            return context

        # Billing and Event
        try:
            query = []
            query += [{"field": "user_id",
                       "op": "eq",
                       "type": "string",
                       "value": self.request.user.id}]
            events = ceilometer.event_list_with_tenant(self.request, limit=8)
            event_list = []
            for e in events:
                # NOTE(jing.liuqing): why no display name for network deletion
                if isinstance(e.traits.display_name, basestring):
                    event_list.append(EventObj(str(uuid.uuid4()),
                                               EVENT_TYPE[e.event_type][0],
                                               e.generated,
                                               e.traits.display_name,
                                               EVENT_TYPE[e.event_type][1]))
            context["event_list"] = event_list
        except Exception:
            pass

        enable_network_overlay = getattr(
            self.request, 'enable_network_overlay', False)
        context["enable_network_overlay"] = enable_network_overlay

        return context


class WarningView(TemplateView):
    template_name = "project/_warning.html"


class UpdateView(workflows.WorkflowView):
    workflow_class = quota_workflows.UpdateQuota
    success_url = reverse_lazy("horizon:project:overview:index")

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        return context

    def get_initial(self):
        initial = super(UpdateView, self).get_initial()
        nova_quotas = api.nova.tenant_quota_get(self.request,
                                                self.request.user.tenant_id)
        neutron_quotas = api.neutron.tenant_quota_get(self.request,
                                                      self.request.
                                                      user.tenant_id)
        cinder_quotas = api.cinder.default_quota_get(self.request,
                                                     self.request.
                                                     user.tenant_id)
        instances = getattr(nova_quotas.get("instances"),
                            'limit', float("inf"))
        vcpu = getattr(nova_quotas.get("cores"),
                       'limit', float("inf"))
        ram = getattr(nova_quotas.get("ram"),
                      'limit', float("inf"))
        floating_ips = getattr(nova_quotas.get("floating_ips"),
                               'limit', float("inf"))
        routers = getattr(neutron_quotas.get("router"),
                          'limit', float("inf"))
        ports = getattr(neutron_quotas.get("port"),
                        'limit', float("inf"))
        networks = getattr(neutron_quotas.get("network"),
                           'limit', float("inf"))
        subnets = getattr(neutron_quotas.get("subnet"),
                          'limit', float("inf"))
        volume = getattr(cinder_quotas.get("volumes"),
                         'limit', float("inf"))
        volume_bytes = getattr(cinder_quotas.get("gigabytes"),
                               'limit', float("inf"))
        sg_groups = getattr(nova_quotas.get("security_groups"),
                            'limit', float("inf"))
        keypairs = getattr(nova_quotas.get("key_pairs"),
                           'limit', float("inf"))
        initial.update({'instances': instances,
                        'cores': vcpu,
                        'ram': ram,
                        'floating_ips': floating_ips,
                        'router': routers,
                        'port': ports,
                        'network': networks,
                        'subnet': subnets,
                        'volumes': volume,
                        'gigabytes': volume_bytes,
                        'security_groups': sg_groups,
                        'keypair': keypairs})
        return initial
