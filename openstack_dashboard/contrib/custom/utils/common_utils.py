# Copyright 2012 Nebula, Inc.
# All rights reserved.

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

import ConfigParser
import os

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from openstack_dashboard import api


def need_ticket(request):
    return (not request.user.is_superuser and
            getattr(request, "enable_role_ticket", False))
    # roles = map(lambda x: x["name"], request.user.roles)
    # if getattr(settings, "TICKET_ADMIN_ROLE", "") in roles:
    #     return True
    # return False


def get_set_path():
    storage_settings = getattr(settings, 'ANIMBUS_STORAGE_PATH', ())
    if storage_settings:
        return storage_settings


def get_set_storage(stats=None, hypervisors=None):
    storage_settings = get_set_path()
    if storage_settings:
        if hypervisors:
            for hypervisor in hypervisors:
                free = 0
                total = 0
                used = 0
                G = 1000 ** 3
                for path in storage_settings:
                    st = os.statvfs(path)
                    free += (st.f_bavail * st.f_frsize) / G
                    total += (st.f_blocks * st.f_frsize) / G
                    used += (st.f_blocks - st.f_bfree) * st.f_frsize / G
                hypervisor.local_gb = total
                hypervisor.local_gb_used = used
                hypervisor.free_disk_gb = free
        else:
            free = 0
            total = 0
            used = 0
            G = 1000 ** 3
            for path in storage_settings:
                st = os.statvfs(path)
                free += (st.f_bavail * st.f_frsize) / G
                total += (st.f_blocks * st.f_frsize) / G
                used += (st.f_blocks - st.f_bfree) * st.f_frsize / G
            stats.local_gb = total
            stats.local_gb_used = used
            stats.free_gb = free


def get_overcommit_stats(stats=None, hypervisors=None):
    animbus_cpu_ratio = getattr(settings, 'CONFIG_CPU_ALLOC_RATIO', 16.0)
    animbus_ram_ratio = getattr(settings, 'CONFIG_RAM_ALLOC_RATIO', 1.5)
    animbus_disk_ratio = getattr(settings, 'CONFIG_DISK_ALLOC_RATIO', 1.0)
    conf = ConfigParser.ConfigParser()
    conf.read("/etc/nova/nova.conf")
    try:
        cpu_ratio = conf.get("libvirt", "cpu_allocation_ratio")
    except Exception:
        cpu_ratio = animbus_cpu_ratio
    try:
        ram_ratio = conf.get("libvirt", "ram_allocation_ratio")
    except Exception:
        ram_ratio = animbus_ram_ratio
    try:
        disk_ratio = conf.get("libvirt", "disk_allocation_ratio")
    except Exception:
        disk_ratio = animbus_disk_ratio
    if hypervisors:
        for hypervisor in hypervisors:
            hypervisor.vcpus = int(hypervisor.vcpus * float(cpu_ratio))
            hypervisor.memory_mb = hypervisor.memory_mb * float(ram_ratio)
            hypervisor.local_gb = hypervisor.local_gb * float(disk_ratio)
    if stats:
        stats.vcpus = int(stats.vcpus * float(cpu_ratio))
        stats.memory_mb = stats.memory_mb * float(ram_ratio)
        stats.local_gb = stats.local_gb * float(disk_ratio)


def zone_list(request):
    """Utility method to retrieve a list of zones."""
    try:
        zones = api.nova.availability_zone_list(request)
        zone_list = [(j, zones[j].zoneName)
                     for j in range(len(zones))
                     if zones[j].zoneState['available']]
    except Exception:
        zone_list = []
        exceptions.handle(request,
                          _('Unable to retrieve availability zones.'))
    return zone_list


def move_element(odict, thekey, newpos):
    odict[thekey] = odict.pop(thekey)
    i = 0
    for key, value in odict.items():
        if key != thekey and i >= newpos:
            odict[key] = odict.pop(key)
        i += 1
    return odict
