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

from openstack_dashboard.dashboards.admin.info import tabs


class ContribServicesTab(tabs.ServicesTab):

    def get_services_data(self):
        services = super(ContribServicesTab, self).get_services_data()
        enable_metering_feature = getattr(
            self.request, 'enable_metering_feature', False)
        if not enable_metering_feature:
            for service in services:
                if service.name == 'ceilometer':
                    services.remove(service)
        return services


tabs.SystemInfoTabs.tabs = (
    ContribServicesTab, tabs.NovaServicesTab, tabs.CinderServicesTab,
    tabs.NetworkAgentsTab, tabs.HeatServiceTab)
