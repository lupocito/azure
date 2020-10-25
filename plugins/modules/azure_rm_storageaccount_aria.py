#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


try:
    from azure.storage.models import Logging, Metrics, RetentionPolicy
    from azure.storage.table import TableService
    from azure.storage.file import FileService
    from azure.storage.queue import QueueService
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible_collections.azure.azcollection.plugins.module_utils.azure_rm_common import AZURE_SUCCESS_STATE, AzureRMModuleBase
from ansible.module_utils._text import to_native

class AzureRMStorageAccount(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            location=dict(type='str'),
            name=dict(type='str', required=True),
            resource_group=dict(required=True, type='str', aliases=['resource_group_name']),
            approve_private_endpoint_connections=dict(type='bool', default=False)
        )

        self.results = dict(
            changed=False,
            state=dict()
        )

        self.account_dict = None
        self.resource_group = None
        self.name = None
        self.location = None
        self.approve_private_endpoint_connections = None
        self.private_endpoint_connection = list()

        super(AzureRMStorageAccount, self).__init__(self.module_arg_spec,
                                                    supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        resource_group = self.get_resource_group(self.resource_group)

        if not self.location:
            # Set default location
            self.location = resource_group.location

        self.account_dict = self.get_account()

        if self.account_dict is not None:
            self.results['state'] = self.account_dict
        else:
            self.results['state'] = dict()

        account_keys = self.storage_client.storage_accounts.list_keys(self.resource_group, self.name)
        blob_client = self.get_blob_client(self.resource_group, self.name, 'block')
        table_client = TableService(self.name, account_keys.keys[0].value, sas_token=None)
        files_client = FileService(self.name, account_keys.keys[0].value, sas_token=None)
        queue_client = QueueService(self.name, account_keys.keys[0].value, sas_token=None)

        # properties = files_client.get_file_service_properties()
        # properties = queue_client.get_queue_service_properties()
        log = Logging(read=True, write=True, delete=True, retention_policy=RetentionPolicy(days=15, enabled=True))
        hour = Metrics(enabled=True, include_apis=True, retention_policy=RetentionPolicy(days=15, enabled=True))
        minutes = Metrics(enabled=True, include_apis=True, retention_policy=RetentionPolicy(days=15, enabled=True))

        blob_client.set_blob_service_properties(logging=log, hour_metrics=hour, minute_metrics=minutes)
        table_client.set_table_service_properties(logging=log, hour_metrics=hour, minute_metrics=minutes)
        files_client.set_file_service_properties(hour_metrics=hour, minute_metrics=minutes)
        queue_client.set_queue_service_properties(logging=log, hour_metrics=hour, minute_metrics=minutes)

        if self.approve_private_endpoint_connections:
            self.private_endpoint_connections()

        return self.results

    def private_endpoint_connections(self):
        list_pec = self.storage_client.private_endpoint_connections.list(self.resource_group, self.name)

        for pec in list_pec:
            if pec.private_link_service_connection_state.status == 'Pending':
                self.results['changed'] = True
                self.account_dict['private_endpoint_connection'] += [pec.name]
                pec.private_link_service_connection_state.status = 'Approved'
                self.storage_client.private_endpoint_connections.put(self.resource_group, self.name, pec.name, pec)

    def get_account(self):
        self.log('Get properties for account {0}'.format(self.name))
        account_obj = None
        account_dict = None

        try:
            account_obj = self.storage_client.storage_accounts.get_properties(self.resource_group, self.name)
        except CloudError:
            pass

        if account_obj:
            account_dict = self.account_obj_to_dict(account_obj)

        return account_dict

    def account_obj_to_dict(self, account_obj):
        account_dict = dict(
            id=account_obj.id,
            name=account_obj.name,
            location=account_obj.location,
            resource_group=self.resource_group
        )
        account_dict['private_endpoint_connection'] = list()

        return account_dict
        
def main():
    AzureRMStorageAccount()


if __name__ == '__main__':
    main()
