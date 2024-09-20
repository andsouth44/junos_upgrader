"""
Copyright (c) Juniper Networks 2024
Created by Andrew Southard <southarda@juniper.net> <andsouth44@gmail.com>
"""

from pathlib import Path
import sys, json, logging


class Helpers:
    @staticmethod
    def create_inputs_json_and_test_params_json():
        with open(Path(sys.path[0]).joinpath('src', 'junos_upgrader', 'upgraders', 'dual_re_upgrader', 'inputs', 'USER_INPUTS.json')) as inputs:
            with open(Path(sys.path[0]).joinpath('src', 'junos_upgrader', 'upgraders', 'dual_re_upgrader', 'inputs', 'TEST_PARAMS.json')) as test_params:
                return json.load(inputs), json.load(test_params)

    @staticmethod
    def create_logger(cwd, logfile):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        file_handler = logging.FileHandler(f'{cwd}/logs/{logfile}', mode='w')
        return formatter, file_handler, logger
