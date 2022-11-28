import os
import socket
from typing import List, Tuple

import cw2.cw_config.cw_conf_keys as KEY
from cw2.cw_config import conf_io, conf_resolver, conf_path, conf_unfolder


class Config:
    def __init__(self, config_path: str = None,
                 experiment_selections: List[str] = None,
                 debug: bool = False, debug_all: bool = False):
        self.slurm_config = None
        self.exp_configs = None

        self.f_name = None
        self.config_path = config_path
        self.exp_selections = experiment_selections

        if config_path is not None:
            self.load_config(config_path, experiment_selections, debug, debug_all)

    def load_config(self,
                    config_path: str,
                    experiment_selections: List[str] = None,
                    debug: bool = False,
                    debug_all: bool = False) -> None:
        """Loads config from YAML file
        The config can include multiple experiments, DEFAULT paramters and a SLURM configuration

        Arguments:
            config_path {str} -- path to a YAML configuraton file
            experiment_selections (List[str], optional): List of specific experiments to run. If None runs all. Defaults to None.
        """

        self.config_path = config_path
        self.f_name = os.path.basename(config_path)

        self.exp_selections = experiment_selections

        slurm_configs, self.exp_configs = self._parse_configs(
            config_path, experiment_selections, debug, debug_all)
        self.slurm_config = self._filter_slurm_configs(slurm_configs)

    @staticmethod
    def _filter_slurm_configs(slurm_configs: List[dict]) -> dict:
        """Returns machine/cluster specific slurm conf (identified by hostname)
           if available, otherwise returns the default one (if available)

        Arguments:
            slurm_configs: (list[dict]) -- all slurm configurations found in the config file
        Returns:
            dict -- SLURM configuration to use for this machine
        """
        default_conf = None
        specific_conf = None
        hostname = socket.gethostname().lower()
        print("Hostname: {}".format(hostname))
        for c in slurm_configs:
            print("Found slurm config: {}".format(c[KEY.NAME]))
            if c[KEY.NAME].lower() == KEY.SLURM.lower():
                print("Seeting default slurm config")
                default_conf = c
            elif c[KEY.NAME].split("_")[1].lower() in hostname:
                print("Setting specific slurm config: {}".format(c[KEY.NAME]))
                specific_conf = c
                specific_conf[KEY.NAME] = KEY.SLURM

        return specific_conf if specific_conf is not None else default_conf

    def _parse_configs(self, config_path: str, experiment_selections: List[str] = None,
                       debug: bool = False, debug_all: bool = False) \
            -> Tuple[List[dict], List[dict]]:
        """parse the config file, including separating the SLURM configuration and expanding grid / list search params

        Arguments:
            config_path {str} -- path to the configuration file
            experiment_selections (List[str], optional): List of specific experiments to run. If None runs all. Defaults to None.

        Returns:
            Tuple[dict, dict] -- SLURM configuration, list of expanded experiment configurations
        """

        slurm_config, default_config, experiment_configs = conf_io.get_configs(config_path, experiment_selections)

        experiment_configs = conf_resolver.resolve_dependencies(default_config, experiment_configs,
                                                                self.config_path)
        experiment_configs = conf_unfolder.unfold_exps(experiment_configs, debug, debug_all)

        return slurm_config, experiment_configs

    def to_yaml(self, dir_path: str = "", relpath: bool = True) -> None:
        """write config back into a YAML file.

        Args:
            fpath (str, optional): path to write to. Will be written to outputdir unless specified differently. Defaults to "".
            relpath (bool, optional): Use relative paths only. Usefull for loading functionality. Defaults to True.
        """

        if dir_path == "":
            dir_path = self.exp_configs[0][KEY.i_BASIC_PATH]

        original_yml_name = os.path.splitext(self.f_name)[0]


        # List so it can be merged easily
        slurm_config = []
        if self.slurm_config is not None:
            slurm_config.append(dict(self.slurm_config))

        readable_configs = self._readable_exp_configs(relpath)

        # Save all named experiment configs in subdir
        grouped_configs = self._group_configs_by_name(readable_configs)
        for exp_name in grouped_configs.keys():
            fpath = os.path.join(dir_path, exp_name, "relative_{}_{}.yml".format(
                original_yml_name, exp_name))
            conf_io.write_yaml(fpath, slurm_config + grouped_configs[exp_name])

        # Save global configs
        fpath = os.path.join(dir_path, "relative_" + self.f_name)

        if self.exp_selections is not None:
            fpath = os.path.splitext(
                fpath)[0] + "_" + "_".join(self.exp_selections) + ".yml"

        # Merge into single list
        data = slurm_config + readable_configs
        conf_io.write_yaml(fpath, data)

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
                c = conf_path.make_rel_paths(c, c[KEY.i_BASIC_PATH])
            res.append(c)
        return res

    def _group_configs_by_name(self, configs: List[dict]) -> dict:
        grouped_configs = {}
        for c in configs:
            name = c[KEY.NAME]
            if name not in grouped_configs:
                grouped_configs[name] = [c]
            else:
                grouped_configs[name].append(c)
        return grouped_configs
