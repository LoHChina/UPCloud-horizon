# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2013 NTT MCL Inc.
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

from django import http
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView

from horizon import views

from openstack_dashboard.contrib.custom.db import api as db_api


class LogicalTopologyView(views.HorizonTemplateView):
    template_name = 'openstack_plus/logical_topology/index.html'
    page_title = _("Logical Topology")


class LogicalTopologyDataView(TemplateView):
    def get(self, request, *args, **kwargs):
        i = 100000
        result = {"links": []}
        hulls_dict = {}
        links = {}
        data = db_api.logical_topologi_data_get_all(request)
        for d in data:
            if d.type == 'hulls':
                hulls_dict.update({str(d.id): d.name})
            if d.link:
                links.update(d.link)
                for key, value in d.link.iteritems():
                    i = i + 1
                    link = {"id": str(i),
                            "source": key,
                            "target": value}
                    result["links"].append(link)
        for d in data:
            if d.type != 'hulls':
                if not result.get(d.type):
                    result[d.type] = []
                object = {"id": str(d.id), "name": d.name,
                          "phycical_node": hulls_dict.get(d.hulls),
                          "haproxy": links.get(str(d.id))}
                result[d.type].append(object)

        return http.HttpResponse(json.dumps(result),
                                 content_type='application/json')
