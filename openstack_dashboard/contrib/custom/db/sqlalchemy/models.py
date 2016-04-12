# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
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
"""
SQLAlchemy models for cinder data.
"""

from django.conf import settings

from oslo_db.sqlalchemy import models
from oslo_serialization import jsonutils
from oslo_utils import timeutils

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy import types as sql_types


CONNECTION = getattr(settings, 'CONNECTION')
BASE = declarative_base()


class JsonBlob(sql_types.TypeDecorator):

    impl = Text

    def process_bind_param(self, value, dialect):
        return jsonutils.dumps(value)

    def process_result_value(self, value, dialect):
        return jsonutils.loads(value)


class HorizonBase(models.TimestampMixin,
                  models.ModelBase):
    """Base class for Cinder Models."""

    __table_args__ = {'mysql_engine': 'InnoDB'}

    # TODO(rpodolyaka): reuse models.SoftDeleteMixin in the next stage
    #                   of implementing of BP db-cleanup
    deleted_at = Column(DateTime)
    deleted = Column(Boolean, default=False)
    metadata = None

    def delete(self, session):
        """Delete this object."""
        self.deleted = True
        self.deleted_at = timeutils.utcnow()
        self.save(session=session)


class Application(BASE, HorizonBase):
    """Represents an application."""

    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    project_id = Column(String(255), nullable=False)
    name = Column(String(255))
    description = Column(String(255))
    website = Column(String(255))
    category = Column(String(255))
    template_data = Column(JsonBlob())
    author = Column(String(255))
    logo = Column(String(255))
    is_public = Column(Boolean, nullable=False, default=False)


class Ticket(BASE, HorizonBase):
    """Represents an application."""

    __tablename__ = 'ticket'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    project_id = Column(String(255), nullable=False)
    title = Column(String(60), nullable=False)
    context = Column(JsonBlob(), nullable=True)
    description = Column(String(10000), nullable=False)
    status = Column(String(60), nullable=False)
    reply = Column(String(10000), nullable=True)
    type = Column(String(60), nullable=False)
    ticket_reply = relationship('TicketReply', backref='ticket',
                                lazy='dynamic')


class TicketReply(BASE, HorizonBase):
    """Represents an application."""

    __tablename__ = 'ticket_reply'
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey('ticket.id'))
    user_id = Column(String(255), nullable=False)
    project_id = Column(String(255), nullable=False)
    title = Column(String(60), nullable=False)
    content = Column(String(10000), nullable=False)
    is_admin = Column(Boolean, default=False)


class EmailSettings(BASE, HorizonBase):
    """Represents an application."""

    __tablename__ = 'email_settings'
    id = Column(Integer, primary_key=True)
    email_host = Column(String(60), nullable=False)
    email_port = Column(String(60), nullable=False)
    email_host_user = Column(String(60), nullable=False)
    email_host_password = Column(String(60), nullable=False)


class Announcement(BASE, HorizonBase):
    """Represents an application."""

    __tablename__ = 'announcement'
    id = Column(Integer, primary_key=True)
    title = Column(String(60), nullable=False)
    content = Column(String(10000), nullable=False)
    keep_days = Column(Integer, nullable=False)
    description = Column(String(1000), nullable=True)


class License(BASE, HorizonBase):
    """Represents a license data."""

    __tablename__ = 'license'
    id = Column(Integer, primary_key=True)
    encrypt_data = Column(String(255), nullable=False)
    last_visit_data = Column(String(255))


class VCenter(BASE, HorizonBase):
    """Represents a license data."""

    __tablename__ = 'vcenter'
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    host_ip = Column(String(255), nullable=False)
    cluster = Column(String(255), nullable=False)


def register_models():
    """Register Models and create metadata.

    Called from cinder.db.sqlalchemy.__init__ as part of loading the driver,
    it will never need to be called explicitly elsewhere unless the
    connection is lost and needs to be reestablished.
    """
    from sqlalchemy import create_engine
    models = (Application, Ticket, EmailSettings, )
    engine = create_engine(CONNECTION, echo=False)
    for model in models:
        model.metadata.create_all(engine)


class Template(BASE, HorizonBase):
    """Represents instance and volume template."""

    __tablename__ = 'template'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255))
    project_id = Column(String(255))
    instance = Column(JsonBlob())
    volume = Column(JsonBlob())


class UserStatistics(BASE, HorizonBase):
    """Represents an application."""

    __tablename__ = 'userstatistics'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), nullable=False)
    project_id = Column(String(64), nullable=False)
    count = Column(Integer, nullable=False)


class GlobalSettings(BASE, HorizonBase):
    """Represents global setting."""

    __tablename__ = 'global_settings'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    value = Column(Boolean, default=False)
    enable = Column(Boolean, default=True)
    extra = Column(JsonBlob())


class LogicalTopology(BASE, HorizonBase):
    """Represents logical topology."""

    __tablename__ = 'logical_topology'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    type = Column(String(255))
    link = Column(JsonBlob())
    hulls = Column(String(255))
    extra = Column(JsonBlob())
