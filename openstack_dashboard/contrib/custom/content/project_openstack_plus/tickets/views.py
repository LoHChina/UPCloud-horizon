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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.template.defaultfilters import capfirst  # noqa
from django.template.defaultfilters import floatformat  # noqa
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView  # noqa
from django.views.generic import View  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.contrib.custom.content.project_openstack_plus.\
    tickets import forms as project_forms
from openstack_dashboard.contrib.custom.content.project_openstack_plus.\
    tickets import tables as project_tables
from openstack_dashboard.contrib.custom.content.project_openstack_plus.\
    tickets import workflows as project_workflows
from openstack_dashboard.contrib.custom.db import api as db_api
from openstack_dashboard.contrib.custom.utils import timeutils


class IndexView(tables.DataTableView):
    table_class = project_tables.TicketsTable
    template_name = 'project_openstack_plus/project_tickets/index.html'

    def get_data(self):
        try:
            tickets = db_api.ticket_get_all(self.request)
        except Exception:
            tickets = []
            msg = _('Ticket list can not be retrieved.')
            exceptions.handle(self.request, msg)

        tickets = filter(lambda x: x.user_id == self.request.user.id,
                         tickets)

        return tickets


class CreateView(workflows.WorkflowView):
    workflow_class = project_workflows.UpdateQuota
    success_url = reverse_lazy("horizon:project:overviews:index")

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        instance_id = self.kwargs['instance_id']
        try:
            return api.nova.server_get(self.request, instance_id)
        except Exception:
            redirect = reverse("horizon:project:instances:index")
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        initial = super(CreateView, self).get_initial()
        nova_quotas = api.nova.tenant_quota_get(
            self.request, self.request.user.tenant_id)
        neutron_quotas = api.neutron.tenant_quota_get(
            self.request, self.request.user.tenant_id)
        cinder_quotas = api.cinder.default_quota_get(
            self.request, self.request.user.tenant_id)
        instances = getattr(nova_quotas.get("instances"),
                            'limit', float("inf"))
        vcpu = getattr(nova_quotas.get("cores"), 'limit', float("inf"))
        ram = getattr(nova_quotas.get("ram"), 'limit', float("inf"))
        floating_ips = getattr(nova_quotas.get("floating_ips"),
                               'limit', float("inf"))
        routers = getattr(neutron_quotas.get("router"), 'limit', float("inf"))
        ports = getattr(neutron_quotas.get("port"), 'limit', float("inf"))
        networks = getattr(neutron_quotas.get("network"),
                           'limit', float("inf"))
        subnets = getattr(neutron_quotas.get("subnet"), 'limit', float("inf"))
        volume = getattr(cinder_quotas.get("volumes"), 'limit', float("inf"))
        volume_bytes = getattr(cinder_quotas.get("gigabytes"),
                               'limit', float("inf"))
        sg_groups = getattr(nova_quotas.get("security_groups"),
                            'limit', float("inf"))
        keypairs = getattr(nova_quotas.get("key_pairs"), 'limit', float("inf"))
        initial.update({'instances': instances, 'cores': vcpu,
                        'ram': ram, 'floating_ips': floating_ips,
                        'router': routers, 'port': ports,
                        'network': networks, 'subnet': subnets,
                        'volumes': volume, 'gigabytes': volume_bytes,
                        'security_groups': sg_groups, 'keypair': keypairs})
        return initial


class Ticket(object):
    def __init__(self, id, title, description,
                 status, status_desc, created_at):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.status_desc = status_desc
        self.created_at = created_at


class DetailView(forms.ModalFormView):
    form_class = project_forms.CreateForm
    template_name = 'project_openstack_plus/project_tickets/detail.html'
    success_url = "horizon:project_openstack_plus:project_tickets:detail"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        ticket_id = self.kwargs['ticket_id']
        ticket_db = db_api.ticket_get_by_id(self.request, ticket_id)
        created_time = timeutils.format_time(ticket_db.created_at)
        status_desc = ticket_db.status.capitalize()
        ticket = Ticket(ticket_db.id, ticket_db.title, ticket_db.description,
                        ticket_db.status, status_desc, created_time)
        all_ticket_reply = db_api.get_all_ticket_reply_by_ticket_id(
            self.request, ticket_id)
        for reply in all_ticket_reply:
            reply.created_at = timeutils.format_time(reply.created_at)
        context["ticket"] = ticket
        context["ticket_id"] = ticket_id
        context["all_ticket_reply"] = all_ticket_reply
        return context

    def get_initial(self):
        return {'ticket_id': self.kwargs["ticket_id"]}

    def get_success_url(self, **kwargs):
        ticket_id = self.kwargs['ticket_id']
        return reverse(self.success_url,
                       kwargs={"ticket_id": ticket_id})
