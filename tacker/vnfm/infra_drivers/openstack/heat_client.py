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

import sys

from heatclient import exc as heatException
from oslo_log import log as logging

from tacker.common import clients
from tacker.extensions import vnfm

LOG = logging.getLogger(__name__)


class HeatClient(object):
    def __init__(self, auth_attr, region_name=None):
        # context, password are unused
        self.heat = clients.OpenstackClients(auth_attr, region_name).heat
        self.stacks = self.heat.stacks
        self.resource_types = self.heat.resource_types
        self.resources = self.heat.resources

    def create(self, fields):
        fields = fields.copy()
        fields.update({
            'timeout_mins': 10,
            'disable_rollback': True})
        if 'password' in fields.get('template', {}):
            fields['password'] = fields['template']['password']

        try:
            return self.stacks.create(**fields)
        except heatException.HTTPException:
            type_, value, tb = sys.exc_info()
            raise vnfm.HeatClientException(msg=value)

    def delete(self, stack_id):
        try:
            self.stacks.delete(stack_id)
        except heatException.HTTPNotFound:
            LOG.warning(_("Stack %(stack)s created by service chain driver is "
                          "not found at cleanup"), {'stack': stack_id})

    def get(self, stack_id):
        return self.stacks.get(stack_id)

    def resource_attr_support(self, resource_name, property_name):
        resource = self.resource_types.get(resource_name)
        return property_name in resource['attributes']

    def resource_get_list(self, stack_id, nested_depth=0):
        return self.heat.resources.list(stack_id,
                                        nested_depth=nested_depth)

    def resource_signal(self, stack_id, rsc_name):
        return self.heat.resources.signal(stack_id, rsc_name)

    def resource_get(self, stack_id, rsc_name):
        return self.heat.resources.get(stack_id, rsc_name)

    def resource_event_list(self, stack_id, rsc_name, **kwargs):
        return self.heat.events.list(stack_id, rsc_name, **kwargs)

    def resource_metadata(self, stack_id, rsc_name):
        return self.heat.resources.metadata(stack_id, rsc_name)
