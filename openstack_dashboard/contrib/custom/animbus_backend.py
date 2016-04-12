# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" Module that inherit from the openstack_auth backend. """

from django.conf import settings

from openstack_auth.backend import KeystoneBackend
from openstack_auth.utils import get_keystone_client

from openstack_dashboard.contrib.custom.db import api as db_api


class AnimbusKeystoneBackend(KeystoneBackend):

    def authenticate(self, auth_url=None, **kwargs):
        user = super(AnimbusKeystoneBackend, self).\
            authenticate(auth_url=None, **kwargs)
        request = kwargs.get('request')
        values = {
            'user_id': request.user.id,
            'project_id': request.user.tenant_id,
            'count': 1}
        db_api.statistics_create(request, values)
        return user


def authenticate():

    endpoint = getattr(settings, 'ENDPOINT', None)
    admin_token = getattr(settings, "ADMIN_TOKEN", None)

    ksclient = get_keystone_client()
    client = ksclient.Client(token=admin_token, endpoint=endpoint)

    return client
