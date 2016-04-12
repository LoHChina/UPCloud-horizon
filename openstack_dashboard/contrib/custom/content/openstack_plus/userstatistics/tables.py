# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.utils.translation import ugettext_lazy as _

from horizon import tables


class UserFilterAction(tables.FilterAction):
    # Change default name of 'filter' to distinguish this one from the
    # project instances table filter, since this is used as part of the
    # session property used for persisting the filter.
    name = "filter_user_statistics"
    filter_type = "server"
    filter_choices = (('month', _("Year-Month ="), True)),


class UserStatisticsTable(tables.DataTable):
    user = tables.Column("username",
                         verbose_name=_("User"))
    tenant = tables.Column("tenant",
                           verbose_name=_("Tenant Name"))
    count = tables.Column("count", verbose_name=_("Count"))

    class Meta(object):
        name = "statistics_list"
        verbose_name = _("UserStatistics")
        table_actions = (UserFilterAction, )
        multi_select = False
