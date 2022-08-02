class ConfigKeyError(Exception):
    """raised when a key is missing in the configuration."""
    pass


class MissingConfigError(Exception):
    """raise when a config document is missing in the configuration."""
    pass


class ExperimentNotFoundError(Exception):
    """raise when experiment selection could not be found in the configuration"""
    pass


class ExperimentSurrender(Exception):
    def __init__(self, payload: dict = None):
        if payload is None:
            payload = {}
        self.payload = payload
