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

from openstack_dashboard.dashboards.identity.users \
    import forms as project_froms

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages

from openstack_dashboard import api

need_not_display = ["service", "services", ]
LOG = logging.getLogger(__name__)


class CreateUserForm(project_froms.CreateUserForm):
    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        project_choices = self.fields['project'].choices
        show_system_service = getattr(
            self.request, 'show_system_service', False)
        if not show_system_service:
            project_choices = filter(
                lambda x: x[1] not in need_not_display, project_choices)

        self.fields['project'].choices = project_choices

    def handle(self, request, data):
        domain = api.keystone.get_default_domain(self.request)
        try:
            LOG.info('Creating user with name "%s"' % data['name'])
            desc = data["description"]
            if "email" in data:
                data['email'] = data['email'] or None
            new_user = \
                api.keystone.user_create(request,
                                         name=data['name'],
                                         email=data['email'],
                                         description=desc,
                                         password=data['password'],
                                         project=data['project'] or None,
                                         enabled=data['enabled'],
                                         domain=domain.id)
            messages.success(request,
                             _('User "%s" was successfully created.')
                             % data['name'])
            if data['project'] and data['role_id']:
                roles = api.keystone.roles_for_user(request,
                                                    new_user.id,
                                                    data['project']) or []
                assigned = [role for role in roles if role.id == str(
                    data['role_id'])]
                if not assigned:
                    try:
                        api.keystone.add_tenant_user_role(request,
                                                          data['project'],
                                                          new_user.id,
                                                          data['role_id'])
                    except Exception:
                        exceptions.handle(request,
                                          _('Unable to add user '
                                            'to primary project.'))
            return new_user
        except exceptions.Conflict:
            system_services = []
            for i, service in enumerate(self.request.user.service_catalog):
                service['id'] = i
                system_services.append(
                    api.keystone.Service(
                        service, self.request.user.services_region).name)
            if data['name'] in system_services:
                msg = _('This is a system user, unable to create.')
                messages.error(request, msg)
            else:
                msg = _('User name "%s" is already used.') % data['name']
                messages.error(request, msg)

        except Exception:
            exceptions.handle(request, _('Unable to create user.'))


class UpdateUserForm(project_froms.UpdateUserForm):
    def __init__(self, request, *args, **kwargs):
        super(UpdateUserForm, self).__init__(request, *args, **kwargs)
        project_choices = self.fields['project'].choices
        show_system_service = getattr(
            request, 'show_system_service', False)
        if not show_system_service:
            project_choices = filter(
                lambda x: x[1] not in need_not_display, project_choices)

        self.fields['project'].choices = project_choices
