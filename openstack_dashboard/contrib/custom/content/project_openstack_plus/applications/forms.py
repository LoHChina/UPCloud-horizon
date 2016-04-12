# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import collections

import json
import logging

import django
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

import six

from oslo_utils import strutils

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard.contrib.custom.content.project_openstack_plus.applications \
    import constants
from openstack_dashboard.contrib.custom.db import api as db_api
from openstack_dashboard.contrib.custom import settings as animbus_settings
from openstack_dashboard.dashboards.project.stacks \
    import forms as project_forms

LOG = logging.getLogger(__name__)


class UploadApplicationTemplateForm(project_forms.TemplateForm):

    name = forms.CharField(label=_("Application Name"), max_length=255)
    category = forms.ChoiceField(label=_('Category'),
                                 choices=constants.APPLICATION_CATEGORY)
    logo = forms.FileField(label=_("Application Logo"))

    base_choices = [('file', _('File'))]
    url_choice = [('url', _('URL'))]
    attributes = {'class': 'switchable', 'data-slug': 'templatesource'}
    template_source = forms.ChoiceField(label=_('Template Source'),
                                        choices=base_choices + url_choice,
                                        widget=forms.Select(attrs=attributes))

    def __init__(self, *args, **kwargs):
        kwargs['next_view'] = ''
        super(UploadApplicationTemplateForm, self).__init__(*args, **kwargs)
        self.fields['environment_source'].widget = forms.widgets.HiddenInput()
        self.fields['environment_upload'].widget = forms.widgets.HiddenInput()
        self.fields['environment_data'].widget = forms.widgets.HiddenInput()
        ordering = [
            'name', 'category', 'logo', 'template_source', 'template_upload',
            'template_url', 'template_data', 'environment_source',
            'environment_upload', 'environment_data']
        # Starting from 1.7 Django uses OrderedDict for fields and keyOrder
        # no longer works for it
        if django.VERSION >= (1, 7):
            self.fields = collections.OrderedDict(
                (key, self.fields[key]) for key in ordering)
        else:
            self.fields.keyOrder = ordering

    def handle_uploaded_file(self, logo_file):
        logo_path = "%s/%s" % (settings.MEDIA_ROOT, logo_file.name)
        with open(logo_path, 'wb+') as destination:
            for chunk in logo_file.chunks():
                destination.write(chunk)

    def handle(self, request, data):
        template_data = self.create_kwargs(data)
        logo_file = self.request.FILES['logo']

        values = {'user_id': request.user.id,
                  'project_id': request.user.tenant_id,
                  'name': data['name'],
                  'description': '',
                  'website': '',
                  'category': data['category'],
                  'template_data': template_data,
                  'author': request.user.username,
                  'logo': logo_file.name,
                  'is_public': True}

        try:
            self.handle_uploaded_file(logo_file)
            db_api.application_create(request, values)
            message = _('Successfully upload '
                        'application template %s') % values['name']
            messages.info(request, message)
            return True
        except Exception:
            error_message = _(
                'Unable to upload application template %s') % values['name']
            exceptions.handle(request, error_message)
            return False


class CreateAppForm(project_forms.CreateStackForm):

    stack_name = forms.RegexField(
        max_length=255,
        label=_('Application Name'),
        help_text=_('Name of the application to create.'),
        regex=r"^[a-zA-Z][a-zA-Z0-9_.-]*$",
        error_messages={'invalid': _('Name must start with a letter and may '
                                     'only contain letters, numbers, '
                                     'underscores, periods and hyphens.')})

    timeout_mins = forms.IntegerField(
        initial=60,
        label=_('Creation Timeout (minutes)'),
        help_text=_('Application creation timeout in minutes.'))

    def _get_app_password_setting(self):
        app_settings = getattr(animbus_settings, 'ANIMBUS_HEAT_STACK', {})
        return app_settings.get('enable_user_pass', True)

    def _build_parameter_fields(self, template_validate):
        try:
            networks = api.neutron.network_list(self.request)
        except Exception:
            keypairs = []
            exceptions.handle(self.request,
                              _('Unable to retrieve network list.'))

        if self._get_app_password_setting():
            self.fields['password'] = forms.CharField(
                label=_('Password for user "%s"') % self.request.user.username,
                help_text=_('This is required for operations to be performed '
                            'throughout the lifecycle of the application'),
                widget=forms.PasswordInput())

        self.help_text = template_validate['Description']

        params = template_validate.get('Parameters', {})

        if template_validate.get('ParameterGroups'):
            params_in_order = []
            for group in template_validate['ParameterGroups']:
                for param in group.get('parameters', []):
                    if param in params:
                        params_in_order.append((param, params[param]))
        else:
            # no parameter groups, so no way to determine order
            params_in_order = sorted(params.items())
        for param_key, param in params_in_order:
            field_key = self.param_prefix + param_key
            field_args = {
                'initial': param.get('Default', None),
                'label': param.get('Label', param_key),
                'help_text': param.get('Description', ''),
                'required': param.get('Default', None) is None
            }

            param_type = param.get('Type', None)
            hidden = strutils.bool_from_string(param.get('NoEcho', 'false'))
            if 'CustomConstraint' in param:
                choices = self._populate_custom_choices(
                    param['CustomConstraint'])
                field_args['choices'] = choices
                field = forms.ChoiceField(**field_args)

            elif 'AllowedValues' in param:
                choices = map(lambda x: (x, x), param['AllowedValues'])
                field_args['choices'] = choices
                field = forms.ChoiceField(**field_args)

            elif param_type == 'Json' and 'Default' in param:
                field_args['initial'] = json.dumps(param['Default'])
                field = forms.CharField(**field_args)

            elif param_type in ('CommaDelimitedList', 'String', 'Json'):
                if param_key == "key_name":
                    try:
                        keypairs = api.nova.keypair_list(self.request)
                    except Exception:
                        keypairs = []
                        exceptions.handle(
                            self.request,
                            _('Unable to retrieve key pair list.'))
                    field_args['choices'] = (
                        [(key.name, key.name) for key in keypairs])
                    field = forms.ChoiceField(**field_args)
                    self.fields[field_key] = field
                    continue

                if param_key == "private_net_id":
                    field_args['choices'] = (
                        [(net.id, net.name)
                         for net in networks
                         if not net.get('router:external')])
                    field = forms.ChoiceField(**field_args)
                    self.fields[field_key] = field
                    continue

                if param_key == "public_net_id":
                    field_args['choices'] = (
                        [(net.id, net.name)
                         for net in networks if net.get('router:external')])
                    field = forms.ChoiceField(**field_args)
                    self.fields[field_key] = field
                    continue

                if param_key == "private_subnet_id":
                    subnets = []
                    net_subnets = [net.subnets for net in networks
                                   if not net.get('router:external')]
                    for subnet in net_subnets:
                        subnets.extend(subnet)
                    field_args['choices'] = (
                        [(subnet.id, subnet.name) for subnet in subnets])
                    field = forms.ChoiceField(**field_args)
                    self.fields[field_key] = field
                    continue

                if 'MinLength' in param:
                    field_args['min_length'] = int(param['MinLength'])
                    field_args['required'] = param.get('MinLength', 0) > 0
                if 'MaxLength' in param:
                    field_args['max_length'] = int(param['MaxLength'])
                if hidden:
                    field_args['widget'] = forms.PasswordInput()
                field = forms.CharField(**field_args)

            elif param_type == 'Number':
                if 'MinValue' in param:
                    field_args['min_value'] = int(param['MinValue'])
                if 'MaxValue' in param:
                    field_args['max_value'] = int(param['MaxValue'])
                field = forms.IntegerField(**field_args)

            elif param_type in ('Boolean', 'boolean'):
                field = forms.BooleanField(**field_args)

            if field:
                self.fields[field_key] = field

    @sensitive_variables('password')
    def handle(self, request, data):
        prefix_length = len(self.param_prefix)
        params_list = [(k[prefix_length:], v) for (k, v) in six.iteritems(data)
                       if k.startswith(self.param_prefix)]
        fields = {
            'stack_name': data.get('stack_name'),
            'timeout_mins': data.get('timeout_mins'),
            'disable_rollback': not(data.get('enable_rollback')),
            'parameters': dict(params_list),
        }

        if self._get_app_password_setting():
            fields['password'] = data.get('password')

        if data.get('template_data'):
            fields['template'] = data.get('template_data')
        else:
            fields['template_url'] = data.get('template_url')

        if data.get('environment_data'):
            fields['environment'] = data.get('environment_data')

        try:
            api.heat.stack_create(self.request, **fields)
            messages.success(request, _("Application creation started."))
            return True
        except Exception:
            exceptions.handle(request)
