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

import datetime

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard.contrib.custom.content.openstack_plus.announcement \
    import forms as project_forms
from openstack_dashboard.contrib.custom.content.openstack_plus.announcement \
    import tables as project_tables
from openstack_dashboard.contrib.custom.content.openstack_plus.announcement \
    import tabs as project_tabs
from openstack_dashboard.contrib.custom.db import api as db_api
from openstack_dashboard.contrib.custom.utils import timeutils


class IndexView(tables.DataTableView):
    table_class = project_tables.AnnouncementTable
    template_name = 'openstack_plus/announcement/index.html'

    def get_data(self):
        try:
            announcements = db_api.announcement_get_all(self.request)
        except Exception:
            announcements = []
            msg = _('Announcement list can not be retrieved.')
            exceptions.handle(self.request, msg)

        return announcements


class UpdateView(forms.ModalFormView):
    form_class = project_forms.UpdateForm
    template_name = 'openstack_plus/announcement/update.html'
    context_object_name = 'announcement'
    success_url = reverse_lazy("horizon:openstack_plus:announcement:index")

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context["announcement_id"] = self.kwargs['announcement_id']
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        announcement_id = self.kwargs['announcement_id']
        try:
            return db_api.announcement_get_by_id(self.request, announcement_id)
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve announcement details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        announcement = self._get_object()
        return {'announcement_id': announcement['id'],
                'title': announcement['title'],
                'description': announcement['description'],
                'keep_days': announcement['keep_days'],
                'content': announcement['content']}


class CreateView(forms.ModalFormView):
    form_class = project_forms.CreateForm
    template_name = 'openstack_plus/announcement/create.html'
    success_url = reverse_lazy("horizon:openstack_plus:announcement:index")


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.AnnouncementDetailTabs
    template_name = 'openstack_plus/announcement/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        announcement, expired = self.get_data()
        context["announcement"] = announcement
        return context

    @staticmethod
    def get_redirect_url():
        return reverse_lazy('horizon:openstack_plus:announcement:index')

    @memoized.memoized_method
    def get_data(self):
        try:
            announcement = db_api.announcement_get_by_id(
                self.request, self.kwargs['announcement_id'])
            time_now = datetime.datetime.utcnow()
            expired = (announcement.keep_days * 24 <
                       (time_now - announcement.created_at).days * 24)
            announcement.created_at = (
                timeutils.format_time(announcement.created_at))
            return announcement, expired
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve announcement details.'),
                              redirect=self.get_redirect_url())

    def get_tabs(self, request, *args, **kwargs):
        announcement, expired = self.get_data()
        return self.tab_group_class(request, announcement=announcement,
                                    expired=expired, **kwargs)
