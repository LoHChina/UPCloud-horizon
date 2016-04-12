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

import json

import influxdb

from django.conf import settings
from django import http
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from openstack_dashboard.dashboards.project.instances import views


METRICS = [
    ['cpu', {'cpu_util': ['darkorange', 'CPU']}],
    ['memory', {'memory.usage': ['darkorange', unicode(_('MEMORY'))]}],
    ['disk_throughput', {'disk.read.bytes.rate':
                         ['darkorange', unicode(_('READ'))],
                         'disk.write.bytes.rate':
                         ['lightblue', unicode(_('WRITE'))]}],
    ['disk_iops', {'disk.read.requests.rate':
                   ['darkorange', unicode(_('READ'))],
                   'disk.write.requests.rate':
                   ['lightblue', unicode(_('WRITE'))]}],
    ['network', {'network.incoming.bytes.rate':
                 ['darkorange', unicode(_('INGRESS'))],
                 'network.outgoing.bytes.rate':
                 ['lightblue', unicode(_('EGRESS'))]}]
]


class MesurementsView(TemplateView):

    @staticmethod
    def _series_for_metric(result):
        if result:
            data = result.raw['series'][0]['values']
            return [{'x': str(date_time),
                     'y': value} for date_time, value in data]
        else:
            return []

    def get(self, request, *args, **kwargs):
        series_data = {}
        resource = self.kwargs['instance_id']
        duration = request.GET.get('duration', None)
        retention = request.GET.get('retention', None)
        influxdb_client = influxdb.InfluxDBClient(
            getattr(settings, 'INFLUXDB_HOST', 'localhost'),
            getattr(settings, 'INFLUXDB_PORT', 8086),
            getattr(settings, 'INFLUXDB_USERNAME', 'root'),
            getattr(settings, 'INFLUXDB_PASSWORD', 'root'),
            getattr(settings, 'INFLUXDB_DATABASE', 'ceilometer'))
        for metric_type, metrics in METRICS:
            series = []
            for metric, color_legend in metrics.items():
                query = ('select mean(value) from /%(resource)s.*%(metric)s/ '
                         'where time > now() - %(retention)s'
                         'GROUP BY time(%(duration)s);'
                         % ({'resource': resource,
                             'metric': metric,
                             'duration': duration,
                             'retention': retention}))
                result = influxdb_client.query(query)

                series.append({"color": color_legend[0],
                               "data": self._series_for_metric(result),
                               "name": color_legend[1]})
            data = {metric_type: {"series": series}}
            series_data.update(data)

        return http.HttpResponse(json.dumps(series_data),
                                 content_type='application/json')


class DetailView(views.DetailView):
    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        enable_metering_feature = getattr(
            self.request, 'enable_metering_feature', False)
        context['instance'].enable_metering_feature = enable_metering_feature
        return context
