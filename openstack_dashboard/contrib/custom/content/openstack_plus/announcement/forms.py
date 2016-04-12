# Copyright 2012 NEC Corporation
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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.contrib.custom.db import api as db_api


class CreateForm(forms.SelfHandlingForm):
    title = forms.CharField(max_length=60, label=_("Title"))
    description = forms.CharField(max_length=1000,
                                  label=_("Description"),
                                  required=False)
    keep_days = forms.IntegerField(label=_("Rotation"),
                                   min_value=1,
                                   max_value=100)
    content = forms.CharField(max_length=10000,
                              widget=forms.Textarea,
                              label=_("Content"))

    def handle(self, request, data):
        try:
            values = {'user_id': request.user.id,
                      'project_id': request.user.tenant_id,
                      'title': data['title'],
                      'description': data['description'],
                      'keep_days': data['keep_days'],
                      'content': data['content']}

            db_api.announcement_create(request, values)
            msg = _('Announcement %s was successfully '
                    'created.') % data['title']
            messages.success(request, msg)
        except Exception:
            msg = _('Failed to update announcement %s') % data['title']
            exceptions.handle(request, ignore=True)
            return False
        return True


class UpdateForm(forms.SelfHandlingForm):
    announcement_id = forms.CharField(widget=forms.HiddenInput())
    title = forms.CharField(max_length=60, label=_("Title"))
    description = forms.CharField(max_length=1000, label=_("Description"),
                                  required=False)
    keep_days = forms.IntegerField(label=_("Rotation"),
                                   min_value=1,
                                   max_value=100)
    content = forms.CharField(max_length=10000, widget=forms.Textarea,
                              label=_("Content"))

    def handle(self, request, data):
        try:
            announcement_id = data['announcement_id']
            values = {'title': data['title'],
                      'description': data['description'],
                      'keep_days': data['keep_days'],
                      'content': data['content']}

            db_api.announcement_update(request, announcement_id, values)
            msg = _('Announcement %s was successfully '
                    'updated.') % data['title']
            messages.success(request, msg)
        except Exception:
            msg = _('Failed to update announcement %s') % data['title']
            exceptions.handle(request, ignore=True)
            return False
        return True
