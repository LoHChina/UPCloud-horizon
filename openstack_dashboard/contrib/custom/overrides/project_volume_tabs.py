# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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
from openstack_dashboard.dashboards.project.volumes import tabs
from openstack_dashboard.dashboards.project.volumes.volumes\
    import tables as volumes_tables
from openstack_dashboard.contrib.custom.content.project.volumes.\
    volumes import tables as contrib_tables
from openstack_dashboard.contrib.custom.content.project.volumes\
    import tabs as contrib_tabs
from openstack_dashboard.contrib.custom.utils import common_utils

from django.utils.translation import string_concat  # noqa
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard import api


class ContribCreateVolume(volumes_tables.CreateVolume):
    def allowed(self, request, volume=None):
        if common_utils.need_ticket(request):
            verbose_name = _("Apply Volume")
        else:
            verbose_name = _("Create Volume")
        limits = api.cinder.tenant_absolute_limits(request)

        gb_available = (limits.get('maxTotalVolumeGigabytes', float("inf"))
                        - limits.get('totalGigabytesUsed', 0))
        volumes_available = (limits.get('maxTotalVolumes', float("inf"))
                             - limits.get('totalVolumesUsed', 0))

        if gb_available <= 0 or volumes_available <= 0:
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ['disabled']
                self.verbose_name = string_concat(self.verbose_name, ' ',
                                                  _("(Quota exceeded)"))
        else:
            self.verbose_name = verbose_name
            classes = [c for c in self.classes if c != "disabled"]
            self.classes = classes
        return True


class ContribLaunchVolume(volumes_tables.LaunchVolume):
    def allowed(self, request, volume=None):
        simplify_vmcreate_option = getattr(
            request, 'simplify_vmcreate_option', False)
        if getattr(volume, 'bootable', '') == 'true':
            return volume.status == "available" and \
                not simplify_vmcreate_option
        return False


class ContribVolumesTable(volumes_tables.VolumesTable):
    class Meta(volumes_tables.VolumesTable.Meta):
        table_actions = (ContribCreateVolume,
                         volumes_tables.AcceptTransfer,
                         volumes_tables.DeleteVolume,
                         volumes_tables.VolumesFilterAction)
        row_actions = (volumes_tables.EditVolume,
                       volumes_tables.ExtendVolume,
                       ContribLaunchVolume,
                       volumes_tables.EditAttachments,
                       volumes_tables.CreateSnapshot,
                       volumes_tables.CreateBackup,
                       contrib_tables.AutoBackupVolume,
                       volumes_tables.RetypeVolume,
                       volumes_tables.UploadToImage,
                       volumes_tables.CreateTransfer,
                       volumes_tables.DeleteTransfer,
                       volumes_tables.DeleteVolume)


tabs.VolumeTab.table_classes = (ContribVolumesTable, )
tabs.VolumeAndSnapshotTabs.tabs = (tabs.VolumeTab,
                                   tabs.SnapshotTab,
                                   tabs.BackupsTab,
                                   contrib_tabs.AutoBackupTab)
