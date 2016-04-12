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


from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api

INDEX_URL = "horizon:identity:projects:index"
PROJECT_USER_MEMBER_SLUG = "update_members"


class UpdateProjectMembersAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(UpdateProjectMembersAction, self).__init__(request,
                                                         *args,
                                                         **kwargs)
        err_msg = _('Unable to retrieve user list. Please try again later.')
        # Use the domain_id from the project
        domain_id = self.initial.get("domain_id", None)
        project_id = ''
        if 'project_id' in self.initial:
            project_id = self.initial['project_id']

        # Get the default role
        try:
            default_role = api.keystone.get_default_role(self.request)
            # Default role is necessary to add members to a project
            if default_role is None:
                default = getattr(settings,
                                  "OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
                msg = (_('Could not find default role "%s" in Keystone') %
                       default)
                raise exceptions.NotFound(msg)
        except Exception:
            exceptions.handle(self.request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        default_role_name = self.get_default_role_field_name()
        self.fields[default_role_name] = forms.CharField(required=False)
        self.fields[default_role_name].initial = default_role.id

        # Get list of available users
        all_users = []
        try:
            all_users = api.keystone.user_list(request,
                                               domain=domain_id)
            services = []
            for i, service in enumerate(self.request.user.service_catalog):
                service['id'] = i
                services.append(
                    api.keystone.Service(
                        service, self.request.user.services_region).name)
            show_system_service = getattr(
                self.request, 'show_system_service', False)
            if not show_system_service:
                need_not_display = services
                # need_not_display.append('admin')
                all_users = filter(lambda x: x.name not in
                                   need_not_display, all_users)
        except Exception:
            exceptions.handle(request, err_msg)
        users_list = [(user.id, user.name) for user in all_users]

        # Get list of roles
        role_list = []
        try:
            role_list = api.keystone.role_list(request)
        except Exception:
            exceptions.handle(request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        for role in role_list:
            field_name = self.get_member_field_name(role.id)
            label = role.name
            self.fields[field_name] = forms.MultipleChoiceField(required=False,
                                                                label=label)
            self.fields[field_name].choices = users_list
            self.fields[field_name].initial = []

        # Figure out users & roles
        if project_id:
            try:
                users_roles = api.keystone.get_project_users_roles(request,
                                                                   project_id)
            except Exception:
                exceptions.handle(request,
                                  err_msg,
                                  redirect=reverse(INDEX_URL))

            for user_id in users_roles:
                roles_ids = users_roles[user_id]
                for role_id in roles_ids:
                    field_name = self.get_member_field_name(role_id)
                    self.fields[field_name].initial.append(user_id)

    class Meta(object):
        name = _("Project Members")
        slug = PROJECT_USER_MEMBER_SLUG
