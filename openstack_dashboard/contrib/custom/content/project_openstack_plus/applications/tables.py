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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard.dashboards.project.stacks \
    import tables as project_tables

from openstack_dashboard.contrib.custom.db import api as db_api


class UploadApplicationTemplate(tables.LinkAction):
    name = "upload_application"
    verbose_name = _("Upload Application Template")
    url = "horizon:project_openstack_plus:applications:upload"
    classes = ("ajax-modal", "btn-launch")
    icon = "cloud-upload"


class DeleteApplicationTemplate(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete App Template",
            u"Delete App Templates",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Delete App Template",
            u"Delete App Templates",
            count
        )

    def delete(self, request, obj_id):
        db_api.application_delete(request, obj_id)


class CreateApplication(tables.LinkAction):
    name = "create_application"
    verbose_name = _("Create Application")
    url = "horizon:project_openstack_plus:applications:create"
    classes = ("ajax-modal",)

    def get_link_url(self, application):
        return reverse(self.url, args=[application.id])


class AppStoreTable(tables.DataTable):
    name = tables.Column(
        "name", verbose_name=_("Name"),
        link="horizon:project_openstack_plus:applications:detail")
    description = tables.Column("description", verbose_name=_("Description"))
    website = tables.Column("website", verbose_name=_("Website"))
    category = tables.Column("category", verbose_name=_("Category"))
    template_data = tables.Column("template_data",
                                  verbose_name=_("Template Data"))
    author = tables.Column("author", verbose_name=_("Author"))
    time = tables.Column("created_at", verbose_name=_("Create Time"))
    public = tables.Column("is_public", verbose_name=_("Public"))

    class Meta(object):
        name = "applications"
        verbose_name = _("App Store")
        template = "project_openstack_plus/applications/_app_store.html"
        table_actions = (UploadApplicationTemplate,)
        row_actions = (CreateApplication, DeleteApplicationTemplate,)


class MyAppsTable(project_tables.StacksTable):

    class Meta(object):
        name = "my_apps"
        verbose_name = _("My Apps")
        template = "project_openstack_plus/applications/_my_apps.html"
        row_class = project_tables.StacksUpdateRow
        table_actions = (project_tables.LaunchStack,
                         project_tables.DeleteStack,)
        row_actions = (project_tables.DeleteStack,
                       project_tables.ChangeStackTemplate,)
