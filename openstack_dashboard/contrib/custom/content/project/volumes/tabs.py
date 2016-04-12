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
from horizon import exceptions
from horizon import tabs

from django.utils.translation import ugettext_lazy as _

from openstack_dashboard import api
from openstack_dashboard.contrib.custom.content.project.volumes.\
    volumes import tables as volume_tables


class AutoBackupTab(tabs.TableTab):
    table_classes = (volume_tables.AutoBackupTable,)
    name = _("Auto Backups")
    slug = "auto_backups_tab"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    class AutoBackup(object):
        def __init__(self, id, name, retention, cycle, type):
            self.id = id
            self.name = name
            self.retention = retention
            self.cycle = cycle
            self.type = type

    def allowed(self, request):
        return getattr(request, "enable_autobackup", False)

    def get_auto_backups_data(self):
        backups = []
        try:
            volumes = api.cinder.volume_list(self.request)
            for volume in volumes:
                for backup in self.get_auto_backups(volume.metadata):
                    backups.append(self.AutoBackup('{0}_{1}'.format(volume.id,
                                                                    backup[2]),
                                                   volume.name,
                                                   backup[0],
                                                   backup[1],
                                                   backup[2]))
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume list.'))
        return backups

    def get_auto_backups(self, metadata):
        backups = []
        for k in ["full", "incremental"]:
            if k in metadata.keys():
                retention, cycle = metadata[k].split(',')
                backups.append((retention, cycle, k))
        return backups
