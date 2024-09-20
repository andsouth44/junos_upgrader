"""
Copyright (c) Juniper Networks 2024
Created by Andrew Southard <southarda@juniper.net> <andsouth44@gmail.com>
"""

import argparse
from jnpr.junos import Device
from jnpr.junos.utils import fs

from upgraders.dual_re_upgrader.dual_re_upgrader import dual_re_upgrade_upgrader
from helpers import Helpers
from jnpr.junos.utils.config import Config
from test_utils import TestUtils
from rpc_processor import RpcProcessor
import pytest


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

    def test_successful_upgrade(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info_success)

        messages = ["There are no differences between the pre and post configs. ✅",
                    "There are no differences between pre and post state. ✅"]

        dual_re_upgrade_upgrader()

        for message in messages:
            assert message in caplog.text

    def test_upgrade_with_warnings(self, monkeypatch, caplog):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info_warnings)

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

