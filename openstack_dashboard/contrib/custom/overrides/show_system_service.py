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

from openstack_dashboard.contrib.custom.content.identity.projects.views \
    import IndexView as ProContribIndexView
from openstack_dashboard.contrib.custom.content.identity.projects.workflows \
    import UpdateProjectMembersAction
from openstack_dashboard.contrib.custom.content.identity.users \
    import forms as contrib_user_forms
from openstack_dashboard.contrib.custom.content.identity.users.views \
    import IndexView as UserContribIndexView

from openstack_dashboard.dashboards.identity.projects import views as pro_views
from openstack_dashboard.dashboards.identity.projects \
    import workflows
from openstack_dashboard.dashboards.identity.users import views as user_views


user_views.IndexView = UserContribIndexView
user_views.CreateView.form_class = contrib_user_forms.CreateUserForm
user_views.UpdateView.form_class = contrib_user_forms.UpdateUserForm
pro_views.IndexView = ProContribIndexView
workflows.UpdateProjectMembers.action_class = UpdateProjectMembersAction
