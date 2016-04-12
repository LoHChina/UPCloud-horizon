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

from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.project.access_and_security.panel \
    import AccessAndSecurity
from openstack_dashboard.dashboards.project.images.panel import Images
from openstack_dashboard.dashboards.project.instances.panel import Instances
from openstack_dashboard.dashboards.project.network_topology.panel \
    import NetworkTopology
from openstack_dashboard.dashboards.project.networks.panel import Networks
from openstack_dashboard.dashboards.project.routers.panel import Routers
from openstack_dashboard.dashboards.project.volumes.panel import Volumes


from openstack_dashboard.contrib.custom.content.openstack_plus.announcement.\
    panel import Announcement
from openstack_dashboard.contrib.custom.content.openstack_plus.ceph_monitor.\
    panel import CephMonitor
from openstack_dashboard.contrib.custom.content.openstack_plus.log_analysis.\
    panel import Log_Analysis
from openstack_dashboard.contrib.custom.content.openstack_plus.\
    logical_network.panel import LogicalTopology
from openstack_dashboard.contrib.custom.content.openstack_plus.monitor.\
    panel import Monitor
from openstack_dashboard.contrib.custom.content.openstack_plus.tickets.panel \
    import Tickets
from openstack_dashboard.contrib.custom.content.openstack_plus.\
    userstatistics.panel import UserStatistics
from openstack_dashboard.contrib.custom.content.openstack_plus.vcenter.panel \
    import VCenter
from openstack_dashboard.contrib.custom.content.openstack_plus.billing.\
    panel import Billing

from openstack_dashboard.contrib.custom.content.project_openstack_plus.\
    announcement.panel import Announcement as project_announcement
from openstack_dashboard.contrib.custom.content.project_openstack_plus.\
    tickets.panel import Tickets as project_tickets
from openstack_dashboard.contrib.custom.content.project_openstack_plus.\
    applications.panel import Applications as project_applications
from openstack_dashboard.contrib.custom.content.project_openstack_plus.\
    billing.panel import Billing as project_billing
from openstack_dashboard.contrib.custom.content.project.overview.panel \
    import Overview as project_overview


class Overviews(horizon.Dashboard):
    name = _("Overview")
    slug = "overview"
    default_panel = "overview"

horizon.register(Overviews)
Overviews.register(project_overview)


class Compute(horizon.Dashboard):
    name = _("Compute")
    slug = "compute"
    default_panel = "instances"
    panels = ('instances', 'images')

horizon.register(Compute)
Compute.register(Instances)
Compute.register(Images)


class Storage(horizon.Dashboard):
    name = _("Storage")
    slug = "storage"
    default_panel = "volumes"

horizon.register(Storage)
Storage.register(Volumes)


class Network(horizon.Dashboard):
    name = _("Network")
    slug = "network"
    default_panel = "network_topology"
    panels = ('network_topology', 'networks', 'routers',)

horizon.register(Network)
Network.register(NetworkTopology)
Network.register(Networks)
Network.register(Routers)


class AccessAndSecurityDashboard(horizon.Dashboard):
    name = _("Access & Security")
    slug = "access_and_security_dashboard"
    default_panel = "access_and_security"

horizon.register(AccessAndSecurityDashboard)
AccessAndSecurityDashboard.register(AccessAndSecurity)


class OpenStackPlus(horizon.Dashboard):
    name = _("Value-Added Plugin")
    slug = "openstack_plus"
    default_panel = "vcenter"
    panels = ('vcenter', 'billing')
    permissions = ('openstack.roles.admin',)

horizon.register(OpenStackPlus)
OpenStackPlus.register(VCenter)
OpenStackPlus.register(Announcement)
OpenStackPlus.register(Tickets)
OpenStackPlus.register(UserStatistics)
OpenStackPlus.register(Log_Analysis)
OpenStackPlus.register(Monitor)
OpenStackPlus.register(CephMonitor)
OpenStackPlus.register(Billing)
OpenStackPlus.register(LogicalTopology)


def navigation(panel, context):
    return not context['request'].user.is_superuser


class ProjectOpenStackPlus(horizon.Dashboard):
    name = _("Value-Added Plugin")
    slug = "project_openstack_plus"
    default_panel = "project_announcement"
    panels = ('project_announcement', 'project_tickets')
    nav = navigation

horizon.register(ProjectOpenStackPlus)
ProjectOpenStackPlus.register(project_announcement)
ProjectOpenStackPlus.register(project_tickets)
ProjectOpenStackPlus.register(project_applications)
ProjectOpenStackPlus.register(project_billing)

horizon.conf.HORIZON_CONFIG['dashboards'] = (
    'overview', 'compute', 'storage', 'network',
    'access_and_security_dashboard', 'project', 'admin', 'identity',
    'project_openstack_plus', 'openstack_plus', 'settings'
)
