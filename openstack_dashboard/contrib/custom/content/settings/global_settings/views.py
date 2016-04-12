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

import json

from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from horizon import forms

from openstack_dashboard.contrib.custom.content.settings.global_settings \
    import forms as sys_setttings_forms
from openstack_dashboard.contrib.custom.db import api as db_api


FEATURE_SWITCH = (
    ('enable_advanced_options',
     _('Enable the "Advanced Options" when creating VM'), True),
    ('enable_access_security',
     _('Enable the options in "Access & Security" when creating VM'), True),
    ('enable_post_creation',
     _('Enable the Post-Creation tab when creating VM'), True),
    ('enable_admin_project',
     _('Enable the admin\'s privilege to create VMs'), True),
    ('simplify_vmcreate_option',
     _('Simplify the options in "Instance Boot Source" when creating VM'),
     True),
    ('enable_image_upload_delete',
     _('Enable the function to upload and delete images'), True),
    ('show_system_service',
     _('Show OpenStack system services in user list'), True),
    ('enable_user_statistics',
     _('Enable the user login statistics for admin'), True),
    ('enable_app_store', _('Enable App Store'), True),
    ('enable_hypervisor_overcommit',
     _('Enable hypervisor show the overcommitment ratio'), True),
    ('enable_metering_feature', _('Enable Metering Feature(Beta)'), False),
    ('enable_storage_qos_feature',
     _('Enable Storage QoS Feature(Beta)'), False),
    ('enable_network_overlay',
     _('Enable advanced network overlay features(Beta)'), False),
    ('enable_vmware', _('Enable VMware Integration Plug-in(Beta)'), False),
    ('enable_fix_ip', _('Enable Fixed IP allocation feature(Beta)'), False),
    ('enable_select_host',
     _('Enable host selection when creating a virtual machine(Beta)'), False),
    ('enabel_vxlan',
     _('Enable VXLAN acceleration(Beta, specified HW is required)'), False),
    ('enable_firewall', _('Enable Software Defined Firewall(Beta)'), False),
    ('enable_role_ticket',
     _('Enable Role Ticket with Instance and Volume(Beta)'), False),
    ('enable_autobackup', _('Enable Auto Backup(Beta)'), False),
    ('enable_register', _('Enable Register(Beta)'), False),
)


class IndexView(forms.ModalFormView):
    form_class = sys_setttings_forms.SysSettingsForm
    template_name = 'settings/global_settings/index.html'
    success_url = reverse_lazy("horizon:settings:global_settings:index")

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['features'] = []
        # Retrieve Global Settings
        for feature in FEATURE_SWITCH:
            feature_value = False
            feature_key, feature_desc, default_enable = feature
            feature_setting = db_api.global_settings_get_by_name(
                self.request, feature_key)
            feature_value_from_request = getattr(
                self.request, feature_key, False)
            feature_enable = getattr(
                feature_setting, 'enable', default_enable)
            context['features'].append(
                (feature_desc,
                 feature_value_from_request or feature_value,
                 feature_key,
                 feature_enable))

        return context

    def get_initial(self):
        names = ['monitor_url', 'log_url', 'ceph_monitor_url']
        all_url = {}
        for name in names:
            url_settings = db_api.global_settings_get_by_name(
                self.request, name)
            try:
                all_url[name] = url_settings.extra
            except Exception:
                all_url[name] = ''

        return all_url


class GlobalSettingsView(TemplateView):

    def post(self, request, *args, **kwargs):
        data = dict(request.POST)
        data.pop('csrfmiddlewaretoken')
        for k, v in data.items():
            if 'false' in v:
                data[k] = 0
            elif 'true' in v:
                data[k] = 1
            else:
                data[k] = v[0]
        try:
            db_api.global_settings_update_by_name(request, data)
        except Exception:
            raise Exception("Could not update global settings.")
        return HttpResponse(json.dumps({}),
                            content_type='application/json')


class UnlockView(forms.ModalFormView):
    form_class = sys_setttings_forms.UnlockForm
    template_name = 'settings/global_settings/unlock.html'
    success_url = reverse_lazy('horizon:settings:global_settings:index')

    def get_context_data(self, **kwargs):
        context = super(UnlockView, self).get_context_data(**kwargs)
        context["feature_key"] = self.kwargs['feature_key']
        return context

    def get_initial(self):
        return {'feature_key': self.kwargs['feature_key']}
