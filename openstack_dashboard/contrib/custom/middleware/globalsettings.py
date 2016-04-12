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

from openstack_dashboard.dashboards.admin.volumes import tabs
from openstack_dashboard.dashboards.admin.volumes.volume_types import tables


class ContribVolumeTypesTable(tables.VolumeTypesTable):
    class Meta(tables.VolumeTypesTable.Meta):
        columns = ('name', 'description', 'encryption')


class ContribVolumeTypesTab(tabs.VolumeTypesTab):
    table_classes = (ContribVolumeTypesTable,)


def storage_qos(enable=False):
    if enable:
        tabs.VolumesGroupTabs.tabs = (
            tabs.VolumeTab, tabs.VolumeTypesTab, tabs.SnapshotTab)
    else:
        tabs.VolumesGroupTabs.tabs = (
            tabs.VolumeTab, ContribVolumeTypesTab, tabs.SnapshotTab)
