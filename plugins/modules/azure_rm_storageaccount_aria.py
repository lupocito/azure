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


DOCUMENTATION = '''
---
module: azure_rm_storageaccount_aria
version_added: "0.1.0"
short_description: Manage Azure storage accounts
description:
    - Create, update or delete a storage account.
options:
    resource_group:
        description:
            - Name of the resource group to use.
        required: true
        aliases:
            - resource_group_name
    name:
        description:
            - Name of the storage account to update or create.
    state:
        description:
            - State of the storage account. Use C(present) to create or update a storage account and use C(absent) to delete an account.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Valid Azure location. Defaults to location of the resource group.
    account_type:
        description:
            - Type of storage account. Required when creating a storage account.
            - C(Standard_ZRS) and C(Premium_LRS) accounts cannot be changed to other account types.
            - Other account types cannot be changed to C(Standard_ZRS) or C(Premium_LRS).
        choices:
            - Premium_LRS
            - Standard_GRS
            - Standard_LRS
            - Standard_RAGRS
            - Standard_ZRS
            - Premium_ZRS
        aliases:
            - type
    custom_domain:
        description:
            - User domain assigned to the storage account.
            - Must be a dictionary with I(name) and I(use_sub_domain) keys where I(name) is the CNAME source.
            - Only one custom domain is supported per storage account at this time.
            - To clear the existing custom domain, use an empty string for the custom domain name property.
            - Can be added to an existing storage account. Will be ignored during storage account creation.
        aliases:
            - custom_dns_domain_suffix
    kind:
        description:
            - The kind of storage.
            - The C(FileStorage) and (BlockBlobStorage) only used when I(account_type=Premium_LRS).
        default: 'Storage'
        choices:
            - Storage
            - StorageV2
            - BlobStorage
            - BlockBlobStorage
            - FileStorage
    access_tier:
        description:
            - The access tier for this storage account. Required when I(kind=BlobStorage).
        choices:
            - Hot
            - Cool
    force_delete_nonempty:
        description:
            - Attempt deletion if resource already exists and cannot be updated.
        type: bool
        aliases:
            - force
    https_only:
        description:
            - Allows https traffic only to storage service when set to C(true).
            - Allows update storage account property when set to C(False).
            - Default value is C(False).
        type: bool
    minimum_tls_version:
        description:
            - The minimum required version of Transport Layer Security (TLS) for requests to a storage account.
            - Default value is C(TLS1_0).
        choices:
            - TLS1_0
            - TLS1_1
            - TLS1_2
        version_added: "1.0.0"
    allow_blob_public_access:
        description:
            - Allows blob containers in account to be set for anonymous public access.
            - If set to false, no containers in this account will be able to allow anonymous public access.
            - Default value is C(True).
        type: bool
        version_added: "1.1.0"
    network_acls:
        description:
            - Manages the Firewall and virtual networks settings of the storage account.
        type: dict
        suboptions:
            default_action:
                description:
                    - Default firewall traffic rule.
                    - If I(default_action=Allow) no other settings have effect.
                choices:
                    - Allow
                    - Deny
                default: Allow
            bypass:
                description:
                    - When I(default_action=Deny) this controls which Azure components can still reach the Storage Account.
                    - The list is comma separated.
                    - It can be any combination of the example C(AzureServices), C(Logging), C(Metrics).
                    - If no Azure components are allowed, explicitly set I(bypass="").
                default: AzureServices
                suboptions:
                    virtual_network_rules:
                        description:
                            - A list of subnets and their actions.
                        suboptions:
                            id:
                                description:
                                    - The complete path to the subnet.
                            action:
                                description:
                                    - The only logical I(action=Allow) because this setting is only accessible when I(default_action=Deny).
                                default: 'Allow'
                    ip_rules:
                        description:
                            - A list of IP addresses or ranges in CIDR format.
                        suboptions:
                            value:
                                description:
                                    - The IP address or range.
                            action:
                                description:
                                    - The only logical I(action=Allow) because this setting is only accessible when I(default_action=Deny).
                                default: 'Allow'
    blob_cors:
        description:
            - Specifies CORS rules for the Blob service.
            - You can include up to five CorsRule elements in the request.
            - If no blob_cors elements are included in the argument list, nothing about CORS will be changed.
            - If you want to delete all CORS rules and disable CORS for the Blob service, explicitly set I(blob_cors=[]).
        type: list
        suboptions:
            allowed_origins:
                description:
                    - A list of origin domains that will be allowed via CORS, or "*" to allow all domains.
                type: list
                required: true
            allowed_methods:
                description:
                    - A list of HTTP methods that are allowed to be executed by the origin.
                type: list
                required: true
            max_age_in_seconds:
                description:
                    - The number of seconds that the client/browser should cache a preflight response.
                type: int
                required: true
            exposed_headers:
                description:
                    - A list of response headers to expose to CORS clients.
                type: list
                required: true
            allowed_headers:
                description:
                    - A list of headers allowed to be part of the cross-origin request.
                type: list
                required: true
    blob_retention_policy:
        description:
            - Indicates whether a retention policy is enabled for the storage service.
            - The minimum value you can specify is 1, the largest value is 365 (one year).
            - Set 0 days to disable retention policy.
        type: int
    blob_versioning:
        description:
            - Enables/disables versioning on blob storages.
            - Only allowed when I(kind=StorageV2), I(kind=BlobStorage) or I(kind=BlockBlobStorage) is selected.
            - Default value is C(False).
        type: bool

extends_documentation_fragment:
    - azure.azcollection.azure
    - azure.azcollection.azure_tags

author:
    - Chris Houseknecht (@chouseknecht)
    - Matt Davis (@nitzmahone)
'''

EXAMPLES = '''
    - name: remove account, if it exists
      azure_rm_storageaccount:
        resource_group: myResourceGroup
        name: clh0002
        state: absent

    - name: create an account
      azure_rm_storageaccount:
        resource_group: myResourceGroup
        name: clh0002
        type: Standard_RAGRS
        tags:
          testing: testing
          delete: on-exit

    - name: Create an account with kind of FileStorage
      azure_rm_storageaccount:
        resource_group: myResourceGroup
        name: c1h0002
        type: Premium_LRS
        kind: FileStorage
        tags:
          testing: testing

    - name: configure firewall and virtual networks
      azure_rm_storageaccount:
        resource_group: myResourceGroup
        name: clh0002
        type: Standard_RAGRS
        network_acls:
          bypass: AzureServices,Metrics
          default_action: Deny
          virtual_network_rules:
            - id: /subscriptions/mySubscriptionId/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/myVnet/subnets/mySubnet
              action: Allow
          ip_rules:
            - value: 1.2.3.4
              action: Allow
            - value: 123.234.123.0/24
              action: Allow

    - name: create an account with blob CORS
      azure_rm_storageaccount:
        resource_group: myResourceGroup
        name: clh002
        type: Standard_RAGRS
        blob_cors:
            - allowed_origins:
                - http://www.example.com/
              allowed_methods:
                - GET
                - POST
              allowed_headers:
                - x-ms-meta-data*
                - x-ms-meta-target*
                - x-ms-meta-abc
              exposed_headers:
                - x-ms-meta-*
              max_age_in_seconds: 200
'''


RETURN = '''
state:
    description:
        - Current state of the storage account.
    returned: always
    type: complex
    contains:
        account_type:
            description:
                - Type of storage account.
            returned: always
            type: str
            sample: Standard_RAGRS
        custom_domain:
            description:
                - User domain assigned to the storage account.
            returned: always
            type: complex
            contains:
                name:
                    description:
                        - CNAME source.
                    returned: always
                    type: str
                    sample: testaccount
                use_sub_domain:
                    description:
                        - Whether to use sub domain.
                    returned: always
                    type: bool
                    sample: true
        delete_retention_policy:
            description:
                - Indicates whether a retention policy is enabled for the storage service.
            returned: always
            type: dict
            sample: {
                    "enabled": true,
                    "days": 15
                    }
        id:
            description:
                - Resource ID.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/clh0003"
        location:
            description:
                - Valid Azure location. Defaults to location of the resource group.
            returned: always
            type: str
            sample: eastus2
        name:
            description:
                - Name of the storage account to update or create.
            returned: always
            type: str
            sample: clh0003
        network_acls:
            description:
                - A set of firewall and virtual network rules
            returned: always
            type: dict
            sample: {
                    "bypass": "AzureServices",
                    "default_action": "Deny",
                    "virtual_network_rules": [
                        {
                            "action": "Allow",
                            "id": "/subscriptions/mySubscriptionId/resourceGroups/myResourceGroup/ \
                                   providers/Microsoft.Network/virtualNetworks/myVnet/subnets/mySubnet"
                            }
                        ],
                    "ip_rules": [
                        {
                            "action": "Allow",
                            "value": "1.2.3.4"
                        },
                        {
                            "action": "Allow",
                            "value": "123.234.123.0/24"
                        }
                    ]
                    }
        primary_endpoints:
            description:
                - The URLs to retrieve the public I(blob), I(queue), or I(table) object from the primary location.
            returned: always
            type: dict
            sample: {
                    "blob": "https://clh0003.blob.core.windows.net/",
                    "queue": "https://clh0003.queue.core.windows.net/",
                    "table": "https://clh0003.table.core.windows.net/"
                    }
        primary_location:
            description:
                - The location of the primary data center for the storage account.
            returned: always
            type: str
            sample: eastus2
        provisioning_state:
            description:
                - The status of the storage account.
                - Possible values include C(Creating), C(ResolvingDNS), C(Succeeded).
            returned: always
            type: str
            sample: Succeeded
        resource_group:
            description:
                - The resource group's name.
            returned: always
            type: str
            sample: Testing
        secondary_endpoints:
            description:
                - The URLs to retrieve the public I(blob), I(queue), or I(table) object from the secondary location.
            returned: always
            type: dict
            sample: {
                    "blob": "https://clh0003-secondary.blob.core.windows.net/",
                    "queue": "https://clh0003-secondary.queue.core.windows.net/",
                    "table": "https://clh0003-secondary.table.core.windows.net/"
                    }
        secondary_location:
            description:
                - The location of the geo-replicated secondary for the storage account.
            returned: always
            type: str
            sample: centralus
        status_of_primary:
            description:
                - The status of the primary location of the storage account; either C(available) or C(unavailable).
            returned: always
            type: str
            sample: available
        status_of_secondary:
            description:
                - The status of the secondary location of the storage account; either C(available) or C(unavailable).
            returned: always
            type: str
            sample: available
        tags:
            description:
                - Resource tags.
            returned: always
            type: dict
            sample: { 'tags1': 'value1' }
        type:
            description:
                - The storage account type.
            returned: always
            type: str
            sample: "Microsoft.Storage/storageAccounts"
        versioning:
            description:
                - State of versioning on blob storages.
            returned: always
            type: bool
            sample: true
'''

try:
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
