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

"""Defines interface for DB access.

The underlying driver is loaded as a :class:`LazyPluggable`.

Functions in this module are imported into the cinder.db namespace. Call these
functions from cinder.db namespace, not the cinder.db.api namespace.

All functions in this module return objects that implement a dictionary-like
interface. Currently, many of these objects are sqlalchemy objects that
implement a dictionary interface. However, a future goal is to have all of
these objects be simple dictionaries.

"""

from oslo_config import cfg
from oslo_db import concurrency as db_concurrency


CONF = cfg.CONF

_BACKEND_MAPPING = {
    'sqlalchemy':
    'openstack_dashboard.contrib.custom.db.sqlalchemy.api'}


IMPL = db_concurrency.TpoolDbapiWrapper(CONF, _BACKEND_MAPPING)


def application_get_all(context, category=None):
    """Get all applications."""
    return IMPL.application_get_all(context, category)


def application_create(context, values):
    """Create an application from the values dictionary."""
    return IMPL.application_create(context, values)


def application_get_by_id(context, application_id):
    """Get the application for a given application_id."""
    return IMPL.application_get_by_id(context, application_id)


def application_delete(context, application_id):
    """Delete the specified application."""
    return IMPL.application_delete(context, application_id)


def ticket_create(context, values):
    """Create an ticket from the values dictionary."""
    return IMPL.ticket_create(context, values)


def ticket_get_all(context, category=None):
    """Get all tickets."""
    return IMPL.ticket_get_all(context, category)


def ticket_get_by_id(context, ticket_id):
    """Get ticket by id."""
    return IMPL.ticket_get_by_id(context, ticket_id)


def ticket_update(context, ticket_id, values):
    """Update ticket by id."""
    return IMPL.ticket_update(context, ticket_id, values)


def ticket_reply_create(context, values):
    """Create an ticket reply from the values dictionary."""
    return IMPL.ticket_reply_create(context, values)


def ticket_reply_get_all(context, category=None):
    """Get all tickets reply."""
    return IMPL.ticket_reply_get_all(context, category)


def get_all_ticket_reply_by_ticket_id(context, ticket_id):
    """Get all tickets reply."""
    return IMPL.get_all_ticket_reply_by_ticket_id(context, ticket_id)


def ticket_reply_get_by_id(context, ticket_reply_id):
    """Get ticket reply by ticket id."""
    return IMPL.ticket_get_by_id(context, ticket_reply_id)


def ticket_reply_update(context, ticket_reply_id, values):
    """Update ticket reply by id."""
    return IMPL.ticket_reply_update(context, ticket_reply_id, values)


def email_settings_create(context, values):
    """Create an eamil settings from the values dictionary."""
    return IMPL.email_settings_create(context, values)


def email_settings_get_all(context, category=None):
    """Get all email settings."""
    return IMPL.email_settings_get_all(context, category)


def email_settings_update(context, email_settngs_id, values):
    """Update email settings by id."""
    return IMPL.email_settings_update(context, email_settngs_id, values)


def announcement_create(context, values):
    """Create an eamil settings from the values dictionary."""
    return IMPL.announcement_create(context, values)


def announcement_get_all(context, category=None):
    """Get all email settings."""
    return IMPL.announcement_get_all(context, category)


def announcement_get_by_id(context, announcement_id):
    """Get ticket reply by ticket id."""
    return IMPL.announcement_get_by_id(context, announcement_id)


def announcement_update(context, announcement_id, values):
    """Update email settings by id."""
    return IMPL.announcement_update(context, announcement_id, values)


def announcement_delete(context, announcement_id):
    """Delete the specified announcement."""
    return IMPL.announcement_delete(context, announcement_id)


def license_data_get(context):
    """Get the license data."""
    return IMPL.license_data_get(context)


def license_data_create(context, values):
    """Create license data."""
    return IMPL.license_data_create(context, values)


def license_last_visit_day_update(context, values):
    """Update the license last_visit_day."""
    return IMPL.license_last_visit_day_update(context, values)


def template_get(context, template_type):
    return IMPL.template_get(context, template_type)


def template_create_or_update(request, values):
    """Create or update instance and volume template"""
    return IMPL.template_create_or_update(request, values)


def statistics_create(context, values):
    """Create an statistics from the values dictionary."""
    return IMPL.statistics_create(context, values)


def statistics_get_by_year_and_month(context, year, month):
    return IMPL.statistics_get_by_year_and_month(context, year, month)


def global_settings_get_by_name(context, name):
    """Get global settings by name"""
    return IMPL.global_settings_get_by_name(context, name)


def global_settings_get(context):
    """Get global settings"""
    return IMPL.global_settings_get(context)


def global_settings_update_by_name(request, values):
    """Create or update global settings by name"""
    return IMPL.global_settings_update_by_name(request, values)


def vcenter_create(context, values):
    """Create vCenter"""
    return IMPL.vcenter_create(context, values)


def vcenter_get_all(context):
    """Get all vCenter info"""
    return IMPL.vcenter_get_all(context)


def vcenter_get_by_id(context, vcenter_id):
    """Get one vCenter info"""
    return IMPL.vcenter_get_by_id(context, vcenter_id)


def logical_topologi_data_get_all(context):
    """Get all logical topology info"""
    return IMPL.logical_topologi_data_get_all(context)
