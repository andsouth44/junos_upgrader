class JunosUpgradeError(Exception):
    """
    Parent class for all Junos Upgrade related exceptions
    """


class JunosPackageInstallError(JunosUpgradeError):
    """
    Parent class for all Junos install related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosConfigApplyError(JunosUpgradeError):
    """
    Parent class for all config apply related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosConfigRescueError(JunosUpgradeError):
    """
    Parent class for all rescue config related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosRebootError(JunosUpgradeError):
    """
    Parent class for all reboot related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosValidationError(JunosUpgradeError):
    """
    Parent class for all junos validation related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosConfigValidationError(JunosUpgradeError):
    """
    Parent class for all validation related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosReSwitchoverError(JunosUpgradeError):
    """
    Parent class for all RE switchover related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosRpcProcessorInitError(JunosUpgradeError):
    """
    Parent class for all Rpc Processor Initialization exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosConnectError(JunosUpgradeError):
    """
    Parent class for all device connection exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)

class JunosInputsError(JunosUpgradeError):
    """
    Parent class for all inputs exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)