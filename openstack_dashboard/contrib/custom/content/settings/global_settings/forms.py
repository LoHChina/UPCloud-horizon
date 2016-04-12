# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import hashlib

from django.forms import ValidationError  # noqa
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import forms
from horizon import messages

from openstack_dashboard.contrib.custom.db import api as db_api

ENABLE_FEATURE_KEY = '00ef039e8201514d7921177647505d12'
INPUT_FEATURE = {
    'monitor_url': False,
    'log_url': False,
    'ceph_monitor_url': False,
}


class SysSettingsForm(forms.SelfHandlingForm):
    monitor_url = forms.CharField(label=_("Monitoring System(Beta) URL"),
                                  help_text=('monitor_url'))
    log_url = forms.CharField(label=_("Log Analysis(Beta) URL"),
                              help_text=('log_url'))
    ceph_monitor_url = forms.CharField(
        label=_("Ceph Monitor(Beta) URL"),
        help_text=('ceph_monitor_url'))

    def __init__(self, request, *args, **kwargs):
        super(SysSettingsForm, self).__init__(request, *args, **kwargs)
        for field in self.fields:
            feature_settings = db_api.global_settings_get_by_name(
                request, field)
            try:
                feature_enable = feature_settings.enable
                if not feature_enable:
                    self.fields[field].widget.attrs['disabled'] = True
            except Exception:
                feature_enable = True
                if not INPUT_FEATURE[field]:
                    self.fields[field].widget.attrs['disabled'] = True

    def handle(self, request, data):

        return True


class UnlockForm(forms.SelfHandlingForm):
    feature_key = forms.CharField(widget=forms.HiddenInput())
    password = forms.CharField(label=_("Password"),
                               required=True)

    def __init__(self, request, *args, **kwargs):
        super(UnlockForm, self).__init__(request, *args, **kwargs)
        feature_key = kwargs.get('initial', {}).get('feature_key')
        self.fields['feature_key'].initial = feature_key

    def clean(self):
        cleaned_data = super(UnlockForm, self).clean()
        if 'password' in cleaned_data:
            passwd = cleaned_data.get('password')
            enable_feature_hash = hashlib.md5(passwd).hexdigest()
            if enable_feature_hash != ENABLE_FEATURE_KEY:
                raise forms.ValidationError(
                    _("Incorrect password for enable features!"))
        return cleaned_data

    @sensitive_variables('data', 'password')
    def handle(self, request, data):
        feature_key = data['feature_key']
        data = {'name': feature_key, 'enable': 1}
        db_api.global_settings_update_by_name(request, data)
        messages.success(request, _('Enable sucessfully.'))
        return True
