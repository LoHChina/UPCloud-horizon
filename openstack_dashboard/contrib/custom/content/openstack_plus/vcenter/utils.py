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

import atexit
import time

from openstack_dashboard.contrib.custom.db import api as db_api

from pyVim.connect import Disconnect
from pyVim.connect import SmartConnect
from pyVmomi import vim


def get_vmware_si(context, vcenter_id):
    vcenter = db_api.vcenter_get_by_id(context, vcenter_id)
    try:
        si = SmartConnect(
            host=vcenter.host_ip,
            user=vcenter.username,
            pwd=vcenter.password)
        atexit.register(Disconnect, si)
    except Exception:
        si = []

    return si


def get_instance_obj(virtual_machine, depth=1):
    maxdepth = 10

    # if this is a group it will have children. if it does, recurse into them
    # and then return
    if hasattr(virtual_machine, 'childEntity'):
        if depth > maxdepth:
            return
        vmList = virtual_machine.childEntity
        for c in vmList:
            instance_list = get_instance_obj(c, depth + 1)
            return instance_list
        return

    summary = virtual_machine.summary
    instance_obj = Instance(summary.config.name)
    instance_obj.id = summary.config.name
    instance_obj.name = summary.config.name
    instance_obj.memory = summary.config.memorySizeMB
    instance_obj.cpu_num = summary.config.numCpu
    instance_obj.ip = summary.guest.ipAddress
    instance_obj.state = summary.runtime.powerState

    return instance_obj


class Instance(object):
    def __init__(self, name):
        self.name = name


def clone_vm(
        content, template, vm_name, si,
        datacenter_name, vm_folder, datastore_name,
        cluster_name, resource_pool, power_on):

    # if none git the first one
    datacenter = get_obj(content, [vim.Datacenter], datacenter_name)

    if vm_folder:
        destfolder = get_obj(content, [vim.Folder], vm_folder)
    else:
        destfolder = datacenter.vmFolder

    if datastore_name:
        datastore = get_obj(content, [vim.Datastore], datastore_name)
    else:
        datastore = get_obj(
            content, [vim.Datastore], template.datastore[0].info.name)

    # if None, get the first one
    cluster = get_obj(content, [vim.ClusterComputeResource], cluster_name)

    if resource_pool:
        resource_pool = get_obj(content, [vim.ResourcePool], resource_pool)
    else:
        resource_pool = cluster.resourcePool

    # set relospec
    relospec = vim.vm.RelocateSpec()
    relospec.datastore = datastore
    relospec.pool = resource_pool

    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.powerOn = power_on

    task = template.Clone(folder=destfolder, name=vm_name, spec=clonespec)
    wait_for_task(task)


def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break

    return obj


def wait_for_task(task):
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result

        if task.info.state == 'error':
            task_done = True


def get_template(content, template):
    template = get_obj(content, [vim.VirtualMachine], template)
    return template


def power_off(si, vm_name):
    vm = None
    entity_stack = si.content.rootFolder.childEntity
    while entity_stack:
        entity = entity_stack.pop()

        if entity.name == vm_name:
            vm = entity
            del entity_stack[0:len(entity_stack)]
        elif hasattr(entity, 'childEntity'):
            entity_stack.extend(entity.childEntity)
        elif isinstance(entity, vim.Datacenter):
            entity_stack.append(entity.vmFolder)

    if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
        # using time.sleep we just wait until the power off action
        # is complete. Nothing fancy here.
        task = vm.PowerOff()
        while task.info.state not in [vim.TaskInfo.State.success,
                                      vim.TaskInfo.State.error]:
            time.sleep(1)


def power_on(si, vm_name):
    vm = None
    entity_stack = si.content.rootFolder.childEntity
    while entity_stack:
        entity = entity_stack.pop()

        if entity.name == vm_name:
            vm = entity
            del entity_stack[0:len(entity_stack)]
        elif hasattr(entity, 'childEntity'):
            entity_stack.extend(entity.childEntity)
        elif isinstance(entity, vim.Datacenter):
            entity_stack.append(entity.vmFolder)

    if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOn:
        # using time.sleep we just wait until the power off action
        # is complete. Nothing fancy here.
        vm.PowerOn()
