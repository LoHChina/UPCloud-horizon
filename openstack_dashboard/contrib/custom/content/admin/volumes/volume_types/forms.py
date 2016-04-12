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
import collections

import django
from django.core.urlresolvers import reverse
from django.forms import ValidationError  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import cinder

from openstack_dashboard.dashboards.admin.volumes.volume_types \
    import forms as project_forms


class CreateVolumeType(project_forms.CreateVolumeType):
    backend = forms.ChoiceField(label=_("Backend"),
                                required=False)

    def __init__(self, request, *args, **kwargs):
        super(CreateVolumeType, self).__init__(request, *args, **kwargs)
        services = cinder.service_list(request)
        choice = []
        for service in services:
            if service.binary == 'cinder-volume':
                host = service.host
                try:
                    new_choice = host.split("@")[1]
                except Exception:
                    new_choice = []
                if new_choice:
                    choice.append((new_choice, new_choice))
        if len(choice) == 0:
            choice = (("",
                       _("No backend found.(Will not set with a backend)")),)
        else:
            choice.insert(0, ("", _("Do not set with a backend")))
        self.fields['backend'].choices = choice
        ordering = ['name', 'backend', 'vol_type_description']
        # Starting from 1.7 Django uses OrderedDict for fields and keyOrder
        # no longer works for it
        if django.VERSION >= (1, 7):
            self.fields = collections.OrderedDict(
                (key, self.fields[key]) for key in ordering)
        else:
            self.fields.keyOrder = ordering

    def handle(self, request, data):
        try:
            # Remove any new lines in the public key
            volume_type = cinder.volume_type_create(
                request,
                data['name'],
                data['vol_type_description'])
            backend = data['backend']
            if backend:
                key = 'volume_backend_name'
                value = backend
                cinder.volume_type_extra_set(request,
                                             volume_type.id,
                                             {key: value})
            messages.success(request, _('Successfully created volume type: %s')
                             % data['name'])
            return volume_type
        except Exception as e:
            if getattr(e, 'code', None) == 409:
                msg = _('Volume type name "%s" already '
                        'exists.') % data['name']
                self._errors['name'] = self.error_class([msg])
            else:
                redirect = reverse("horizon:admin:volumes:index")
                exceptions.handle(request,
                                  _('Unable to create volume type.'),
                                  redirect=redirect)
