"""
Copyright (c) Juniper Networks 2024
Created by Andrew Southard <southarda@juniper.net> <andsouth44@gmail.com>
"""
import re, time, sys, difflib
from lxml import etree
from jnpr.junos.utils.config import Config, ConfigLoadError
from rpc_caller import RpcCaller
from junos_upgrader_exceptions import *


class RpcProcessor:
    def __init__(self, **kwargs):
        self.logger = kwargs["logger"]
        self.upgrade_error_log = kwargs["upgrade_error_log"]
        self.upgrade_warning_log = kwargs["upgrade_warning_log"]
        self.host = kwargs["host"]
        self.username = kwargs["username"]
        self.password = kwargs["password"]
        self.port = kwargs["port"]
        self.connection_retries = kwargs["connection_retries"]
        self.connection_retry_interval = kwargs["connection_retry_interval"]

        self.dev = RpcCaller(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                logger=self.logger,
                connection_retries=self.connection_retries,
                connection_retry_interval=self.connection_retry_interval)

        self.dev.open()

    def __str__(self):
        return (f"Instance of RpcProcessor("
                f" logger object: {self.logger},"
                f" upgrade_error_log: {self.upgrade_error_log},"
                f" upgrade_warning_log: {self.upgrade_warning_log},"
                f" host: {self.host},"
                f" username: {self.username},"
                f" password: xxxxxx,"
                f" port: {self.port},"
                f" connection_retries: {self.connection_retries},"
                f" DeviceRpc object: {self.dev})")

    def get_config_as_etree(self):
        try:
            return self.dev.show_configuration({'database': 'committed'})
        except Exception as e:
            error = f'\u274C ERROR: Unable to get configuration. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def get_config_in_set_format(self):
        try:
            config = self.dev.show_configuration(options={'database':'committed', 'format':'set'})
            config = etree.tostring(config, encoding='unicode', pretty_print='True')
            return config
        except Exception as e:
            error = f'\u274C ERROR: Unable to get configuration. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_chassis_hardware(self, record: dict):
        self.logger.info('Recording chassis hardware')
        try:
            chassis_module_list = []
            chassis_hardware = self.dev.show_chassis_hardware()
            if chassis_hardware.findall('chassis/chassis-module') is not None:
                for module in chassis_hardware.findall('chassis/chassis-module'):
                    module_name = module.find('name').text
                    description = module.find('description').text
                    chassis_module_list.append({'name': module_name, 'description': description})
                record['chassis_hardware'] = chassis_module_list
            self.logger.info('Chassis hardware recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to record chassis hardware. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_no_chassis_major_alarms(self):
        self.logger.info('Verify no major alarms on chassis')
        try:
            alarm_list = []
            chass_alms = self.dev.show_chassis_alarms({})
            if chass_alms.find('alarm-summary/no-active-alarms') is not None:
                self.logger.info('No Major alarms on chassis. \u2705')
                return True
            alarms = chass_alms.findall('alarm-detail')
            for alarm in alarms:
                if alarm.find('alarm-class') is not None:
                    if alarm.find('alarm-class').text.strip() == 'Major':
                        alarm_list.append(alarm.find('alarm-description').text.strip())
            if len(alarm_list) > 0:
                error = f'\u274C ERROR: The following major alarms exist on the chassis:'
                self.logger.error(error)
                self.upgrade_error_log.append(error)
                for description in alarm_list:
                    self.logger.info(f'{description}')
                    self.upgrade_error_log.append(description)
            else:
                self.logger.info('No Major alarms on chassis. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify alarms on chassis. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_no_chassis_alarms(self):
        self.logger.info('Verify no alarms on chassis')
        try:
            alarm_list = []
            chass_alms = self.dev.show_chassis_alarms({})
            if chass_alms.find('alarm-summary/no-active-alarms') is not None:
                self.logger.info('No alarms on chassis. \u2705')
                return True
            alarms = chass_alms.findall('alarm-detail')
            for alarm in alarms:
                if alarm.find('alarm-description') is not None:
                    alarm_list.append(alarm.find('alarm-description').text.strip())
            if len(alarm_list) > 0:
                error = f'\u274C ERROR: The following alarms exist on the chassis:'
                self.logger.error(error)
                self.upgrade_error_log.append(error)
                for description in alarm_list:
                    self.logger.info(f'{description}')
                    self.upgrade_error_log.append(description)
            else:
                self.logger.info('No alarms on chassis. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify alarms on chassis. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_re_mastership(self, slot: int, tries: int) -> bool:
        self.logger.info(f'Verifying RE{str(slot)} is master')
        try:
            for i in range(1, tries + 1):
                self.logger.info(f'Checking if RE{str(slot)} is master. Attempt {i} of {self.connection_retries}')
                re_info = self.dev.show_chassis_routing_engine(slot=str(slot))
                state = re_info.find('route-engine/mastership-state').text
                if state != 'master':
                    if i == 1:
                        error = f'\u274C ERROR: RE{str(slot)} is not master'
                        self.logger.error(error)
                        self.upgrade_error_log.append(error)
                        break
                    self.logger.info(f'RE{str(slot)} is not yet master. Re-trying in 30 seconds')
                    time.sleep(30)
                else:
                    self.logger.info(f'RE{str(slot)} is master. \u2705')
                    return True
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify that RE{str(slot)} is master. Exception: {e}'
            self. logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_re_model(self, re_model: str, slot: int):
        self.logger.info(f'Verify model version of RE{str(slot)}')
        try:
            re_info = self.dev.show_chassis_routing_engine(slot=str(slot))
            model = re_info.find('route-engine/model').text
            if model == re_model:
                self.logger.info(f'RE{str(slot)} model version is {model}. \u2705')
                return True
            else:
                error = f'\u274C ERROR: RE{str(slot)} is not the expected model version. RE{str(slot)} is {model}, expecting {re_model}'
                self.logger.error(error)
                self.upgrade_error_log.append(error)
                return False
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify RE{str(slot)} model version. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_re_status(self, slot: int):
        self.logger.info(f'Verify status of RE{str(slot)}')
        try:
            re_info = self.dev.show_chassis_routing_engine(slot=str(slot))
            status = re_info.find('route-engine/status').text
            if status == 'OK':
                self.logger.info(f'RE{str(slot)} status is {status}. \u2705')
                return True
            else:
                error = f'\u274C ERROR: RE{str(slot)} has status of: {status}, expecting status=OK'
                self.logger.error(error)
                self.upgrade_error_log.append(error)
                return False
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify RE{str(slot)} status. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_re_memory_utilization(self, max_mem_util: int, slot: int):
        self.logger.info(f'Verify RE{str(slot)} memory utilization')
        try:
            re_info = self.dev.show_chassis_routing_engine(slot=str(slot))
            util_percent = re_info.find('route-engine/memory-buffer-utilization').text
            if int(util_percent) <= max_mem_util:
                self.logger.info(f'RE{str(slot)} memory utilization is {util_percent}%. \u2705')
                return True
            else:
                error = f'\u274C ERROR: RE{str(slot)} memory utilization is {util_percent}%. Expecting <= {max_mem_util}%'
                self.logger.error(error)
                self.upgrade_error_log.append(error)
                return False
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify RE{str(slot)} memory utilization. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_cpu_idle_time(self, min_cpu_idle: int, slot: int):
        self.logger.info(f'Verify RE{str(slot)} CPU idle')
        try:
            re_info = self.dev.show_chassis_routing_engine(slot=str(slot))
            idle_percent = re_info.find('route-engine/cpu-idle').text
            if int(idle_percent) >= min_cpu_idle:
                self.logger.info(f'RE{str(slot)} CPU idle percentage is {idle_percent}%. \u2705')
                return True
            else:
                error = f'\u274C ERROR: RE{str(slot)} CPU idle percentage is {idle_percent}%. Expecting >= {min_cpu_idle}%'
                self.logger.error(error)
                self.upgrade_error_log.append(error)
                return False
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify RE{str(slot)} CPU idle percentage. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_bgp_peers_by_group(self, bgp_group_names: list, min_peers_by_group: list):
        self.logger.info(f'Verify minimum number of established BGP peers for each group in list {bgp_group_names}.')
        try:
            for group, min_peer in zip(bgp_group_names, min_peers_by_group):
                summary = self.dev.show_bgp_summary_group_name(group)
                if summary.findall('bgp-peer') is not None:
                    peers = summary.findall('bgp-peer')
                    peer_list = []
                    for peer in peers:
                        if peer.find('peer-state').text == 'Established':
                            peer_list.append(peer.find('peer-address').text)

                    peer_count = len(peer_list)

                    if peer_count >= min_peer:
                        self.logger.info(f'BGP has {peer_count} established BGP peers for group {group}. \u2705')
                    else:
                        error = f'\u274C ERROR: BGP has {peer_count} established BGP peers for group {group}. Expecting >= {min_peer}'
                        self.logger.error(error)
                        self.upgrade_error_log.append(error)
                        return False
            return True
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify BGP peers for BGP groups. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_protocol_replication(self, show_errors: bool = True):
        self.logger.info('Verify protocol replication')
        try:
            replication_state = self.dev.show_task_replication()
            protocols = []
            states = []
            # Todo - Fix list expression
            # protocols = [protocols.append(protocol.text) for protocol in replication_state.findall('task-protocol-replication-name')]
            # states = [states.append(state.text) for state in replication_state.findall('task-protocol-replication-state')]
            # state_dict = dict(zip(protocols, states))

            for protocol in replication_state.findall('task-protocol-replication-name'):
                protocols.append(protocol.text)
            for state in replication_state.findall('task-protocol-replication-state'):
                states.append(state.text)
            state_dict = dict(zip(protocols, states))

            state_error = False
            for protocol, state in state_dict.items():
                if show_errors:
                    if state != 'Complete':
                        error = f'\u274C ERROR: Replication state is not complete for {protocol}'
                        self.logger.error(error)
                        self.upgrade_error_log.append(error)
                        state_error = True

            if 'OSPF' not in state_dict and 'IS-IS' not in state_dict:
                if show_errors:
                    error = f'\u274C ERROR: Neither OSPF or ISIS are present in the replication state output'
                    self.logger.error(error)
                    self.upgrade_error_log.append(error)
                    state_error = True

            if not state_error:
                self.logger.info(
                    'All protocol replication state is complete and either (or both) OSPF or ISIS are present. \u2705')
                return True
            else:
                return False
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify replication state. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_pic_status(self):
        self.logger.info('Verify PIC status')
        try:
            slots = []
            states = []
            pic_info = self.dev.show_chassis_fpc_pic_status()

            # for slot in pic_info.findall('fpc/pic/pic-slot'):
            #     slots.append(int(slot.text))
            # for state in pic_info.findall('fpc/pic/pic-state'):
            #     states.append(state.text)

            slots = [slot.text for slot in pic_info.findall('fpc/pic/pic-slot')]
            states = [state.text for state in pic_info.findall('fpc/pic/pic-state')]
            state_dict = dict(zip(slots, states))

            state_error = False
            for slot, state in state_dict.items():
                if state != 'Online':
                    error = f'\u274C ERROR: All PICs should be Online. PIC in slot {slot} is {state}'
                    self.logger.error(error)
                    self.upgrade_error_log.append(error)
                    state_error = True
            if not state_error:
                self.logger.info('All PICs are Online. \u2705')
                return True
            else:
                return False
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify PIC status. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_active_junos_version(self, expected_junos: str, slot: int):
        self.logger.info(f'Verify running Junos version on RE{str(slot)}')
        try:
            software_info = self.dev.show_version()
            ver_re = software_info.find('junos-version').text
            if ver_re == expected_junos:
                self.logger.info(f'RE{str(slot)} is running the expected Junos version {expected_junos} \u2705')
                return True
            else:
                error = f'\u274C ERROR: RE{str(slot)} is not running the expected Junos version. RE{str(slot)} is running {ver_re}, expecting {expected_junos}'
                self.logger.error(error)
                self.upgrade_error_log.append(error)
                return False
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify existing Junos running on RE{str(slot)}. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)
            return False

    def verify_proposed_junos_install_package_exists_on_re(self, junos_package_path: str, proposed_package_name: str, slot: int):
        self.logger.info(f'Verify proposed Junos install package exists on RE{str(slot)}')
        self.logger.debug(f'Junos package path: {junos_package_path}')
        self.logger.debug(f'Proposed package name: {proposed_package_name}')
        try:
            re_files = self.dev.fs.ls(path=junos_package_path)
            file_exists = False
            for file in re_files['files']:
                if file == proposed_package_name:
                    self.logger.info(f'RE{str(slot)} has the new Junos package: {proposed_package_name} in {junos_package_path}. \u2705')
                    file_exists = True
                    break
            if not file_exists:
                error = f'\u274C ERROR: RE{str(slot)} does not have the new Junos package {proposed_package_name} in {junos_package_path}'
                self.logger.error(error)
                self.upgrade_error_log.append(error)
                return False
            else:
                return True
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify that new Junos package exists on RE{str(slot)}. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_number_of_disks_on_re(self, slot: int, expected_disks: int):
        self.logger.info(f'Verify number of disks on RE{str(slot)}')
        try:
            info = self.dev.show_vmhost_version_information({'format': 'text'})
            info = etree.tostring(info, encoding='unicode', pretty_print='True')
            disk_count = sum(1 for _ in re.finditer("Junos Disk", info))
            if disk_count == 2:
                self.logger.info('RE has 2 disks. \u2705')
                return True
            else:
                error = f'\u274C ERROR: RE{str(slot)} does not have correct number of disks. RE{str(slot)} has {disk_count}, expecting {expected_disks}'
                self.logger.error(error)
                self.upgrade_error_log.append(error)
                return False
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify number of disks on RE{str(slot)}. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_number_of_up_isis_adjacencies(self, min_isis_adjacencies: int, slot: int):
        self.logger.info("Verify number of 'Up' ISIS adjacencies")
        try:
            adjacency_count = 0
            isis_info = self.dev.show_isis_adjacency()
            if isis_info.findall('isis-adjacency') is not None:
                for adjacency in isis_info.findall('isis-adjacency'):
                    if adjacency.find('adjacency-state').text == 'Up':
                        adjacency_count += 1
                if adjacency_count >= min_isis_adjacencies:
                    self.logger.info(f"RE{str(slot)} has {adjacency_count} ISIS 'Up' adjacencies. \u2705")
                    return True
                else:
                    error = f"\u274C ERROR: RE has insufficient ISIS 'Up' adjacencies. Expecting >= {min_isis_adjacencies}, but has {adjacency_count}"
                    self.logger.error(error)
                    self.upgrade_error_log.append(error)
                    return False
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify number of ISIS adjacencies. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_isis_adjacency_info(self, record: dict):
        self.logger.info('Recording ISIS adjacency info')
        try:
            isis_list = []
            isis_adj_info = self.dev.show_isis_adjacency(detail=True)
            if isis_adj_info.findall('isis-adjacency') is not None:
                for isis_adj in isis_adj_info.findall('isis-adjacency'):
                    interface = isis_adj.find('interface-name').text
                    level = isis_adj.find('level').text
                    state = isis_adj.find('adjacency-state').text
                    isis_list.append({'interface': interface, 'level': level, 'state': state})
                record['isis-adjacency-info'] = isis_list
                self.logger.info('ISIS adjacency info recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to save ISIS adjacency info to capture file. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_bgp_summary_info(self, record: dict):
        self.logger.info('Recording BGP summary info')
        try:
            peer_list = []
            bgp_summary = self.dev.show_bgp_summary()
            if bgp_summary.findall('bgp-peer') is not None:
                for peer in bgp_summary.findall('bgp-peer'):
                    address = peer.find('peer-address').text
                    state = peer.find('peer-state').text
                    peer_list.append({'address': address, 'state': state})
            record['bgp-summary'] = peer_list
            self.logger.info('BGP summary info recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to record BGP summary info. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_protocol_replication_state(self, record: dict):
        self.logger.info('Recording protocol replication state')
        try:
            replication_state_list = []
            replication_state = self.dev.show_task_replication()
            if replication_state.findall('task-protocol-replication-name') is not None:
                list_of_state_items = list(replication_state)
                for item in list_of_state_items:
                    if item.tag == 'task-protocol-replication-name':
                        index = list_of_state_items.index(item)
                        replication_state_list.append({item.text:list_of_state_items[index+1].text})
            record['replication-state'] = replication_state_list
            self.logger.info('Protocol replication state recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to save protocol replication state. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_pic_info(self, record: dict):
        self.logger.info('Recording PIC info')
        try:
            pic_list = []
            pic_info = self.dev.show_chassis_fpc_pic_status()
            if pic_info.findall('fpc') is not None:
                for fpc in pic_info.findall('fpc'):
                    fpc_slot = fpc.find('slot').text
                    fpc_state = fpc.find('state').text
                    fpc_description = fpc.find('description').text
                    if fpc.findall('pic') is not None:
                        for pic in fpc.findall('pic'):
                            pic_slot = pic.find('pic-slot').text
                            pic_state = pic.find('pic-state').text
                            pic_type = pic.find('pic-type').text
                            pic_list.append({'fpc_slot': fpc_slot, 'fpc_state': fpc_state, 'fpc_description': fpc_description, 'pic_slot': pic_slot, 'pic_state': pic_state, 'pic_description': pic_type})
                record['pic-info'] = pic_list
            self.logger.info('PIC info recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to record PIC info. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_chassis_alarms(self, record: dict):
        self.logger.info('Recording chassis alarms')
        try:
            alarm_list = []
            chassis_alarms = self.dev.show_chassis_alarms()
            if chassis_alarms.find('alarm-summary/active-alarm-count') is None:
                record['chassis-alarms'] = "No active alarms"
            elif chassis_alarms.findall('alarm-detail') is not None:
                for alarm in chassis_alarms.findall('alarm-detail'):
                    alarm_class = alarm.find('alarm-class').text
                    alarm_description = alarm.find('alarm-description').text
                    alarm_type = alarm.find('alarm-type').text
                    alarm_list.append(
                        {'alarm-class': alarm_class,
                         'alarm_description': alarm_description,
                         'alarm_type': alarm_type})
                record['chassis-alarms'] = alarm_list
            self.logger.info('Chassis alarms recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to record chassis alarms. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_interface_state(self, record: dict):
        self.logger.info('Recording interface state info')
        try:
            interface_list = []
            interface_info = self.dev.show_interfaces(terse=True)
            if interface_info.findall('physical-interface') is not None:
                for physical_interface in interface_info.findall('physical-interface'):
                    if physical_interface.findall('logical-interface') is not None:
                        for logical_interface in physical_interface.findall('logical-interface'):
                            name = logical_interface.find('name').text
                            admin_state = logical_interface.find('admin-status').text
                            oper_state = logical_interface.find('oper-status').text
                            interface_list.append(
                                {'name': name, 'admin-status': admin_state,
                                 'oper-status': oper_state})
                record['interface-summary'] = interface_list
            self.logger.info('Interface state info recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to record interface state info. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_subscriber_count_for_each_subscriber_type(self, record: dict):
        self.logger.info('Record subscriber count for each subscriber type')
        try:
            subs = self.dev.show_subscribers(detail=True, dev_timeout=300)
            sub_type_counts = {}
            if subs.findall('subscriber') is not None:
                for sub in subs.findall('subscriber'):
                    key = sub.find('access-type').text.lower()
                    if key not in sub_type_counts.keys():
                        sub_type_counts[key] = 1
                    else:
                        sub_type_counts[key] += 1
            record['subscriber-count-per-type'] = sub_type_counts
            self.logger.info('Subscriber type count recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to record subscriber count for each type. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_pppoe_subscriber_count(self, record: dict):
        self.logger.info('Record PPPOE subscriber count')
        try:
            subs = self.dev.show_subscribers(client_type='pppoe', count=True, dev_timeout=300)
            record['pppoe-subscriber-count'] = subs
            self.logger.info('PPPOE subscriber count recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to record PPPOE subscriber count. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_dhcp_subscriber_count(self, record: dict):
        self.logger.info('Record DHCP subscriber count')
        try:
            subs = self.dev.show_subscribers(client_type='dhcp', count=True, dev_timeout=300)
            record['dhcp-subscriber-count'] = subs
            self.logger.info('DHCP subscriber count recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to record DHCP subscriber count. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_vrf_subscriber_count(self, record: dict, vrf: str):
        self.logger.info(f'Record VRF-{vrf} subscriber count')
        try:
            subs = self.dev.show_subscribers(client_type='iptv', count=True, dev_timeout=300, vrf=vrf)
            record[f'{vrf}-subscriber-count'] = subs
            self.logger.info(f'{vrf} subscriber count recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to record {vrf} subscriber count. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_subscriber_count_is_zero(self):
        self.logger.info('Verify subscriber count is zero. This may take some time.')
        try:
            sub_count = self.dev.show_subscribers(count=True)
            count = sub_count.find('subscriber/number-of-subscribers').text.strip()
            if count == '0':
                self.logger.info('Subscriber count is 0. \u2705')
                return True
            else:
                error = f'\u26A0\uFE0F WARNING: Subscriber count is {count}. Expecting 0.'
                self.logger.error(error)
                self.upgrade_warning_log.append(error)
                return False
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify subscriber count. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_pppoe_subscriber_count(self):
        self.logger.info('Verify pppoe subscriber count. This may take some time.')
        try:
            sub_count = self.dev.show_subscribers(client_type='pppoe', count=True, dev_timeout=300)
            count = sub_count.find('subscriber/number-of-subscribers').text.strip()
            if count == '0':
                self.logger.info('Subscriber count for PPPOE is 0. \u2705')
                return True
            else:
                error = f'\u26A0\uFE0F WARNING: Subscriber count for PPPOE is {count}. Expecting 0.'
                self.logger.error(error)
                self.upgrade_warning_log.append(error)
                return False
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify PPPOE subscriber count. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_subscriber_count_by_vrf(self, vrf):
        self.logger.info(f'Verify vrf {vrf} subscriber count. This may take some time.')
        try:
            sub_count = self.dev.show_subscribers(routing_instance=vrf, count=True, dev_timeout=300)
            count = sub_count.find('subscriber/number-of-subscribers').text.strip()
            if count == '0':
                self.logger.info(f'Subscriber count for vrf {vrf} is 0. \u2705')
                return True
            else:
                error = f'\u26A0\uFE0F WARNING: Subscriber count for vrf {vrf} is {count}. Expecting 0.'
                self.logger.error(error)
                self.upgrade_warning_log.append(error)
                return False
        except Exception as e:
            error = f'\u274C ERROR: Unable to verify vrf {vrf} subscriber count. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_l2_circuit_in_up_state(self):
        self.logger.info("Verifying L2 circuits in 'Up' state")
        try:
            circuit_info = self.dev.show_l2circuit_connections()
            up_circuits = 0
            if circuit_info.findall('l2circuit-neighbor') is not None:
                for circuit in circuit_info.findall('l2circuit-neighbor'):
                    if circuit.find('connection/connection-status').text == 'Up':
                        up_circuits += 1
                self.logger.info(f"There are {up_circuits} L2 Circuits in 'Up' state.")
        except Exception as e:
            error = f"\u274C ERROR: Unable to verify L2 circuits in 'Up' state. Exception: {e}"
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_l2_circuit_info(self, record: dict):
        self.logger.info('Recording L2 circuit info')
        try:
            l2_circuit_info = self.dev.show_l2circuit_connections()
            if l2_circuit_info.findall('l2circuit-neighbor') is None:
                record['l2-circuit-info'] = "No L2 circuits"
            else:
                l2_circuit_list = []
                for neighbor in l2_circuit_info.findall('l2circuit-neighbor'):
                    connection_address = neighbor.find('neighbor-address').text
                    connection_id = neighbor.find('connection/connection-id').text
                    connection_type = neighbor.find('connection/connection-type').text
                    connection_status = neighbor.find('connection/connection-status').text
                    l2_circuit_list.append(
                        {'connection-address': connection_address,
                         'connection-id': connection_id,
                         'connection-type': connection_type,
                         'connection-status': connection_status})
                record['l2circuit-info'] = l2_circuit_list
            self.logger.info('L2 circuit info recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to record L2 circuit info. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def verify_ldp_sessions_in_operational_and_open_state(self):
        self.logger.info('Verifying LDP sessions in operational state')
        try:
            ldp_info = self.dev.show_ldp_session()
            ldp_operational_sessions = 0
            if ldp_info.findall('ldp-session') is None:
                self.upgrade_warning_log("\u26A0\uFE0F Warning: There are no LDP sessions in operational state")
            elif ldp_info.findall('ldp-session') is not None:
                for ldp_session in ldp_info.findall('ldp-session'):
                    if (ldp_session.find('ldp-session-state').text.strip() == 'Operational' and
                            ldp_session.find('ldp-connection-state').text.strip() == 'Open'):
                        ldp_operational_sessions += 1
                self.logger.info(f'There are {ldp_operational_sessions} LDP sessions in operational state. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to get LDP session info. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_ldp_session_info(self, record: dict):
        self.logger.info('Recording LDP session state')
        try:
            ldp_neighbor_list = []
            ldp_info = self.dev.show_ldp_session()
            if ldp_info.findall('ldp-session') is not None:
                for ldp_session in ldp_info.findall('ldp-session'):
                    neighbor = ldp_session.find('ldp-neighbor-address').text
                    session_state = ldp_session.find('ldp-session-state').text
                    connection_state = ldp_session.find('ldp-connection-state').text
                    ldp_neighbor_list.append(
                        {'neighbor': neighbor,
                         'session_state': session_state,
                         'connection_state': connection_state})
                record['ldp-neighbors'] = ldp_neighbor_list
            self.logger.info('LDP session info saved. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to save LDP session info. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_route_summary(self, record: dict):
        self.logger.info('Recording route summary')
        try:
            route_summary_list = []
            route_summ = self.dev.show_route_summary()
            if route_summ.findall('route-table') is not None:
                for route_table in route_summ.findall('route-table'):
                    route_table_name = route_table.find('table-name').text
                    if route_table.findall('protocols') is not None:
                        for protocol in route_table.findall('protocols'):
                            protocol_name = protocol.find('protocol-name').text
                            protocol_route_count = protocol.find('protocol-route-count').text
                            active_routes = protocol.find('active-route-count').text
                            route_summary_list.append(
                                {'route_table_name': route_table_name,
                                 'protocol-name': protocol_name,
                                 'protocol-route-count': protocol_route_count,
                                 'active-routes': active_routes})
                        record['route-summary'] = route_summary_list
            self.logger.info('Route summary recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to record route summary. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def record_bfd_session_info(self, record: dict):
        self.logger.info('Recording bfd session info')
        try:
            bfd_sess = self.dev.show_bfd_session()
            if bfd_sess.find('sessions') is not None:
                if int(bfd_sess.find('sessions').text) == 0:
                    record['bfd-session-state'] = "No sessions"
                elif int(bfd_sess.find('sessions').text) > 0:
                    record['bfd-session-state'] = bfd_sess.find('sessions').text
            self.logger.info('BFD session info recorded. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to record bfd session info. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def copy_file_on_device(self, source_path: str, dest_path: str):
        self.logger.info(f'Copying file from {source_path} to {dest_path}')
        try:
            copied = self.dev.copy_file_rpc(source_path, dest_path)
            if copied:
                self.logger.info(f'File copied from {source_path} to {dest_path}. \u2705')
            else:
                error = f'\u274C ERROR: Copy failed from {source_path} to {dest_path}.'
                self.logger.error(error)
                self.upgrade_error_log.append(error)
        except Exception as e:
            error = f'\u274C ERROR: Unable to copy file from {source_path} to {dest_path}. Exception: {e}'
            self.logger.error(error)
            self.upgrade_error_log.append(error)

    def load_and_commit_config_on_device(self, path: str, mode: str):
        self.logger.info(f'Loading and committing config {path}')
        try:
            with Config(dev=self.dev.device, mode=mode) as cu:
                cu.load(path=path, format='set', ignore_warning='statement not found')
                self.logger.info('Loaded ok')
                cu.commit(sync=True)
                self.logger.info('Config loaded and committed successfully. \u2705')
        except ConfigLoadError as e:
            error = (f'\u274C ERROR: There is a problem with one or more of the commands in file {path}'
                     f' that you are trying to apply to the device. Please check the syntax of the'
                     f' commands. Exception: {e}')
            self.logger.error(error)
            raise JunosConfigApplyError
        except Exception as e:
            error = f'\u274C ERROR: Unable to load config. Exception: {e}'
            self.logger.error(error)
            raise JunosConfigApplyError

    def create_rescue_config(self, mode: str):
        self.logger.info('Creating rescue config')
        try:
            with Config(dev=self.dev.device, mode=mode) as cu:
                if cu.rescue(action='save'):
                    self.logger.info('Rescue config created successfully. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to create rescue config. Exception: {e}'
            self.logger.error(error)
            raise JunosConfigRescueError

    def install_junos_on_device(self, junos_package_path: str, new_junos_package: str, re_number: int):
        self.logger.debug(f'Inputs are - junos_package_path: {junos_package_path}, new_junos_package: {new_junos_package}, re_number: {re_number}')
        self.logger.info(f'Installing {new_junos_package}. This may take up to 10 minutes.')
        try:
            package = f"{junos_package_path}{new_junos_package}"
            if re_number == 0:
                self.dev.request_vmhost_software_add(package_name=package, re0=True, no_validate=True, ignore_warning=True, dev_timeout=900)
            elif re_number == 1:
                self.dev.request_vmhost_software_add(package_name=package, re1=True, no_validate=True, ignore_warning=True, dev_timeout=900)
            else:
                raise ValueError("RE number must be an int of 0 or 1")

            self.logger.info(f'New package: {new_junos_package} installed. \u2705')

            # TODO - figure out why SW module does not work reliably
            # ok, msg = self.dev.sw.install(package=package, progress=self.update_progress, vmhost=True,
            #                      no_copy=True, all_re=False, validate=False, ignore_warning=True)
            # if ok:
            #     self.logger.info(f'Installation of {package} successful. Rebooting')
            #     rsp = self.dev.sw.reboot(all_re=False, vmhost=True)
            #     self.logger.info(f'Result of reboot is {rsp}')
            # else:
            #     self.logger.error(f'\u274C ERROR: Install of new Junos not successful. Exception: {ok}')
            #     raise JunosInstallError
        except Exception as e:
            error = f'\u274C ERROR: Unable to install Junos. Exception: {e}'
            self.logger.error(error)
            raise JunosPackageInstallError

    def reboot_re(self, re_number: int):
        self.logger.info(f'Initiating reboot of RE{re_number}.')
        try:
            self.dev.request_vmhost_reboot_re(re_number)
            self.logger.info(f'RE{re_number} rebooted. It may take up to 10 minutes for the RE to come back online. \u2705')
        except Exception as e:
            error = f'\u274C ERROR: Unable to initiate reboot of RE{str(re_number)}. Exception: {e}'
            self.logger.error(error)
            raise JunosRebootError

    def validate_junos_on_device(self, path: str, package: str):
        self.logger.info(f'Validating {package}. This may take several minutes.')
        try:
            validation_response = self.dev.request_vmhost_software_validate(f'{path}{package}')

            if "mgd: error: configuration check-out failed" in validation_response:
                error = f'\u26A0\uFE0F WARNING: Validation failure. Reason: '
                self.logger.error(error)
                self.upgrade_warning_log.append(f'\u26A0\uFE0F WARNING: Validation failure')
                validation_response_lines = validation_response.splitlines()
                for line in validation_response_lines:
                    if 'Chassis control process' in line:
                        self.logger.info(line)
            else:
                self.logger.info(f'Validation successful. \u2705')
                return True
        except Exception as e:
            error = f'\u26A0\uFE0F WARNING: Unable to validate. Exception: {e}'
            self.logger.error(error)
            raise JunosValidationError

    def check_matching_junos_on_partitions(self, image: str):
        self.logger.info(f'Checking that image: {image} exists on both partitions')
        try:
            info = self.dev.show_vmhost_version_information({'format': 'text'})
            info = etree.tostring(info, encoding='unicode', pretty_print='True')
            matches = re.findall(image, info)
            if len(matches) == 2:
                self.logger.info(f'Junos image {image} exists on both partitions. \u2705')
            else:
                self.logger.error(f'\u274C ERROR: Junos image: {image} does not exist on both partitions')
                self.upgrade_warning_log.append(f'\u26A0\uFE0F WARNING: Junos image {image} does not exist on both partitions')
        except Exception as e:
            error = f"\u26A0\uFE0F WARNING: Unable to confirm image on both partitions. Exception: {e}"
            self.logger.error(error)

    def re_switchover(self):
        try:
            resp = self.dev.request_chassis_routing_engine_master_switch(no_confirm=True, ignore_warning=True)
            messages = resp.findall('message')
            if "Complete" in messages[-1].text:
                self.logger.info('RE switchover initiated. \u2705')
            else:
                error = f'\u274C ERROR: RE switchover initiation failed'
                self.logger.error(error)
                self.upgrade_error_log.append(error)
                return JunosReSwitchoverError
        except Exception as e:
            error = f"\u274C ERROR: Unable to initiate RE switchover. Exception: {e}"
            self.logger.error(error)
            self.upgrade_error_log.append(error)
            raise JunosReSwitchoverError

    def request_vmhost_snapshot(self):
        self.logger.info('Creating vmhost snapshot. This may take several minutes:')
        try:
            resp = self.dev.request_vmhost_snapshot()
            if "Software snapshot done" in resp.text:
                self.logger.info('Snapshot created. \u2705')
            else:
                error = f'\u26A0\uFE0F WARNING: Create snapshot failed'
                self.logger.error(error)
                self.upgrade_warning_log.append(error)
        except Exception as e:
            error = f"\u26A0\uFE0F WARNING: Unable to create snapshot. Exception: {e}"
            self.logger.error(error)
            self.upgrade_warning_log.append(error)

    def confirm_replication_complete(self):
        try:
            for i in range(1, self.connection_retries + 1):
                self.logger.info(f'Checking protocol replication. Attempt {i} of {self.connection_retries}')
                if not self.verify_protocol_replication(show_errors=False):
                    self.logger.info('Protocol replication not complete. Re-trying in 20 seconds')
                    time.sleep(20)
                else:
                    return True
            self.upgrade_warning_log.append('\u26A0\uFE0F WARNING: "Protocol replication not complete')
        except Exception as e:
            error = f"\u26A0\uFE0F WARNING: Unable to confirm replication is complete. Exception: {e}"
            self.logger.error(error)
            self.upgrade_warning_log.append(error)

    ##################### Utility Methods #####################

    @staticmethod
    def countdown_timer(seconds):
        for remaining in range(seconds, 0, -1):
            sys.stdout.write("\r")
            sys.stdout.write(f"Time remaining: {remaining:2d} seconds")
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\n")

    def compare_state_dicts(self, dict1, dict2, parent_key=""):
        differences = {}

        # Get the union of the keys from both dictionaries
        all_keys = dict1.keys() | dict2.keys()

        for key in all_keys:
            full_key = f"{parent_key}.{key}" if parent_key else key

            if key not in dict1:
                differences[full_key] = ("Missing in dict1", dict2[key])
            elif key not in dict2:
                differences[full_key] = (dict1[key], "Missing in dict2")
            else:
                # If the value is a dictionary, recurse into it
                if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                    sub_diff = self.compare_state_dicts(dict1[key], dict2[key], full_key)
                    if sub_diff:
                        differences.update(sub_diff)
                # If the value is a list, compare element by element
                elif isinstance(dict1[key], list) and isinstance(dict2[key], list):
                    if len(dict1[key]) != len(dict2[key]):
                        differences[full_key] = (dict1[key], dict2[key])
                    else:
                        for i, (v1, v2) in enumerate(zip(dict1[key], dict2[key])):
                            if isinstance(v1, dict) and isinstance(v2, dict):
                                sub_diff = self.compare_state_dicts(v1, v2, f"{full_key}[{i}]")
                                if sub_diff:
                                    differences.update(sub_diff)
                            elif v1 != v2:
                                differences[f"{full_key}[{i}]"] = (v1, v2)
                # Compare values directly if not dictionaries or lists
                elif dict1[key] != dict2[key]:
                    differences[full_key] = (dict1[key], dict2[key])

        return differences

    def run_compare_state_dicts(self, dict1, dict2):
        differences = self.compare_state_dicts(dict1, dict2)
        if len(differences) == 0:
            self.logger.info('There are no differences between pre and post state. \u2705')
        else:
            self.logger.info('\u26A0\uFE0F WARNING: There are the following differences between pre and post state:')
            for key, value in differences.items():
                self.logger.error(f"Parameter {key}: has values: before {value[0]}, after {value[1]}")

    def compare_configs(self, pre_upgrade, post_upgrade):
        try:
            pre_upgrade_lines = pre_upgrade.splitlines()
            post_upgrade_lines = post_upgrade.splitlines()
            pre_upgrade_lines_sorted = sorted(pre_upgrade_lines)
            post_upgrade_lines_sorted = sorted(post_upgrade_lines)

            diff = difflib.unified_diff(
                    pre_upgrade_lines_sorted,
                    post_upgrade_lines_sorted,
                    lineterm='')

            differences = []
            count = 0
            for item in diff:
                count += 1
                differences.append(item)
            if count == 0:
                self.logger.info('There are no differences between the pre and post configs. \u2705')
                return
            else:
                self.logger.info('\u26A0\uFE0F WARNING: There are the following differences between the pre and post configs:')
                for difference in differences:
                    if difference.startswith('+') and not difference.startswith('+++') or difference.startswith(
                            '-') and not difference.startswith('---'):
                        self.logger.info(difference)
        except Exception as e:
            error = f"\u274C ERROR: Unable to compare pre and post configs. Exception: {e}"
            self.logger.error(error)
