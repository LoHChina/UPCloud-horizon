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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.contrib.custom.content.openstack_plus.vcenter \
    import utils
from openstack_dashboard.contrib.custom.db import api as db_api
from openstack_dashboard.contrib.custom import settings as animbus_settings


VCENTER_TEMPLATE = getattr(animbus_settings, 'VCENTER_TEMPLATE_SETTINGS', {})
VCENTER_TEMPLATE_CHOICES = VCENTER_TEMPLATE.get('vcenter_template', [])


class VCenterForm(forms.SelfHandlingForm):
    username = forms.CharField(max_length=255, label=_("vCenter UserName"))
    password = forms.CharField(max_length=255, label=_("vCenter Password"))
    host_ip = forms.IPField(label=_("vCenter Address"))
    cluster = forms.CharField(max_length=255, label=_("vCenter Cluster"))

    failure_url = 'horizon:openstack_plus:vcenter:index'

    def handle(self, request, data):
        try:
            db_api.vcenter_create(request, data)
            msg = _('New vCenter Environment successfully.')
            messages.success(request, msg)
            return True
        except Exception:
            msg = _('Unable to new vCenter Environment.')
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)


class LaunchInstanceForm(forms.SelfHandlingForm):
    vcenter_id = forms.CharField(widget=forms.HiddenInput())

    name = forms.CharField(label=_("Instance Name"),
                           max_length=255)

    template = forms.ChoiceField(label=_("Template"),
                                 widget=forms.Select(),
                                 help_text=_("templete for launch instance."))

    def __init__(self, request, *args, **kwargs):
        super(LaunchInstanceForm, self).__init__(request, *args, **kwargs)
        template_choice = [(name) for name in VCENTER_TEMPLATE_CHOICES]
        self.fields['template'].choices = template_choice

    def handle(self, request, data):

        vcenter_id = data.get('vcenter_id')
        instance_name = data.get('name')
        template = data.get('template')
        try:
            si = utils.get_vmware_si(self.request, vcenter_id)
            content = si.RetrieveContent()
            template = utils.get_template(content, template)
            if template:
                utils.clone_vm(
                    content, template, instance_name, si,
                    datacenter_name=None, vm_folder=None,
                    datastore_name=None, cluster_name=None,
                    resource_pool=None, power_on=True)
            messages.success(request, _('Launch instance %s.') % instance_name)
        except Exception:
            exceptions.handle(request, _("Unable to launch instance."))
        return True
