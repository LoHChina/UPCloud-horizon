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

from django.utils.translation import ugettext_lazy as _

from horizon import messages

from openstack_dashboard.dashboards.project.images.images import tables
from openstack_dashboard.dashboards.project.images.images import views
from openstack_dashboard.views import splash


def create_action_allowed(self, request, image):
    if getattr(request, 'enable_image_upload_delete', False):
        return True
    else:
        return False


def delete_action_allowed(self, request, image):
    if getattr(request, 'enable_image_upload_delete', False):
        return True
    else:
        return False

    # Protected images can not be deleted.
    if image and image.protected:
        return False
    if image:
        return image.owner == request.user.tenant_id
    # Return True to allow table-level bulk delete action to appear.
    return True

tables.CreateImage.allowed = create_action_allowed
tables.DeleteImage.allowed = delete_action_allowed


class ContribCreateView(views.CreateView):
    def get(self, request, *args, **kwargs):
        enable_image_upload_delete = getattr(
            self.request, 'enable_image_upload_delete', False)
        if not enable_image_upload_delete:
            response = splash(request)
            msg = _('Sorry,The image upload and delete function is disable, '
                    'please connect with administrator')
            messages.warning(request, msg)
        else:
            response = super(ContribCreateView, self).get(request,
                                                          *args, **kwargs)
        return response

views.CreateView = ContribCreateView
