"""
Copyright (c) Juniper Networks 2024
Created by Andrew Southard <southarda@juniper.net> <andsouth44@gmail.com>
"""

import os, sys, logging, argparse
import jnpr.junos
from rpc_processor import RpcProcessor
from junos_upgrader_exceptions import JunosRpcProcessorInitError, JunosInputsError
from helpers import Helpers


def upgrader_template():
    """
    This is a template to assist users in developing new upgraders

    """

    #  Create inputs_json dict by reading all json files in inputs folder
    try:
        inputs_json = Helpers.create_inputs_json()
    except KeyError:
        raise
    except Exception as e:
        raise JunosInputsError(e)

    #  Extract input parameters from inputs_json dict
    re0_host: str = inputs_json.get("RE0_HOST")
    re1_host: str = inputs_json.get("RE1_HOST")
    port: str = inputs_json.get("PORT")
    user: str = inputs_json.get("USERNAME")
    pw: str = inputs_json.get("PASSWORD")
    logfile_name: str = inputs_json.get("LOGFILE_NAME")
    connection_retries: int = inputs_json.get("CONNECTION_RETRIES")
    connection_retry_interval: int = inputs_json.get("CONNECTION_RETRY_INTERVAL")
    # extract other params as required

    # process input arguments
    parser = argparse.ArgumentParser(description="A Junos upgrade script for XXXXX")
    parser.add_argument(
            '-d', '--dryrun',
            dest='dryrun',
            action='store_true',
            help='Run the script without making any changes (default: False)',
            default=False
    )
    parser.add_argument(
            '-f', '--force',
            dest='force',
            action='store_true',
            help='Run the script ignoring any pre-checks errors (default: False)',
            default=False
    )

    parser.add_argument(
            '-g', '--debug',
            dest='debug',
            action='store_true',
            help='Run the script with more detailed logging (default: False)',
            default=False
    )

    # parse input flags
    args = parser.parse_args()

    # initialize logging
    cwd = os.path.dirname(os.path.abspath(__file__))
    formatter, file_handler, logger = Helpers.create_logger(cwd, logfile_name)

    # process input flags
    if args.debug:
        file_handler.setLevel(logging.DEBUG)
    else:
        file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    if args.debug:
        stream_handler.setLevel(logging.DEBUG)
    else:
        stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    if args.dryrun:
        logger.info("Dryrun mode is enabled.")
    else:
        logger.info("Dryrun mode is disabled.")

    if args.force:
        logger.info("Force mode is enabled.")
    else:
        logger.info("Force mode is disabled.")

    # Create lists to store exceptions and warnings as we go, for use at the end
    upgrade_error_log = []
    upgrade_warning_log = []

    # Create dicts to store pre and post state data for comparison later
    pre_upgrade_record = {}
    post_upgrade_record = {}

    logger.info('********** RUNNING RE0 PRE-CHECKS **********')

    # Instantiate instance of RpcProcessor class for RE0
    logger.debug('Create instance of RpcProcessor class for re0')
    try:
        rpc_processor_re0 = RpcProcessor(
                logger=logger,
                upgrade_error_log=upgrade_error_log,
                upgrade_warning_log=upgrade_warning_log,
                host=re0_host,
                username=user,
                password=pw,
                port=port,
                connection_retries=connection_retries,
                connection_retry_interval=connection_retry_interval)
    except Exception as e:
        error = f'Unable to create instance of UpgradeUtils: {e}'
        logger.error(error)
        upgrade_error_log.append(error)
        raise JunosRpcProcessorInitError(e)

    logger.debug(f'Juniper PyEZ Version: {jnpr.junos.__version__}')
    logger.debug(rpc_processor_re0)

    # get pre upgrade config
    pre_upgrade_config = rpc_processor_re0.get_config_in_set_format()

    # Include here a series of method calls for the pre-check steps appropriate for your upgrade
    # Each method call calls a method from the rpc_processor class

    if len(upgrade_warning_log) != 0:
        # 1 or more pre-check warnings
        error = '********** \u26A0\uFE0F: THERE ARE ONE OR MORE PRE-CHECK WARNINGS **********'
        logger.error(error)

        for warning in upgrade_warning_log:
            logger.error(warning)

    if len(upgrade_error_log) != 0 and not args.force:
        # 1 or more pre-check errors
        error = '********** \u274C: THERE ARE ONE OR MORE PRE-CHECK ERRORS **********'
        logger.error(error)
        error = '********** PLEASE FIX THE FOLLOWING ERRORS BEFORE RE-TRYING **********'
        logger.error(error)

        for error in upgrade_error_log:
            logger.error(error)

        rpc_processor_re0.dev.close()

        sys.exit()

    else:
        # PRE-CHECKS COMPLETE
        logger.info('********** PRE-CHECKS COMPLETE **********')
        if args.dryrun:
            logger.info('********** DRY RUN FLAG SET. ENDING UPGRADE SCRIPT **********')
            sys.exit()
        elif len(upgrade_error_log) != 0 and args.force:
            logger.info('********** FORCE FLAG SET. CONTINUING WITH UPGRADE DESPITE ERRORS **********')
        else:
            logger.info('********** CONTINUING WITH UPGRADE **********')

    logger.info('********** UPGRADING **********')

    # Include a series of method calls for the upgrade steps appropriate for your upgrade
    # Each method call calls a method from the rpc_processor class

    logger.info('********** RUNNING POST UPGRADE CHECKS AND GATHERING STATE DATA **********')

    # Include here a series of method calls for the post upgrade checks appropriate for your upgrade
    # Each method call calls a method from the rpc_processor class

    # get post upgrade config
    post_upgrade_config = rpc_processor_re0.get_config_in_set_format()

    # write post upgrade config to log file
    with open('logs/post_upgrade_config.txt', 'w') as file:
        file.write(post_upgrade_config)

    logger.info('********** UPGRADE COMPLETE **********')

    # if 1 or more warnings
    if len(upgrade_warning_log) != 0:
        error = '********** \u26A0\uFE0F: THERE ARE ONE OR MORE UPGRADE WARNINGS **********'
        logger.error(error)

        for warning in upgrade_warning_log:
            logger.error(warning)

    # if 1 or more errors
    if len(upgrade_error_log) != 0:
        error = '********** \u274C: THERE ARE ONE OR MORE UPGRADE ERRORS **********'
        logger.error(error)

        for error in upgrade_error_log:
            logger.error(error)

    logger.info('********** COMPARING PRE & POST CONFIG **********')

    rpc_processor_re0.compare_configs(pre_upgrade_config, post_upgrade_config)

    logger.info('********** COMPARING PRE & POST STATE **********')

    rpc_processor_re0.run_compare_state_dicts(pre_upgrade_record, post_upgrade_record)

    logger.info('Enjoy your favorite beverage! \U0001F600')


if __name__ == "__main__":
    upgrader_template()
