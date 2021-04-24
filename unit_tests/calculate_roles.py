
# Unit tests for the deleted nodes calculation algorithm
# Run the tests using `python calculate_roles.py` from this directory
# or if you prefer tox by executing 'tox' after installing tox

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'playbooks/filter_plugins'))
from calculate_roles import OpenStackParams, ContrailCluster, OpenstackCluster
import unittest
import mock
import json


class MyTests(unittest.TestCase):

    def setUp(self):
        self.instances_dict_test_add = {
            'srvr1': {
                'ip': '10.84.22.71',
                'roles': {
                    'openstack': None,
                    'analytics': None,
                    'analytics_database': None,
                    'config': None,
                    'config_database': None,
                    'control': None,
                    'webui': None
                }
            },
            'srvr2': {
                'ip': '10.84.22.72',
                'roles': {
                    'openstack_compute': None,
                    'vrouter': None
                }
            },
            'srvr3': {
                'ip': '10.84.22.73',
                'roles': {
                    'openstack_compute': None,
                    'vrouter': None
                }
            }
        }
        self.instances_dict_test_delete = {
            'srvr1': {
                'ip': '10.84.22.71',
                'roles': {
                    'openstack': None,
                    'analytics': None,
                    'analytics_database': None,
                    'config': None,
                    'config_database': None,
                    'control': None,
                    'webui': None
                }
            },
            'srvr2': {
                'ip': '10.84.22.72',
                'roles': {
                    'openstack_compute': None,
                    'vrouter': None
                }
            },
            'srvr3': {
                'ip': '10.84.22.73',
                'roles': {
                }
            }
        }
        self.global_configuration = {'ENABLE_DESTROY': True}
        self.contrail_configuration = {
            'CONFIG_NODES': '10.84.22.71',
            'CLOUD_ORCHESTRATOR': 'openstack',
            'KEYSTONE_AUTH_HOST': '10.84.22.71'}
        self.hv = {
            '10.84.22.71': {'ansible_all_ipv4_addresses': ['10.84.22.71']},
            '10.84.22.72': {'ansible_all_ipv4_addresses': ['10.84.22.72']},
            '10.84.22.73': {'ansible_all_ipv4_addresses': ['10.84.22.73']}
        }

    def my_token(self, cc):
        # print("Got TOKEN")
        return

    def my_os_hypervisors_add(self):
        from requests.models import Response
        os_hypervisors_test_add = {
            'hypervisors': [{
                'status': 'enabled',
                'service': {
                    'host': 'b2s43-vm2', 'disabled_reason': None, 'id': 8
                },
                'vcpus_used': 0, 'hypervisor_type': 'QEMU', 'id': 1,
                'local_gb_used': 0, 'state': 'up',
                'hypervisor_hostname': 'b2s43-vm2.englab.juniper.net',
                'host_ip': '10.84.22.72'
            }]
        }
        the_response = Response()
        the_response.status_code = 200
        the_response._content = json.dumps(os_hypervisors_test_add).encode()
        return the_response

    def my_os_hypervisors_del(self):
        from requests.models import Response
        os_hypervisors_test_delete = {
            'hypervisors': [{
                'status': 'enabled',
                'service': {
                    'host': 'b2s43-vm2', 'disabled_reason': None, 'id': 8
                },
                'vcpus_used': 0, 'hypervisor_type': 'QEMU', 'id': 1,
                'local_gb_used': 0, 'state': 'up',
                'hypervisor_hostname': 'b2s43-vm2.englab.juniper.net',
                'host_ip': '10.84.22.72'
            }, {
                'status': 'enabled',
                'service': {
                    'host': 'b2s43-vm3', 'disabled_reason': None, 'id': 9
                },
                'vcpus_used': 0, 'hypervisor_type': 'QEMU', 'id': 2,
                'local_gb_used': 0, 'state': 'up',
                'hypervisor_hostname': 'b2s43-vm3.englab.juniper.net',
                'host_ip': '10.84.22.73'
            }]
        }
        the_response = Response()
        the_response.status_code = 200
        the_response._content = json.dumps(os_hypervisors_test_delete).encode()
        return the_response

    @mock.patch.object(OpenStackParams, 'get_ks_auth_token', my_token)
    def test_contrail_params(self):
        cc = ContrailCluster(
            self.instances_dict_test_delete,
            self.contrail_configuration, {})
        self.assertEqual("http", cc.proto)
        self.contrail_configuration.update({'SSL_ENABLE': True})
        cc2 = ContrailCluster(
            self.instances_dict_test_delete,
            self.contrail_configuration, {})
        self.assertEqual("https", cc2.proto)

    @mock.patch.object(OpenStackParams, 'get_ks_auth_token', my_token)
    def test_os_params(self):
        os_par = OpenStackParams(self.contrail_configuration, None)
        self.assertEqual("http", os_par.ks_auth_proto)
        kc = {'kolla_globals': {'kolla_enable_tls_external': True}}
        os_par_new = OpenStackParams(self.contrail_configuration, kc)
        self.assertEqual("https", os_par_new.ks_auth_proto)

    @mock.patch.object(OpenStackParams, 'get_ks_auth_token', my_token)
    @mock.patch.object(OpenStackParams, 'get_os_hypervisors', my_os_hypervisors_del)
    def test_calculate_deleted_os_nodes_dict(self):
        os_cluster = OpenstackCluster(
            self.instances_dict_test_delete,
            self.contrail_configuration, {})
        inst_nodes, del_nodes = os_cluster.discover_openstack_roles(self.hv)
        self.assertIn('srvr3', del_nodes)
        self.assertEqual(inst_nodes['srvr3']['deleted_roles'], ['openstack_compute'])
        self.assertEqual(inst_nodes['srvr3']['existing_roles'], ['openstack_compute'])
        self.assertFalse(inst_nodes['srvr3']['instance_roles'])

    @mock.patch.object(OpenStackParams, 'get_ks_auth_token', my_token)
    @mock.patch.object(OpenStackParams, 'get_os_hypervisors', my_os_hypervisors_add)
    def test_calculate_added_os_nodes_dict(self):
        os_cluster = OpenstackCluster(
            self.instances_dict_test_add,
            self.contrail_configuration, {})
        inst_nodes, del_nodes = os_cluster.discover_openstack_roles(self.hv)
        self.assertFalse(del_nodes)
        self.assertFalse(inst_nodes['srvr3']['deleted_roles'])
        self.assertEqual(inst_nodes['srvr3']['new_roles'], ['openstack_compute'])


if __name__ == '__main__':
    unittest.main()
