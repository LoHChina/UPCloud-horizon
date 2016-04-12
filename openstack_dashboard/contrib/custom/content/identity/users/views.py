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

from openstack_dashboard import api

from openstack_dashboard.dashboards.identity.users \
    import views as pro_views


class IndexView(pro_views.IndexView):

    def _get_services(self):
        services = []
        for i, service in enumerate(self.request.user.service_catalog):
            service['id'] = i
            services.append(
                api.keystone.Service(
                    service, self.request.user.services_region).name)
        return services

    def get_data(self):
        users = super(IndexView, self).get_data()
        show_system_service = getattr(
            self.request, 'show_system_service', False)
        if not show_system_service:
            need_not_display = self._get_services()
            # need_not_display.append('admin')
            users = filter(lambda x: x.name not in
                           need_not_display, users)
        return users
