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

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms

from openstack_dashboard.contrib.custom.db import api as db_api

LOG = logging.getLogger(__name__)


class UpdateForm(forms.SelfHandlingForm):
    instances = forms.IntegerField(min_value=-1, label=_("Instances"))
    cores = forms.IntegerField(min_value=-1, label=_("VCPUs"))
    ram = forms.IntegerField(min_value=-1, label=_("RAM (MB)"))
    floating_ips = forms.IntegerField(min_value=-1, label=_("Floating IPs"))
    router = forms.IntegerField(min_value=-1, label=_("Routers"))
    port = forms.IntegerField(min_value=-1, label=_("Ports"))
    network = forms.IntegerField(min_value=-1, label=_("Networks"))
    subnet = forms.IntegerField(min_value=-1, label=_("Subnets"))
    volumes = forms.IntegerField(min_value=-1, label=_("Volumes"))
    gigabytes = forms.IntegerField(
        min_value=-1, label=_("Total Size of Volumes and Snapshots (GB)"))
    security_groups = forms.IntegerField(
        min_value=-1,
        label=_("Security Groups"))
    keypair = forms.IntegerField(min_value=-1, label=_("Key Pairs"))
    description = forms.CharField(
        max_length=255,
        widget=forms.Textarea,
        label=_("Description"),
        required=False)

    def __init__(self, request, *args, **kwargs):
        super(UpdateForm, self).__init__(request, *args, **kwargs)

    def handle(self, request, data):
        pass
        # super(UpdateForm, self).clean()


class CreateForm(forms.SelfHandlingForm):
    reply = forms.CharField(
        max_length=10000, widget=forms.Textarea, label=_("Ticket Reply"))

    def handle(self, request, data):
        ticket_id = self.initial['ticket_id']
        ticket = db_api.ticket_get_by_id(self.request, ticket_id)
        title = "%s_reply" % (ticket.title)
        try:
            values = {'user_id': request.user.id,
                      'project_id': request.user.tenant_id,
                      'ticket_id': ticket_id,
                      'title': title,
                      'content': data['reply']}

            db_api.ticket_reply_create(request, values)
        except Exception:
            exceptions.handle(request, ignore=True)
            return False
        return True
