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

import datetime

from django import template

from horizon.templatetags.horizon import horizon_nav

from openstack_dashboard.contrib.custom.db import api as db_api
from openstack_dashboard.contrib.custom.overrides import sidebar

from openstack_dashboard import api


register = template.Library()


@register.inclusion_tag('horizon/_sidebar.html', takes_context=True)
def custom_horizon_nav(context):
    nav = horizon_nav(context)
    current_panel = nav['current_panel']
    if nav['current'].slug == "project":
        for dash, panels in nav['components']:
            panels_list = [panel.slug for panel in panels.values()[0]]
            if current_panel in panels_list and dash.slug != 'project':
                nav['current'] = dash
                break

    for dash, panels in nav['components']:
        # Resort Network Dashboard
        if dash.slug == "network":
            panels_dict = dict(
                [(panel.slug, panel) for panel in panels.values()[0]])
            sorted_panels = [
                panels_dict.get(key) for key in sidebar.Network.panels]
            panels[panels.keys()[0]] = sorted_panels

        # Resort Compute Dashboard
        if dash.slug == "compute":
            panels_dict = dict(
                [(panel.slug, panel) for panel in panels.values()[0]])
            sorted_panels = [
                panels_dict.get(key) for key in sidebar.Compute.panels]
            panels[panels.keys()[0]] = sorted_panels

    # add monitor_url and log_url
    ceph_monitor_url = 'ceph_monitor_url'
    monitor_url = 'monitor_url'
    log_url = 'log_url'
    ceph_monitor_obj = db_api.global_settings_get_by_name(
        context['request'], ceph_monitor_url)
    monitor_obj = db_api.global_settings_get_by_name(
        context['request'], monitor_url)
    log_obj = db_api.global_settings_get_by_name(context['request'], log_url)
    ceph_monitor_url = getattr(ceph_monitor_obj, 'extra', '')
    monitor_url = getattr(monitor_obj, 'extra', '')
    log_url = getattr(log_obj, 'extra', '')
    if ceph_monitor_url == '':
        ceph_monitor_url = '/ceph_monitor'
    if monitor_url == '':
        monitor_url = '/monitor'
    if log_url == '':
        log_url = '/log'
    nav['ceph_monitor_url'] = ceph_monitor_url
    nav['log_url'] = log_url
    nav['monitor_url'] = monitor_url

    return nav


@register.inclusion_tag('context_selection/_app_store.html',
                        takes_context=True)
def show_app_store(context):
    can_access_app_store = (api.base.is_service_enabled(
                            context['request'], 'orchestration') and
                            not context['request'].user.is_superuser
                            and getattr(context['request'],
                            'enable_app_store', False))
    return {'can_access_app_store': can_access_app_store}


@register.inclusion_tag('context_selection/_announcement.html',
                        takes_context=True)
def show_announcement(context):
    announcements = db_api.announcement_get_all(context['request'])
    time_now = datetime.datetime.utcnow()
    announcement_list = filter(
        lambda x: x.keep_days * 24 > (time_now - x.created_at).days * 24,
        announcements)

    return {'announcement': True,
            "announcement_list": announcement_list,
            'announcement_len': len(announcement_list)}
