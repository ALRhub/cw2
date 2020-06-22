import os
import shutil
from typing import List

import attrdict
from copy import deepcopy
from cw2 import cw_logging, experiment


class Job():
    def __init__(self, exp_config: attrdict.AttrDict, reps: List[int], exp_cls: experiment.AbstractExperiment.__class__, logger: cw_logging.AbstractLogger, delete_old_files: bool = False, root_dir: str = ""):
        self.config = deepcopy(exp_config)
        self.repetitions = reps
        self.exp = exp_cls()
        self.logger = logger
        self.__create_experiment_directory(delete_old_files, root_dir)

    # TODO: save new path with root dir appended?

    def __create_experiment_directory(self, delete_old_files=False, root_dir=""):
        # create experiment path and subdir
        os.makedirs(os.path.join(root_dir, self.config.path), exist_ok=True)

        # create a directory for the log path
        os.makedirs(os.path.join(
            root_dir, self.config.log_path), exist_ok=True)

        # create log path for each repetition
        rep_path_map = {}
        for r in self.repetitions:
            rep_path = os.path.join(
                root_dir, self.config.log_path, 'rep_{:02d}'.format(r), '')
            rep_path_map[r] = rep_path


        for _, rep_path in rep_path_map.items():
            if delete_old_files:
                try:
                    shutil.rmtree(os.path.join(root_dir, rep_path))
                except:
                    pass
            os.makedirs(rep_path, exist_ok=True)

        self.config['rep_log_paths'] = rep_path_map

    def run_rep(self, r: int):
        c = self.config
        self.exp.initialize(c, r)
        self.logger.initialize(c, r)

        for n in range(c.iterations):
            res = self.exp.iterate(c, r, n)
            self.logger.log_raw_result(res, r, n)

            self.exp.save_state(c, r, n)
        self.exp.finalize()
        self.logger.finalize()

    def get_rep_path(self, r: int):
        return self.config['rep_log_paths'][r]

class JobFactory():
    def __init__(self, exp_cls: experiment.AbstractExperiment.__class__, logger: cw_logging.AbstractLogger, delete_old_files: bool = False, root_dir: str = ""):
        self.exp_cls = exp_cls
        self.logger = logger
        self.delete_old_files = delete_old_files
        self.root_dir = root_dir

    def _divide_repetitions(self, exp_conf: attrdict.AttrDict) -> list:
        reps = []
        max_rep = exp_conf.repetitions
        rep_portion = 1

        if "reps_per_job" in exp_conf:
            rep_portion = exp_conf["reps_per_job"]

        for start_rep in range(0, max_rep, rep_portion):
            if start_rep + rep_portion - 1 < max_rep:
                reps.append(range(start_rep, start_rep + rep_portion))
            else:
                reps.append(range(start_rep, max_rep))
        return reps

    def create_jobs(self, exp_configs: List[attrdict.AttrDict]) -> List[Job]:
        joblist = []
        for exp_conf in exp_configs:
            reps = self._divide_repetitions(exp_conf)

            for rep_list in reps:
                j = Job(
                    exp_conf,
                    rep_list,
                    self.exp_cls,
                    self.logger,
                    self.delete_old_files,
                    self.root_dir
                )
                joblist.append(j)
        return joblist
