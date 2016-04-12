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

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import forms
from openstack_dashboard.contrib.custom.content.settings.email_settings \
    import forms as email_setttings_forms
from openstack_dashboard.contrib.custom.db import api as db_api


class EmailSettingsView(forms.ModalFormView):
    form_class = email_setttings_forms.EmailSettingsForm
    form_id = "email_settings_modal"
    modal_header = _("Email Settings")
    modal_id = "email_settings_modal"
    page_title = _("Email Settings")
    submit_label = _("Save")
    submit_url = reverse_lazy("horizon:settings:email_settings:index")
    success_url = reverse_lazy("horizon:settings:email_settings:index")
    template_name = 'settings/email_settings/settings.html'

    def get_initial(self):
        email_settings = db_api.email_settings_get_all(self.request)
        if email_settings:
            return {'email_host': email_settings[0].email_host,
                    'email_port': email_settings[0].email_port,
                    'email_host_user':
                        email_settings[0].email_host_user,
                    'email_host_password':
                        email_settings[0].email_host_password}
