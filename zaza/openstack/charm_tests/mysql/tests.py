# Copyright 2019 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Keystone SAML Mellon Testing."""

import logging
import time

import zaza.charm_lifecycle.utils as lifecycle_utils
import zaza.model
import zaza.openstack.charm_tests.test_utils as test_utils
import zaza.openstack.utilities.juju as juju_utils
import zaza.openstack.utilities.openstack as openstack_utils


class MySQLTest(test_utils.OpenStackBaseTest):
    """Base for mysql or percona-cluster charm tests."""

    @classmethod
    def setUpClass(cls):
        """Run class setup for running mysql tests."""
        super(MySQLTest, cls).setUpClass()
        cls.application = "mysql"


class PerconaClusterTest(test_utils.OpenStackBaseTest):
    """Base for mysql or percona-cluster charm tests."""

    @classmethod
    def setUpClass(cls):
        """Run class setup for running mysql tests."""
        super(PerconaClusterTest, cls).setUpClass()
        cls.application = "percona-cluster"

    #TODO Feature parity tests for percona amulet tests


class PerconaClusterColdStartTest(PerconaClusterTest):
    @classmethod
    def setUpClass(cls):
        """Run class setup for running mysql Cold Start tests."""
        super(PerconaClusterColdStartTest, cls).setUpClass()
        cls.overcloud_keystone_session = openstack_utils.get_undercloud_keystone_session()
        cls.nova_client = openstack_utils.get_nova_session_client(
            cls.overcloud_keystone_session)
        cls.machines = juju_utils.get_machine_uuids_for_application(cls.application)

    def test_100_cold_stop(self):
        self.machines.sort()
        # Avoid hitting an update-status hook
        logging.debug("Wait till model is idle ...")
        zaza.model.block_until_all_units_idle()
        logging.info("Stopping instances: {}".format(self.machines))
        for uuid in self.machines:
            self.nova_client.servers.stop(uuid)
        # Unfortunately, juju reports units in workload status "active"
        # when they are in fact down. So we have to rely on a simple wait 
        # and idle check.
        logging.debug("Sleep ...")
        time.sleep(30)
        logging.debug("Wait till model is idle ...")
        zaza.model.block_until_all_units_idle()

    def test_101_cold_start(self):
        self.machines.sort(reverse=True)
        logging.info("Starting instances: {}".format(self.machines))
        for uuid in self.machines:
            self.nova_client.servers.start(uuid)
        test_config = lifecycle_utils.get_charm_config()
        logging.debug("Sleep ...")
        time.sleep(60)
        logging.debug("Wait till model is idle ...")
        zaza.model.block_until_all_units_idle()
        logging.debug("Wait for application states ...")
        zaza.model.wait_for_application_states(
            states=test_config.get('target_deploy_status', {}))
