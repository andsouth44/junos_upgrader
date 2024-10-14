class JunosUpgradeError(Exception):
    """
    Parent class for all Junos Upgrade related exceptions
    """


class JunosPackageInstallError(JunosUpgradeError):
    """
    Parent class for all Junos install related exceptions
    """


class JunosConfigApplyError(JunosUpgradeError):
    """
    Parent class for all config apply related exceptions
    """


class JunosConfigRescueError(JunosUpgradeError):
    """
    Parent class for all rescue config related exceptions
    """


class JunosRebootError(JunosUpgradeError):
    """
    Parent class for all reboot related exceptions
    """


class JunosValidationError(JunosUpgradeError):
    """
    Parent class for all junos validation related exceptions
    """


class JunosConfigValidationError(JunosUpgradeError):
    """
    Parent class for all validation related exceptions
    """


class JunosReSwitchoverError(JunosUpgradeError):
    """
    Parent class for all RE switchover related exceptions
    """


class JunosRpcProcessorInitError(JunosUpgradeError):
    """
    Parent class for all Rpc Processor Initialization exceptions
    """


class JunosConnectError(JunosUpgradeError):
    """
    Parent class for all device connection exceptions
    """

class JunosInputsError(JunosUpgradeError):
    """
    Parent class for all inputs exceptions
    """