#
# Copyright 2012 Nebula, Inc.
#
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
from horizon import tables

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from openstack_dashboard.contrib.custom.api import cinder
from openstack_dashboard.dashboards.project.volumes.\
    volumes import tables as volumes_tables


class AutoBackupVolume(volumes_tables.VolumePolicyTargetMixin,
                       tables.LinkAction):
    name = "backup"
    verbose_name = _("Auto Backup")
    url = "horizon:auto_backup"
    classes = ("ajax-modal", "btn-extend")
    policy_rules = (("volume", "volume:extend"),)

    def allowed(self, request, volume=None):
        return getattr(request, 'enable_autobackup', False)


class DeleteAutoBackup(volumes_tables.VolumePolicyTargetMixin,
                       tables.DeleteAction):
    verbose_name = _("Delete Backup")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Volume",
            u"Delete Volumes",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Volume",
            u"Scheduled deletion of Volumes",
            count
        )

    def delete(self, request, obj_id):
        volume_id, backup_type = obj_id.split("_")
        volume = cinder.volume_get(request, volume_id)
        import copy
        metadata = copy.copy(volume.metadata)
        del metadata[backup_type]
        cinder.update_all_metadata(request, volume, metadata)

    def allowed(self, request, volume=None):
        return getattr(request, "enable_autobackup", False)


class AutoBackupTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"))
    retention = tables.Column("retention",
                              verbose_name=_("Retention"))
    cycle = tables.Column("cycle",
                          verbose_name=_("Cycle"))
    type = tables.Column("type",
                         verbose_name=_("Type"))

    class Meta(object):
        name = "auto_backups"
        verbose_name = _("Auto Backups")
        row_actions = (DeleteAutoBackup,)
