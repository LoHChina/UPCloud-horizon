# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2014 IBM Corp.
# All Rights Reserved.
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

"""Implementation of SQLAlchemy backend."""


import sys
import threading

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from oslo_config import cfg
from oslo_db import options
from oslo_db.sqlalchemy import session as db_session
from oslo_utils import timeutils
from sqlalchemy.sql.expression import literal_column

from openstack_dashboard.contrib.custom.db.sqlalchemy import models

from horizon import exceptions as exception


CONF = cfg.CONF

CONNECTION = getattr(settings, 'CONNECTION')

options.set_defaults(CONF, connection=CONNECTION)

_LOCK = threading.Lock()
_FACADE = None


def _create_facade_lazily():
    global _LOCK
    with _LOCK:
        global _FACADE
        if _FACADE is None:
            _FACADE = db_session.EngineFacade(
                CONF.database.connection,
                **dict(CONF.database.iteritems())
            )

        return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def get_backend():
    """The backend is this module itself."""

    return sys.modules[__name__]


def is_admin_context(context):
    """Indicates if the request context is an administrator."""
    return context.user.is_superuser


def is_user_context(context):
    """Indicates if the request context is a normal user."""
    return not context.user.is_superuser


def require_admin_context(f):
    """Decorator to require admin request context.

    The first argument to the wrapped function must be the context.

    """

    def wrapper(*args, **kwargs):
        if not is_admin_context(args[0]):
            raise exception.AdminRequired()
        return f(*args, **kwargs)
    return wrapper


def require_context(f):
    """Decorator to require *any* user or admin context.

    The first argument to the wrapped function must be the context.

    """

    def wrapper(*args, **kwargs):
        if not is_admin_context(args[0]) and not is_user_context(args[0]):
            raise exception.NotAuthorized()
        return f(*args, **kwargs)
    return wrapper


def model_query(context, *args, **kwargs):
    """Query helper that accounts for context's `read_deleted` field.

    :param context: context to query under
    :param session: if present, the session to use
    :param read_deleted: if present, overrides context's read_deleted field.
    :param project_only: if present and context is user-type, then restrict
            query to match the context's project_id.
    """
    session = kwargs.get('session') or get_session()
    read_deleted = kwargs.get('read_deleted') or context.read_deleted
    project_only = kwargs.get('project_only')

    query = session.query(*args)

    if read_deleted == 'no':
        query = query.filter_by(deleted=False)
    elif read_deleted == 'yes':
        pass  # omit the filter to include deleted and active
    elif read_deleted == 'only':
        query = query.filter_by(deleted=True)
    else:
        raise Exception(
            _("Unrecognized read_deleted value '%s'") % read_deleted)

    if project_only and is_user_context(context):
        query = query.filter_by(project_id=context.project_id)

    return query


@require_context
def application_get_all(context, category):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.Application, read_deleted="no")
        if category:
            return query.filter_by(category=category).all()
        else:
            return query.all()


@require_context
def application_create(context, values):
    application = models.Application()
    application.update(values)

    session = get_session()
    with session.begin():
        application.save(session)
        return application


@require_context
def application_get_by_id(context, application_id):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.Application, read_deleted="no").\
            filter_by(id=application_id)
        return query.first()


@require_context
def application_delete(context, application_id):
    session = get_session()
    with session.begin():
        model_query(
            context, models.Application, read_deleted="no").\
            filter_by(id=application_id).\
            update({'deleted': True,
                    'deleted_at': timeutils.utcnow(),
                    'updated_at': literal_column('updated_at')})


@require_context
def ticket_create(context, values):
    ticket = models.Ticket()
    ticket.update(values)

    session = get_session()
    with session.begin():
        ticket.save(session)
        return ticket


@require_context
def ticket_get_all(context, category):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.Ticket, read_deleted="no")
        if category:
            return query.filter_by(category=category).all()
        else:
            return query.order_by(models.Ticket.created_at.desc()).all()


@require_context
def ticket_get_by_id(context, ticket_id):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.Ticket, read_deleted="no").\
            filter_by(id=ticket_id)
        return query.first()


@require_context
def ticket_update(context, ticket_id, values):
    session = get_session()
    with session.begin():
        model_query(
            context, models.Ticket, read_deleted="no").\
            filter_by(id=ticket_id).\
            update(values)


@require_context
def ticket_reply_create(context, values):
    ticket_reply = models.TicketReply()
    ticket_reply.update(values)

    session = get_session()
    with session.begin():
        ticket_reply.save(session)
        return ticket_reply


@require_context
def ticket_reply_get_all(context, category):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.TicketReply, read_deleted="no")
        if category:
            return query.filter_by(category=category).all()
        else:
            return query.order_by(models.TicketReply.created_at.desc()).all()


@require_context
def ticket_reply_get_by_id(context, ticket_reply_id):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.TicketReply, read_deleted="no").\
            filter_by(id=ticket_reply_id)
        return query.first()


@require_context
def get_all_ticket_reply_by_ticket_id(context, ticket_id):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.TicketReply, read_deleted="no").\
            filter_by(ticket_id=ticket_id)
        return query.all()


@require_context
def ticket_reply_update(context, ticket_reply_id, values):
    session = get_session()
    with session.begin():
        model_query(
            context, models.TicketReply, read_deleted="no").\
            filter_by(id=ticket_reply_id).\
            update(values)


@require_context
def email_settings_create(context, values):
    email_settings = models.EmailSettings()
    email_settings.update(values)

    session = get_session()
    with session.begin():
        email_settings.save(session)
        return email_settings


@require_context
def email_settings_get_all(context, category):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.EmailSettings, read_deleted="no")
        if category:
            return query.filter_by(category=category).all()
        else:
            return query.order_by(models.EmailSettings.created_at.desc()).all()


@require_context
def email_settings_update(context, email_settings_id, values):
    session = get_session()
    with session.begin():
        model_query(
            context, models.EmailSettings, read_deleted="no").\
            filter_by(id=email_settings_id).\
            update(values)


@require_context
def announcement_create(context, values):
    announcement = models.Announcement()
    announcement.update(values)

    session = get_session()
    with session.begin():
        announcement.save(session)
        return announcement


@require_context
def announcement_get_all(context, category):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.Announcement, read_deleted="no")
        if category:
            return query.filter_by(category=category).all()
        else:
            return query.order_by(models.Announcement.created_at.desc()).all()


@require_context
def announcement_update(context, announcement_id, values):
    session = get_session()
    with session.begin():
        model_query(
            context, models.Announcement, read_deleted="no").\
            filter_by(id=announcement_id).\
            update(values)


@require_context
def announcement_get_by_id(context, announcement_id):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.Announcement, read_deleted="no").\
            filter_by(id=announcement_id)
        return query.first()


@require_context
def announcement_delete(context, announcement_id):
    session = get_session()
    with session.begin():
        model_query(
            context, models.Announcement, read_deleted="no").\
            filter_by(id=announcement_id).\
            update({'deleted': True,
                    'deleted_at': timeutils.utcnow(),
                    'updated_at': literal_column('updated_at')})


def license_data_get(context):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.License, read_deleted="no").\
            order_by(models.License.id.desc()).first()
        return query


def license_data_create(context, values):
    license = models.License()
    license.update(values)

    session = get_session()
    with session.begin():
        license.save(session)
        return license


def license_last_visit_day_update(context, values):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.License, read_deleted="no").\
            order_by(models.License.id.desc()).first()
        query.update(values)


def template_get(context, template_type):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.Template, read_deleted="no").first()

    if query:
        return query[template_type]
    else:
        return False


def template_create_or_update(request, values):
    """Create or update instance and volume template"""

    session = get_session()

    result = model_query(request, models.Template,
                         read_deleted="no")

    with session.begin():
        if result.first():
            result.update(values)
        else:
            values['user_id'] = request.user.id
            values['project_id'] = request.user.tenant_id

            try:
                template_ref = models.Template()
                template_ref.update(values)
                template_ref.save(session=session)
            except Exception as e:
                raise Exception(e)


@require_context
def statistics_create(context, values):
    statistics = models.UserStatistics()
    statistics.update(values)

    session = get_session()
    with session.begin():
        statistics.save(session)
        return statistics


@require_context
def statistics_get_by_year_and_month(context, year, month):
    session = get_session()
    query = session.query(models.UserStatistics).\
        filter(models.UserStatistics.created_at.like(
            "{0}-{1}%".format(year, month))).all()
    return query


@require_context
def vcenter_create(context, values):
    vcenter = models.VCenter()
    vcenter.update(values)

    session = get_session()
    with session.begin():
        vcenter.save(session)
        return vcenter


@require_context
def vcenter_get_all(context):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.VCenter, read_deleted="no")
        return query.all()


@require_context
def vcenter_get_by_id(context, vcenter_id):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.VCenter, read_deleted="no")
        return query.filter_by(id=vcenter_id).all()[0]


@require_context
def global_settings_get_by_name(context, name):
    session = get_session()
    with session.begin():
        query = model_query(context,
                            models.GlobalSettings,
                            read_deleted="no").filter_by(name=name)
        return query.first()


@require_context
def global_settings_get(context):
    session = get_session()
    with session.begin():
        query = model_query(context, models.GlobalSettings, read_deleted="no")
        return query.all()


@require_context
def global_settings_update_by_name(request, values):
    """Create or update global settings"""

    session = get_session()
    result = model_query(request, models.GlobalSettings,
                         read_deleted="no").filter_by(name=values['name'])

    with session.begin():
        if result.first():
            result.update(values)
        else:
            try:
                template_ref = models.GlobalSettings()
                template_ref.update(values)
                template_ref.save(session=session)
            except Exception as e:
                raise Exception(str(e))


@require_context
def logical_topologi_data_get_all(context):
    session = get_session()
    with session.begin():
        query = model_query(
            context, models.LogicalTopology, read_deleted="yes")
        return query.all()
