#!/usr/bin/python

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import time
import logging
from blockadeUtils.blockade import Blockade
from clusterUtils.cluster_utils import ClusterUtils


logger = logging.getLogger(__name__)
parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
FILE = os.path.join(parent_dir, "compose", "ozoneblockade",
                    "docker-compose.yaml")
SCALE = 3
CONTAINER_LIST = []
OM = []
SCM = []
DATANODES = []


def setup():
    global CONTAINER_LIST, OM, SCM, DATANODES
    Blockade.blockade_destroy()
    CONTAINER_LIST = ClusterUtils.cluster_setup(FILE, SCALE)
    exit_code, output = Blockade.blockade_status()
    assert exit_code == 0, "blockade status command failed with output=[%s]" % \
                           output
    OM = filter(lambda x: 'ozoneManager' in x, CONTAINER_LIST)
    SCM = filter(lambda x: 'scm' in x, CONTAINER_LIST)
    DATANODES = sorted(list(filter(lambda x: 'datanode' in x, CONTAINER_LIST)))

    exit_code, output = \
        ClusterUtils.run_freon(FILE, 1, 1, 1, 10240, "RATIS", "THREE")
    assert exit_code == 0, "freon run failed with output=[%s]" % output


def teardown():
    logger.info("Inside teardown")
    Blockade.blockade_destroy()


def teardown_module():
    ClusterUtils.cluster_destroy(FILE)


def test_three_dns_isolate_onescmfailure():
    """
    In this test, all datanodes are isolated from each other.
    One of the datanodes (third datanode) cannot communicate with SCM.
    Expectation :
    The container replica state in first datanode should be closed.
    The container replica state in second datanode should be closed.
    The container replica state in third datanode should be open.
    """
    first_set = [OM[0], SCM[0], DATANODES[0]]
    second_set = [OM[0], SCM[0], DATANODES[1]]
    third_set = [OM[0], DATANODES[2]]
    Blockade.blockade_create_partition(first_set, second_set, third_set)
    Blockade.blockade_status()
    ClusterUtils.run_freon(FILE, 1, 1, 1, 10240, "RATIS", "THREE")
    logger.info("Waiting for %s seconds before checking container status",
                os.environ["CONTAINER_STATUS_SLEEP"])
    time.sleep(int(os.environ["CONTAINER_STATUS_SLEEP"]))
    all_datanodes_container_status = \
        ClusterUtils.find_all_datanodes_container_status(FILE, SCALE)
    first_datanode_status = all_datanodes_container_status[0]
    second_datanode_status = all_datanodes_container_status[1]
    third_datanode_status = all_datanodes_container_status[2]
    assert first_datanode_status == 'CLOSED'
    assert second_datanode_status == 'CLOSED'
    assert third_datanode_status == 'OPEN'


def test_three_dns_isolate_twoscmfailure():
    """
    In this test, all datanodes are isolated from each other.
    two datanodes cannot communicate with SCM (second datanode and third
    datanode)
    Expectation :
    The container replica state in first datanode should be quasi-closed.
    The container replica state in second datanode should be open.
    The container replica state in third datanode should be open.
    """
    first_set = [OM[0], SCM[0], DATANODES[0]]
    second_set = [OM[0], DATANODES[1]]
    third_set = [OM[0], DATANODES[2]]
    Blockade.blockade_create_partition(first_set, second_set, third_set)
    Blockade.blockade_status()
    ClusterUtils.run_freon(FILE, 1, 1, 1, 10240, "RATIS", "THREE")
    logger.info("Waiting for %s seconds before checking container status",
                os.environ["CONTAINER_STATUS_SLEEP"])
    time.sleep(int(os.environ["CONTAINER_STATUS_SLEEP"]))
    all_datanodes_container_status = \
        ClusterUtils.find_all_datanodes_container_status(FILE, SCALE)
    first_datanode_status = all_datanodes_container_status[0]
    second_datanode_status = all_datanodes_container_status[1]
    third_datanode_status = all_datanodes_container_status[2]
    assert first_datanode_status == 'QUASI_CLOSED'
    assert second_datanode_status == 'OPEN'
    assert third_datanode_status == 'OPEN'


def test_three_dns_isolate_threescmfailure():
    """
    In this test, all datanodes are isolated from each other and also cannot
    communicate with SCM.
    Expectation :
    The container replica state in first datanode should be open.
    The container replica state in second datanode should be open.
    The container replica state in third datanode should be open.
    """
    first_set = [OM[0], DATANODES[0]]
    second_set = [OM[0], DATANODES[1]]
    third_set = [OM[0], DATANODES[2]]
    Blockade.blockade_create_partition(first_set, second_set, third_set)
    Blockade.blockade_status()
    ClusterUtils.run_freon(FILE, 1, 1, 1, 10240, "RATIS", "THREE")
    logger.info("Waiting for %s seconds before checking container status",
                os.environ["CONTAINER_STATUS_SLEEP"])
    time.sleep(int(os.environ["CONTAINER_STATUS_SLEEP"]))
    all_datanodes_container_status = \
        ClusterUtils.find_all_datanodes_container_status(FILE, SCALE)
    first_datanode_status = all_datanodes_container_status[0]
    second_datanode_status = all_datanodes_container_status[1]
    third_datanode_status = all_datanodes_container_status[2]
    assert first_datanode_status == 'OPEN'
    assert second_datanode_status == 'OPEN'
    assert third_datanode_status == 'OPEN'