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
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon.utils import memoized
from openstack_dashboard import api
from openstack_dashboard.contrib.custom.api import ceilometer
from openstack_dashboard.contrib.custom.content.openstack_plus.billing.query \
    import tables as query_tables
from openstack_dashboard.contrib.custom.content.openstack_plus.billing.summary \
    import tables as summary_tables

billing_price = getattr(animbus_settings, "ANIMBUS_PRICES", None)

need_not_calculate = ["services", ]


class StatisticsObj(object):
    def __init__(self, id, tenant_id, cost):
        self.id = id
        self.tenant_id = tenant_id
        self.cost = cost


class SummaryObj(object):
    def __init__(self, id, tenant_name, total_cost):
        self.id = id
        self.tenant_name = tenant_name
        self.total_cost = total_cost


class QueryObj(object):
    def __init__(self, id, name, tenant_name,
                 user_name, charging_start,
                 charging_end, obj_type, cost, price, remarks='-'):
        self.id = id
        self.name = name
        self.tenant_name = tenant_name
        self.user_name = user_name
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
    template_name = ("openstack_plus/billing/summary_table.html")
    preload = False

    def get_all_tenant(self):
        tenants, has_more = api.keystone.tenant_list(self.request)
        tenants = filter(lambda x: x.name not in need_not_calculate, tenants)
        return tenants

    def get_statistics_list(self, obj_list):
        statistics_list = []
        for i in obj_list:
            sobj = StatisticsObj(str(uuid.uuid4()),
                                 i['tenant_id'],
                                 round(i['cost'], 2))
            statistics_list.append(sobj)
        return statistics_list

    def get_summary_data(self):
        tenant_list = self.get_all_tenant()
        try:
            data = ceilometer.BillingStatistics().summary_statics()

            summary_list = []

            instance_list = self.get_statistics_list(data["instances"])
            volume_list = self.get_statistics_list(data["volumes"])
            snapshot_list = self.get_statistics_list(data["snapshots"])
            image_list = self.get_statistics_list(data["images"])
            network_list = self.get_statistics_list(data["networks"])
            router_list = self.get_statistics_list(data["routers"])
            floatingip_list = self.get_statistics_list(data["floatingips"])
            summary_sobj_list = instance_list + volume_list + snapshot_list +\
                network_list + router_list + floatingip_list + image_list
            for t in filter(lambda x: x.name not in
                            need_not_calculate, tenant_list):
                total_cost = 0.00
                for i in summary_sobj_list:
                    if i.tenant_id == t.id:
                        total_cost += round(i.cost, 2)
                s_obj = SummaryObj(str(uuid.uuid4()),
                                   t.name,
                                   total_cost)
                summary_list.append(s_obj)

        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve "
                                "billing summary information"))
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
    template_name = ("openstack_plus/billing/query_table.html")
    preload = False

    @memoized.memoized_method
    def _get_tenant_list(self):
        try:
            tenants, has_more = api.keystone.tenant_list(self.request)
            tenants = filter(lambda x: x.name not in
                             need_not_calculate, tenants)
        except Exception:
            tenants = []
            msg = _('Unable to retrieve billing project information.')
            exceptions.handle(self.request, msg)

        tenant_dict = SortedDict([(t.id, t) for t in tenants])
        return tenant_dict

    @memoized.memoized_method
    def _get_user_list(self):
        try:
            users = api.keystone.user_list(self.request)
        except Exception:
            users = []
            msg = _('Unable to retrieve billing users information.')
            exceptions.handle(self.request, msg)

        user_dict = SortedDict([(u.id, u) for u in users])
        return user_dict

    def statistics_with_month_tenant(self, year, month, tenant_id):
        query = []
        query += [{"field": "tenant_id",
                   "op": "eq",
                   "type": "string",
                   "value": tenant_id}]
        start_time = datetime.datetime(year, month, 1)
        month += 1
        if month > 12:
            year += 1
            month -= 12
        end_time = datetime.datetime(year, month, 1)
        return ceilometer.statistics(self.request, query, start_time, end_time)

    def get_query_data(self):
        try:
            result_list = []
            date_month = self.request.GET.get("date_month")
            query_type = self.request.GET.get("query_type")
            tenant_id = self.request.GET.get("tenant_id")
            if not tenant_id:
                result_list = []
            else:
                year, month = date_month.split("-")
                year, month = int(year), int(month)
                data = (ceilometer.BillingStatistics().
                        statistics_with_month(tenant_id, year, month))

                tenant_dict = self._get_tenant_list()
                user_dict = self._get_user_list()

                def get_tenant_name(i):
                    tenant = tenant_dict.get(i['tenant_id'], None)
                    return getattr(tenant, 'name', None)

                def get_user_name(i):
                    user = user_dict.get(i['user_id'], None)
                    return getattr(user, 'name', None)

                if query_type == "instances" or query_type == "all" \
                   or query_type is None:
                    for i in data['instances']:
                        if i["meta"]['state'] == "active":
                            status = _("ON")
                        else:
                            status = _("OFF")
                        result_list.append(QueryObj(str(uuid.uuid4()),
                                                    i['meta']['display_name'],
                                                    get_tenant_name(i),
                                                    get_user_name(i),
                                                    i['charge_start'],
                                                    i['charge_end'],
                                                    _("Instance"),
                                                    i['cost'],
                                                    (_("%s/hours") %
                                                     (i['price'])),
                                                    remarks=status))

                if query_type == "images" or query_type == "all":
                    for i in data["images"]:
                        result_list.append(QueryObj(str(uuid.uuid4()),
                                                    i["meta"]["display_name"],
                                                    get_tenant_name(i),
                                                    get_user_name(i),
                                                    i["charge_start"],
                                                    i["charge_end"],
                                                    _("Image"),
                                                    i["cost"],
                                                    (_("%s/hours") %
                                                     (i["price"]))))
                if query_type == "volumes" or query_type == "all":
                    for i in data['volumes']:
                        result_list.append(QueryObj(str(uuid.uuid4()),
                                                    i['meta']['display_name'],
                                                    get_tenant_name(i),
                                                    get_user_name(i),
                                                    i['charge_start'],
                                                    i['charge_end'],
                                                    _("Volume"),
                                                    i['cost'],
                                                    (_("%s/hours") %
                                                     (i['price']))))
                if query_type == "snapshot" or query_type == "all":
                    for i in data['snapshots']:
                        result_list.append(QueryObj(str(uuid.uuid4()),
                                                    i['meta']['display_name'],
                                                    get_tenant_name(i),
                                                    get_user_name(i),
                                                    i['charge_start'],
                                                    i['charge_end'],
                                                    _("Volume Snapshots"),
                                                    i['cost'],
                                                    (_("%s/hours") %
                                                     (i['price']))))

                if query_type == "network" or query_type == "all" \
                   or query_type is None:
                    for i in data['networks']:
                        result_list.append(QueryObj(str(uuid.uuid4()),
                                                    i['meta']['display_name'],
                                                    get_tenant_name(i),
                                                    get_user_name(i),
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
                                                    get_tenant_name(i),
                                                    get_user_name(i),
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
                                                    get_tenant_name(i),
                                                    get_user_name(i),
                                                    i['charge_start'],
                                                    i['charge_end'],
                                                    _("Floating IP"),
                                                    i['cost'],
                                                    (_("%s/hours") %
                                                     (str(i['price'])))))
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve billing "
                                "query information"))
            return []
        return result_list

    def get_context_data(self, request, **kwargs):
        date_month = self.request.GET.get("date_month")
        query_type = self.request.GET.get("query_type")
        tenant_id = self.request.GET.get("tenant_id")
        tenants, has_more = api.keystone.tenant_list(self.request)
        tenants = filter(lambda x: x.name not in need_not_calculate, tenants)
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
        context["tenants"] = tenants
        context["tenant_id"] = tenant_id
        enable_network_overlay = getattr(
            self.request, 'enable_network_overlay', False)
        context["enable_network_overlay"] = enable_network_overlay
        return context


class SummaryAndQueryTabs(tabs.TabGroup):
    slug = "summary_and_query"
    tabs = (SummaryTab, QueryTab)
    sticky = True
