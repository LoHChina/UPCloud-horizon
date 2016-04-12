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

from django.utils import encoding
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.contrib.custom.db import api as db_api


class EmailSettingsForm(forms.SelfHandlingForm):
    email_host = forms.CharField(
        max_length=60,
        label=_("Email Host"),
        widget=forms.TextInput(attrs={'placeholder': 'smtp.example.com'}))
    email_port = forms.IntegerField(
        min_value=-1,
        label=_("Email Port"),
        widget=forms.TextInput(attrs={'placeholder': '25'}))
    email_host_user = forms.EmailField(
        max_length=100,
        label=_("Email Host User"),
        widget=forms.TextInput(attrs={'placeholder': 'animbus@example.com'}))
    email_host_password = forms.CharField(
        max_length=60,
        label=_("Email Host Password"),
        widget=forms.PasswordInput(render_value=True))

    def handle(self, request, data):
        try:
            email_settings = db_api.email_settings_get_all(self.request)
            if email_settings:
                values = {"email_host": data["email_host"],
                          "email_port": data["email_port"],
                          "email_host_user": data["email_host_user"],
                          "email_host_password": data["email_host_password"]}
                db_api.email_settings_update(request,
                                             email_settings[0].id, values)
            else:
                values = {'email_host': data["email_host"],
                          'email_port': data['email_port'],
                          'email_host_user': data['email_host_user'],
                          'email_host_password': data["email_host_password"]}

                db_api.email_settings_create(request, values)
            messages.success(request,
                             encoding.force_text(_("Settings saved.")))
        except Exception:
            exceptions.handle(request, ignore=True)
            return False
        return True
