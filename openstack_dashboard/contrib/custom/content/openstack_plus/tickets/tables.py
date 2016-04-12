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
from horizon.utils import filters


TICKET_DISPLAY_CHOICES = {
    ("new", _("New")),
    ("closed", _("Closed")),
    ("feedback", _("Feedback")),
}


class EditTicket(tables.LinkAction):
    name = "manage_ticket"
    verbose_name = _("Manage Ticket")
    url = "horizon:openstack_plus:tickets:update"
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, datum):
        return (datum.status not in ('closed', ))


def get_createtime(ticket):
    if hasattr(ticket, "created_at"):
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        created_at = ticket.created_at.strftime(fmt)
        return created_at
    return _("Not available")


class TicketsTable(tables.DataTable):
    title = tables.Column("title",
                          verbose_name=_("Ticket Title"),
                          link="horizon:openstack_plus:tickets:detail")
    created = tables.Column(get_createtime,
                            verbose_name=_("Created"),
                            filters=(filters.parse_isotime,))
    tenant = tables.Column("tenant_name", verbose_name=_("Project"))
    user = tables.Column("user_name", verbose_name=_("User Name"))
    description = tables.Column("description",
                                verbose_name=_("Ticket Discription"),)
    status = tables.Column("status", verbose_name=_("Ticket Status"),
                           display_choices=TICKET_DISPLAY_CHOICES)

    class Meta(object):
        name = "tickets_list"
        verbose_name = _("Tickets")
        row_actions = (EditTicket,)
