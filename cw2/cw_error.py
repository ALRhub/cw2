class ConfigKeyError(Exception):
    """raised when a key is missing in the configuration."""
    pass


class MissingConfigError(Exception):
    """raise when a config document is missing in the configuration."""
    pass
