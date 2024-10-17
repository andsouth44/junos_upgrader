"""
Copyright (c) Juniper Networks 2024
Created by Andrew Southard <southarda@juniper.net> <andsouth44@gmail.com>
"""

from pathlib import Path
import sys, json, logging, os


class Helpers:
    @staticmethod
    def create_inputs_json() -> dict:
        directory_path = Path(sys.path[0]).joinpath('inputs')
        combined_data = {}

        for filename in os.listdir(directory_path):
            if filename.endswith(".json"):
                file_path = os.path.join(directory_path, filename)
                print(f"Opening file: {file_path}")

                with open(file_path, 'r') as json_file:
                    try:
                        data = json.load(json_file)
                        for key, value in data.items():
                            if key in combined_data:
                                raise KeyError(f"Key {key} from {file_path} already exists")
                        combined_data.update(data)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON in file {filename}: {e}")

        return combined_data

    @staticmethod
    def create_logger(cwd, logfile):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        file_handler = logging.FileHandler(f'{cwd}/logs/{logfile}', mode='w')
        return formatter, file_handler, logger
