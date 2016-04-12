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

import ast
import json
import logging

from django.core.urlresolvers import reverse
from django.forms import ValidationError  # noqa
from django.template.defaultfilters import filesizeformat  # noqa
from django.utils import text
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions

from openstack_dashboard import api
from openstack_dashboard.api import glance
from openstack_dashboard.usage import quotas

from openstack_dashboard.contrib.custom.api import cinder as animbus_cinder
from openstack_dashboard.contrib.custom.db import api as db_api

from openstack_auth import views as auth_views

LOG = logging.getLogger(__name__)


class EditTicket(forms.SelfHandlingForm):
    CHOICES = [('closed', _('Close')),
               ('feedback', _('Feedback')),
               ('resolved', _('Resolved'))]
    status = forms.ChoiceField(choices=CHOICES,
                               widget=forms.RadioSelect(),
                               label=_("Status"),
                               initial='resolved')
    reply = forms.CharField(max_length=2550,
                            widget=forms.Textarea, label=_("Reply"))
    ticket_id = forms.CharField(widget=forms.HiddenInput())

    failure_url = 'horizon:openstack_plus:tickets:index'

    def handle(self, request, data):
        try:
            ticket_id = data["ticket_id"]
            if data["status"] in ['closed', 'resolved']:
                status = 'closed'
            else:
                status = data["status"]
            values = {"status": status, "reply": data["reply"]}
            db_api.ticket_update(request, ticket_id, values)
            ticket = db_api.ticket_get_by_id(request, ticket_id)
            reply_title = "%s_reply" % (ticket.title)
            reply_values = {'user_id': request.user.id,
                            'project_id': request.user.tenant_id,
                            'ticket_id': ticket_id,
                            'title': reply_title,
                            'content': data['reply'],
                            'is_admin': True}

            db_api.ticket_reply_create(request, reply_values)
            ticket = db_api.ticket_get_by_id(request, ticket_id)
            if ticket.type == 'quota' and data["status"] == 'resolved':
                context = ast.literal_eval(ticket.context)
                cinder_data = {'gigabytes': context["gigabytes"],
                               'volumes': context["volumes"]}
                nova_data = {"instances": context["instances"],
                             "cores": context["cores"], "ram": context["ram"],
                             "security_groups": context["security_groups"],
                             "key_pairs": context["keypair"]}
                neutron_data = {"floatingip": context["floating_ips"],
                                "router": context["router"],
                                "port": context["port"],
                                "network": context["network"],
                                "subnet": context["subnet"]}
                api.nova.tenant_quota_update(request,
                                             ticket.project_id,
                                             **nova_data)
                api.cinder.tenant_quota_update(request,
                                               ticket.project_id,
                                               **cinder_data)
                api.neutron.tenant_quota_update(request,
                                                ticket.project_id,
                                                **neutron_data)
            elif ticket.type == 'volume' and data["status"] == 'resolved':
                self.create_volume(request, ticket)
            elif ticket.type == 'instance' and data["status"] == 'resolved':
                self.create_instance(request, ticket)
            elif (ticket.type == 'resize_volume' and
                  data["status"] == 'resolved'):
                self.extend_volume(request, ticket)
            elif (ticket.type == 'resize_instance' and
                  data["status"] == 'resolved'):
                self.server_resize(request, ticket)
            msg = _('Ticket was successfully updated.')
            LOG.debug(msg)
            messages.success(request, msg)
            return ticket
        except Exception:
            msg = _('Unable to update ticket')
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)

    def server_resize(self, request, ticket):
        data = json.loads(ticket.context)
        instance_id = data.get('instance_id', None)
        flavor = data.get('flavor', None)
        disk_config = data.get('disk_config', None)
        try:
            api.nova.server_resize(request, instance_id, flavor, disk_config)
            return True
        except Exception:
            return False

    def extend_volume(self, request, ticket):
        data = json.loads(ticket.context)
        try:
            volume = api.cinder.volume_extend(request,
                                              data['volume_id'],
                                              data['new_size'])

            message = _('Extending volume: "%s"') % data['name']
            messages.info(request, message)
            return volume
        except Exception:
            redirect = reverse("horizon:project:volumes:index")
            exceptions.handle(request,
                              _('Unable to extend volume.'),
                              redirect=redirect)

    def create_volume(self, request, ticket):
        data = json.loads(ticket.context)
        admin_id = request.user.tenant_id

        self.add_role(request, ticket)

        # code refrence project/volumes/volumes/forms.py
        usages = quotas.tenant_quota_usages(request, ticket.project_id)
        # TODO(xuanmingyi) must test
        availableGB = usages['gigabytes']['available']
        availableVol = usages['volumes']['available']

        snapshot_id = None
        image_id = None
        volume_id = None
        source_type = data.get('volume_source_type', None)
        az = data.get('available_zone', None) or None
        if (data.get("snapshot_source", None) and
                source_type in [None, 'snapshot_source']):
            # Create from Snapshot
            # TODO(xuanmingyi) why?
            auth_views.switch(request, ticket.project_id)
            snapshot = animbus_cinder.volume_snapshot_get(
                request,
                data["snapshot_source"])
            auth_views.switch(request, admin_id)
            snapshot_id = snapshot.id
            if (data['size'] < snapshot.size):
                error_message = _('The volume size cannot be less than '
                                  'the snapshot size (%sGB)') % snapshot.size
                raise ValidationError(error_message)
            az = None
        elif (data.get("image_source", None) and
                source_type in [None, "image_source"]):
            image = glance.image_get(request,
                                     data["image_source"])
            image_id = image.id
            image_size = functions.bytes_to_gigabytes(
                image.size)
            if (data['size'] < image_size):
                error_message = _(
                    'The volume size cannot be less than '
                    'the image size (%s)') % filesizeformat(image.size)
                raise ValidationError(error_message)
            properties = getattr(image, 'properties', {})
            min_disk_size = (getattr(image, 'min_disk', 0) or
                             properties.get('min_disk', 0))
            if (min_disk_size > 0 and data['size'] < min_disk_size):
                error_message = _(
                    'The volume size cannot be less than '
                    'the image minimum disk size (%sGB)') % min_disk_size
                raise ValidationError(error_message)
        elif (data.get("volume_source", None) and
              source_type in [None, 'volume_source']):
            auth_views.switch(request, ticket.project_id)
            volume = animbus_cinder.volume_get(request, data["volume_source"])
            auth_views.switch(request, admin_id)
            volume_id = volume.id

            if data['size'] < volume.size:
                error_message = _(
                    'The volume size cannot be less than '
                    'the source volume size (%sGB)') % volume.size
                raise ValidationError(error_message)
        else:
            if type(data['size']) is str:
                data['size'] = int(data['size'])

        if availableGB < data['size']:
            error_message = _('A volume of %(req)iGB cannot be created as '
                              'you only have %(avail)iGB of your quota '
                              'available.')
            params = {'req': data['size'],
                      'avail': availableGB}
            raise ValidationError(error_message, params)
        elif availableVol <= 0:
            error_message = _('You are already using all of your available'
                              ' volumes.')
            raise ValidationError(error_message)
        auth_views.switch(request, ticket.project_id)

        volume = animbus_cinder.volume_create(request,
                                              data['size'],
                                              data['name'],
                                              data['description'],
                                              data['type'],
                                              snapshot_id=snapshot_id,
                                              image_id=image_id,
                                              metadata={},
                                              availability_zone=az,
                                              source_volid=volume_id,
                                              project_id=ticket.project_id)

        auth_views.switch(request, admin_id)

    def create_instance(self, request, ticket):
        context = json.loads(ticket.context)
        admin_id = request.user.tenant_id
        custom_script = context.get('script_data', '')
        dev_mapping_1 = None
        dev_mapping_2 = None

        image_id = ''

        source_type = context.get('source_type', None)
        if source_type in ['image_id', 'instance_snapshot_id']:
            image_id = context['source_id']
        elif source_type in ['volume_id', 'volume_snapshot_id']:
            dev_mapping_1 = {
                context['device_name']: '%s::%s' % (
                    context['source_id'],
                    int(bool(context['delete_on_terminate'])))}
        elif source_type == 'volume_image_id':
            dev_mapping_2 = [
                {'device_name': str(context['device_name']),
                 'source_type': 'image',
                 'destination_type': 'volume',
                 'delete_on_termination':
                     int(bool(context['delete_on_terminate'])),
                 'uuid': context['source_id'],
                 'boot_index': '0',
                 'volume_size': context['volume_size']
                 }
            ]

        netids = context.get('network_id', None)
        if netids:
            nics = [{"net-id": netid, "v4-fixed-ip": ""}
                    for netid in netids]
        else:
            nics = None

        avail_zone = context.get('availability_zone', None)

        self.add_role(request, ticket)

        auth_views.switch(request, ticket.project_id)

        if api.neutron.is_port_profiles_supported():
            net_id = context['network_id'][0]
            LOG.debug("Horizon->Create Port with %(netid)s %(profile_id)s",
                      {'netid': net_id, 'profile_id': context['profile_id']})
            port = None
            try:
                port = api.neutron.port_create(
                    request, net_id, policy_profile_id=context['profile_id'])
            except Exception:
                msg = (_('Port not created for profile-id (%s).') %
                       context['profile_id'])
                exceptions.handle(request, msg)
            if port and port.id:
                nics = [{"port-id": port.id}]

        api.nova.server_create(request,
                               context['name'],
                               image_id,
                               context['flavor'],
                               context['keypair_id'],
                               text.normalize_newlines(custom_script),
                               context['security_group_ids'],
                               block_device_mapping=dev_mapping_1,
                               block_device_mapping_v2=dev_mapping_2,
                               nics=nics,
                               availability_zone=avail_zone,
                               instance_count=int(context['count']),
                               admin_pass=context['admin_pass'],
                               disk_config=context.get('disk_config'),
                               config_drive=context.get('config_drive'))

        auth_views.switch(request, admin_id)

    def add_role(self, request, ticket):
        available_roles = api.keystone.role_list(request)
        current_roles = api.keystone.roles_for_user(request,
                                                    request.user.id,
                                                    ticket.project_id)
        member_role = filter(lambda x: x.name == "_member_",
                             available_roles)[0]
        if member_role not in current_roles:
            api.keystone.add_tenant_user_role(
                request,
                project=ticket.project_id,
                user=request.user.id,
                role=member_role.id)


class CreateForm(forms.SelfHandlingForm):
    reply = forms.CharField(max_length=10000,
                            widget=forms.Textarea,
                            label=_("Ticket Reply"))

    def handle(self, request, data):
        ticket_id = self.initial['ticket_id']
        ticket = db_api.ticket_get_by_id(self.request, ticket_id)
        title = "%s_reply" % (ticket.title)
        try:
            values = {'user_id': request.user.id,
                      'project_id': request.user.tenant_id,
                      'ticket_id': ticket_id,
                      'title': title,
                      'content': data['reply'],
                      'is_admin': True}

            db_api.ticket_reply_create(request, values)
            if ticket.status == "new":
                values = {"status": "feedback"}
                db_api.ticket_update(request, ticket_id, values)
        except Exception:
            exceptions.handle(request, ignore=True)
            return False
        return True
