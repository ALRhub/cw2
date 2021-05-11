import itertools
import os
import re
from copy import deepcopy
from typing import List, Tuple

import attrdict
import yaml

from cw2 import util
from cw2.cw_data import cw_logging


class Config:
    def __init__(self, config_path=None, experiment_selections=None):
        self.slurm_config = None
        self.exp_configs = None

        if config_path is not None:
            self.load_config(config_path, experiment_selections)

    def load_config(self, config_path: str, experiment_selections: List[str] = None):
        """Loads config from YAML file
        The config can include multiple experiments, DEFAULT paramters and a SLURM configuration

        Arguments:
            config_path {str} -- path to a YAML configuraton file
            experiment_selections (List[str], optional): List of specific experiments to run. If None runs all. Defaults to None.
        """

        self.config_path = config_path
        self.f_name = os.path.basename(config_path)

        self.exp_selections = experiment_selections

        self.slurm_config, self.exp_configs = self.__parse_configs(
            config_path, experiment_selections)

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
                if exp_conf is not None:
                    all_configs.append(attrdict.AttrDict(exp_conf))
        return all_configs

    def __parse_configs(self, config_path: str, experiment_selections: List[str] = None) -> Tuple[attrdict.AttrDict, List[attrdict.AttrDict]]:
        """parse the config file, including seperating the SLURM configuration and expanding grid / list search params

        Arguments:
            config_path {str} -- path to the configuration file
            experiment_selections (List[str], optional): List of specific experiments to run. If None runs all. Defaults to None.

        Returns:
            Tuple[attrdict.AttrDict, attrdict.AttrDict] -- SLURM configuration, list of expanded experiment configurations
        """
        all_configs = self.__read_config(self.config_path)

        slurm_config, default_config, experiment_configs = self.__seperate_configs(
            all_configs, experiment_selections)

        experiment_configs = self.__merge_default(
            default_config, experiment_configs)

        experiment_configs = self.__expand_experiments(experiment_configs)
        experiment_configs = self.__unroll_exp_reps(experiment_configs)

        return slurm_config, experiment_configs

    def __seperate_configs(self, all_configs: List[attrdict.AttrDict], experiment_selections: List[str]) -> Tuple[attrdict.AttrDict, attrdict.AttrDict, List[attrdict.AttrDict]]:
        """seperates the list of individual configs into the 'special' SLURM, DEFAULT and normal experiment configs

        Arguments:
            all_configs {List[attrdict.AttrDict]} -- a list of all configurations
            experiment_selections (List[str], optional): List of specific experiments to run. If None runs all. Defaults to None.

        Returns:
            Tuple[attrdict.AttrDict, attrdict.AttrDict, List[attrdict.AttrDict]] -- SLURM, DEFAULT, Experiment Configurations, in this order
        """
        default_config = None
        slurm_config = None
        experiment_configs = []

        for c in all_configs:
            name = c["name"]

            if name.lower() == 'slurm':
                slurm_config = c
            elif name.lower() == 'default':
                default_config = c
            else:
                if experiment_selections is None or name in experiment_selections:
                    experiment_configs.append(c)

        if len(experiment_configs) == 0:
            cw_logging.getLogger().warning("No experiment found in config file.")

        return slurm_config, default_config, experiment_configs

    def __merge_default(self, default_config: attrdict.AttrDict, experiment_configs: List[attrdict.AttrDict]) -> List[attrdict.AttrDict]:
        """merges each individual experiment configuration with the default parameters

        Arguments:
            default_config {attrdict.AttrDict} -- default configuration parameters
            experiment_configs {List[attrdict.AttrDict]} -- a list of individual experiment configurations

        Returns:
            List[attrdict.AttrDict] -- a list of all experiment configurations
        """
        if default_config is None:
            return experiment_configs

        expanded_exp_configs = []
        for c in experiment_configs:
            merge_c = deepcopy(default_config)
            merge_c = util.deep_update(merge_c, c)
            expanded_exp_configs.append(merge_c)
        return expanded_exp_configs

    def __expand_experiments(self, experiment_configs: List[attrdict.AttrDict]) -> List[attrdict.AttrDict]:
        """Expand the experiment configuration with concrete parameter instantiations

        Arguments:
            experiment_configs {List[attrdict.AttrDict]} -- List with experiment configs

        Returns:
            List[attrdict.AttrDict] -- List of experiment configs, with set parameters
        """

        # get all options that are iteratable and build all combinations (grid) or tuples (list)
        expanded_config_list = []
        for config in experiment_configs:
            # Set Default Values
            # save path argument from YML for grid modification
            if '_basic_path' not in config:
                config['_basic_path'] = config["path"]
            # save name argument from YML for grid modification
            if '_experiment_name' not in config:
                config['_experiment_name'] = config["name"]
            # add empty string for parent DIR in case of grid
            if '_nested_dir' not in config:
                config['_nested_dir'] = ''

            if 'grid' in config:
                config = self.__grid_to_list(config)

            if 'list' in config:
                iter_func = zip
                key = 'list'
                expanded_config_list += self.__params_combine(
                    config, key, iter_func)
            else:
                expanded_config_list.append(config)
        return self.__normalize_expanded_paths(expanded_config_list)

    def __grid_to_list(self, config: attrdict.AttrDict):
        tuple_dict = util.flatten_dict_to_tuple_keys(config['grid'])
        _param_names = ['.'.join(t) for t in tuple_dict]
        for values in itertools.product(*tuple_dict.values()):
            for i, t in enumerate(tuple_dict.keys()):
                util.append_deep_dictionary(
                    config['list'], t, values[i]
                )
        del config['grid']
        return config

    def __params_combine(self, config: attrdict.AttrDict, key: str, iter_func) -> List[attrdict.AttrDict]:
        combined_configs = []
        # convert list/grid dictionary into flat dictionary, where the key is a tuple of the keys and the
        # value is the list of values
        tuple_dict = util.flatten_dict_to_tuple_keys(config[key])
        _param_names = ['.'.join(t) for t in tuple_dict]

        param_lengths = map(len, tuple_dict.values())
        if len(set(param_lengths)) != 1:
            cw_logging.getLogger().warning("list params of experiment \"{}\" are not of equal length.".format(config['name']))

        # create a new config for each parameter setting
        for values in iter_func(*tuple_dict.values()):
            _config = deepcopy(config)

            # Remove Grid/List Argument
            del _config[key]

            # Expand Grid/List Parameters
            for i, t in enumerate(tuple_dict.keys()):
                util.insert_deep_dictionary(
                    _config['params'], t, values[i])

            # Rename and append
            _converted_name = convert_param_names(_param_names, values)
            _config['_experiment_name'] = _config['name'] + \
                '__' + _converted_name
            _config['_nested_dir'] = _config['name']
            combined_configs.append(_config)
        return combined_configs

    def __normalize_expanded_paths(self, expanded_config_list: List[attrdict.AttrDict]) -> List[attrdict.AttrDict]:
        """normalizes path key after expansion operation

        Args:
            expanded_config_list (List[attrdict.AttrDict]): list fo expanded experiment configs

        Returns:
            List[attrdict.AttrDict]: noramlized expanded experiment configs
        """
        # Set Path and LogPath Args depending on the name
        for _config in expanded_config_list:
            _config['path'] = os.path.join(
                _config["_basic_path"], _config['_nested_dir'], _config["_experiment_name"])
            _config['log_path'] = os.path.join(_config["path"], 'log')
        return expanded_config_list

    def __unroll_exp_reps(self, exp_configs: List[attrdict.AttrDict]) -> List[attrdict.AttrDict]:
        """unrolls experiment repetitions into their own configuration object

        Args:
            exp_configs (List[attrdict.AttrDict]): List of experiment configurations

        Returns:
            List[attrdict.AttrDict]: List of unrolled experiment configurations
        """
        unrolled_exps = []

        for config in exp_configs:
            if '_rep_idx' in config:
                unrolled_exps.append(config)
                continue

            for r in range(config['repetitions']):
                c = deepcopy(config)
                c['_rep_idx'] = r
                c['_rep_log_path'] = os.path.join(
                    c["log_path"], 'rep_{:02d}'.format(r))
                unrolled_exps.append(c)
        return unrolled_exps

    def to_yaml(self, dir_path: str = "", relpath: bool = True) -> None:
        """write config back into a YAML file.

        Args:
            fpath (str, optional): path to write to. Will be written to outputdir unless specified differently. Defaults to "".
            relpath (bool, optional): Use relative paths only. Usefull for loading functionality. Defaults to True.
        """

        if dir_path == "":
            dir_path = self.exp_configs[0]["_basic_path"]

        original_yml_name = os.path.splitext(self.f_name)[0]

        # List so it can be merged easily
        slurm_config = [dict(self.slurm_config)]

        readable_configs = self._readable_exp_configs(relpath)

        # Save all named experiment configs in subdir
        grouped_configs = self._group_configs_by_name(readable_configs)
        for exp_name in grouped_configs.keys():
            fpath = os.path.join(dir_path, exp_name, "relative_{}_{}.yml".format(
                original_yml_name, exp_name))
            write_yaml(fpath, slurm_config + grouped_configs[exp_name])

        # Save global configs
        fpath = os.path.join(dir_path, "relative_" + self.f_name)

        if self.exp_selections is not None:
            fpath = os.path.splitext(
                fpath)[0] + "_" + "_".join(self.exp_selections) + ".yml"

        # Merge into single list
        data = slurm_config + readable_configs
        write_yaml(fpath, data)

    def _readable_exp_configs(self, relpath: bool = True) -> List[dict]:
        """Internal function to get more readable objects when written as yaml
        Converts to dict() and optionally use relative paths only
        Args:
            relpath (bool, optional): True if the new experiment config file should use relative paths only. Defaults to True.

        Returns:
            List[dict]: list of transformed experiment configuration dicts
        """
        res = []
        for exp in self.exp_configs:
            # Convert attrdict to dict for prettier yaml write
            c = dict(exp)
            if relpath:
                c = self._make_rel_paths(c, c["_basic_path"])
            res.append(c)
        return res

    def _make_rel_paths(self, config: dict, base_path: str) -> dict:
        c = config.copy()
        _basic_path = base_path
        c["log_path"] = os.path.join(
            ".", os.path.relpath(c["log_path"], _basic_path))
        c["_rep_log_path"] = os.path.join(
            ".", os.path.relpath(c["_rep_log_path"], _basic_path))
        c["path"] = os.path.join(
            ".", os.path.relpath(c["path"], _basic_path))
        c["_basic_path"] = os.path.join(
            ".", os.path.relpath(c["_basic_path"], _basic_path))
        return c

    def _group_configs_by_name(self, configs: List[dict]) -> dict:
        grouped_configs = {}
        for c in configs:
            name = c['name']
            if name not in grouped_configs:
                grouped_configs[name] = [c]
            else:
                grouped_configs[name].append(c)
        return grouped_configs


def convert_param_names(_param_names, values) -> str:
    """create new shorthand name derived from parameter and value association
    Arguments:
        _param_names -- parameter names for the experiment
        values -- concrete values for each parameter

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


def write_yaml(fpath, data):
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    with open(fpath, 'w') as f:
        yaml.dump_all(data, f, default_flow_style=False)
