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

from __future__ import division

import datetime

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard.usage.base import BaseUsage as usage_BaseUsage


class BaseUsage(usage_BaseUsage):
    def _get_neutron_usage(self, limits, resource_name):
        resource_map = {
            'floatingip': {
                'api': api.network.tenant_floating_ip_list,
                'limit_name': 'totalFloatingIpsUsed',
                'message': _('Unable to retrieve floating IP addresses.')
            },
            'router': {
                'api': api.neutron.router_list,
                'limit_name': 'totalRoutersUsed',
                'message': _('Unable to retrieve routers.')
            },
            'port': {
                'api': api.neutron.port_list,
                'limit_name': 'totalPortsUsed',
                'message': _('Unable to retrieve ports.')
            },
            'network': {
                'api': api.neutron.network_list_for_tenant,
                'limit_name': 'totalNetworksUsed',
                'message': _('Unable to retrieve networks.')
            },
            'subnet': {
                'api': api.neutron.subnet_list,
                'limit_name': 'totalSunetsUsed',
                'message': _('Unable to retrieve subnets.')
            },
            'keypair': {
                'api': api.nova.keypair_list,
                'limit_name': 'totalKeypairsUsed',
                'message': _('Unable to retrieve keypairs.')
            },
            'security_group': {
                'api': api.network.security_group_list,
                'limit_name': 'totalSecurityGroupsUsed',
                'message': _('Unable to retrieve security groups.')
            }
        }

        resource = resource_map[resource_name]
        try:
            method = resource['api']
            if method.func_name == "network_list_for_tenant":
                current_used = len(method(self.request,
                                   self.request.user.tenant_id))
            else:
                current_used = len(method(self.request))
        except Exception:
            current_used = 0
            msg = resource['message']
            exceptions.handle(self.request, msg)

        limits[resource['limit_name']] = current_used

    def _set_neutron_limit(self, limits, neutron_quotas, resource_name):
        limit_name_map = {
            'floatingip': 'maxTotalFloatingIps',
            'security_group': 'maxSecurityGroups',
            'router': 'maxTotalRouters',
            'port': 'maxTotalPorts',
            'subnet': 'maxTotalSubnets',
            'keypair': 'maxTotalKeypairs',
            'network': 'maxTotalNetworks',
        }

        nova_quotas = api.nova.tenant_quota_get(self.request, self.project_id)

        if neutron_quotas is None:
            resource_max = float("inf")
        else:
            if resource_name == "keypair":
                resource_max = getattr(nova_quotas.get("key_pairs"),
                                       'limit',
                                       float("inf"))
            else:
                resource_max = getattr(neutron_quotas.get(resource_name),
                                       'limit',
                                       float("inf"))
            if resource_max == -1:
                resource_max = float("inf")

        limits[limit_name_map[resource_name]] = resource_max

    def get_neutron_limits(self):
        if not api.base.is_service_enabled(self.request, 'network'):
            return
        try:
            neutron_quotas_supported = (
                api.neutron.is_quotas_extension_supported(self.request))
            neutron_sg_used = (
                api.neutron.is_extension_supported(self.request,
                                                   'security-group'))
            if api.network.floating_ip_supported(self.request):
                self._get_neutron_usage(self.limits, 'floatingip')
            if neutron_sg_used:
                self._get_neutron_usage(self.limits, 'security_group')
            self._get_neutron_usage(self.limits, 'router')
            self._get_neutron_usage(self.limits, 'network')
            self._get_neutron_usage(self.limits, 'subnet')
            self._get_neutron_usage(self.limits, 'port')
            self._get_neutron_usage(self.limits, 'keypair')

            # Quotas are an optional extension in Neutron. If it isn't
            # enabled, assume the floating IP limit is infinite.
            nova_quotas = api.nova.tenant_quota_get(self.request,
                                                    self.project_id)
            if neutron_quotas_supported:
                neutron_quotas = api.neutron.tenant_quota_get(self.request,
                                                              self.project_id)
            else:
                neutron_quotas = None
        except Exception:
            # Assume neutron security group and quotas are enabled
            # because they are enabled in most Neutron plugins.
            neutron_sg_used = True
            neutron_quotas = None
            msg = _('Unable to retrieve network quota information.')
            exceptions.handle(self.request, msg)

        self._set_neutron_limit(self.limits, neutron_quotas, 'floatingip')
        self._set_neutron_limit(self.limits, neutron_quotas, 'router')
        self._set_neutron_limit(self.limits, neutron_quotas, 'network')
        self._set_neutron_limit(self.limits, neutron_quotas, 'subnet')
        self._set_neutron_limit(self.limits, neutron_quotas, 'port')
        self._set_neutron_limit(self.limits, nova_quotas, 'keypair')
        if neutron_sg_used:
            self._set_neutron_limit(self.limits, neutron_quotas,
                                    'security_group')


class GlobalUsage(BaseUsage):
    show_terminated = True

    def get_usage_list(self, start, end):
        return api.nova.usage_list(self.request, start, end)


class ProjectUsage(BaseUsage):
    attrs = ('memory_mb', 'vcpus', 'uptime',
             'hours', 'local_gb')

    def get_usage_list(self, start, end):
        show_terminated = self.request.GET.get('show_terminated',
                                               self.show_terminated)
        instances = []
        terminated_instances = []
        usage = api.nova.usage_get(self.request, self.project_id, start, end)
        # Attribute may not exist if there are no instances
        if hasattr(usage, 'server_usages'):
            now = self.today
            for server_usage in usage.server_usages:
                # This is a way to phrase uptime in a way that is compatible
                # with the 'timesince' filter. (Use of local time intentional.)
                server_uptime = server_usage['uptime']
                total_uptime = now - datetime.timedelta(seconds=server_uptime)
                server_usage['uptime_at'] = total_uptime
                if server_usage['ended_at'] and not show_terminated:
                    terminated_instances.append(server_usage)
                else:
                    instances.append(server_usage)
        usage.server_usages = instances
        return (usage,)
