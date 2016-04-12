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


from openstack_dashboard.api import cinder
from openstack_dashboard.contrib.custom.db import api as db_api
from openstack_dashboard.contrib.custom.utils import common_utils
from openstack_dashboard.dashboards.project.volumes.volumes \
    import forms as project_forms
from openstack_dashboard.dashboards.project.volumes.volumes import views
from openstack_dashboard import exceptions as dashboard_exception
from openstack_dashboard.usage import quotas

from django import shortcuts

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils import encoding
from django.utils.translation import ugettext_lazy as _

import json

from horizon import exceptions
from horizon import forms


TICKET_INDEX = "horizon:project_openstack_plus:project_tickets:index"


class ContribCreateForm(project_forms.CreateForm):
    def handle(self, request, data):
        if common_utils.need_ticket(request):
            description = unicode(_("Volume: {0}GB"))
            description = description.format(data["size"])
            values = {'user_id': request.user.id,
                      'project_id': request.user.tenant_id,
                      'title': unicode(_("Apply Volume")),
                      'description': description,
                      'context': json.dumps(data),
                      'status': "new",
                      'type': 'volume'}
            db_api.ticket_create(request, values)
            return shortcuts.redirect(reverse(TICKET_INDEX))
        else:
            super(ContribCreateForm, self).handle(request, data)
            return True


class CreateView(forms.ModalFormView):
    form_class = ContribCreateForm
    modal_header = _("Create Volume")
    template_name = 'project/volumes/volumes/create.html'
    submit_label = _("Create Volume")
    submit_url = reverse_lazy("horizon:project:volumes:volumes:create")
    success_url = reverse_lazy('horizon:project:volumes:volumes_tab')
    page_title = _("Create a Volume")

    def get_context_data(self, **kwargs):
        if common_utils.need_ticket(self.request):
            self.modal_header = _("Apply Volume")
            self.submit_label = _("Apply Volume")
        context = super(CreateView, self).get_context_data(**kwargs)
        try:
            context['usages'] = quotas.tenant_limit_usages(self.request)
            context['volume_types'] = self._get_volume_types()
        except Exception:
            exceptions.handle(self.request)
        return context

    def _get_volume_types(self):
        try:
            volume_types = cinder.volume_type_list(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume type list.'))

        # check if we have default volume type so we can present the
        # description of no volume type differently
        default_type = None
        try:
            default_type = cinder.volume_type_default(self.request)
        except dashboard_exception.NOT_FOUND:
            pass

        if default_type is not None:
            d_name = getattr(default_type, "name", "")
            message =\
                _("If \"No volume type\" is selected, the default "
                  "volume type \"%(name)s\" will be set for the "
                  "created volume.")
            params = {'name': d_name}
            no_type_description = encoding.force_text(message % params)
        else:
            message = \
                _("If \"No volume type\" is selected, the volume will be "
                  "created without a volume type.")

            no_type_description = encoding.force_text(message)

        type_descriptions = [{'name': 'no_type',
                              'description': no_type_description}] + \
                            [{'name': type.name,
                              'description': getattr(type, "description", "")}
                             for type in volume_types]

        return json.dumps(type_descriptions)


class ContribExtendForm(project_forms.ExtendForm):
    def handle(self, request, data):
        if common_utils.need_ticket(request):
            description = unicode(_("Resize Volume: {0}GB"))
            description = description.format(data["new_size"])
            data["volume_id"] = self.initial['id']
            values = {'user_id': request.user.id,
                      'project_id': request.user.tenant_id,
                      'title': unicode(_("Apply Extend Volume")),
                      'description': description,
                      'context': json.dumps(data),
                      'status': "new",
                      'type': 'resize_volume'}
            db_api.ticket_create(request, values)
            return shortcuts.redirect(reverse(TICKET_INDEX))
        else:
            super(ContribExtendForm, self).handle(request, data)
            return True


class ExtendView(forms.ModalFormView):
    form_class = ContribExtendForm
    modal_header = _("Extend Volume")
    template_name = 'project/volumes/volumes/extend.html'
    submit_label = _("Extend Volume")
    submit_url = "horizon:project:volumes:volumes:extend"
    success_url = reverse_lazy("horizon:project:volumes:index")
    page_title = _("Extend Volume")

    def get_object(self):
        if not hasattr(self, "_object"):
            volume_id = self.kwargs['volume_id']
            try:
                self._object = cinder.volume_get(self.request, volume_id)
            except Exception:
                self._object = None
                exceptions.handle(self.request,
                                  _('Unable to retrieve volume information.'))
        return self._object

    def get_context_data(self, **kwargs):
        if common_utils.need_ticket(self.request):
            self.modal_header = "Apply Extend Volume"
            self.submit_label = "Apply Extend Volume"
        context = super(ExtendView, self).get_context_data(**kwargs)
        context['volume'] = self.get_object()
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        try:
            usages = quotas.tenant_limit_usages(self.request)
            usages['gigabytesUsed'] = (usages['gigabytesUsed']
                                       - context['volume'].size)
            context['usages'] = usages
        except Exception:
            exceptions.handle(self.request)
        return context

    def get_initial(self):
        volume = self.get_object()
        return {'id': self.kwargs['volume_id'],
                'name': volume.name,
                'orig_size': volume.size}


views.CreateView = CreateView
views.ExtendView = ExtendView
