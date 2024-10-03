"""
Copyright (c) Juniper Networks 2024
Created by Andrew Southard <southarda@juniper.net> <andsouth44@gmail.com>
"""

import argparse
from jnpr.junos import Device
from jnpr.junos.utils import fs
import pytest
import logging

from upgraders.dual_re_upgrader.dual_re_upgrader import dual_re_upgrade_upgrader
from helpers import Helpers
from jnpr.junos.utils.config import Config
from test_utils import TestUtils
from rpc_processor import (RpcProcessor, JunosRpcProcessorInitError, JunosConfigApplyError, JunosConfigRescueError,
                           JunosPackageInstallError, JunosRebootError, JunosConnectError)
from rpc_caller import RpcCaller


class TestUpgradeProcessor:
    @pytest.fixture(scope="function", autouse=True)
    def before(self, monkeypatch):
        monkeypatch.setattr(Helpers, "create_inputs_json_and_test_params_json",
                            TestUtils.create_mock_inputs_json_and_test_params_json)
        monkeypatch.setattr(Helpers, "create_logger", TestUtils.create_mock_logger)
        monkeypatch.setattr(Device, 'open', TestUtils.set_device_connected)
        monkeypatch.setattr(Device, 'close', TestUtils.do_nothing)
        monkeypatch.setattr(Device, 'transform', TestUtils.do_nothing)
        monkeypatch.setattr(argparse.ArgumentParser, "parse_args", TestUtils.MockArgs)
        monkeypatch.setattr(fs.FS, "ls", TestUtils.get_re_files)
        monkeypatch.setattr(fs.FS, "cp", TestUtils.return_success)
        monkeypatch.setattr(Config, "__enter__", TestUtils.MockConfig.__enter__)
        monkeypatch.setattr(Config, "__exit__", TestUtils.do_nothing)
        monkeypatch.setattr(Config, "commit", TestUtils.return_success)
        monkeypatch.setattr(Config, "rescue", TestUtils.return_success)
        monkeypatch.setattr(RpcProcessor, "countdown_timer", TestUtils.do_nothing)

    def test_given_successful_upgrade_when_run_then_return_success_messages(self, monkeypatch, caplog):

        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        messages = ["There are no differences between the pre and post configs. ✅",
                    "There are no differences between pre and post state. ✅"]
        dual_re_upgrade_upgrader()
        for message in messages:
            assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_successful_upgrade_when_diff_in_config_and_state_then_return_config_and_state_warning_messages(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        messages = ["⚠️ WARNING: There are the following differences between the pre and post configs:",
                    "-set interfaces xe-1/0/5:2 unit 10 family inet address 1.1.1.1/30",
                    "+set interfaces xe-1/0/5:2 unit 10 family inet address 1.1.1.2/30",
                    "-set interfaces xe-1/0/5:2 unit 40 vlan-id 40",
                    "+set interfaces xe-1/0/5:2 unit 40 vlan-id 41",
                    "⚠️ WARNING: There are the following differences between pre and post state:",
                    "Parameter subscriber-count-per-type.pppoe: has values: before 5, after 4",
                    "Parameter subscriber-count-per-type.vlan: has values: before 10, after 9"]
        dual_re_upgrade_upgrader()
        for message in messages:
            assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_init_rpc_processor_then_raise_rpc_processor_init_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        monkeypatch.setattr(RpcCaller, 'open', TestUtils.raise_exception)
        with pytest.raises(JunosRpcProcessorInitError):
            dual_re_upgrade_upgrader()
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_config_get_fail_then_raise_sysexit_and_get_config_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = "❌ ERROR: Unable to get configuration. Exception: Type 'NoneType' cannot be serialized."
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_chassis_alarm_then_raise_sysexit_and_chassis_alarm_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: The following alarms exist on the chassis:")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_verify_mastership_fail_then_raise_sysexit_and_re_mastership_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: RE0 is not master")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_re_status_bad_then_raise_sysexit_and_re_status_fail_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: RE0 has status of: Bad, expecting status=OK")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_re_mem_util_high_then_raise_sysexit_and_re_mem_fail_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: RE0 memory utilization is 80%. Expecting <= 50%")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_re_cpu_util_high_then_raise_sysexit_and_re_cpu_fail_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: RE0 CPU idle percentage is 15%. Expecting >= 40%")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_replication_not_complete_then_raise_sysexit_and_replication_not_complete_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Replication state is not complete for IS-IS")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_pic_status_fail_then_raise_sysexit_and_pic_status_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: All PICs should be Online. PIC in slot 0 is Offline")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_active_sw_ver_incorrect_then_raise_sysexit_and_sw_ver_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: RE0 is not running the expected Junos version. RE0 is running 22.4R3.25, expecting 19.4R3-S4.1")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_incorrect_re_model_then_raise_sysexit_and_re_model_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: RE1 is not the expected model version. RE1 is RE-S-1700x8")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_new_junos_package_not_existing_then_raise_sysexit_and_sw_version_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        monkeypatch.setattr(fs.FS, "ls", TestUtils.get_re_files_no_new_package)
        message = ("❌ ERROR: RE1 does not have the new Junos package junos-vmhost-install-mx-x86-64-22.4R3.25.tgz in /var/tmp/")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_incorrect_number_of_disks_on_re_then_raise_sysexit_and_number_of_disks_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: RE0 does not have correct number of disks. RE0 has 1, expecting 2")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_incorrect_number_of_isis_adjacencies_then_raise_sysexit_and_number_of_isis_adjacencies_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: RE has insufficient ISIS \'Up\' adjacencies. Expecting >= 2, but has 1")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_backup_config_file_then_raise_sysexit_and_copy_file_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        monkeypatch.setattr(fs.FS, "cp", TestUtils.return_fail)
        message = ("❌ ERROR: Copy failed from re0:/config/juniper.conf.1.gz to re0:/var/tmp/PreUpgrade.conf.gz.")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_record_chassis_inventory_then_raise_sysexit_and_record_chassis_inventory_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to record chassis hardware. Exception: \'NoneType\' object has no attribute \'findall\'")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_record_subscribers_then_raise_sysexit_and_get_subscribers_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to record subscriber count for each type. Exception: \'NoneType\' object has no attribute \'findall\'")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_record_isis_adjacencies_then_raise_sysexit_and_get_isis_adjacencies_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to save ISIS adjacency info to capture file. Exception: 'NoneType' object has no attribute 'findall'")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_record_bgp_summary_then_raise_sysexit_and_get_bgp_summary_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to record BGP summary info. Exception: 'NoneType' object has no attribute 'findall'")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_record_interface_state_then_raise_sysexit_and_get_interface_state_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to record interface state info. Exception: 'NoneType' object has no attribute 'findall'")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_record_ldp_session_info_then_raise_sysexit_and_get_ldp_session_info_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to save LDP session info. Exception: 'NoneType' object has no attribute 'findall'")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_record_replication_state_then_raise_sysexit_and_get_replication_state_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to verify replication state. Exception: 'NoneType' object has no attribute 'findall'")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_record_bfd_session_info_then_raise_sysexit_and_get_bfd_session_info_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to record bfd session info. Exception: 'NoneType' object has no attribute 'find'")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_record_pic_info_then_raise_sysexit_and_get_pic_info_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to verify PIC status. Exception: 'NoneType' object has no attribute 'findall'")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_record_chassis_alarms_then_raise_sysexit_and_get_chassis_alarms_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to verify alarms on chassis. Exception: 'bool' object has no attribute 'find'")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_record_l2ckt_info_then_raise_sysexit_and_get_l2ckt_info_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to record L2 circuit info. Exception: 'NoneType' object has no attribute 'findall'")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_record_route_summary_then_raise_sysexit_and_get_route_summary_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to record route summary. Exception: 'NoneType' object has no attribute 'findall'")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.ShowJunosVersion.reset()
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_load_config_then_raise_junos_config_apply_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        monkeypatch.setattr(TestUtils.MockConfig, "load", TestUtils.raise_exception)
        message = ("❌ ERROR: Unable to load config. Exception: test")
        with pytest.raises(JunosConfigApplyError):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_create_rescue_config_then_raise_junos_config_rescue_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        monkeypatch.setattr(TestUtils.MockConfig, "rescue", TestUtils.raise_exception)
        message = ("❌ ERROR: Unable to create rescue config. Exception: test")
        with pytest.raises(JunosConfigRescueError):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_load_package_then_raise_junos_install_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to install Junos. Exception: test")
        with pytest.raises(JunosPackageInstallError):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_unable_to_reboot_then_raise_junos_package_reboot_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Unable to initiate reboot of RE1. Exception: test")
        with pytest.raises(JunosRebootError):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_fail_when_device_unreachable_after_reboot_then_raise_junos_rpc_processor_init_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        monkeypatch.setattr(Device, 'open', TestUtils.do_nothing)
        message = ("UpgradeUtils: Cannot connect to 10.10.10.11. Maximum number of retries has been reached")
        with pytest.raises(JunosRpcProcessorInitError):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()

    def test_given_upgrade_warning_when_junos_not_matching_on_partitions_then_warning_in_log(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ('❌ ERROR: Junos image: junos-install-mx-x86-64-22.4R3.25 does not exist on both partitions')
        dual_re_upgrade_upgrader()
        assert message in caplog.text
        TestUtils.mocker_resetter()