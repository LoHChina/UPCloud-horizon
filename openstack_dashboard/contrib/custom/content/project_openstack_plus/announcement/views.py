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

from django.views import generic

from horizon import forms

from openstack_dashboard.contrib.custom.db import api as db_api


class AnnouncementView(forms.ModalFormMixin, generic.TemplateView):
    template_name = 'project_openstack_plus/project_announcement/notice.html'

    def get_context_data(self, **kwargs):
        context = super(AnnouncementView, self).get_context_data(**kwargs)
        announcement = db_api.announcement_get_by_id(
            self.request, self.kwargs['announcement_id'])
        context["announcement"] = announcement
        return context
