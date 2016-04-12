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

from horizon import tables
from horizon.utils import filters

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from openstack_dashboard.contrib.custom.db import api as db_api

from openstack_dashboard import policy

TICKET_DISPLAY_CHOICES = {
    ("new", _("New")),
    ("closed", _("Closed")),
    ("feedback", _("Feedback")),
}


class CreateTicket(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Ticket")
    url = "horizon:project_openstack_plus:project_tickets:create"
    classes = ("ajax-modal",)
    icon = "plus"


def get_createtime(ticket):
    if hasattr(ticket, "created_at"):
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        created_at = ticket.created_at.strftime(fmt)
        return created_at
    return _("Not available")


class CloseTicket(policy.PolicyTargetMixin, tables.DeleteAction):
    name = "close"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Close Ticket",
            u"Close Ticket",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Close Ticket",
            u"Close Ticket",
            count
        )

    def allowed(self, request, ticket=None):
        return ticket and ticket.status != "closed"

    def delete(self, request, obj_id):
        db_api.ticket_update(request, obj_id,
                             {"status": "closed"})


class TicketsTable(tables.DataTable):
    title = tables.Column(
        "title",
        verbose_name=_("Ticket Title"),
        link="horizon:project_openstack_plus:project_tickets:detail")
    created = tables.Column(get_createtime,
                            verbose_name=_("Created"),
                            filters=(filters.parse_isotime,))
    description = tables.Column("description",
                                verbose_name=_("Ticket Description"),)
    status = tables.Column("status",
                           verbose_name=_("Ticket Status"),
                           display_choices=TICKET_DISPLAY_CHOICES)

    def get_object_display(self, obj):
        return obj.title

    class Meta(object):
        name = "tickets_list"
        verbose_name = _("Tickets")
        table_actions = (CreateTicket,)
        row_actions = (CloseTicket, )
