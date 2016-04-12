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

import datetime

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from horizon.utils import filters

from openstack_dashboard.contrib.custom.db import api as db_api


class CreateAnnouncement(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Announcement")
    url = "horizon:openstack_plus:announcement:create"
    classes = ("ajax-modal",)
    icon = "plus"


class EditAnnouncement(tables.LinkAction):
    name = "update_announcement"
    verbose_name = _("Edit Announcement")
    url = "horizon:openstack_plus:announcement:update"
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, datum):
        time_now = datetime.datetime.utcnow()
        return (datum.keep_days) * 24 > \
            (time_now - datum.created_at).days * 24


class DeleteAnnouncement(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Announcement",
            u"Delete Announcements",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Announcement",
            u"Deleted Announcements",
            count
        )

    def delete(self, request, obj_id):
        db_api.announcement_delete(request, obj_id)


def get_createtime(announcement):
    if hasattr(announcement, "created_at"):
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        created_at = announcement.created_at.strftime(fmt)
        return created_at
    return _("Not available")


def is_expired(announcement):
    if hasattr(announcement, "created_at"):
        time_now = datetime.datetime.utcnow()
        return str(announcement.keep_days * 24 <
                   (time_now - announcement.created_at).days * 24)
    return "False"

ANNOUNCEMENT_CHOICES = {("True", _("True")),
                        ("False", _("False"))}


class AnnouncementTable(tables.DataTable):
    title = tables.Column("title",
                          verbose_name=_("Announcement Title"),
                          link="horizon:openstack_plus:announcement:detail")
    content = tables.Column("content", verbose_name=_("Content"))
    created = tables.Column(get_createtime,
                            verbose_name=_("Created Time"),
                            filters=(filters.parse_isotime,))
    rotation = tables.Column("keep_days", verbose_name=_("Rotation(days)"))
    is_expired = tables.Column(is_expired, verbose_name=_("Expired"),
                               display_choices=ANNOUNCEMENT_CHOICES)
    description = tables.Column("description",
                                verbose_name=_("Discription"),)

    def get_object_display(self, obj):
        return obj.title

    class Meta(object):
        name = "announcement_list"
        verbose_name = _("Announcement")
        row_actions = (EditAnnouncement, DeleteAnnouncement)
        table_actions = (CreateAnnouncement, DeleteAnnouncement)
