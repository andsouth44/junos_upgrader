"""
Copyright (c) Juniper Networks 2024
Created by Andrew Southard <southarda@juniper.net> <andsouth44@gmail.com>
"""

from jnpr.junos import Device
from jnpr.junos.utils.fs import FS
from lxml import etree
import time

from junos_upgrader_exceptions import JunosConnectError


class RpcCaller:
    def __init__(self, host, username, password, port, logger, connection_retries=20, connection_retry_interval=5):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.logger = logger
        self.connection_retries = connection_retries
        self.connection_retry_interval = connection_retry_interval
        self.device = Device(host=host, user=username, password=password, port=port, conn_open_timeout=30, normalize=True)
        self.fs = FS(self.device)

    def __str__(self):
        return (f"Instance of RpcCaller("
                f" host: {self.host},"
                f" username: {self.username},"
                f" password: xxxxxx,"
                f" port: {self.port}"
                f" connection_retries: {self.connection_retries},"
                f" device object: {self.device},"
                f" file system object: {self.fs})")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self):
        self.close()

    def open(self):
        for i in range(1, self.connection_retries + 1):
            try:
                self.logger.info(f'Trying to connect to {self.host}. Attempt {i} of {self.connection_retries}.')
                self.device.open()
                if self.device.connected:
                    self.logger.info(f'Connected to {self.host} \u2705')
                    return self
            except Exception as e:
                error = f'Cannot connect to {self.host}. Re-trying in {self.connection_retry_interval} seconds. Error: {e}'
                time.sleep(self.connection_retry_interval)
                self.logger.info(error)
        error = f'Cannot connect to {self.host}. Maximum number of retries has been reached'
        raise JunosConnectError(error)

    def close(self):
        self.device.close()
        if not self.device.connected:
            self.logger.info(f'Disconnected from {self.host}')

    def show_chassis_routing_engine(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_route_engine_information(*args, **kwargs)

    def show_bgp_summary_for_bgp_group_name(self, group_name) -> etree.ElementTree:
        return self.device.rpc.get_bgp_summary_information(group=group_name)

    def show_bgp_summary(self) -> etree.ElementTree:
        return self.device.rpc.get_bgp_summary_information()

    def show_task_replication(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_routing_task_replication_state(*args, **kwargs)

    def show_version(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_software_information(*args, **kwargs)

    def show_vmhost_hardware(self, slot: int) -> etree.ElementTree:
        if slot == 0:
            return self.device.rpc.get_vmhost_hardware(re0=True)
        elif slot == 1:
            return self.device.rpc.get_vmhost_hardware(re1=True)

    def show_isis_adjacency(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_isis_adjacency_information(*args, **kwargs)

    def show_ospf_neighbor(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_ospf_neighbor_information(*args, **kwargs)

    def show_chassis_fpc_pic_status(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_pic_information(*args, **kwargs)

    def show_chassis_alarms(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_alarm_information(*args, **kwargs)

    def show_configuration(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_config(*args, **kwargs)

    def show_chassis_hardware(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_chassis_inventory(*args, **kwargs)

    def show_bgp_summary(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_bgp_summary_information(*args, **kwargs)

    def show_interfaces(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_interface_information(*args, **kwargs)

    def show_subscribers(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_subscribers(*args, **kwargs)

    def show_l2circuit_connections(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_l2ckt_connection_information(*args, **kwargs)

    def show_ldp_session(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_ldp_session_information(*args, **kwargs)

    def show_route_summary(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_route_summary_information(*args, **kwargs)

    def show_bfd_session(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_bfd_session_information(*args, **kwargs)

    def copy_file_rpc(self, source_path: str, dest_path: str) -> bool:
        return self.fs.cp(source_path, dest_path)

    def request_vmhost_snapshot(self, slot: int) -> etree.Element:
        if slot == 0:
            return self.device.rpc.get_vmhost_snapshot_information(re0=True)
        if slot == 1:
            return self.device.rpc.get_vmhost_snapshot_information(re1=True)
        else:
            raise ValueError("Slot must be an int of 0 or 1")

    def show_vmhost_version_information(self, *args, **kwargs) -> etree.ElementTree:
        return self.device.rpc.get_vmhost_version_information(*args, **kwargs)

    def request_chassis_routing_engine_master_switch(self, *args, **kwargs) -> etree.Element:
        return self.device.rpc.request_chassis_routing_engine_switch(*args, **kwargs)

    def request_vmhost_software_validate(self, package) -> str:
        validation_resp = self.device.rpc.request_vmhost_package_validate(
                {'format': 'text'},
                package_name=package,
                dev_timeout=600,
                ignore_warning='Host software installation has failed',
                )
        return etree.tostring(validation_resp, encoding='unicode', pretty_print='True')

    def request_vmhost_snapshot(self) -> etree.Element:
        return self.device.rpc.request_vmhost_snapshot(dev_timeout=360, ignore_warning=True)

    def request_vmhost_software_add(self, *args, **kwargs) -> etree.Element:
        return self.device.rpc.request_vmhost_package_add(*args, **kwargs)

    def request_vmhost_reboot_re(self, re_number: int) -> etree.Element:
        if re_number == 0:
            return self.device.rpc.request_vmhost_reboot(re0=True, dev_timeout=900)
        elif re_number == 1:
            return self.device.rpc.request_vmhost_reboot(re1=True, dev_timeout=900)
        else:
            raise ValueError("RE number must be an int of 0 or 1")
