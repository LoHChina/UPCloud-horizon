# Copyright 2013 Nebula, Inc.
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

import datetime
import uuid

from django.conf import settings as animbus_settings
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from openstack_dashboard.contrib.custom.api import ceilometer
from openstack_dashboard.contrib.custom.content.project_openstack_plus.billing.query \
    import tables as query_tables
from openstack_dashboard.contrib.custom.content.project_openstack_plus.billing.summary \
    import tables as summary_tables

billing_price = getattr(animbus_settings, "ANIMBUS_PRICES", None)


class SummaryObj(object):
    def __init__(self, id, obj_type, count, total_cost):
        self.id = id
        self.obj_type = obj_type
        self.count = count
        self.total_cost = total_cost


class QueryObj(object):
    def __init__(self, id, name, charging_start, charging_end,
                 obj_type, cost, price, remarks='-'):
        self.id = id
        self.name = name
        self.charging_start = charging_start
        self.charging_end = charging_end
        self.obj_type = obj_type
        self.cost = cost
        self.price = price
        self.remarks = remarks


class SummaryTab(tabs.TableTab):
    table_classes = (summary_tables.SummaryTable,)
    name = _("Summary")
    slug = "summary_tab"
    template_name = ("project_openstack_plus/billing/summary_table.html")
    preload = False

    def count(self, instances):
        return len(list(set(map(lambda x: x["resource_id"], instances))))

    def cost(self, instances):
        return sum(map(lambda x: x["cost"], instances))

    def get_summary_data(self):
        try:
            data = (ceilometer.BillingStatistics().
                    summary_statics(self.request.user.tenant_id))
            summary_list = []
            summary_list.append(SummaryObj(str(uuid.uuid4()),
                                           _("Instance"),
                                           self.count(data["instances"]),
                                           self.cost(data["instances"])))
            summary_list.append(SummaryObj(str(uuid.uuid4()),
                                           _("Image"),
                                           self.count(data["images"]),
                                           self.cost(data["images"])))
            summary_list.append(SummaryObj(str(uuid.uuid4()),
                                           _("Volume"),
                                           self.count(data["volumes"]),
                                           self.cost(data["volumes"])))
            summary_list.append(SummaryObj(str(uuid.uuid4()),
                                           _("Volume Snapshots"),
                                           self.count(data["snapshots"]),
                                           self.cost(data["snapshots"])))
            summary_list.append(SummaryObj(str(uuid.uuid4()),
                                           _("Network"),
                                           self.count(data["networks"]),
                                           self.cost(data["networks"])))
            if not getattr(self.request, 'enable_network_overlay', False):
                summary_list.append(SummaryObj(str(uuid.uuid4()),
                                               _("Floating IP"),
                                               self.count(data["floatingips"]),
                                               self.cost(data["floatingips"])))
                summary_list.append(SummaryObj(str(uuid.uuid4()),
                                               _("Router"),
                                               self.count(data["routers"]),
                                               self.cost(data["routers"])))
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve volume/instance "
                                "attachment information"))
            summary_list = []
        return summary_list

    def get_context_data(self, request, **kwargs):
        context = super(tabs.TableTab, self).get_context_data(request,
                                                              **kwargs)
        for table_name, table in self._tables.items():
            # If there's only one table class, add a shortcut name as well.
            if len(self.table_classes) == 1:
                table.data = self.get_summary_data()
                context["table"] = table
            context["%s_table" % table_name] = table
            summary_list = self.get_summary_data()
            total_cost = 0.00
            for item in summary_list:
                total_cost += item.total_cost
            context["total_cost"] = total_cost
        return context


class QueryTab(tabs.TableTab):
    table_classes = (query_tables.QueryTable,)
    name = _("Query")
    slug = "query_tab"
    template_name = ("project_openstack_plus/billing/query_table.html")
    preload = False

    def get_query_data(self):
        try:
            result_list = []
            date_month = self.request.GET.get("date_month")
            query_type = self.request.GET.get("query_type")
            if query_type is None and date_month is None:
                return []
            year, month = date_month.split("-")
            year, month = int(year), int(month)
            data = (ceilometer.BillingStatistics().
                    statistics_with_month(self.request.user.tenant_id,
                                          year,
                                          month))

            if query_type == "instances" or query_type == "all" \
               or query_type is None:
                for i in data['instances']:
                    if i["meta"]['state'] == "active":
                        status = _("ON")
                    else:
                        status = _("OFF")
                    result_list.append(QueryObj(str(uuid.uuid4()),
                                                i['meta']['display_name'],
                                                i['charge_start'],
                                                i['charge_end'],
                                                _("Instance"),
                                                i['cost'],
                                                _("%s/hours") % (i['price']),
                                                remarks=status))
            if query_type == "images" or query_type == "all" \
               or query_type is None:
                for i in data['images']:
                    result_list.append(QueryObj(str(uuid.uuid4()),
                                                i['meta']['display_name'],
                                                i['charge_start'],
                                                i['charge_end'],
                                                _("Image"),
                                                i['cost'],
                                                _("%s/hours") % (i['price'])))
            if query_type == "volumes" or query_type == "all" \
               or query_type is None:
                for i in data['volumes']:
                    result_list.append(QueryObj(str(uuid.uuid4()),
                                                i['meta']['display_name'],
                                                i['charge_start'],
                                                i['charge_end'],
                                                _("Volume"),
                                                i['cost'],
                                                _("%s/hours") % (i['price'])))
            if query_type == "snapshot" or query_type == "all" \
               or query_type is None:
                for i in data['snapshots']:
                    result_list.append(QueryObj(str(uuid.uuid4()),
                                                i['meta']['display_name'],
                                                i['charge_start'],
                                                i['charge_end'],
                                                _("Volume Snapshots"),
                                                i['cost'],
                                                _("%s/hours") % (i['price'])))
            if query_type == "network" or query_type == "all" \
               or query_type is None:
                for i in data['networks']:
                    result_list.append(QueryObj(str(uuid.uuid4()),
                                                i['meta']['display_name'],
                                                i['charge_start'],
                                                i['charge_end'],
                                                _("Network"),
                                                i['cost'],
                                                (_("%s/hours") %
                                                 (str(i['price'])))))
            if query_type == "router" or query_type == "all" \
               or query_type is None:
                for i in data['routers']:
                    result_list.append(QueryObj(str(uuid.uuid4()),
                                                i['meta']['display_name'],
                                                i['charge_start'],
                                                i['charge_end'],
                                                _("Router"),
                                                i['cost'],
                                                (_("%s/hours") %
                                                 (str(i['price'])))))
            if query_type == "floatingip" or query_type == "all" \
               or query_type is None:
                for i in data['floatingips']:
                    result_list.append(QueryObj(str(uuid.uuid4()),
                                                i['meta']['display_name'],
                                                i['charge_start'],
                                                i['charge_end'],
                                                _("Floating IP"),
                                                i['cost'],
                                                (_("%s/hours") %
                                                 (str(i['price'])))))
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve volume/instance "
                                "attachment information"))
            return []
        return result_list

    def get_context_data(self, request, **kwargs):
        date_month = self.request.GET.get("date_month")
        query_type = self.request.GET.get("query_type")
        context = super(tabs.TableTab, self).get_context_data(request,
                                                              **kwargs)
        if not date_month and not query_type:
            now_month = str(datetime.date(datetime.date.today().year,
                                          datetime.date.today().month,
                                          1))[0:7]
            context["date_month"] = now_month
            context["query_type"] = "all"
        else:
            context["date_month"] = date_month
            context["query_type"] = query_type
        for table_name, table in self._tables.items():
            # If there's only one table class, add a shortcut name as well.
            if len(self.table_classes) == 1:
                table.data = self.get_query_data()
                context["table"] = table
            context["%s_table" % table_name] = table
        enable_network_overlay = getattr(
            self.request, 'enable_network_overlay', False)
        context["enable_network_overlay"] = enable_network_overlay
        return context


class SummaryAndQueryTabs(tabs.TabGroup):
    slug = "summary_and_query"
    tabs = (SummaryTab, QueryTab)
    sticky = True
