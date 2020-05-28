import itertools
import os
import re
from copy import deepcopy
from typing import List, Tuple

import attrdict
import yaml

import util


class Config:
    def __init__(self, config_path=None):
        self.slurm_config = None
        self.exp_configs = None

        if config_path is not None:
            self.load_config(config_path)

    def load_config(self, config_path: str):
        """Loads config from YAML file
        The config can include multiple experiments, DEFAULT paramters and a SLURM configuration

        Arguments:
            config_path {str} -- path to a YAML configuraton file
        """

        self.config_path = config_path

        self.slurm_config, self.exp_configs = self.__parse_configs(config_path)

    def __read_config(self, config_path: str) -> List[attrdict.AttrDict]:
        """reads a YAML configuration file containing potentially multiple experiments

        Arguments:
            config_path {str} -- path to the YAML config file

        Returns:
            List[attrdict.AttrDict] -- all configs found in the yaml file
        """
        all_configs = []

        with open(config_path, 'r') as f:
            for exp_conf in yaml.load_all(f, yaml.FullLoader):
                all_configs.append(attrdict.AttrDict(exp_conf))
        return all_configs

    def __parse_configs(self, config_path: str) -> Tuple[attrdict.AttrDict, attrdict.AttrDict]:
        """parse the config file, including seperating the SLURM configuration and expanding grid / list search params

        Arguments:
            config_path {str} -- path to the configuration file

        Returns:
            Tuple[attrdict.AttrDict, attrdict.AttrDict] -- SLURM configuration, list of expanded experiment configurations
        """
        all_configs = self.__read_config(self.config_path)

        slurm_config, default_config, experiment_configs = self.__seperate_configs(
            all_configs)

        experiment_configs = self.__merge_default(
            default_config, experiment_configs)

        experiment_configs = self.__expand_experiments(experiment_configs)

        return slurm_config, experiment_configs

    def __seperate_configs(self, all_configs: List[attrdict.AttrDict]) -> Tuple[attrdict.AttrDict, attrdict.AttrDict, List[attrdict.AttrDict]]:
        """seperates the list of individual configs into the 'special' SLURM, DEFAULT and normal experiment configs

        Arguments:
            all_configs {List[attrdict.AttrDict]} -- a list of all configurations

        Returns:
            Tuple[attrdict.AttrDict, attrdict.AttrDict, List[attrdict.AttrDict]] -- SLURM, DEFAULT, Experiment Configurations, in this order
        """
        default_config = None
        slurm_config = None
        experiment_configs = []

        for c in all_configs:
            name = c.name.lower()

            if name == 'slurm':
                slurm_config = c
            elif name == 'default':
                default_config = c
            else:
                experiment_configs.append(c)

        return slurm_config, default_config, experiment_configs

    def __merge_default(self, default_config: attrdict.AttrDict, experiment_configs: List[attrdict.AttrDict]) -> List[attrdict.AttrDict]:
        """merges each individual experiment configuration with the default parameters

        Arguments:
            default_config {attrdict.AttrDict} -- default configuration parameters
            experiment_configs {List[attrdict.AttrDict]} -- a list of individual experiment configurations

        Returns:
            List[attrdict.AttrDict] -- a list of all experiment configurations
        """
        expanded_exp_configs = []
        for c in experiment_configs:
            merge_c = deepcopy(default_config)
            merge_c = util.deep_update(merge_c, c)
            expanded_exp_configs.append(merge_c)
        return expanded_exp_configs

    # TODO: "Expand 2 Jobs"-Name ??
    def __expand_experiments(self, experiment_configs: List[attrdict.AttrDict]) -> List[attrdict.AttrDict]:
        """Expand the experiment configuration with concrete parameter instantiations
        TODO: Copied from cluster_work_v1. Maybe rework??

        Arguments:
            experiment_configs {List[attrdict.AttrDict]} -- List with experiment configs

        Returns:
            List[attrdict.AttrDict] -- List of experiment configs, with set parameters
        """

        # get all options that are iteratable and build all combinations (grid) or tuples (list)
        expanded_config_list = []
        for config in experiment_configs:
            if 'grid' in config or 'list' in config:
                if 'grid' in config:
                    # if we want a grid then we choose the product of all parameters
                    iter_fun = itertools.product
                    key = 'grid'
                else:
                    # if we want a list then we zip the parameters together
                    iter_fun = zip
                    key = 'list'

                # TODO add support for both list and grid

                # convert list/grid dictionary into flat dictionary, where the key is a tuple of the keys and the
                # value is the list of values
                tuple_dict = util.flatten_dict_to_tuple_keys(config[key])
                _param_names = ['.'.join(t) for t in tuple_dict]

                # create a new config for each parameter setting
                for values in iter_fun(*tuple_dict.values()):
                    # create config file for
                    _config = deepcopy(config)
                    del _config[key]

                    _converted_name = convert_param_names(_param_names, values)
                    _config['_experiment_path'] = config.path

                    _config['path'] = os.path.join(
                        config.path, _converted_name)
                    _config['experiment_name'] = _config.name
                    _config['name'] += '__' + _converted_name

                    # Use dedicated logging path or use "internal" one
                    if 'log_path' in config:
                        _config['log_path'] = os.path.join(
                            config.log_path, config.name, _converted_name, 'log')
                    else:
                        _config['log_path'] = os.path.join(
                            _config.path, 'log')

                    for i, t in enumerate(tuple_dict.keys()):
                        util.insert_deep_dictionary(
                            _config['params'], t, values[i])
                    expanded_config_list.append(_config)
            else:
                expanded_config_list.append(config)

        return expanded_config_list


def convert_param_names(_param_names, values) -> str:
    """create new shorthand name derived from parameter and value association
    TODO: Argument Descriptions
    Arguments:
        _param_names {[type]} -- [description]
        values {[type]} -- [description]

    Returns:
        str -- shorthand name
    """

    _converted_name = '_'.join("{}{}".format(
        util.shorten_param(k), v) for k, v in zip(_param_names, values))
    # _converted_name = re.sub("[' \[\],()]", '', _converted_name)
    _converted_name = re.sub("[' ]", '', _converted_name)
    _converted_name = re.sub('["]', '', _converted_name)
    _converted_name = re.sub("[(\[]", '_', _converted_name)
    _converted_name = re.sub("[)\]]", '', _converted_name)
    _converted_name = re.sub("[,]", '_', _converted_name)
    return _converted_name
