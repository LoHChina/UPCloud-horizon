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

import copy
import json

from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from openstack_dashboard.dashboards.project.instances import views
from openstack_dashboard.dashboards.project.instances.workflows \
    import create_instance

from openstack_dashboard.contrib.custom.db import api as db_api
from openstack_dashboard.contrib.custom.utils import common_utils

import logging


from django.conf import settings
from django.http import HttpResponse  # noqa
from django.template.defaultfilters import filesizeformat  # noqa
from django.utils.text import normalize_newlines  # noqa
from django.utils.translation import string_concat  # noqa
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils

from openstack_dashboard.contrib.custom.views import _check_ip

from openstack_dashboard.dashboards.project.instances \
    import tables as instances_tables

LOG = logging.getLogger(__name__)

TICKET_INDEX = "horizon:project_openstack_plus:project_tickets:index"


class ConSetInstanceDetailsAction(create_instance.SetInstanceDetailsAction):

    class Meta(object):
        name = _("Details")
        help_text_template = ("project/instances/"
                              "_launch_details_help.html")

    def __init__(self, request, context, *args, **kwargs):
        super(ConSetInstanceDetailsAction, self).\
            __init__(request, context, *args, **kwargs)
        # simplify_vmcreate_option
        if getattr(request, 'simplify_vmcreate_option', False):
            filter_id = ["volume_id", "volume_image_id", "volume_snapshot_id"]
            choices = [choice for choice in self.fields['source_type'].choices
                       if choice[0] not in filter_id]
            self.fields['source_type'].choices = choices

        # Init the choice for Hypervisor host
        enable_select_host = getattr(
            self.request, 'enable_select_host', False)
        if enable_select_host:
            zone_list = common_utils.zone_list(self.request)
            for zone in zone_list:
                zone_field = 'zone' + '-' + str(zone[0])
                self.fields[zone_field] = forms.CharField(
                    widget=forms.HiddenInput(),
                    initial=zone[1],
                    required=False)
            aggregates = api.nova.aggregate_details_list(request)
            for choice in zone_list:
                if choice[0] != '':
                    agg_field_name = 'agg' + str(choice[0])
                    data = 'data-source' + '-' + choice[1]
                    self.fields[agg_field_name] = forms.ChoiceField(
                        label=_("Aggregate"),
                        widget=forms.Select(attrs={
                                            'class': 'switched switchable',
                                            'data-slug': agg_field_name,
                                            'data-switch-on': 'source',
                                            data: _('Aggregate')}),
                        required=False)
                    self.fields = common_utils.move_element(
                        self.fields, agg_field_name, 1)
                    new_choice = []
                    for aggregate in aggregates:
                        if aggregate.availability_zone == choice[1]:
                            new_choice.insert(0,
                                              (aggregate.id, aggregate.name))
                    if len(new_choice) == 0:
                        new_choice = (("",
                                      _("No host aggregate found")),)
                    else:
                        new_choice = new_choice
                    self.fields[agg_field_name].choices = new_choice
                    if new_choice[0][0]:
                        for choice in new_choice:
                            host_field_name = 'host' + str(choice[0])
                            data = 'data' + '-' + agg_field_name + '-' + \
                                str(choice[0])
                            self.fields[host_field_name] = forms.ChoiceField(
                                label=_("Hypervisor hostname"),
                                widget=forms.Select(
                                    attrs={'class': 'switched',
                                           'data-switch-on': agg_field_name,
                                           data: _('Hypervisor hostname')}),
                                required=False)
                            self.fields = common_utils.move_element(
                                self.fields, host_field_name, 2)
                            for aggregate in aggregates:
                                if aggregate.name == choice[1]:
                                    new_choice = []
                                    for hostname in aggregate.hosts:
                                        new_choice.insert(0,
                                                          (hostname, hostname))
                                    if len(new_choice) == 0:
                                        new_choice = (
                                            ("Null",
                                             _("No available host found")),)
                                    elif len(new_choice) == 1:
                                        self.fields[host_field_name].initial = \
                                            new_choice[0][0]
                                    else:
                                        new_choice.insert(0, ("", _("Auto")))
                                    self.fields[host_field_name].choices = \
                                        new_choice

    def clean(self):
        cleaned_data = super(ConSetInstanceDetailsAction, self).clean()
        # Validate the host is Null
        az = cleaned_data.get('availability_zone', None)
        flavor_id = cleaned_data.get('flavor')
        count = cleaned_data.get('count', 1)
        if az:
            for key in cleaned_data.keys():
                if cleaned_data[key] == az and key != 'availability_zone':
                    agg_id = key.split('-')[1]
                    agg_field = 'agg' + str(agg_id)
                    host_id = cleaned_data.get(agg_field, None)
                    host_field = 'host' + str(host_id)
                    host = cleaned_data.get(host_field, None)
                    if host == 'Null':
                        msg = _("No available host found!")
                        self._errors[host_field] = self.error_class([msg])

                    # Validate the Hypervisor capacity with flavor and count
                    hypervisors = api.nova.hypervisor_list(self.request)
                    flavor = api.nova.flavor_get(self.request, flavor_id)
                    for hypervisor in hypervisors:
                        if hypervisor.hypervisor_hostname == host:
                            free_cpu = hypervisor.vcpus - hypervisor.vcpus_used
                            free_disk = hypervisor.free_disk_gb
                            free_ram = hypervisor.free_ram_mb
                            need_cpu = count * flavor.vcpus
                            need_ram = count * flavor.ram
                            need_disk = count * flavor.disk
                            if (need_ram > free_ram or
                                    need_cpu > free_cpu or
                                    need_disk > free_disk):
                                error_message = _("The host capacity is not "
                                                  "enough to support VM "
                                                  "creating, please reduce "
                                                  "your VM flavor or "
                                                  "quantity")
                                raise forms.ValidationError(error_message)
        return cleaned_data


class ContribSetInstanceDetails(create_instance.SetInstanceDetails):
    action_class = ConSetInstanceDetailsAction
    contributes = ("source_type", 'hypervisor', "source_id", "aggregate",
                   "availability_zone", "name", "count", "flavor",
                   "device_name", "volume_type",  # Can be None for an image.
                   "delete_on_terminate")

    def contribute(self, data, context):
        context = super(ContribSetInstanceDetails, self).\
            contribute(data, context)
        hypervisor_zone = context["availability_zone"]
        if hypervisor_zone:
            for key in data.keys():
                if data[key] == hypervisor_zone and key != 'availability_zone':
                    agg_id = key.split('-')[1]
                    agg_field = 'agg' + str(agg_id)
                    host_id = data.get(agg_field, None)
                    host_field = 'host' + str(host_id)
                    context["hypervisor"] = data.get(host_field, None)
        return context


class ContribSetNetworkAction(workflows.Action):
    network = forms.MultipleChoiceField(label=_("Networks"),
                                        widget=forms.CheckboxSelectMultiple(),
                                        error_messages={
                                            'required': _(
                                                "At least one network must"
                                                " be specified.")},
                                        help_text=_("Launch instance with"
                                                    " these networks"))
    if api.neutron.is_port_profiles_supported():
        widget = None
    else:
        widget = forms.HiddenInput()
    profile = forms.ChoiceField(label=_("Policy Profiles"),
                                required=False,
                                widget=widget,
                                help_text=_("Launch instance with "
                                            "this policy profile"))

    def __init__(self, request, *args, **kwargs):
        super(ContribSetNetworkAction, self).__init__(request, *args, **kwargs)
        network_list = self.fields["network"].choices
        if len(network_list) == 1:
            self.fields['network'].initial = [network_list[0][0]]
        if api.neutron.is_port_profiles_supported():
            self.fields['profile'].choices = (
                self.get_policy_profile_choices(request))
        enable_fix_ip = getattr(
            self.request, 'enable_fix_ip', False)
        if enable_fix_ip:
            for net in network_list:
                try:
                    network = api.neutron.network_get(self.request, net[0])
                    subnet = network['subnets'][0]
                except Exception:
                    continue
                fix_ip_field = 'fix_ip%s' % (net[0])
                self.fields[fix_ip_field] = forms.CharField(
                    widget=forms.HiddenInput(attrs={"cidr": subnet.cidr}),
                    required=False)

    class Meta(object):
        name = _("Networking")
        permissions = ('openstack.services.network',)
        help_text = _("Select networks for your instance.")

    def populate_network_choices(self, request, context):
        return instance_utils.network_field_data(request)

    def get_policy_profile_choices(self, request):
        profile_choices = [('', _("Select a profile"))]
        for profile in self._get_profiles(request, 'policy'):
            profile_choices.append((profile.id, profile.name))
        return profile_choices

    def _get_profiles(self, request, type_p):
        profiles = []
        try:
            profiles = api.neutron.profile_list(request, type_p)
        except Exception:
            msg = _('Network Profiles could not be retrieved.')
            exceptions.handle(request, msg)
        return profiles


class ContribSetNetwork(workflows.Step):
    action_class = ContribSetNetworkAction
    # Disabling the template drag/drop only in the case port profiles
    # are used till the issue with the drag/drop affecting the
    # profile_id detection is fixed.
    if api.neutron.is_port_profiles_supported():
        contributes = ("network_id", "profile_id",)
    else:
        template_name = "project/instances/_update_networks.html"
        contributes = ("network_id", "fix_ip_id", )

    def contribute(self, data, context):
        if data:
            networks = self.workflow.request.POST.getlist("network")
            # If no networks are explicitly specified, network list
            # contains an empty string, so remove it.
            networks = [n for n in networks if n != '']
            for net in networks:
                fix_ip_str = "fix_ip%s" % (net)
                fix_ip = self.workflow.request.POST.getlist(fix_ip_str)
                context[fix_ip_str] = fix_ip
            if networks:
                context['network_id'] = networks

            if api.neutron.is_port_profiles_supported():
                context['profile_id'] = data.get('profile', None)
        return context


class ContribLaunchInstance(create_instance.LaunchInstance):

    default_steps = (create_instance.SelectProjectUser,
                     ContribSetInstanceDetails,
                     create_instance.SetAccessControls,
                     ContribSetNetwork,
                     create_instance.PostCreationStep,
                     create_instance.SetAdvanced)

    def _order_steps(self):
        steps = super(ContribLaunchInstance, self)._order_steps()
        if common_utils.need_ticket(self.request):
            self.name = _("Apply Instance")
            self.finalize_button_name = _("Apply")
            self.success_message = _('Apply instnace %(count)s'
                                     'named "%(name)s".')
            self.failure_message = _('Unable to apply %(count)s'
                                     'named "%(name)s".')
            self.handle = self._handle
            self.success_url = TICKET_INDEX
        enable_advanced_options = getattr(
            self.request, 'enable_advanced_options', False)
        enable_access_security = getattr(
            self.request, 'enable_access_security', False)
        enable_post_creation = getattr(
            self.request, 'enable_post_creation', False)

        for step in copy.deepcopy(steps):
            if not enable_access_security:
                if step.action_class.slug == 'setaccesscontrolsaction':
                    steps.remove(step)
            if not enable_advanced_options:
                if step.action_class.slug == 'setadvancedaction':
                    steps.remove(step)
            if not enable_post_creation:
                if step.action_class.slug == 'customizeaction':
                    steps.remove(step)

        return steps

    def get_context_data(self, **kwargs):
        context = super(ContribLaunchInstance, self).get_context_data(**kwargs)
        enable_fix_ip = getattr(self.request, 'enable_fix_ip', False)
        context['WEBROOT'] = getattr(settings, 'WEBROOT', '/')
        context['ENABLE_FIXED_IP'] = str(enable_fix_ip)
        return context

    @sensitive_variables('context')
    def _handle(self, request, context):
        description = unicode(_("VCPUs: {0} / RAM: {1}MB / DISK: {2}GB"))
        try:
            flavor = api.nova.flavor_get(request, context["flavor"])
            description = description.format(flavor.vcpus,
                                             flavor.ram,
                                             flavor.disk)
        except Exception:
            description = ""
        values = {
            'user_id': request.user.id,
            'project_id': request.user.tenant_id,
            'title': unicode(_("Apply Instance")),
            'description': description,
            'context': json.dumps(context),
            'status': "new",
            'type': 'instance'}
        db_api.ticket_create(request, values)
        return True

    @sensitive_variables('context')
    def handle(self, request, context):
        custom_script = context.get('script_data', '')

        dev_mapping_1 = None
        dev_mapping_2 = None

        image_id = ''
        context['keypair_id'] = context.get("keypair_id", "")
        context['security_group_ids'] = context.get("security_group_ids", "")
        context['admin_pass'] = context.get("admin_pass", "")
        context['confirm_admin_pass'] = context.get("confirm_admin_pass", "")

        # Determine volume mapping options
        source_type = context.get('source_type', None)
        if source_type in ['image_id', 'instance_snapshot_id']:
            image_id = context['source_id']
        elif source_type in ['volume_id', 'volume_snapshot_id']:
            try:
                if api.nova.extension_supported("BlockDeviceMappingV2Boot",
                                                request):
                    # Volume source id is extracted from the source
                    volume_source_id = context['source_id'].split(':')[0]
                    device_name = context.get('device_name', '') \
                        .strip() or None
                    dev_source_type_mapping = {
                        'volume_id': 'volume',
                        'volume_snapshot_id': 'snapshot'
                    }
                    dev_mapping_2 = [
                        {'device_name': device_name,
                         'source_type': dev_source_type_mapping[source_type],
                         'destination_type': 'volume',
                         'delete_on_termination':
                             bool(context['delete_on_terminate']),
                         'uuid': volume_source_id,
                         'boot_index': '0',
                         'volume_size': context['volume_size']
                         }
                    ]
                else:
                    dev_mapping_1 = {context['device_name']: '%s::%s' %
                                     (context['source_id'],
                                     bool(context['delete_on_terminate']))
                                     }
            except Exception:
                msg = _('Unable to retrieve extensions information')
                exceptions.handle(request, msg)
        elif source_type == 'volume_image_id':
            device_name = context.get('device_name', '').strip() or None
            dev_mapping_2 = [
                {'device_name': device_name,  # None auto-selects device
                 'source_type': 'image',
                 'destination_type': 'volume',
                 'delete_on_termination':
                     bool(context['delete_on_terminate']),
                 'uuid': context['source_id'],
                 'boot_index': '0',
                 'volume_size': context['volume_size']
                 }
            ]

        netids = context.get('network_id', None)
        if netids:
            nics = []
            for netid in netids:
                try:
                    fixed_ip = context.get('fix_ip{0}'.format(netid))[0]
                except IndexError:
                    fixed_ip = ""
                if _check_ip(self.request, netid, fixed_ip):
                    nics.append({"net-id": netid, "v4-fixed-ip": fixed_ip})
                else:
                    nics.append({"net-id": netid, "v4-fixed-ip": ""})
        else:
            nics = None

        avail_zone = context.get('availability_zone', None)
        hypervisor = context.get('hypervisor', None)
        if hypervisor:
            avail_zone = avail_zone + ':' + hypervisor

        port_profiles_supported = api.neutron.is_port_profiles_supported()

        if port_profiles_supported:
            nics = self.set_network_port_profiles(request,
                                                  context['network_id'],
                                                  context['profile_id'])
        try:
            api.nova.server_create(request,
                                   context['name'],
                                   image_id,
                                   context['flavor'],
                                   context['keypair_id'],
                                   normalize_newlines(custom_script),
                                   context['security_group_ids'],
                                   block_device_mapping=dev_mapping_1,
                                   block_device_mapping_v2=dev_mapping_2,
                                   nics=nics,
                                   availability_zone=avail_zone,
                                   instance_count=int(context['count']),
                                   admin_pass=context['admin_pass'],
                                   disk_config=context.get('disk_config'),
                                   config_drive=context.get('config_drive'))
            return True
        except Exception:
            if port_profiles_supported:
                ports_failing_deletes = create_instance.\
                    _cleanup_ports_on_failed_vm_launch(request, nics)
                if ports_failing_deletes:
                    ports_str = ', '.join(ports_failing_deletes)
                    msg = (_('Port cleanup failed for these port-ids (%s).')
                           % ports_str)
                    exceptions.handle(request, msg)
            exceptions.handle(request)
        return False


class ContribLaunchLink(tables.LinkAction):
    name = "launch"
    verbose_name = _("Launch Instance")
    url = "horizon:project:instances:launch"
    classes = ("ajax-modal", "btn-launch")
    icon = "cloud-upload"
    policy_rules = (("compute", "compute:create"),)
    ajax = True

    def __init__(self, attrs=None, **kwargs):
        kwargs['preempt'] = True
        super(ContribLaunchLink, self).__init__(attrs, **kwargs)

    def allowed(self, request, datum):
        if common_utils.need_ticket(request):
            verbose_name = _("Apply Instance")
        else:
            verbose_name = _("Launch Instance")
        try:
            limits = api.nova.tenant_absolute_limits(request, reserved=True)

            instances_available = limits['maxTotalInstances'] \
                - limits['totalInstancesUsed']
            cores_available = limits['maxTotalCores'] \
                - limits['totalCoresUsed']
            ram_available = limits['maxTotalRAMSize'] - limits['totalRAMUsed']

            if instances_available <= 0 or cores_available <= 0 \
                    or ram_available <= 0:
                if "disabled" not in self.classes:
                    self.classes = [c for c in self.classes] + ['disabled']
                    self.verbose_name = string_concat(self.verbose_name, ' ',
                                                      _("(Quota exceeded)"))
            else:
                self.verbose_name = verbose_name
                classes = [c for c in self.classes if c != "disabled"]
                self.classes = classes
        except Exception:
            LOG.exception("Failed to retrieve quota information")
            # If we can't get the quota information, leave it to the
            # API to check when launching
        return True  # The action should always be displayed

    def single(self, table, request, object_id=None):
        self.allowed(request, None)
        return HttpResponse(self.render())


class ContribInstancesTable(instances_tables.InstancesTable):
    class Meta(instances_tables.InstancesTable.Meta):
        table_actions = (ContribLaunchLink,
                         instances_tables.TerminateInstance,
                         instances_tables.InstancesFilterAction)


class LaunchInstanceView(workflows.WorkflowView):
    workflow_class = ContribLaunchInstance

    def get_initial(self):
        initial = super(LaunchInstanceView, self).get_initial()
        initial['project_id'] = self.request.user.tenant_id
        initial['user_id'] = self.request.user.id
        return initial

    def get_context_data(self, **kwargs):
        context = super(LaunchInstanceView, self).get_context_data(**kwargs)
        enable_fix_ip = getattr(self.request, 'enable_fix_ip', False)
        context['WEBROOT'] = getattr(settings, 'WEBROOT', '/')
        context['ENABLE_FIXED_IP'] = enable_fix_ip
        return context


views.IndexView.table_class = ContribInstancesTable
views.LaunchInstanceView = LaunchInstanceView
