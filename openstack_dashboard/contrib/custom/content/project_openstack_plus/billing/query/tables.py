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

from django import template
from django.utils.translation import ugettext_lazy as _

from datetime import datetime
from horizon import tables


def get_charge_time(billing):
    template_name = 'project_openstack_plus/billing/_charge_time.html'
    fmt = "%Y-%m-%d %H:%M:%S"
    if hasattr(billing, "charging_start"):
        charge_start = (datetime.fromtimestamp(billing.charging_start).
                        strftime(fmt))
    if hasattr(billing, "charging_end"):
        charge_end = datetime.fromtimestamp(billing.charging_end).strftime(fmt)
    context = {"charge_start": charge_start,
               "charge_end": charge_end}
    return template.loader.render_to_string(template_name, context)


class QueryTable(tables.DataTable):
    obj_type = tables.Column("obj_type",
                             verbose_name=_("Type"),)
    display_name = tables.Column("name",
                                 verbose_name=_("Name"),)
    charge_time = tables.Column(get_charge_time,
                                verbose_name=_("Charge Time"),
                                attrs={'data-type': "charge_time"})
    cost = tables.Column("cost",
                         verbose_name=_("Cost(CNY)"),)
    Price = tables.Column("price",
                          verbose_name=_("Price(CNY)"),)
    remarks = tables.Column('remarks',
                            verbose_name=_("Remarks"),)

    class Meta(object):
        name = "query"
        verbose_name = _("Query")
