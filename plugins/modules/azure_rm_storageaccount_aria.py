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
            approve_private_endpoint_connections=dict(type='bool', default=False),
            enable_monitoring=dict(type='int')
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
        self.enable_monitoring = None

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

        if self.enable_monitoring is not None:
            self.enable_monitoring_function()

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

    def enable_monitoring_function(self):
        account_keys = self.storage_client.storage_accounts.list_keys(self.resource_group, self.name)

        blob_client = self.get_blob_client(self.resource_group, self.name)
        table_client = TableService(self.name, account_keys.keys[0].value, sas_token=None)
        files_client = FileService(self.name, account_keys.keys[0].value, sas_token=None)
        queue_client = QueueService(self.name, account_keys.keys[0].value, sas_token=None)

        blob_properties = blob_client.get_blob_service_properties()
        table_properties = table_client.get_table_service_properties()
        file_properties = files_client.get_file_service_properties()
        queue_properties = queue_client.get_queue_service_properties()


        self.account_dict['monitoring'] = dict(blob=dict(enabled=blob_properties.logging.retention_policy.enabled, days=blob_properties.logging.retention_policy.days),
                                               queue=dict(enabled=queue_properties.logging.retention_policy.enabled, days=queue_properties.logging.retention_policy.days),
                                               file=dict(enabled=file_properties.hour_metrics.retention_policy.enabled, days=file_properties.hour_metrics.retention_policy.days),
                                               table=dict(enabled=table_properties.logging.retention_policy.enabled, days=table_properties.logging.retention_policy.days))

        enabled = False if self.enable_monitoring == 0 else True
        log = Logging(read=enabled, write=enabled, delete=enabled, retention_policy=RetentionPolicy(days=self.enable_monitoring, enabled=enabled))
        hour = Metrics(enabled=enabled, include_apis=enabled, retention_policy=RetentionPolicy(days=self.enable_monitoring, enabled=enabled))
        minutes = Metrics(enabled=enabled, include_apis=enabled, retention_policy=RetentionPolicy(days=self.enable_monitoring, enabled=enabled))

        if (not self.compare_logging(blob_properties.logging, log) and 
            not self.compare_hour_metrics(blob_properties.hour_metrics, hour) and 
            not self.compare_minute_metrics(blob_properties.minute_metrics, minutes)):
            self.results['changed'] = True
            blob_client.set_blob_service_properties(logging=log, hour_metrics=hour, minute_metrics=minutes)
            self.account_dict['monitoring']['blob']['enabled'] = enabled
            self.account_dict['monitoring']['blob']['days'] = self.enable_monitoring if self.enable_monitoring != 0 else None

        if (not self.compare_logging(table_properties.logging, log) and 
            not self.compare_hour_metrics(table_properties.hour_metrics, hour) and 
            not self.compare_minute_metrics(table_properties.minute_metrics, minutes)):
            self.results['changed'] = True
            table_client.set_table_service_properties(logging=log, hour_metrics=hour, minute_metrics=minutes)
            self.account_dict['monitoring']['table']['enabled'] = enabled
            self.account_dict['monitoring']['table']['days'] = self.enable_monitoring if self.enable_monitoring != 0 else None

        if (not self.compare_hour_metrics(file_properties.hour_metrics, hour) and 
            not self.compare_minute_metrics(file_properties.minute_metrics, minutes)):
            self.results['changed'] = True
            files_client.set_file_service_properties(hour_metrics=hour, minute_metrics=minutes)
            self.account_dict['monitoring']['file']['enabled'] = enabled
            self.account_dict['monitoring']['file']['days'] = self.enable_monitoring if self.enable_monitoring != 0 else None

        if (not self.compare_logging(queue_properties.logging, log) and 
            not self.compare_hour_metrics(queue_properties.hour_metrics, hour) and 
            not self.compare_minute_metrics(queue_properties.minute_metrics, minutes)):
            self.results['changed'] = True
            queue_client.set_queue_service_properties(logging=log, hour_metrics=hour, minute_metrics=minutes)
            self.account_dict['monitoring']['queue']['enabled'] = enabled
            self.account_dict['monitoring']['queue']['days'] = self.enable_monitoring if self.enable_monitoring != 0 else None

    def compare_logging(self, log1 ,log2):
        if (log1.delete == log2.delete and 
            log1.read == log2.read and 
            log1.write == log2.write and 
            log1.retention_policy.enabled == log2.retention_policy.enabled and
            log1.retention_policy.days in [log2.retention_policy.days, None]):
            return True
        return False

    def compare_hour_metrics(self, hour1 ,hour2):
        if (hour1.enabled == hour2.enabled and 
            hour1.include_apis in [hour2.include_apis, None] and
            hour1.retention_policy.enabled == hour2.retention_policy.enabled and
            hour1.retention_policy.days in [hour2.retention_policy.days, None]):
            return True
        return False

    def compare_minute_metrics(self, minute1 ,minute2):
        if (minute1.enabled == minute2.enabled and 
            minute1.include_apis in [minute2.include_apis, None] and
            minute1.retention_policy.enabled == minute2.retention_policy.enabled and
            minute1.retention_policy.days in [minute2.retention_policy.days, None]):
            return True
        return False

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
        account_dict['monitoring'] = dict(blob=dict(enabled=None, days=None),
                                          queue=dict(enabled=None, days=None),
                                          file=dict(enabled=None, days=None),
                                          table=dict(enabled=None, days=None))

        return account_dict
        
def main():
    AzureRMStorageAccount()


if __name__ == '__main__':
    main()
