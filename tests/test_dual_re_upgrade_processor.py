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
from tests.test_utils import TestUtils
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
        # monkeypatch.setattr(RpcProcessor, "verify_active_junos_version", TestUtils.return_success)

    def test_successful_upgrade(self, monkeypatch):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info_success)
        dual_re_upgrade_upgrader()

    def test_upgrade_with_warnings(self, monkeypatch):
        monkeypatch.setattr(Device, "execute", TestUtils.get_device_info_warnings)
        dual_re_upgrade_upgrader()
