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


class SummaryTable(tables.DataTable):
    resource = tables.Column("obj_type",
                             verbose_name=_("Resource"),)
    count = tables.Column("count",
                          verbose_name=_("Count"))
    total = tables.Column("total_cost",
                          verbose_name=_("Total Consumption(CNY)"))

    class Meta(object):
        name = "summary"
        verbose_name = _("Summary")
