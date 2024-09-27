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
from rpc_processor import RpcProcessor


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
        TestUtils.ShowJunosVersion.reset()

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
        TestUtils.ShowJunosVersion.reset()

    def test_given_upgrade_fail_when_config_get_fail_then_raise_sysexit_and_get_config_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = "❌ ERROR: Unable to get configuration. Exception: Type 'NoneType' cannot be serialized."
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text

    def test_given_upgrade_fail_when_chassis_alarm_then_raise_sysexit_and_chassis_alarm_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: The following alarms exist on the chassis:")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text

    def test_given_upgrade_fail_when_verify_mastership_fail_then_raise_sysexit_and_re_mastership_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: RE0 is not master")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text

    def test_given_upgrade_fail_when_re_status_bad_then_raise_sysexit_and_re_status_fail_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: RE0 has status of: Bad, expecting status=OK")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text

    def test_given_upgrade_fail_when_re_mem_util_high_then_raise_sysexit_and_re_mem_fail_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: RE0 memory utilization is 80%. Expecting <= 50%")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text

    def test_given_upgrade_fail_when_re_cpu_util_high_then_raise_sysexit_and_re_cpu_fail_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: RE0 CPU idle percentage is 15%. Expecting >= 40%")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text

    def test_given_upgrade_fail_when_replication_not_complete_then_raise_sysexit_and_replication_not_complete_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: Replication state is not complete for IS-IS")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text

    def test_given_upgrade_fail_when_pic_status_fail_then_raise_sysexit_and_pic_status_error(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info)
        monkeypatch.setattr(logging.Logger, "addHandler", TestUtils.do_nothing)
        message = ("❌ ERROR: All PICs should be Online. PIC in slot 0 is Offline")
        with pytest.raises(SystemExit):
            dual_re_upgrade_upgrader()
        assert message in caplog.text
