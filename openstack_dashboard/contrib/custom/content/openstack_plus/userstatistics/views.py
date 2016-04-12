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
import time
import uuid

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api

from openstack_dashboard.contrib.custom.content.openstack_plus.userstatistics \
    import tables as project_tables
from openstack_dashboard.contrib.custom.db import api as db_api

need_not_statistic = ["service", "services"]


class IndexView(tables.DataTableView):
    table_class = project_tables.UserStatisticsTable
    template_name = 'openstack_plus/userstatistics/index.html'

    def get_data(self):
        tenant_list = self.get_all_tenant()
        user_list = self.get_all_user()
        tenant_dict = dict([(t.id, t) for t in tenant_list])
        date_month = self.table.get_filter_string()
        if date_month:
            format_str = date_month + '-' + str('01')
            try:
                time.strptime(format_str, "%Y-%m-%d")
            except Exception:
                msg = _("Qurey data '%s' does not "
                        "match format 'YYYY-MM'") % date_month
                exceptions.handle(self.request, msg)
                statistics_list = []
                return sorted(statistics_list, key=lambda p: p.count,
                              reverse=True)
        try:
            if not date_month:
                year = str(datetime.datetime.today())[0:4]
                month = str(datetime.datetime.today())[5:7]
            else:
                year = date_month.split('-')[0]
                month = (date_month.split('-')[1]).zfill(2)
            statistics = db_api.statistics_get_by_year_and_month(
                self.request, year, month)
            statistics_list = []
            for user in user_list:
                if user.project_id in tenant_dict:
                    total_count = 0
                    for statistic in statistics:
                        if statistic.user_id == user.id:
                            total_count += statistic.count
                    tenant_id = user.tenantId
                    tenant = tenant_dict.get(tenant_id, None)
                    tenant_name = getattr(tenant, "name", None)
                    s_obj = UserStatisticsObj(str(uuid.uuid4()),
                                              user.id,
                                              user.username,
                                              tenant_name,
                                              total_count)
                    statistics_list.append(s_obj)
                if not user.project_id:
                    total_count = 0
                    for statistic in statistics:
                        if statistic.user_id == user.id:
                            total_count += statistic.count
                    tenant_name = None
                    s_obj = UserStatisticsObj(str(uuid.uuid4()),
                                              user.id,
                                              user.username,
                                              tenant_name,
                                              total_count)
                    statistics_list.append(s_obj)
        except Exception:
            statistics = []
            statistics_list = []
            msg = _('Statistics list can not be retrieved.')
            exceptions.handle(self.request, msg)

        return sorted(statistics_list, key=lambda p: p.count, reverse=True)

    def get_all_tenant(self):
        try:
            tenants, has_more = api.keystone.tenant_list(self.request)
            tenants = filter(lambda x: x.name not in
                             need_not_statistic, tenants)
        except Exception:
            tenants = []
            msg = _('Unable to retrieve tenant information.')
            exceptions.handle(self.request, msg)
        return tenants

    def get_all_user(self):
        try:
            users = api.keystone.user_list(self.request)
        except Exception:
            users = []
            msg = _('Unable to retrieve users information.')
            exceptions.handle(self.request, msg)
        return users


class UserStatisticsObj(object):
    def __init__(self, id, user_id, username, tenant, count):
        self.id = id
        self.username = username
        self.tenant = tenant
        self.count = count
