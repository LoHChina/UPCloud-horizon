# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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
from horizon import forms

from django.utils.translation import ugettext_lazy as _

from openstack_dashboard.contrib.custom import api
from openstack_dashboard.contrib.custom.api import cinder


class AutoBackupForm(forms.SelfHandlingForm):
    retention = forms.IntegerField(label=_("Retention"),
                                   required=True)

    CYCLE_CHOICES = [('daily', _('Daily')),
                     ('weekly', _('Weekly')),
                     ('monthly', _('Monthly'))]
    cycle = forms.ChoiceField(label=_('Cycle'),
                              widget=forms.Select(),
                              choices=(CYCLE_CHOICES),
                              initial='daily',
                              required=True)

    TYPE_CHOICES = [('full', _('Full')),
                    ('incremental', _('Incremental'))]
    type = forms.ChoiceField(label=_('Type'),
                             widget=forms.Select(),
                             choices=(TYPE_CHOICES),
                             initial='full',
                             required=True)

    def __init__(self, request, *args, **kwargs):
        super(AutoBackupForm, self).__init__(request, *args, **kwargs)
        volume_id = kwargs.get('initial', {}).get('volume_id', [])
        self.fields['volume_id'] = forms.CharField(widget=forms.HiddenInput(),
                                                   initial=volume_id)

    def handle(self, request, data):
        volume = cinder.volume_get(request,
                                   data['volume_id'])
        api.cinder.set_metadata(self.request, volume,
                                self.get_metadata(volume.metadata, data))
        return volume

    def get_metadata(self, metadata, data):
        metadata.update({data["type"]: "{0},{1}".format(data["retention"],
                                                        data["cycle"])})
        return metadata
