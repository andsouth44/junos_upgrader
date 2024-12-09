"""
Copyright (c) Juniper Networks 2024
Created by Andrew Southard <southarda@juniper.net> <andsouth44@gmail.com>
"""

import os, sys, logging, argparse, json
import jnpr.junos
from rpc_processor import RpcProcessor
from junos_upgrader_exceptions import JunosPackageInstallError, JunosRpcProcessorInitError, JunosInputsError, JunosReSwitchoverError
from helpers import Helpers


def dual_re_upgrade_upgrader():
    """
    This upgrader is designed to upgrade the JunOS on MX series routers with dual REs
    and redundancy features configured.
    See README.md file for details.

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
    active_junos: str = inputs_json.get("ACTIVE_JUNOS")
    new_junos_short: str = inputs_json.get("NEW_JUNOS")
    junos_package_path: str = inputs_json.get("JUNOS_PACKAGE_PATH")
    logfile_name: str = inputs_json.get("LOGFILE_NAME")
    config_file_to_backup: str = inputs_json.get("CONFIG_FILE_TO_BACKUP")
    re_model: str = inputs_json.get("RE_MODEL")
    min_isis_adj: int = inputs_json.get("MIN_ISIS_ADJ")
    min_ospf_nei: int = inputs_json.get("MIN_OSPF_NEI")
    max_mem_utilization: int = inputs_json.get("MAX_MEM_UTILIZATION_PERCENT")
    min_cpu_idle: int = inputs_json.get("MIN_CPU_IDLE_PERCENT")
    post_reboot_delay: int = inputs_json.get("POST_REBOOT_DELAY")
    post_switchover_delay: int = inputs_json.get("POST_SWITCHOVER_DELAY")
    post_script_completion_delay: int = inputs_json.get("POST_SCRIPT_COMPLETION_DELAY")
    connection_retries: int = inputs_json.get("CONNECTION_RETRIES")
    connection_retry_interval: int = inputs_json.get("CONNECTION_RETRY_INTERVAL")

    # derive additional junos package name parameters
    new_junos_package: str = f"junos-vmhost-install-mx-x86-64-{new_junos_short}.tgz"
    new_junos: str = f"junos-install-mx-x86-64-{new_junos_short}"

    # process input arguments
    parser = argparse.ArgumentParser(description="A Junos upgrade script for dual RE MX")
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

    if pre_upgrade_config is not None:
        # write pre upgrade config to log file
        with open('logs/pre_upgrade_config.txt', 'w') as file:
            file.write(pre_upgrade_config)

    # verify no chassis alarms
    rpc_processor_re0.verify_no_chassis_alarms()

    # Verify RE0 is Master
    rpc_processor_re0.verify_re_mastership(slot=0, tries=1)

    # verify RE0 status
    status = rpc_processor_re0.verify_re_status(slot=0)
    if status:

        # verify RE0 memory usage
        rpc_processor_re0.verify_re_memory_utilization(max_mem_util=max_mem_utilization, slot=0)

        # verify RE0 CPU idle
        rpc_processor_re0.verify_cpu_idle_time(min_cpu_idle, slot=0)

    # verify protocol replication
    rpc_processor_re0.verify_protocol_replication()

    # verify PIC status
    rpc_processor_re0.verify_pic_status()

    # verify existing Junos version on RE0
    rpc_processor_re0.verify_active_junos_version(expected_junos=active_junos, slot=0)

    # verify RE0 model version
    rpc_processor_re0.verify_re_model(re_model, slot=0)

    # verify proposed Junos package exists on RE0
    rpc_processor_re0.verify_proposed_junos_install_package_exists_on_re(
        junos_package_path=junos_package_path,
        proposed_package_name=new_junos_package, slot=0)

    # verify number of disks on RE0
    rpc_processor_re0.verify_number_of_disks_on_re(slot=0, expected_disks=2)

    # verify minimum number of 'Up' ISIS adjacencies
    rpc_processor_re0.verify_number_of_up_isis_adjacencies(min_isis_adjacencies=min_isis_adj, slot=0)

    # verify minimum number of 'Full' OSPF neighbors
    rpc_processor_re0.verify_number_of_full_ospf_neighbors(min_ospf_neighbors=min_ospf_nei, slot=0)

    # backup config files
    rpc_processor_re0.copy_file_on_device(f're0:/config/{config_file_to_backup}', 're0:/var/tmp/PreUpgrade.conf.gz')
    rpc_processor_re0.copy_file_on_device(f're1:/config/{config_file_to_backup}', 're1:/var/tmp/PreUpgrade.conf.gz')

    # record chassis hardware
    rpc_processor_re0.record_chassis_hardware(pre_upgrade_record)

    # record subscriber count for each subscriber type
    rpc_processor_re0.record_subscriber_count_for_each_subscriber_type(pre_upgrade_record)

    # record isis adjacencies
    rpc_processor_re0.record_isis_adjacency_info(pre_upgrade_record)

    # record ospf neighbors
    rpc_processor_re0.record_ospf_neighbor_info(pre_upgrade_record)

    # record bgp summary
    rpc_processor_re0.record_bgp_summary_info(pre_upgrade_record)

    # record interface state
    rpc_processor_re0.record_interface_state(pre_upgrade_record)

    # record ldp adjacencies
    rpc_processor_re0.record_ldp_session_info(pre_upgrade_record)

    # record protocol replication state
    rpc_processor_re0.record_protocol_replication_state(pre_upgrade_record)

    # record bfd session info
    rpc_processor_re0.record_bfd_session_info(pre_upgrade_record)

    # record PIC info
    rpc_processor_re0.record_pic_info(pre_upgrade_record)

    # record chassis alarms
    rpc_processor_re0.record_chassis_alarms(pre_upgrade_record)

    # record L2 circuit info
    rpc_processor_re0.record_l2_circuit_info(pre_upgrade_record)

    # record route summary
    rpc_processor_re0.record_route_summary(pre_upgrade_record)

    logger.info('********** RUNNING RE1 PRE-CHECKS **********')

    # Instantiate instance of RpcProcessor class for RE1
    logger.debug('Create instance of RpcProcessor class for re1')
    try:
        rpc_processor_re1 = RpcProcessor(
                logger=logger,
                upgrade_error_log=upgrade_error_log,
                upgrade_warning_log=upgrade_warning_log,
                host=re1_host,
                username=user,
                password=pw,
                port=port,
                connection_retries=connection_retries,
                connection_retry_interval=connection_retry_interval)
    except Exception as e:
        error = f'Unable to create instance of UpgradeUtils: {e}'
        logger.error(error)
        sys.exit()

    logger.debug(rpc_processor_re1)

    # verify RE1 status
    status = rpc_processor_re1.verify_re_status(slot=1)
    if status:

        # verify RE1 memory usage
        rpc_processor_re1.verify_re_memory_utilization(max_mem_util=max_mem_utilization, slot=1)

        # verify RE1 CPU idle
        rpc_processor_re1.verify_cpu_idle_time(min_cpu_idle, slot=1)

    # verify existing Junos version on RE1
    rpc_processor_re0.verify_active_junos_version(expected_junos=active_junos, slot=1)

    # verify RE1 model version
    rpc_processor_re1.verify_re_model(re_model, slot=1)

    # verify proposed Junos package exists on RE1
    rpc_processor_re1.verify_proposed_junos_install_package_exists_on_re(
        junos_package_path=junos_package_path,
        proposed_package_name=new_junos_package, slot=1)

    # verify number of disks on RE1
    rpc_processor_re1.verify_number_of_disks_on_re(slot=0, expected_disks=2)

    # write state info to log file
    with open('logs/pre_upgrade_state.json', 'w') as file:
        json.dump(pre_upgrade_record, file, indent=4)

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
        #
        # # write error log to log file
        # with open('logs/upgrade.log', 'w') as file:
        #     for error in upgrade_error_log:
        #         file.write(error)

        rpc_processor_re0.dev.close()
        rpc_processor_re1.dev.close()

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

    logger.info('********** UPGRADING RE1 **********')

    logger.info('Applying commands to deactivate redundancy features')
    deactivate_commands = 'inputs/deactivate_redundancy.txt'
    rpc_processor_re0.load_and_commit_config_on_device(deactivate_commands, 'private')

    rpc_processor_re1.create_rescue_config('private')

    # Installing and rebooting new Junos version on RE1, Partition 1
    rpc_processor_re1.install_junos_on_device(junos_package_path=junos_package_path, new_junos_package=new_junos_package, re_number=1)
    rpc_processor_re1.reboot_re(1)
    logger.info(f'RE1 rebooting, waiting {post_reboot_delay} seconds before trying to reconnect')
    rpc_processor_re1.countdown_timer(post_reboot_delay)
    rpc_processor_re1.dev.open()

    # Installing and rebooting new Junos version on RE1, Partition 2
    rpc_processor_re1.install_junos_on_device(junos_package_path=junos_package_path, new_junos_package=new_junos_package, re_number=1)
    rpc_processor_re1.reboot_re(1)
    logger.info(f'RE1 rebooting, waiting {post_reboot_delay} seconds before trying to reconnect')
    rpc_processor_re1.countdown_timer(post_reboot_delay)
    rpc_processor_re1.dev.open()

    rpc_processor_re1.check_matching_junos_on_partitions(new_junos)

    # Validate new Junos version on RE1
    rpc_processor_re1.validate_junos_on_device(junos_package_path, new_junos_package)

    # verify that new Junos is now running on RE1
    if not rpc_processor_re1.verify_active_junos_version(expected_junos=new_junos_short, slot=1):
        raise JunosPackageInstallError(f'RE1 is not running the expected Junos version {new_junos_short}')

    logger.info('Initiating switchover to RE1 as master')
    rpc_processor_re0.re_switchover()

    logger.info(f'Waiting {post_switchover_delay} seconds for switchover to complete')
    rpc_processor_re0.countdown_timer(post_switchover_delay)

    # Verify RE1 is Master
    if not rpc_processor_re1.verify_re_mastership(slot=1, tries=connection_retries):
        raise JunosReSwitchoverError

    logger.info('********** UPGRADING RE0 **********')

    # make sure we are still connected to re0
    if not rpc_processor_re0.dev.device.connected:
        rpc_processor_re0.dev.open()

    # create and save rescue config on the device
    rpc_processor_re0.create_rescue_config('private')

    # Installing and rebooting new Junos version on RE0, Partition 1
    rpc_processor_re0.install_junos_on_device(junos_package_path=junos_package_path, new_junos_package=new_junos_package, re_number=0)
    rpc_processor_re0.reboot_re(0)
    logger.info(f'RE0 rebooting, waiting {post_reboot_delay} seconds before trying to reconnect')
    rpc_processor_re0.countdown_timer(post_reboot_delay)
    rpc_processor_re0.dev.open()

    # Installing and rebooting new Junos version on RE0, Partition 2
    rpc_processor_re0.install_junos_on_device(junos_package_path=junos_package_path, new_junos_package=new_junos_package, re_number=0)
    rpc_processor_re0.reboot_re(0)
    logger.info(f'RE0 rebooting, waiting {post_reboot_delay} seconds before trying to reconnect')
    rpc_processor_re0.countdown_timer(post_reboot_delay)
    rpc_processor_re0.dev.open()

    # check that new junos is installed on both partitions of re
    rpc_processor_re0.check_matching_junos_on_partitions(new_junos)

    # Validate new Junos version on RE0
    rpc_processor_re0.validate_junos_on_device(junos_package_path, new_junos_package)

    # verify that new Junos is now running on RE0
    if not rpc_processor_re0.verify_active_junos_version(expected_junos=new_junos_short, slot=0):
        raise JunosPackageInstallError(f'RE0 is not running the expected Junos version {new_junos_short}')

    if not rpc_processor_re1.dev.device.connected:
        rpc_processor_re1.dev.open()

    logger.info('Initiating switchover to RE0 as master')
    rpc_processor_re1.re_switchover()

    logger.info(f'Waiting {post_switchover_delay} seconds for switchover to complete')
    rpc_processor_re1.countdown_timer(post_switchover_delay)

    # Verify RE0 is Master
    if not rpc_processor_re0.verify_re_mastership(slot=0, tries=connection_retries):
        raise JunosReSwitchoverError

    logger.info(f'Waiting {post_script_completion_delay} seconds for convergence after switchover')
    rpc_processor_re0.countdown_timer(post_script_completion_delay)

    logger.info('Applying commands to activate redundancy features')
    activate_commands = 'inputs/activate_redundancy.txt'
    rpc_processor_re0.load_and_commit_config_on_device(activate_commands, 'private')

    # check that redundancy is operational by checking that replication is complete
    rpc_processor_re0.confirm_replication_complete()

    # delay to ensure everything is stable before running post checks
    logger.info(f'Waiting {post_script_completion_delay} seconds for routing convergence')
    rpc_processor_re0.countdown_timer(post_script_completion_delay)

    logger.info('********** RUNNING POST UPGRADE CHECKS AND GATHERING STATE DATA **********')

    # reset active junos param prior to post upgrade checks because we are now running new version
    active_junos: str = new_junos_short

    # verify no chassis alarms
    rpc_processor_re0.verify_no_chassis_alarms()

    # verify minimum number of 'Up' ISIS adjacencies
    rpc_processor_re0.verify_number_of_up_isis_adjacencies(min_isis_adjacencies=min_isis_adj, slot=0)

    # verify minimum number of 'Full' OSPF neighbors
    rpc_processor_re0.verify_number_of_full_ospf_neighbors(min_ospf_neighbors=min_ospf_nei, slot=0)

    # record chassis hardware
    rpc_processor_re0.record_chassis_hardware(post_upgrade_record)

    # record subscriber count for each subscriber type
    rpc_processor_re0.record_subscriber_count_for_each_subscriber_type(post_upgrade_record)

    # record isis adjacencies
    rpc_processor_re0.record_isis_adjacency_info(post_upgrade_record)

    # record ospf neighbors
    rpc_processor_re0.record_ospf_neighbor_info(post_upgrade_record)

    # record bgp neighbors
    rpc_processor_re0.record_bgp_summary_info(post_upgrade_record)

    # record interface state
    rpc_processor_re0.record_interface_state(post_upgrade_record)

    # record ldp adjacencies
    rpc_processor_re0.record_ldp_session_info(post_upgrade_record)

    # record protocol replication state
    rpc_processor_re0.record_protocol_replication_state(post_upgrade_record)

    # record bfd session info
    rpc_processor_re0.record_bfd_session_info(post_upgrade_record)

    # record PIC info
    rpc_processor_re0.record_pic_info(post_upgrade_record)

    # record chassis alarms
    rpc_processor_re0.record_chassis_alarms(post_upgrade_record)

    # record L2 circuit info
    rpc_processor_re0.record_l2_circuit_info(post_upgrade_record)

    # record route summary
    rpc_processor_re0.record_route_summary(post_upgrade_record)

    # write state info to log file
    with open('logs/post_upgrade_state.json', 'w') as file:
        json.dump(post_upgrade_record, file, indent=4)

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

    # write post upgrade config to log file
    with open('logs/post_upgrade_config.txt', 'w') as file:
        file.write(post_upgrade_config)

    logger.info('********** COMPARING PRE & POST CONFIG **********')

    rpc_processor_re0.compare_configs(pre_upgrade_config, post_upgrade_config)

    logger.info('********** COMPARING PRE & POST STATE **********')

    rpc_processor_re0.run_compare_state_dicts(pre_upgrade_record, post_upgrade_record)

    logger.info('Enjoy your favorite beverage! \U0001F600')


if __name__ == "__main__":
    dual_re_upgrade_upgrader()
