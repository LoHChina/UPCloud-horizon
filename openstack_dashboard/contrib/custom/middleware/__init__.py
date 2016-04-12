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

from openstack_dashboard.contrib.custom.db import api as db_api
from openstack_dashboard.contrib.custom.middleware import globalsettings


class ContribMiddleware(object):

    def process_request(self, request):
        global_settings = db_api.global_settings_get(request)
        for setting in global_settings:
            setattr(request, setting.name, setting.value)

        # Storage Qos switch
        storage_qos_switch = getattr(
            request, "enable_storage_qos_feature", False)
        globalsettings.storage_qos(enable=storage_qos_switch)
