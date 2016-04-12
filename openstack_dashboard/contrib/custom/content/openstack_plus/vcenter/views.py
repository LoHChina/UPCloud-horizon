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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard.contrib.custom.content.openstack_plus.vcenter \
    import forms as project_forms
from openstack_dashboard.contrib.custom.content.openstack_plus.vcenter \
    import tables as project_tables
from openstack_dashboard.contrib.custom.content.openstack_plus.vcenter \
    import utils
from openstack_dashboard.contrib.custom.db import api as db_api
from openstack_dashboard.views import splash

VMWARE_POWER_STATES = {
    1: 'PoweredOn',
    4: 'PoweredOff'}


class IndexView(TemplateView):
    template_name = 'openstack_plus/vcenter/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        try:
            all_vcenter = db_api.vcenter_get_all(self.request)
        except Exception:
            all_vcenter = []
            msg = _('Unable to retrieve vCenter information.')
            exceptions.handle(self.request, msg)
        context['vcenters'] = all_vcenter
        return context

    def get(self, request, *args, **kwargs):
        enable_vmware = getattr(
            self.request, 'enable_vmware', False)
        if not enable_vmware:
            response = splash(request)
            msg = _('Oops,this feature had been disabled, please go to '
                    '"Global Settings" page to check the configuration')
            messages.warning(request, msg)
        else:
            response = super(IndexView, self).get(request, *args, **kwargs)
        return response


class VCenterView(forms.ModalFormView):
    form_class = project_forms.VCenterForm
    template_name = 'openstack_plus/vcenter/new.html'
    success_url = reverse_lazy("horizon:openstack_plus:vcenter:index")


class VCenterInstancesView(tables.DataTableView):
    table_class = project_tables.VCenterInstancesTable
    template_name = 'openstack_plus/vcenter/instances.html'

    def get_data(self):
        instance_list = []
        try:
            si = utils.get_vmware_si(self.request,
                                     self.kwargs.get('vcenter_id'))
            content = si.RetrieveContent()
            children = content.rootFolder.childEntity
            for child in children:
                if hasattr(child, 'vmFolder'):
                    datacenter = child
                else:
                    # some other non-datacenter type object
                    continue

                vm_folder = datacenter.vmFolder
                vm_list = vm_folder.childEntity
                for virtual_machine in vm_list:
                    instance_obj = utils.get_instance_obj(virtual_machine, 10)
                    instance_list.append(instance_obj)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve vmware instances.'))

        return instance_list


class Instance(object):
    def __init__(self, name):
        self.name = name


class LaunchInstanceView(forms.ModalFormView):
    form_class = project_forms.LaunchInstanceForm
    template_name = 'openstack_plus/vcenter/create.html'
    page_title = _("Launch Instance")

    @memoized.memoized_method
    def get_context_data(self, **kwargs):
        context = super(LaunchInstanceView, self).get_context_data(**kwargs)
        context['vcenter_id'] = self.kwargs['vcenter_id']
        return context

    def get_initial(self):
        return {'vcenter_id': self.kwargs['vcenter_id']}

    def get_success_url(self):
        return reverse("horizon:openstack_plus:vcenter:instances",
                       args=(self.kwargs['vcenter_id'],))

    def get_failure_url(self):
        return reverse("horizon:openstack_plus:vcenter:instances",
                       args=(self.kwargs['vcenter_id'],))
