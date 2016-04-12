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

import base64
import os
import re

import animbus_backend

from django.conf import settings
from django.core import mail as define_mail
from django.core.urlresolvers import reverse  # noqa
from django.core.urlresolvers import reverse_lazy  # noqa
from django.forms import ValidationError  # noqa
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django import template as dj_template
from django.template import loader
from django.utils.translation import ugettext_lazy as _  # noqa
from django.views.generic import TemplateView
from django.views.generic import View

from horizon import exceptions
from horizon import forms
from horizon.utils import validators

from neutronclient.v2_0 import client as neutron_client

from openstack_dashboard import api
from openstack_dashboard.contrib.custom.db import api as db_api

email_backend = getattr(settings, "EMAIL_BACKEND", None)
email_use_tls = getattr(settings, "EMAIL_USE_TLS", None)
email_dir = getattr(settings, "EMAIL_DIR", None)

domain_name = getattr(settings, "DOMAIN_NAME", None)


def admin_neutron_client(request):
    k = filter(lambda x: x["name"] == 'keystone',
               request.user.token.serviceCatalog)[0]
    auth_url = k.get("endpoints")[0].get("adminURL")
    username = getattr(settings, "OS_USERNAME", "")
    password = getattr(settings, "OS_PASSWORD", "")
    tenant = getattr(settings, "OS_TENANT_NAME", "")
    neutron = neutron_client.Client(username=username,
                                    password=password,
                                    tenant_name=tenant,
                                    auth_url=auth_url)
    return neutron


def _check_ip(request, network_id, fixed_ip):
    try:
        fixed_ip = re.findall(r'\d+.\d+.\d+.\d+', fixed_ip)[0]
    except Exception:
        return False

    def format_ip(ip):
        a, b, c, d = map(int, ip.split('.'))
        return "%03d.%03d.%03d.%03d" % (a, b, c, d)
    try:
        network = api.neutron.network_get(request, network_id)
        subnet = network['subnets'][0]
    except Exception:
        return False
    flag = False
    for allocation_pool in subnet['allocation_pools']:
        start = allocation_pool.get('start')
        end = allocation_pool.get('end')
        sorted_ips = sorted(map(format_ip, [start, end, fixed_ip]))
        if sorted_ips[1] == format_ip(fixed_ip):
            flag = True
    if not flag:
        return False
    neutron = admin_neutron_client(request)
    for port in neutron.list_ports().get('ports'):
        fixed_ips = port['fixed_ips']
        for ip in fixed_ips:
            if ip.get('subnet_id') == subnet.id and \
               ip.get('ip_address') == fixed_ip:
                return False

    return True


def check_ip(request):
    response = HttpResponse(_check_ip(request,
                                      request.GET.get("network", ""),
                                      request.GET.get("fixed_ip", "")))
    return response


class BaseUserForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(BaseUserForm, self).__init__(request, *args, **kwargs)
        project_choices = []
        try:
            ks = animbus_backend.authenticate()
            projects = ks.tenants.list()
            for project in projects:
                if project.enabled and project.name != "admin" \
                   and project.name != "services":
                    project_choices.append((project.id, project.name))
            if not project_choices:
                project_choices.insert(0, ('', _("No available projects")))
            elif len(project_choices) > 1:
                project_choices.insert(0, ('', _("Select a project")))
            self.fields['project'].choices = project_choices
        except Exception:
            exceptions.handle(request, _('Something wrong with authenticate.'))

    def clean(self):
        '''Check to make sure password fields match.'''
        data = super(forms.Form, self).clean()
        if 'password' in data:
            if data['password'] != data.get('confirm_password', None):
                raise ValidationError(_('Passwords do not match.'))
        return data


class RegisterForm(BaseUserForm):
    domain_id = forms.CharField(label=_("Domain ID"),
                                required=False,
                                widget=forms.HiddenInput())
    domain_name = forms.CharField(label=_("Domain Name"),
                                  required=False,
                                  widget=forms.HiddenInput())
    email = forms.EmailField(label=_("Email"),
                             required=True)
    password = forms.RegexField(
        label=_("Password"),
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})
    confirm_password = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(render_value=False))
    project = forms.ChoiceField(label=_("Project"), )

    def clean(self):
        '''Check to make sure password fields match.'''
        data = super(forms.Form, self).clean()
        if 'password' in data:
            if data['password'] != data.get('confirm_password', None):
                raise ValidationError(_('Passwords do not match.'))
        return data

    def handle(self, request, data):
        email = data['email']
        password = data['password']
        project = data['project']
        try:
            try:
                ks = animbus_backend.authenticate()
            except Exception:
                raise ValidationError(_('Something wrong with authenticate'))

            try:
                new_user = ks.users.create(name=email,
                                           email=email,
                                           password=password,
                                           tenant_id=project,
                                           enabled=False)
            except Exception:
                raise ValidationError(_('The user has already exist.'))

            user64 = base64.encodestring(new_user.id)
            template = loader.get_template(os.path.join(email_dir,
                                                        "enable.html"))
            if domain_name:
                domain = domain_name
            else:
                domain = request.get_host()
            enable_url = "http://%s%s?p=%s" % (
                domain,
                reverse("horizon:activate_account"),
                user64)
            context = dj_template.Context({'email': email,
                                           'enable_url': enable_url})
            content = template.render(context)
            try:
                email_settings = db_api.email_settings_get_all(self.request)
                from_mail = email_settings[0].email_host_user
                email_host = email_settings[0].email_host
                email_port = email_settings[0].email_port
                email_host_password = email_settings[0].email_host_password
                define_mail.settings.EMAIL_HOST = email_host
                define_mail.settings.EMAIL_HOST_USER = from_mail
                define_mail.settings.EMAIL_BACKEND = email_backend
                define_mail.settings.EMAIL_USE_TLS = email_use_tls
                define_mail.settings.EMAIL_PORT = int(email_port)
                define_mail.settings.EMAIL_HOST_PASSWORD = email_host_password
                email_msg = define_mail.message.EmailMessage(
                    'Register Success', content, from_mail, [email])
                email_msg.content_subtype = "html"
                email_msg.send()
            except Exception:
                ks.users.delete(new_user.id)
                raise ValidationError(_('Email system error.'))
            return True
        except ValidationError as e:
            self.api_error(e.messages[0])
            return False
        except Exception:
            exceptions.handle(request, _('Unable to create new user.'))
            return False


class RegisterView(forms.ModalFormView):
    form_class = RegisterForm
    template_name = 'auth/register.html'
    success_url = 'horizon:register_success'

    def get_success_url(self):
        username = self.request.POST['email']
        user64 = base64.encodestring(username)
        return reverse(self.success_url,
                       kwargs={"username": user64})


class RegisterSuccessView(TemplateView):
    def get_context_data(self, username=None):
        return {'username': base64.decodestring(username)}
    template_name = 'auth/register_success.html'


class EnableView(View):
    def get(self, request):
        try:
            user64 = self.request.GET.get("p")
            user_id = base64.decodestring(user64)
            ks = animbus_backend.authenticate()
            user = ks.users.get(user_id)
            if user.enabled:
                enabled = True
            else:
                enabled = False
                ks.users.update_enabled(user_id, True)
            response = render_to_response('auth/enable_success.html',
                                          {'username': user.username,
                                           'enabled': enabled},
                                          dj_template.RequestContext(request))
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to activate account.'),)
            response = render_to_response('auth/enable_success.html',
                                          {"error": True},
                                          dj_template.RequestContext(request))
        return response


class ForgetpwdForm(forms.SelfHandlingForm):
    email = forms.EmailField(label=_("Please input your eamil"),
                             required=True)

    def handle(self, request, data):
        email = data['email']
        try:
            try:
                ks = animbus_backend.authenticate()
            except Exception:
                raise ValidationError(_('Something wrong with authenticate'))

            user_list = ks.users.list()
            flag = False
            for user in user_list:
                if user.username == email:
                    flag = True
                    user64 = base64.encodestring(user.id)
            if flag:
                template = loader.get_template(
                    os.path.join(email_dir, "forgot_pwd.html"))
                if domain_name:
                    domain = domain_name
                else:
                    domain = request.get_host()
                forgot_pwd_url = "http://%s%s" % (
                    domain,
                    reverse("horizon:reset_forgot_pwd",
                            kwargs={"user_id": user64}))
                context = dj_template.Context(
                    {'email': email,
                     'forgot_pwd_url': forgot_pwd_url})
                content = template.render(context)
                try:
                    email_setting = db_api.email_settings_get_all(self.request)
                    from_mail = email_setting[0].email_host_user
                    email_host = email_setting[0].email_host
                    email_port = email_setting[0].email_port
                    email_password = email_setting[0].email_host_password
                    define_mail.settings.EMAIL_HOST = email_host
                    define_mail.settings.EMAIL_HOST_USER = from_mail
                    define_mail.settings.EMAIL_BACKEND = email_backend
                    define_mail.settings.EMAIL_USE_TLS = email_use_tls
                    define_mail.settings.EMAIL_PORT = int(email_port)
                    define_mail.settings.EMAIL_HOST_PASSWORD = email_password
                    email_msg = define_mail.message.EmailMessage(
                        'Reset Password',
                        content, from_mail, [email])
                    email_msg.content_subtype = "html"
                    email_msg.send()
                except Exception:
                    raise ValidationError(_('Email system error.'))
                return True
            else:
                raise ValidationError(_('The user not exist.'))
        except ValidationError as e:
            self.api_error(e.messages[0])
            return False
        except Exception:
            exceptions.handle(request, _('Unable to find password.'))
            return False


class ForgetpwdView(forms.ModalFormView):
    form_class = ForgetpwdForm
    template_name = 'auth/forgot_pwd.html'
    success_url = 'horizon:forgotpwd_email'

    def get_success_url(self):
        username = self.request.POST['email']
        user64 = base64.encodestring(username)
        return reverse(self.success_url,
                       kwargs={"username": user64})


class ForgetpwdEmailView(TemplateView):
    def get_context_data(self, username=None):
        return {'username': base64.decodestring(username)}
    template_name = 'auth/forgotpwd_email.html'


class ResetpwdForm(forms.SelfHandlingForm):
    password = forms.RegexField(
        label=_("Please input new password"),
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})
    confirm_password = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(render_value=False))
    user_id = forms.CharField(label=_("User ID"),
                              required=True,
                              widget=forms.HiddenInput())

    def clean(self):
        '''Check to make sure password fields match.'''
        data = super(forms.Form, self).clean()
        if 'password' in data:
            if data['password'] != data.get('confirm_password', None):
                raise ValidationError(_('Passwords do not match.'))
        return data

    def handle(self, request, data):
        try:
            try:
                ks = animbus_backend.authenticate()
            except Exception:
                raise ValidationError(_('Something wrong with authenticate'))
            user_id = data["user_id"]
            new_password = data['password']
            ks.users.update_password(user_id, new_password)
            return True
        except ValidationError as e:
            self.api_error(e.messages[0])
            return False
        except Exception:
            exceptions.handle(request, _('Unable to reset password.'))
            return False


class ResetpwdView(forms.ModalFormView):
    form_class = ResetpwdForm
    template_name = 'auth/reset_pwd.html'
    success_url = 'horizon:reset_pwd_success'

    def get_context_data(self, **kwargs):
        context = super(ResetpwdView, self).get_context_data(**kwargs)
        context["user_id"] = self.kwargs['user_id']
        return context

    def get_initial(self):
        user64_id = self.kwargs['user_id']
        user_id = base64.decodestring(user64_id)
        return {'user_id': user_id}

    def get_success_url(self):
        user_id = self.request.POST['user_id']
        ks = animbus_backend.authenticate()
        user = ks.users.get(user_id)
        user64 = base64.encodestring(user.username)
        return reverse(self.success_url,
                       kwargs={"username": user64})


class ResetSuccessView(TemplateView):
    def get_context_data(self, username=None):
        return {'username': base64.decodestring(username)}
    template_name = 'auth/reset_success.html'
