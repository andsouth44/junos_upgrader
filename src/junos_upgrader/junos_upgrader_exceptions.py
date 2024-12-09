class JunosUpgradeError(Exception):
    """
    Parent class for all Junos Upgrade related exceptions
    """


class JunosPackageInstallError(JunosUpgradeError):
    """
    Custom error class for all Junos install related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosConfigApplyError(JunosUpgradeError):
    """
    Custom error class for all config apply related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosConfigRescueError(JunosUpgradeError):
    """
    Custom error class for all rescue config related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosRebootError(JunosUpgradeError):
    """
    Custom error class for all reboot related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosValidationError(JunosUpgradeError):
    """
    Custom error class for all junos validation related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosConfigValidationError(JunosUpgradeError):
    """
    Custom error class for all validation related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosReSwitchoverError(JunosUpgradeError):
    """
    Custom error class for all RE switchover related exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosRpcProcessorInitError(JunosUpgradeError):
    """
    Custom error class for all Rpc Processor Initialization exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosConnectError(JunosUpgradeError):
    """
    Custom error class for all device connection exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)


class JunosInputsError(JunosUpgradeError):
    """
    Custom error class for all inputs exceptions
    """
    def __init__(self, error_message: str):
        super().__init__(error_message)
