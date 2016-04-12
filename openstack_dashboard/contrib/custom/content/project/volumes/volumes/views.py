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
from horizon import exceptions
from horizon import forms

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard.contrib.custom.content.project.volumes.volumes\
    import forms as project_forms

from openstack_dashboard.contrib.custom.api import cinder


class AutoBackupView(forms.ModalFormView):
    form_class = project_forms.AutoBackupForm
    template_name = 'project/volumes/volumes/backup.html'
    success_url = reverse_lazy("horizon:project:volumes:index")

    def get_object(self):
        if not hasattr(self, "_object"):
            vol_id = self.kwargs['volume_id']
            try:
                self._object = cinder.volume_get(self.request, vol_id)
            except Exception:
                msg = _('Unable to retrieve volume.')
                url = reverse('horizon:project:volumes:index')
                exceptions.handle(self.request, msg, redirect=url)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(AutoBackupView, self).get_context_data(**kwargs)
        volume = self.get_object()
        context["volume"] = volume
        return context

    def get_initial(self):
        volume = self.get_object()
        return {"volume_id": volume.id}
