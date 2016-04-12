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

import json

import influxdb

from django.conf import settings
from django import http
from django.template.defaultfilters import floatformat  # noqa
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard.contrib.custom.utils import common_utils


class IndexView(TemplateView):
    template_name = 'admin/overviews/index.html'

    def get_nova_services_data(self):
        try:
            services = api.nova.service_list(self.request)
        except Exception:
            msg = _('Unable to get nova services list.')
            exceptions.check_message(["Connection", "refused"], msg)
            exceptions.handle(self.request, msg)
            services = []
        return services

    def get_network_agents_data(self):
        try:
            agents = api.neutron.agent_list(self.request)
            enable_network_overlay = getattr(
                self.request, 'enable_network_overlay', False)
            if enable_network_overlay:
                for agent in agents:
                    if agent.agent_type == 'L3 agent':
                        agents.remove(agent)
        except Exception:
            msg = _('Unable to get network agents list.')
            exceptions.check_message(["Connection", "refused"], msg)
            exceptions.handle(self.request, msg)
            agents = []
        return agents

    def get_hypervisor_data(self):
        try:
            stats = api.nova.hypervisor_stats(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve hypervisor statistics.'))
            stats = []
        common_utils.get_set_storage(stats=stats)
        return stats

    def get_instances_data(self):
        instances = []
        try:
            instances, self._more = api.nova.server_list(self.request,
                                                         all_tenants=True)
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              _('Unable to retrieve instance list.'))

        active_instances = 0
        shutoff_instances = 0
        suspended_instances = 0
        error_instances = 0
        for instance in instances:
            if instance.status == 'ACTIVE':
                active_instances += 1
            elif instance.status == 'SHUTOFF':
                shutoff_instances += 1
            elif instance.status in ('SUSPENDED', "PAUSED"):
                suspended_instances += 1
            elif instance.status == 'ERROR':
                error_instances += 1

        return {'active_instances': active_instances,
                'shutoff_instances': shutoff_instances,
                'suspended_instances': suspended_instances,
                'error_instances': error_instances,
                'instances': instances}

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        instances_info = self.get_instances_data()
        computer_services = self.get_nova_services_data()
        network_services = self.get_network_agents_data()
        services = computer_services + network_services
        context_dict = {
            'computer_services': computer_services,
            'network_services': network_services,
            'stats': self.get_hypervisor_data(),
            'hypervisor_version': getattr(settings,
                                          'HYPERVISOR_VERSION',
                                          '1.5.3'),
            'hypervisor': getattr(settings, 'HYPERVISOR', 'KVM'),
            'hosts': len(set([service.host for service in services])),
            'neutron_enable': api.base.is_service_enabled(self.request,
                                                          'network')
        }
        context.update(context_dict)
        context.update(instances_info)

        return context


METRICS = [
    ('volume_iops', 'cluster.disk.iops.total.rate',
     'darkorange', "IOPS"),
    ('volume_throghput', 'cluster.disk.io.total.rate',
     'darkseagreen', "B/s"),
    ('network_bandwidth', 'cluster.network.bits.total.rate',
     'lightblue', "bps"),
]


class MesurementsView(TemplateView):

    @staticmethod
    def _series_for_metric(result):
        if result:
            data = result.raw['series'][0]['values']
            return [{'x': str(date_time),
                     'y': value or 0} for date_time, value in data]
        else:
            return []

    def get(self, request, *args, **kwargs):
        series_data = {}
        duration = request.GET.get('duration', '5m')
        retention = request.GET.get('retention', '6h')
        influxdb_client = influxdb.InfluxDBClient(
            getattr(settings, 'INFLUXDB_HOST', 'localhost'),
            getattr(settings, 'INFLUXDB_PORT', 8086),
            getattr(settings, 'INFLUXDB_USERNAME', 'root'),
            getattr(settings, 'INFLUXDB_PASSWORD', 'root'),
            getattr(settings, 'INFLUXDB_DATABASE', 'ceilometer'))
        for metric_type, metric, color_legend, unit in METRICS:
            series = []
            query = ('select mean(value) from /.*%(metric)s/ '
                     'where time > now() - %(retention)s'
                     'GROUP BY time(%(duration)s);'
                     % ({'metric': metric,
                         'duration': duration,
                         'retention': retention}))
            result = influxdb_client.query(query)

            series.append({"color": color_legend,
                           "data": self._series_for_metric(result),
                           "name": metric_type,
                           "unit": unit})

            data = {metric_type: {"series": series}}
            series_data.update(data)

        return http.HttpResponse(json.dumps(series_data),
                                 content_type='application/json')
