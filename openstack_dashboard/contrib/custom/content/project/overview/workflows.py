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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.contrib.custom.db import api as db_api


class ApplyInfoAction(workflows.Action):
    title = forms.CharField(max_length=60, label=_("Title"),
                            initial=_("Apply Quotas"))
    description = forms.CharField(max_length=255, widget=forms.Textarea,
                                  label=_("Description"))

    class Meta(object):
        name = _("Apply Reason")
        slug = 'apply_info'
        help_text = _("Please input the reason of applying to expand quotas.")


class ApplyInfo(workflows.Step):
    action_class = ApplyInfoAction
    contributes = ("title", "description")


class ApplyQuotaAction(workflows.Action):
    instances = forms.IntegerField(label=_("Instances"))
    cores = forms.IntegerField(min_value=-1, label=_("VCPUs(Core)"))
    ram = forms.IntegerField(min_value=-1, label=_("RAM (MB)"))
    floating_ips = forms.IntegerField(min_value=-1, label=_("Floating IPs"))
    router = forms.IntegerField(min_value=-1, label=_("Routers"))
    port = forms.IntegerField(min_value=-1, label=_("Ports"))
    network = forms.IntegerField(min_value=-1, label=_("Networks"))
    subnet = forms.IntegerField(min_value=-1, label=_("Subnets"))
    volumes = forms.IntegerField(min_value=-1, label=_("Volumes"))
    gigabytes = forms.IntegerField(
        min_value=-1, label=_("Total Size of Volumes and Snapshots (GB)"))
    security_groups = forms.IntegerField(min_value=-1,
                                         label=_("Security Groups"))
    keypair = forms.IntegerField(min_value=-1, label=_("Key Pairs"))

    def __init__(self, request, context, *args, **kwargs):
        super(ApplyQuotaAction, self).__init__(request, context,
                                               *args, **kwargs)
        if getattr(self.request, 'enable_network_overlay', False):
            self.fields['floating_ips'].widget = forms.HiddenInput()
            self.fields['router'].widget = forms.HiddenInput()

    def clean(self):
        nova_quotas = api.nova.tenant_quota_get(self.request,
                                                self.request.user.tenant_id)
        neutron_quotas = api.neutron.tenant_quota_get(self.request,
                                                      self.request.
                                                      user.tenant_id)
        cinder_quotas = api.cinder.default_quota_get(self.request,
                                                     self.request.
                                                     user.tenant_id)
        instances_quota = getattr(nova_quotas.get("instances"),
                                  'limit', float("inf"))
        vcpu_quota = getattr(nova_quotas.get("cores"),
                             'limit', float("inf"))
        ram_quota = getattr(nova_quotas.get("ram"),
                            'limit', float("inf"))
        floating_ips_quota = getattr(nova_quotas.get("floating_ips"),
                                     'limit', float("inf"))
        routers_quota = getattr(neutron_quotas.get("router"),
                                'limit', float("inf"))
        ports_quota = getattr(neutron_quotas.get("port"),
                              'limit', float("inf"))
        networks_quota = getattr(neutron_quotas.get("network"),
                                 'limit', float("inf"))
        subnets_quota = getattr(neutron_quotas.get("subnet"),
                                'limit', float("inf"))
        volume_quota = getattr(cinder_quotas.get("volumes"),
                               'limit', float("inf"))
        volume_bytes_quota = getattr(cinder_quotas.get("gigabytes"),
                                     'limit', float("inf"))
        sg_groups_quota = getattr(nova_quotas.get("security_groups"),
                                  'limit', float("inf"))
        keypairs_quota = getattr(nova_quotas.get("key_pairs"),
                                 'limit', float("inf"))
        cleaned_data = self.cleaned_data
        if cleaned_data['instances'] < instances_quota:
            raise forms.ValidationError('Instance quota value '
                                        'can not be less '
                                        'than the default '
                                        'value: "%s"' % (str(instances_quota)))
        if cleaned_data['cores'] < vcpu_quota:
            raise forms.ValidationError('Cpu quota value '
                                        'can not be less '
                                        'than the default '
                                        'value: "%s"' % (str(vcpu_quota)))
        if cleaned_data['ram'] < ram_quota:
            raise forms.ValidationError('Ram quota value '
                                        'can not be less '
                                        'than the default '
                                        'value: "%s"' % (str(ram_quota)))
        if cleaned_data['floating_ips'] < floating_ips_quota:
            raise forms.ValidationError('Floating ip quota '
                                        'value can not be '
                                        'less than the '
                                        'default value: '
                                        '"%s"' % (str(floating_ips_quota)))
        if cleaned_data['router'] < routers_quota:
            raise forms.ValidationError('Router quota value '
                                        'can not be less '
                                        'than the default '
                                        'value: "%s"' % (str(routers_quota)))
        if cleaned_data['port'] < ports_quota:
            raise forms.ValidationError('Port quota value '
                                        'can not be less '
                                        'than the default '
                                        'value: "%s"' % (str(ports_quota)))
        if cleaned_data['network'] < networks_quota:
            raise forms.ValidationError('Networks quota value '
                                        'can not be less than '
                                        'the default '
                                        'value: "%s"' % (str(networks_quota)))
        if cleaned_data['subnet'] < subnets_quota:
            raise forms.ValidationError('Subnets quota value '
                                        'can not be less '
                                        'than the default '
                                        'value: "%s"' % (str(subnets_quota)))
        if cleaned_data['volumes'] < volume_quota:
            raise forms.ValidationError('Volume quota value '
                                        'can not be less '
                                        'than the default '
                                        'value: "%s"' % (str(volume_quota)))
        if cleaned_data['gigabytes'] < volume_bytes_quota:
            raise forms.ValidationError('Total Size of Volumes '
                                        'and Snapshots quota '
                                        'value can not be '
                                        'less than the '
                                        'default value: '
                                        '"%s"' % (str(volume_bytes_quota)))
        if cleaned_data['security_groups'] < sg_groups_quota:
            raise forms.ValidationError('Security groups '
                                        'quota value can '
                                        'not be less than '
                                        'the default value: '
                                        '"%s"' % (str(sg_groups_quota)))
        if cleaned_data['keypair'] < keypairs_quota:
            raise forms.ValidationError('Key Pairs groups '
                                        'quota value can not '
                                        'be less than the '
                                        'default value: '
                                        '"%s"' % (str(keypairs_quota)))
        if cleaned_data['instances'] == instances_quota and \
           cleaned_data['cores'] == vcpu_quota and \
           cleaned_data['ram'] == ram_quota and \
           cleaned_data['floating_ips'] == floating_ips_quota and \
           cleaned_data['router'] == routers_quota and \
           cleaned_data['port'] == ports_quota and \
           cleaned_data['network'] == networks_quota and \
           cleaned_data['subnet'] == subnets_quota and \
           cleaned_data['volumes'] == volume_quota and \
           cleaned_data['gigabytes'] == volume_bytes_quota and \
           cleaned_data['security_groups'] == sg_groups_quota and \
           cleaned_data['keypair'] == keypairs_quota:
                raise forms.ValidationError(_("At least one must be larger "
                                            "than the default value."))

    def handle(self, request, data):
        try:
            quota_context = {"instances": self.data['instances'],
                             "cores": self.data["cores"],
                             "ram": self.data["ram"],
                             "floating_ips": self.data["floating_ips"],
                             "router": self.data["router"],
                             "port": self.data["port"],
                             "network": self.data["network"],
                             "subnet": self.data["subnet"],
                             "volumes": self.data["volumes"],
                             "gigabytes": self.data["gigabytes"],
                             "security_groups": self.data["security_groups"],
                             "keypair": self.data["keypair"]}
            values = {'user_id': request.user.id,
                      'project_id': request.user.tenant_id,
                      'title': data['title'],
                      'description': data['description'],
                      'context': str(quota_context),
                      'status': "new",
                      'type': 'quota'}

            db_api.ticket_create(request, values)
        except Exception:
            exceptions.handle(request, ignore=True)
            return False
        return True

    class Meta(object):
        name = _("Apply Quotas")
        slug = 'apply_quota'
        help_text = _("From here you can apply to "
                      "expand the default quotas "
                      "(max limits) and at least "
                      "one must be larger "
                      "than the default value.")


class ApplyQuota(workflows.Step):
    action_class = ApplyQuotaAction
    contributes = ('instances', 'cores', 'ram', 'floating_ips',
                   'router', 'port', 'network',
                   'subnet', 'volumes', 'gigabytes',
                   'security_groups', 'keypair')


class UpdateQuota(workflows.Workflow):
    slug = "update_quota"
    name = _("Apply Quotas")
    finalize_button_name = _("Save")
    success_message = _('Apply quotas successfully')
    failure_message = _('Unable to apply quotas.')
    success_url = "horizon:project:overview:index"
    default_steps = (ApplyInfo,
                     ApplyQuota)

    def format_status_message(self, message):
        return "Apply to expand quotas successfully."
