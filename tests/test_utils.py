"""
Copyright (c) Juniper Networks 2024
Created by Andrew Southard <southarda@juniper.net> <andsouth44@gmail.com>
"""

import json
from pathlib import Path
import sys
import os
from lxml import etree
import logging
import inspect


class TestUtils:

    @staticmethod
    def get_test_name():
        cwd = os.path.dirname(os.path.abspath(__file__))
        current_frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(current_frame)
        for frame_info in outer_frames:
            if frame_info.filename == f'{cwd}/test_dual_re_upgrade_processor.py':
                return frame_info.function

    class MockArgs:
        def __init__(self):
            self.debug = False
            self.dryrun = False
            self.force = False

    class MockConfig:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self, *args, **kwargs):
            return TestUtils.MockConfig()

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def load(self, *args, **kwargs):
            pass

        @staticmethod
        def commit(*args, **kwargs):
            return True

        def lock(self, *args, **kwargs):
            pass

        def unlock(self, *args, **kwargs):
            pass

        def rescue(self, *args, **kwargs):
            return True

        def __repr__(self):
            pass

    class MockEtreeResponse:
        def __init__(self, text):
            self.text = text

    class ShowConfigMockerSuccess:
        def mock_file_load(file_name) -> etree.ElementTree:
            return etree.parse(Path(sys.path[0]).joinpath('resources', file_name))

        load1 = mock_file_load('rpc_responses/get_configuration_in_set_format.xml')
        load2 = mock_file_load('rpc_responses/get_configuration_in_set_format.xml')
        config_files_to_be_returned = [load1, load2]
        config_idx = 0

        @classmethod
        def get_config(cls):
            config_files = cls.config_files_to_be_returned[cls.config_idx]
            cls.config_idx += 1
            return config_files

        @classmethod
        def reset(cls):
            cls.config_idx = 0

    class ShowConfigMockerWarnings:
        def mock_file_load(file_name) -> etree.ElementTree:
            return etree.parse(Path(sys.path[0]).joinpath('resources', file_name))

        load1 = mock_file_load('rpc_responses/get_configuration_in_set_format.xml')
        load2 = mock_file_load('rpc_responses/get_configuration_in_set_format_post_upgrade.xml')
        config_files_to_be_returned = [load1, load2]
        config_idx = 0

        @classmethod
        def get_config(cls):
            config_files = cls.config_files_to_be_returned[cls.config_idx]
            cls.config_idx += 1
            return config_files

        @classmethod
        def reset(cls):
            cls.config_idx = 0

    class ShowSubscribersMockerSuccess:
        def mock_file_load(file_name) -> etree.ElementTree:
            return etree.parse(Path(sys.path[0]).joinpath('resources', file_name))

        first_load = mock_file_load('rpc_responses/get_subscriber_detail_as_xml.xml')
        second_load = mock_file_load('rpc_responses/get_subscriber_detail_as_xml.xml')
        subscribers_files_to_be_returned = [first_load, second_load]
        subscribers_idx = 0

        @classmethod
        def get_subscribers(cls):
            subscribers_files = cls.subscribers_files_to_be_returned[cls.subscribers_idx]
            cls.subscribers_idx += 1
            return subscribers_files

        @classmethod
        def reset(cls):
            cls.subscribers_idx = 0

    class ShowSubscribersMockerWarnings:
        def mock_file_load(file_name) -> etree.ElementTree:
            return etree.parse(Path(sys.path[0]).joinpath('resources', file_name))

        first_load = mock_file_load('rpc_responses/get_subscriber_detail_as_xml.xml')
        second_load = mock_file_load('rpc_responses/get_subscriber_detail_as_xml_post_upgrade.xml')
        subscribers_files_to_be_returned = [first_load, second_load]
        subscribers_idx = 0

        @classmethod
        def get_subscribers(cls):
            subscribers_files = cls.subscribers_files_to_be_returned[cls.subscribers_idx]
            cls.subscribers_idx += 1
            return subscribers_files

        @classmethod
        def reset(cls):
            cls.subscribers_idx = 0

    class ShowJunosVersion:
        def mock_file_load(file_name) -> etree.ElementTree:
            return etree.parse(Path(sys.path[0]).joinpath('resources', file_name))

        load1 = mock_file_load('rpc_responses/get_software_information_old.xml')
        load2 = mock_file_load('rpc_responses/get_software_information_old.xml')
        load3 = mock_file_load('rpc_responses/get_software_information_new.xml')
        load4 = mock_file_load('rpc_responses/get_software_information_new.xml')

        junos_versions_to_be_returned = [load1, load2, load3, load4]
        version_idx = 0

        @classmethod
        def get_version(cls):
            version_file = cls.junos_versions_to_be_returned[cls.version_idx]
            cls.version_idx += 1
            return version_file

        @classmethod
        def reset(cls):
            cls.version_idx = 0

    @staticmethod
    def mocker_resetter():
        mockers = [TestUtils.ShowJunosVersion,
                   TestUtils.ShowSubscribersMockerWarnings,
                   TestUtils.ShowSubscribersMockerSuccess,
                   TestUtils.ShowConfigMockerWarnings,
                   TestUtils.ShowConfigMockerSuccess]

        for mocker in mockers:
            mocker.reset()

    @staticmethod
    def logger_resetter(logfile):
        cwd = os.path.dirname(os.path.abspath(__file__))
        os.remove(f'{cwd}/logs/{logfile}')

    @staticmethod
    def create_mock_inputs_json():
        directory_path = Path(sys.path[0]).joinpath('inputs')
        combined_data = {}

        # Iterate over all files in the directory
        for filename in os.listdir(directory_path):
            # Check if the file has a .json suffix
            if filename.endswith(".json"):
                file_path = os.path.join(directory_path, filename)
                print(f"Opening file: {file_path}")

                # Open the .json file
                with open(file_path, 'r') as json_file:
                    try:
                        data = json.load(json_file)
                        for key, value in data.items():
                            if key in combined_data:
                                raise KeyError(f"Key {key} from {file_path} already exists")
                        # if no duplicate keys, add data to combined data dict
                        combined_data.update(data)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON in file {filename}: {e}")

        return combined_data

    @staticmethod
    def create_mock_logger(cwd, logfile):
        cwd = os.path.dirname(os.path.abspath(__file__))
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        file_handler = logging.FileHandler(f'{cwd}/logs/{logfile}', mode='w')
        return formatter, file_handler, logger

    @staticmethod
    def remove_logger_handlers(logger):
        for handler in logger.handlers:
            logger.removeHandler(handler)

    @staticmethod
    def do_nothing(*args, **kwargs):
        return

    @staticmethod
    def return_success(*args, **kwargs) -> bool:
        return True

    @staticmethod
    def return_fail(*args, **kwargs) -> bool:
        return False

    @staticmethod
    def return_none(*args, **kwargs) -> None:
        return None

    @staticmethod
    def set_device_connected(dev) -> None:
        dev.connected = True

    @staticmethod
    def raise_exception(*args, **kwargs):
        raise Exception("test")

    @staticmethod
    def load_test_file(file_name) -> dict:
        with open(Path(sys.path[0]).joinpath('resources', file_name)) as f:
            return json.load(f)

    @staticmethod
    def load_test_file_as_etree(file_name) -> etree.ElementTree:
        return etree.parse(Path(sys.path[0]).joinpath('resources', file_name))

    @staticmethod
    def load_test_file_as_element(file_name) -> etree.Element:
        """
        Some RPCs return a lxml.etree._Element instead of a lxml.etree.elementTree.
        An lxml.etree._Element is the root element of a lxml.etree.elementTree.
        This method returns the root element from a xml file.
        """
        element_tree = etree.parse(Path(sys.path[0]).joinpath('resources', file_name))
        return element_tree.getroot()

    @staticmethod
    def get_re_files(*args, **kwargs):
        return TestUtils.load_test_file('rpc_responses/get_re_files.json')

    @staticmethod
    def get_re_files_no_new_package(*args, **kwargs):
        return TestUtils.load_test_file('rpc_responses/get_re_files_no_new_package.json')

    @staticmethod
    def get_device_info(*args, **kwargs):
        calling_test_name = TestUtils.get_test_name()
        if (args[1].tag == 'get-configuration'
                and calling_test_name == 'test_given_successful_upgrade_when_diff_in_config_and_state_then_return_config_and_state_warning_messages'):
            return TestUtils.ShowConfigMockerWarnings.get_config()
        elif (args[1].tag == 'get-configuration'
              and calling_test_name == 'test_given_upgrade_fail_when_config_get_fail_then_raise_sysexit_and_get_config_error'):
            return TestUtils.do_nothing()
        elif args[1].tag == 'get-configuration':
            return TestUtils.ShowConfigMockerSuccess.get_config()
        elif (args[1].tag == 'get-alarm-information'
              and calling_test_name == 'test_given_upgrade_fail_when_chassis_alarm_then_raise_sysexit_and_chassis_alarm_error'):
            return TestUtils.load_test_file_as_etree('rpc_responses/get_chassis_alarm_information_as_xml.xml')
        elif (args[1].tag == 'get-alarm-information'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_record_chassis_alarms_then_raise_sysexit_and_get_chassis_alarms_error'):
            return TestUtils.return_fail()
        elif args[1].tag == 'get-alarm-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_chassis_alarm_information_none_as_xml.xml')
        elif (args[1].tag == 'get-route-engine-information'
              and calling_test_name == 'test_given_upgrade_fail_when_verify_mastership_fail_then_raise_sysexit_and_re_mastership_error'):
            return TestUtils.load_test_file_as_etree('rpc_responses/get_re_info_backup_mastership.xml')
        elif (args[1].tag == 'get-route-engine-information'
              and calling_test_name == 'test_given_upgrade_fail_when_re_status_bad_then_raise_sysexit_and_re_status_fail_error'):
            return TestUtils.load_test_file_as_etree('rpc_responses/get_re_info_bad_status.xml')
        elif (args[1].tag == 'get-route-engine-information'
              and calling_test_name == 'test_given_upgrade_fail_when_re_mem_util_high_then_raise_sysexit_and_re_mem_fail_error'):
            return TestUtils.load_test_file_as_etree('rpc_responses/get_re_info_bad_buffer.xml')
        elif (args[1].tag == 'get-route-engine-information'
              and calling_test_name == 'test_given_upgrade_fail_when_re_cpu_util_high_then_raise_sysexit_and_re_cpu_fail_error'):
            return TestUtils.load_test_file_as_etree('rpc_responses/get_re_info_bad_cpu.xml')
        elif (args[1].tag == 'get-route-engine-information'
              and calling_test_name == 'test_given_upgrade_fail_when_incorrect_re_model_then_raise_sysexit_and_re_model_error'):
            return TestUtils.load_test_file_as_etree('rpc_responses/get_re_info_bad_model.xml')
        elif args[1].tag == 'get-route-engine-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_re_info.xml')
        elif (args[1].tag == 'get-routing-task-replication-state'
              and calling_test_name == 'test_given_upgrade_fail_when_replication_not_complete_then_raise_sysexit_and_replication_not_complete_error'):
            return TestUtils.load_test_file_as_etree('rpc_responses/get_protocol_replication_state_not_complete.xml')
        elif (args[1].tag == 'get-routing-task-replication-state'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_record_replication_state_then_raise_sysexit_and_get_replication_state_error'):
            return TestUtils.return_none()
        elif args[1].tag == 'get-routing-task-replication-state':
            return TestUtils.load_test_file_as_element('rpc_responses/get_protocol_replication_state.xml')
        elif (args[1].tag == 'get-pic-information'
              and calling_test_name == 'test_given_upgrade_fail_when_pic_status_fail_then_raise_sysexit_and_pic_status_error'):
            return TestUtils.load_test_file_as_etree('rpc_responses/get_pic_info_as_xml_bad_status.xml')
        elif (args[1].tag == 'get-pic-information'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_record_pic_info_then_raise_sysexit_and_get_pic_info_error'):
            return TestUtils.return_none()
        elif args[1].tag == 'get-pic-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_pic_info_as_xml.xml')
        elif (args[1].tag == 'get-software-information'
              and calling_test_name == 'test_given_upgrade_fail_when_active_sw_ver_incorrect_then_raise_sysexit_and_sw_ver_error'):
            return TestUtils.load_test_file_as_etree('rpc_responses/get_software_information_new.xml')
        elif args[1].tag == 'get-software-information':
            return TestUtils.ShowJunosVersion.get_version()
        elif (args[1].tag == 'get-vmhost-version-information'
              and calling_test_name == 'test_given_upgrade_fail_when_incorrect_number_of_disks_on_re_then_raise_sysexit_and_number_of_disks_error'):
            return TestUtils.load_test_file_as_etree('rpc_responses/get_vmhost_version_one_disk.xml')
        elif (args[1].tag == 'get-vmhost-version-information'
              and calling_test_name == 'test_given_upgrade_warning_when_junos_not_matching_on_partitions_then_warning_in_log'):
            return TestUtils.load_test_file_as_etree('rpc_responses/get_vmhost_version_not_matching.xml')
        elif args[1].tag == 'get-vmhost-version-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_vmhost_version.xml')
        elif (args[1].tag == 'get-isis-adjacency-information'
              and calling_test_name == 'test_given_upgrade_fail_when_incorrect_number_of_isis_adjacencies_then_raise_sysexit_and_number_of_isis_adjacencies_error'):
            return TestUtils.load_test_file_as_etree('rpc_responses/get_isis_adjacency_information_one_adj.xml')
        elif (args[1].tag == 'get-isis-adjacency-information'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_record_isis_adjacencies_then_raise_sysexit_and_get_isis_adjacencies_error'):
            return TestUtils.return_none()
        elif args[1].tag == 'get-isis-adjacency-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_isis_adjacency_information.xml')
        elif (args[1].tag == 'get-ospf-neighbor-information'
              and calling_test_name == 'test_given_upgrade_fail_when_incorrect_number_of_ospf_neighbors_then_raise_sysexit_and_number_of_ospf_neighbors_error'):
            return TestUtils.load_test_file_as_etree('rpc_responses/get_ospf_neighbor_information_one_nei.xml')
        elif args[1].tag == 'get-ospf-neighbor-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_ospf_neighbor_information.xml')
        elif (args[1].tag == 'get-chassis-inventory'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_record_chassis_inventory_then_raise_sysexit_and_record_chassis_inventory_error'):
            return TestUtils.return_none()
        elif args[1].tag == 'get-chassis-inventory':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_chassis_hardware_as_xml.xml')
        elif (args[1].tag == 'get-subscribers'
              and calling_test_name == 'test_given_successful_upgrade_when_diff_in_config_and_state_then_return_config_and_state_warning_messages'):
            return TestUtils.ShowSubscribersMockerWarnings.get_subscribers()
        elif (args[1].tag == 'get-subscribers'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_record_subscribers_then_raise_sysexit_and_get_subscribers_error'):
            return TestUtils.return_none()
        elif args[1].tag == 'get-subscribers':
            return TestUtils.ShowSubscribersMockerSuccess.get_subscribers()
        elif (args[1].tag == 'get-bgp-summary-information'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_record_bgp_summary_then_raise_sysexit_and_get_bgp_summary_error'):
            return TestUtils.return_none()
        elif args[1].tag == 'get-bgp-summary-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_bgp_peers_by_group.xml')
        elif (args[1].tag == 'get-interface-information'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_record_interface_state_then_raise_sysexit_and_get_interface_state_error'):
            return TestUtils.return_none()
        elif args[1].tag == 'get-interface-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_interface_info_terse_as_xml.xml')
        elif (args[1].tag == 'get-ldp-session-information'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_record_ldp_session_info_then_raise_sysexit_and_get_ldp_session_info_error'):
            return TestUtils.return_none()
        elif args[1].tag == 'get-ldp-session-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_ldp_session_info_as_xml.xml')
        elif (args[1].tag == 'get-bfd-session-information'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_record_bfd_session_info_then_raise_sysexit_and_get_bfd_session_info_error'):
            return TestUtils.return_none()
        elif args[1].tag == 'get-bfd-session-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_bfd_session_info_as_xml.xml')
        elif (args[1].tag == 'get-l2ckt-connection-information'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_record_l2ckt_info_then_raise_sysexit_and_get_l2ckt_info_error'):
            return TestUtils.return_none()
        elif args[1].tag == 'get-l2ckt-connection-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_l2_circuit_info_as_xml.xml')
        elif (args[1].tag == 'get-route-summary-information'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_record_route_summary_then_raise_sysexit_and_get_route_summary_error'):
            return TestUtils.return_none()
        elif args[1].tag == 'get-route-summary-information':
            return TestUtils.load_test_file_as_etree('rpc_responses/get_route_summary_as_xml.xml')
        elif (args[1].tag == 'request-vmhost-package-add'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_load_package_then_raise_junos_install_error'):
            return TestUtils.raise_exception()
        elif args[1].tag == 'request-vmhost-package-add':
            return TestUtils.do_nothing()
        elif (args[1].tag == 'request-vmhost-reboot'
              and calling_test_name == 'test_given_upgrade_fail_when_unable_to_reboot_then_raise_junos_package_reboot_error'):
            return TestUtils.raise_exception()
        elif args[1].tag == 'request-vmhost-reboot':
            return TestUtils.do_nothing()
        elif args[1].tag == 'request-vmhost-package-validate' and args[1].attrib == {'format': 'text'}:
            return TestUtils.load_test_file_as_etree('rpc_responses/request_vmhost_package_validate.xml')
        elif (args[1].tag == 'request-chassis-routing-engine-switch'
              and calling_test_name == 'test_given_upgrade_fail_when_device_re_switchover_fail_then_raise_junos_re_switchover_error'):
            return TestUtils.load_test_file_as_etree('rpc_responses/request_re_switchover_fail.xml')
        elif args[1].tag == 'request-chassis-routing-engine-switch':
            return TestUtils.load_test_file_as_etree('rpc_responses/request_re_switchover.xml')
        else:
            assert False
