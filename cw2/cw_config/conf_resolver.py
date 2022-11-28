import os
from copy import deepcopy
from typing import List

from cw2 import util
from cw2.cw_config import conf_io
from cw2.cw_config import cw_conf_keys as KEY
from cw2.cw_error import ConfigKeyError, MissingConfigError


def resolve_dependencies(default_config: dict, experiment_configs: List[dict], conf_path: str) -> List[dict]:
    """resolves all internal (DEFAULT) and external (import) dependencies

    Args:
        default_config (dict): DEFAULT exp configuration
        experiment_configs (List[dict]): list of experiment configurations
        conf_path (str): path of the "calling" config file

    Returns:
        List[dict]: list of experiment configurations without unresolved dependencies
    """
    experiment_configs = merge_default(default_config, experiment_configs)

    abs_path = os.path.abspath(conf_path)
    experiment_configs = import_external_yml(experiment_configs, abs_path)
    return experiment_configs


def merge_default(default_config: dict, experiment_configs: List[dict]) -> List[dict]:
    """merges each individual experiment configuration with the default parameters

    Arguments:
        default_config {dict} -- default configuration parameters
        experiment_configs {List[dict]} -- a list of individual experiment configurations

    Returns:
        List[dict] -- a list of all experiment configurations
    """
    if default_config is None:
        return experiment_configs

    expanded_exp_configs = []
    for c in experiment_configs:
        merge_c = deepcopy(default_config)
        merge_c = util.deep_update(merge_c, c)
        expanded_exp_configs.append(merge_c)
    return expanded_exp_configs


def import_external_yml(experiment_configs: List[dict], abs_path: str, traversal_dict: dict = None) -> List[dict]:
    """recursively imports external yaml files
    The external yaml files are first merged with their own DEFAULT configuration,
    then their external dependencies get resolved.

    Args:
        experiment_configs (List[dict]): list of experiment configurations
        abs_path (str): Absolute file path of the YAML file which gets resolved..
        traversal_dict (dict, optional): Dictionary(abs_path, exp_name) Serves as a failsafe to detect cyclic imports.
                                         Defaults to None.

    Raises:
        ConfigKeyError: if a cyclic import is attempted
        MissingConfigError: if the linked config cannot be found

    Returns:
        List[dict]: a list of resolved experiment configurations.
    """

    if traversal_dict is None:
        traversal_dict = {
            abs_path: []
        }

    resolved_configs = []
    for config in experiment_configs:
        # SKIP
        if KEY.IMPORT_PATH not in config and KEY.IMPORT_EXP not in config:
            resolved_configs.append(config)
            continue

        # Record current step
        traversal_dict[abs_path].append(config[KEY.NAME])

        import_yml = abs_path
        if KEY.IMPORT_PATH in config:
            import_yml = config[KEY.IMPORT_PATH]

        # Get absolute Path for import
        import_yml = os.path.abspath(
            os.path.join(os.path.dirname(abs_path), import_yml))

        all_external_configs = conf_io.read_yaml(import_yml)

        ext_exp_name = KEY.DEFAULT
        if custom_import_exp(config):
            ext_exp_name = config[KEY.IMPORT_EXP]

        # Recursion Anchor:
        if import_yml in traversal_dict and ext_exp_name in traversal_dict[import_yml]:
            raise ConfigKeyError(
                "Cyclic YML import with {} : {}".format(import_yml, ext_exp_name))

        # Default Merge External
        _, external, ext_selection = conf_io.separate_configs(all_external_configs, [ext_exp_name], suppress=True)

        if custom_import_exp(config):
            if len(ext_selection) == 0:
                raise MissingConfigError(
                    "Could not import {} from {}".format(ext_exp_name, import_yml))

            external = merge_default(external, ext_selection)[0]

        # Register new Anchor
        if import_yml not in traversal_dict:
            traversal_dict[import_yml] = []
        traversal_dict[import_yml].append(ext_exp_name)

        # Recursion call
        ext_resolved_conf = import_external_yml([external], import_yml, traversal_dict)[0]

        # Delete Anchor when coming back
        del traversal_dict[import_yml]

        resolved_conf = merge_default(ext_resolved_conf, [config])[0]
        resolved_conf = archive_import_keys(resolved_conf)
        resolved_configs.append(resolved_conf)
    return resolved_configs


def custom_import_exp(config: dict) -> bool:
    """check if the config uses a custom import_exp

    Args:
        config (dict): experiment configuration

    Returns:
        bool: True if a custom import_exp key is defined
    """
    if KEY.IMPORT_EXP not in config:
        return False
    if config[KEY.IMPORT_EXP].lower() == KEY.DEFAULT:
        return False
    return True


def archive_import_keys(config: dict) -> dict:
    """
    Args:
        config (dict): experiment configuration


    Returns:
        dict: experiment configuration with archived import keys
    """
    removal_keys = [KEY.IMPORT_PATH, KEY.IMPORT_EXP]
    replacement_keys = [KEY.i_IMPORT_PATH_ARCHIVE, KEY.i_IMPORT_EXP_ARCHIVE]

    for removal, replacement in zip(removal_keys, replacement_keys):
        if removal in config:
            config[replacement] = config[removal]
            del config[removal]
    return config