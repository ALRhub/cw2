import os
from typing import List, Tuple

import attrdict
import yaml

from cw2.cw_config import cw_conf_keys as KEY
from cw2.cw_data import cw_logging
from cw2.cw_error import MissingConfigError


def get_configs(config_path: str, experiment_selections: List[str]) -> Tuple[dict, dict, List[dict]]:
    """reads and seperates the experiment configs from a yaml file

    Args:
        config_path (str): path to the yaml file
        experiment_selections (List[str]): a list of selected experiment names

    Returns:
        Tuple[dict, dict, List[dict]]: SLURM, DEFAULT, Experiment Configurations
    """
    all_configs = read_yaml(config_path)
    return seperate_configs(all_configs, experiment_selections)


def read_yaml(config_path: str) -> List[dict]:
    """reads a YAML configuration file containing potentially multiple experiments

    Arguments:
        config_path {str}: path to the YAML config file

    Returns:
        List[dict]: all configs found in the yaml file
    """
    if not os.path.exists(config_path):
        raise MissingConfigError("Could not find {}".format(config_path))

    all_configs = []

    with open(config_path, 'r') as f:
        for exp_conf in yaml.load_all(f, yaml.FullLoader):
            if exp_conf is not None:
                all_configs.append(attrdict.AttrDict(exp_conf))
    return all_configs


def seperate_configs(all_configs: List[dict], experiment_selections: List[str]) -> Tuple[
    dict, dict, List[dict]]:
    """seperates the list of individual configs into the 'special' SLURM, DEFAULT and normal experiment configs

    Arguments:
        all_configs {List[dict]}: a list of all configurations
        experiment_selections (List[str], optional): List of specific experiments to run. If None runs all. Defaults to None.

    Returns:
        Tuple[dict, dict, List[dict]]: SLURM, DEFAULT, Experiment Configurations, in this order
    """
    default_config = None
    slurm_config = None
    experiment_configs = []

    for c in all_configs:
        name = c[KEY.NAME]

        if name.lower() == KEY.SLURM:
            slurm_config = c
        elif name.lower() == KEY.DEFAULT:
            default_config = c
        else:
            if experiment_selections is None or name in experiment_selections:
                experiment_configs.append(c)

    if len(experiment_configs) == 0:
        cw_logging.getLogger().warning("No experiment found in config file.")

    return slurm_config, default_config, experiment_configs


def write_yaml(fpath, data):
    """write a yaml file

    Args:
        fpath : path
        data : payload
    """
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    with open(fpath, 'w') as f:
        yaml.dump_all(data, f, default_flow_style=False)
