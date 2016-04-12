# Copyright 2012 NEC Corporation
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

"""
Views for managing Neutron Networks.
"""
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

from django.utils.datastructures import SortedDict

import ast

import json

from openstack_dashboard import api

from openstack_dashboard.contrib.custom.utils import timeutils

from openstack_dashboard.contrib.custom.content.openstack_plus.tickets \
    import forms as project_forms
from openstack_dashboard.contrib.custom.content.openstack_plus.tickets \
    import tables as project_tables
from openstack_dashboard.contrib.custom.db import api as db_api

from openstack_dashboard.dashboards.project.volumes.volumes import views


class IndexView(tables.DataTableView):
    table_class = project_tables.TicketsTable
    template_name = 'openstack_plus/tickets/index.html'

    @memoized.memoized_method
    def _get_tenant_list(self):
        try:
            tenants, has_more = api.keystone.tenant_list(self.request)
        except Exception:
            tenants = []
            msg = _('Unable to retrieve ticket project information.')
            exceptions.handle(self.request, msg)

        tenant_dict = SortedDict([(t.id, t) for t in tenants])
        return tenant_dict

    @memoized.memoized_method
    def _get_user_list(self):
        try:
            users = api.keystone.user_list(self.request)
        except Exception:
            users = []
            msg = _('Unable to retrieve ticket users information.')
            exceptions.handle(self.request, msg)

        user_dict = SortedDict([(u.id, u) for u in users])
        return user_dict

    def get_data(self):
        try:
            tickets = db_api.ticket_get_all(self.request)
        except Exception:
            tickets = []
            msg = _('Ticket list can not be retrieved.')
            exceptions.handle(self.request, msg)

        if tickets:
            tenant_dict = self._get_tenant_list()
            for ticket in tickets:
                tenant = tenant_dict.get(ticket['project_id'], None)
                ticket.tenant_name = getattr(tenant, 'name', None)
            user_dict = self._get_user_list()
            for ticket in tickets:
                user = user_dict.get(ticket['user_id'], None)
                ticket.user_name = getattr(user, 'name', None)

        return tickets


class UpdateView(forms.ModalFormView):
    form_class = project_forms.EditTicket
    template_name = 'openstack_plus/tickets/update.html'
    context_object_name = 'ticket'
    success_url = reverse_lazy("horizon:openstack_plus:tickets:index")

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context["ticket_id"] = self.kwargs['ticket_id']
        ticket_id = self.kwargs['ticket_id']
        try:
            ticket = db_api.ticket_get_by_id(self.request, ticket_id)
        except Exception:
            ticket = None
        if ticket is not None:
            context["type"] = ticket.type
            if ticket.type == "quota":
                context["ticket"] = ast.literal_eval(ticket.context)
            elif ticket.type == "volume":
                volume = json.loads(ticket.context)
                context["volume"] = volume
                try:
                    if(volume["volume_source_type"] == "volume_source"):
                        volume = api.cinder.volume_get(
                            self.request,
                            volume["volume_source"])
                        context["volume_source"] = volume
                    elif(volume["volume_source_type"] == "image_source"):
                        image = api.glance.image_get(
                            self.request,
                            volume["image_source"])
                        context["volume_source"] = image
                    elif(volume["volume_source_type"] == "snapshot_source"):
                        snapshot = api.cinder.volume_snapshot_get(
                            self.request,
                            volume["snapshot_source"])
                        context["volume_source"] = snapshot
                    context["volume_source_error"] = False
                except Exception:
                    context["volume_source_error"] = True
            elif ticket.type == "instance":
                context["instance"] = json.loads(ticket.context)
                context["flavor"] = api.nova.flavor_get(
                    self.request, context["instance"]["flavor"])
            elif ticket.type == "resize_volume":
                context["volume"] = json.loads(ticket.context)
            elif ticket.type == "resize_instance":
                context["instance"] = json.loads(ticket.context)
            else:
                # ticket.type == "normal"
                context["description"] = ticket.description
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        ticket_id = self.kwargs['ticket_id']
        try:
            return db_api.ticket_get_by_id(self.request, ticket_id)
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve ticket details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        ticket = self._get_object()
        return {'ticket_id': ticket['id']}


class CreateView(views.CreateView):
    def post(self, request, *args, **kwargs):
        ticket_id = self.kwargs['ticket_id']
        ticket = db_api.ticket_get_by_id(self.request, ticket_id)
        request.POST.update(json.loads(ticket.context))
        return super(CreateView, self).post(request, *args, **kwargs)


class Ticket(object):
    def __init__(self, id, title, description, status,
                 status_desc, created_at):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.status_desc = status_desc
        self.created_at = created_at


class TicketReply(object):
    def __init__(self, id, user_id, create_time, content, user_name, is_admin):
        self.id = id
        self.user_id = user_id
        self.create_time = create_time
        self.content = content
        self.user_name = user_name
        self.is_admin = is_admin


class DetailView(forms.ModalFormView):
    form_class = project_forms.CreateForm
    template_name = 'openstack_plus/tickets/detail.html'
    success_url = "horizon:openstack_plus:tickets:detail"

    @memoized.memoized_method
    def _get_user_list(self):
        try:
            users = api.keystone.user_list(self.request)
        except Exception:
            users = []
            msg = _('Unable to retrieve ticket users information.')
            exceptions.handle(self.request, msg)

        user_dict = SortedDict([(u.id, u) for u in users])
        return user_dict

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
        reply_list = []
        user_dict = self._get_user_list()
        for reply in all_ticket_reply:
            created_time = timeutils.format_time(reply.created_at)
            user = user_dict.get(reply['user_id'], None)
            user_name = getattr(user, 'name', None)
            reply_list.append(TicketReply(reply.id, reply.user_id,
                              created_time, reply.content,
                              user_name, reply.is_admin))
        context["ticket"] = ticket
        context["ticket_id"] = ticket_id
        context["all_ticket_reply"] = reply_list

        return context

    def get_initial(self):
        return {'ticket_id': self.kwargs["ticket_id"]}

    def get_success_url(self, **kwargs):
        ticket_id = self.kwargs['ticket_id']
        return reverse(self.success_url,
                       kwargs={"ticket_id": ticket_id})
