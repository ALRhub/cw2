import itertools
import os
import re
from copy import deepcopy
from typing import List, Tuple

import attrdict
import yaml

from cw2 import util
from cw2.cw_data import cw_logging
from cw2.cw_error import ConfigKeyError, MissingConfigError


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

        self.slurm_config, self.exp_configs = self._parse_configs(
            config_path, experiment_selections)

    def _read_config(self, config_path: str) -> List[attrdict.AttrDict]:
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

    def _parse_configs(self, config_path: str, experiment_selections: List[str] = None) -> Tuple[attrdict.AttrDict, List[attrdict.AttrDict]]:
        """parse the config file, including seperating the SLURM configuration and expanding grid / list search params

        Arguments:
            config_path {str} -- path to the configuration file
            experiment_selections (List[str], optional): List of specific experiments to run. If None runs all. Defaults to None.

        Returns:
            Tuple[attrdict.AttrDict, attrdict.AttrDict] -- SLURM configuration, list of expanded experiment configurations
        """
        all_configs = self._read_config(config_path)

        slurm_config, default_config, experiment_configs = self._seperate_configs(
            all_configs, experiment_selections)

        experiment_configs = self._merge_default(
            default_config, experiment_configs)

        experiment_configs = self._import_external_yml(experiment_configs)

        experiment_configs = self._expand_experiments(experiment_configs)
        experiment_configs = self._unroll_exp_reps(experiment_configs)

        return slurm_config, experiment_configs

    def _seperate_configs(self, all_configs: List[attrdict.AttrDict], experiment_selections: List[str]) -> Tuple[attrdict.AttrDict, attrdict.AttrDict, List[attrdict.AttrDict]]:
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

    def _merge_default(self, default_config: attrdict.AttrDict, experiment_configs: List[attrdict.AttrDict]) -> List[attrdict.AttrDict]:
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

    def _import_external_yml(self, experiment_configs: List[attrdict.AttrDict], traversal_dict: dict = None) -> List[attrdict.AttrDict]:
        # Create Traversal Dict Root
        abs_path = None

        if traversal_dict is None:
            abs_path = os.path.abspath(self.config_path)
            traversal_dict = {
                abs_path: []
            }
        

        resolved_configs = []
        for config in experiment_configs:
            if "import_path" not in config:
                resolved_configs.append(config)
                continue

            if abs_path is not None:
                traversal_dict[abs_path].append(config["name"])
            
            # Get absolute Path for import
            import_yml = os.path.abspath(
                os.path.join(
                    os.path.dirname(self.config_path),
                    config["import_path"]
                )
            )

            all_external_configs = self._read_config(import_yml)

            if "import_exp" in config:
                ext_exp = config["import_exp"]
                
                # Recursion Anchor:
                if import_yml in traversal_dict and ext_exp in traversal_dict[import_yml]:
                    raise ConfigKeyError("Cyclic YML import with {} : {}".format(import_yml, ext_exp))

                # Default Merge External
                _, ext_default, ext_selection = self._seperate_configs(
                    all_external_configs, [ext_exp])

                if len(ext_selection) == 0:
                    raise MissingConfigError(
                        "Could not import {} from {}".format(ext_exp, import_yml))
                
                ext_def_merge = self._merge_default(ext_default, ext_selection)[0]
            else:
                # Recursion Anchor:
                if import_yml in traversal_dict and "DEFAULT" in traversal_dict[import_yml]:
                    raise ConfigKeyError("Cyclic YML import with {} : {}".format(import_yml, "DEFAULT"))
                _, ext_def_merge, _ = self._seperate_configs(all_external_configs, None)

            
            # Register new Anchor
            if import_yml not in traversal_dict:
                traversal_dict[import_yml] = []
            if "import_exp" in config:
                traversal_dict[import_yml].append(config["import_exp"])
            else:
                traversal_dict[import_yml].append("DEFAULT")
            
            # Recursion call
            ext_resolved_conf = self._import_external_yml([ext_def_merge], traversal_dict)[0]

            # Delete Anchor when coming back
            del traversal_dict[import_yml]

            resolved_configs.append(self._merge_default(ext_resolved_conf, [config])[0])
        return resolved_configs



    def _expand_experiments(self, _experiment_configs: List[attrdict.AttrDict]) -> List[attrdict.AttrDict]:
        """Expand the experiment configuration with concrete parameter instantiations

        Arguments:
            experiment_configs {List[attrdict.AttrDict]} -- List with experiment configs

        Returns:
            List[attrdict.AttrDict] -- List of experiment configs, with set parameters
        """

        # get all options that are iteratable and build all combinations (grid) or tuples (list)
        experiment_configs = deepcopy(_experiment_configs)
        expanded_config_list = []
        for config in experiment_configs:
            iter_func = None
            key = None

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

            # In-Between Step to solve grid AND list combinations
            if all(k in config for k in ("grid", "list")):
                iter_func = zip
                key = 'list'

                experiment_configs += self._params_combine(
                    config, key, iter_func)
                continue

            if 'grid' in config:
                iter_func = itertools.product
                key = 'grid'

            if 'list' in config:
                iter_func = zip
                key = 'list'

            expansion = self._params_combine(config, key, iter_func)

            if 'ablative' in config:
                expansion += self._ablative_expand(expansion)

            expanded_config_list += expansion
        return self._normalize_expanded_paths(expanded_config_list)

    def _params_combine(self, config: attrdict.AttrDict, key: str, iter_func) -> List[attrdict.AttrDict]:
        """combines experiment parameter with its list/grid combinations

        Args:
            config (attrdict.AttrDict): an single experiment configuration
            key (str): the combination key, e.g. 'list' or 'grid'
            iter_func: itertool-like function for creating the combinations

        Returns:
            List[attrdict.AttrDict]: list of parameter-combined experiments
        """
        if iter_func is None:
            return [config]

        combined_configs = []
        # convert list/grid dictionary into flat dictionary, where the key is a tuple of the keys and the
        # value is the list of values
        tuple_dict = util.flatten_dict_to_tuple_keys(config[key])
        _param_names = ['.'.join(t) for t in tuple_dict]

        param_lengths = map(len, tuple_dict.values())
        if key == "list" and len(set(param_lengths)) != 1:
            cw_logging.getLogger().warning(
                "list params of experiment \"{}\" are not of equal length.".format(config['name']))

        # create a new config for each parameter setting
        for values in iter_func(*tuple_dict.values()):
            _config = deepcopy(config)

            # Remove Grid/List Argument
            del _config[key]

            if "params" not in _config:
                _config["params"] = {}

            # Expand Grid/List Parameters
            for i, t in enumerate(tuple_dict.keys()):
                util.insert_deep_dictionary(
                    _config['params'], t, values[i])

            _config = self._extend_config_name(_config, _param_names, values)
            combined_configs.append(_config)
        return combined_configs

    def _ablative_expand(self, conf_list: List[attrdict.AttrDict]) -> List[attrdict.AttrDict]:
        """expand experiment configurations according to the "ablative" design

        Args:
            conf_list (List[attrdict.AttrDict]): a list of experiment configurations

        Returns:
            List[attrdict.AttrDict]: list of experiment configurations with ablative expansion
        """
        combined_configs = []
        for config in conf_list:
            tuple_dict = util.flatten_dict(config['ablative'])

            for key in tuple_dict.keys():
                _config = deepcopy(config)

                if "params" not in _config:
                    _config["params"] = {}

                util.insert_deep_dictionary(
                    _config['params'], key, tuple_dict[key]
                )

                _config = self._extend_config_name(
                    _config, [key], [tuple_dict[key]])
                combined_configs.append(_config)
        return combined_configs

    def _extend_config_name(self, config: attrdict.AttrDict, param_names: list, values: list) -> attrdict.AttrDict:
        """extend an experiment name with a shorthand derived from the parameters and their values

        Args:
            config (attrdict.AttrDict): experiment config
            param_names (list): list of parameter names
            values (list): list of parameter values

        Returns:
            attrdict.AttrDict: experiment config with extended name
        """
        # Rename and append
        _converted_name = convert_param_names(param_names, values)

        # Use __ only once as a seperator
        sep = '__'
        if '_experiment_name' in config and sep in config['_experiment_name']:
            sep = '_'

        config['_experiment_name'] = config['_experiment_name'] + \
            sep + _converted_name
        config['_nested_dir'] = config['name']
        return config

    def _normalize_expanded_paths(self, expanded_config_list: List[attrdict.AttrDict]) -> List[attrdict.AttrDict]:
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

    def _unroll_exp_reps(self, exp_configs: List[attrdict.AttrDict]) -> List[attrdict.AttrDict]:
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


def convert_param_names(_param_names: list, values: list) -> str:
    """create new shorthand name derived from parameter and value association
    Arguments:
        _param_names (list): parameter names for the experiment
        values (list): concrete values for each parameter

    Returns:
        str: shorthand name
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
