import os
import shutil
from typing import List
import logging

import attrdict
from copy import deepcopy
from cw2 import cw_logging, experiment


class Job():
    """Class defining a computation job.
    Can contain 1..n repetitions. Each job should encapsulate all information necessary for execution.
    """

    def __init__(self, exp_config: attrdict.AttrDict, reps: List[int], exp_cls: experiment.AbstractExperiment.__class__, logger: cw_logging.AbstractLogger, delete_old_files: bool = False, root_dir: str = ""):
        self.config = deepcopy(exp_config)
        self.repetitions = reps
        self.exp = exp_cls()
        self.logger = logger
        self.__create_experiment_directory(delete_old_files, root_dir)

    def __create_experiment_directory(self, delete_old_files=False, root_dir=""):
        """internal function creating the directories in which the job will write its data.

        Args:
            delete_old_files (bool, optional): Should the directory be emptied beforehand?. Defaults to False.
            root_dir (str, optional): [description]. Defaults to "".
        """
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

        # XXX: Disable Delete for now
        """
        if delete_old_files:
            for _, rep_path in rep_path_map.items():
                try:
                    shutil.rmtree(os.path.join(root_dir, rep_path))
                except:
                    pass
        """
        os.makedirs(rep_path, exist_ok=True)

        self.config['rep_log_paths'] = rep_path_map

    def run_rep(self, r: int, overwrite: bool):
        """Execute a single repetition of the job. 

        Args:
            r (int): repetition number
        """
        if not overwrite and self._check_rep_exists(r):
            logging.warning(
                "Skipping run, as {} is not empty. Use -o to overwrite.".format(self.get_rep_path(r)))
            return

        c = self.config
        self.exp.initialize(c, r)
        self.logger.initialize(c, r)

        self.exp.run(c, r, self.logger)

        self.exp.finalize()
        self.logger.finalize()

    def _check_rep_exists(self, r: int) -> bool:
        """internal function. checks if the repetition has already been run in the past.

        Args:
            r (int): repetition number

        Returns:
            bool: True if the repetition was already run
        """
        rep_path = self.get_rep_path(r)
        return len(os.listdir(rep_path)) != 0

    def get_rep_path(self, r: int) -> str:
        """returns the path of the job and repetition combination

        Args:
            r (int): repetition number

        Returns:
            str: path of this job and repetition combination
        """
        return self.config['rep_log_paths'][r]


class JobFactory():
    """Facotry class to create single jobs from experiment configuration.
    Specifially used to map experiment repetitions to Jobs.
    """

    def __init__(self, exp_cls: experiment.AbstractExperiment.__class__, logger: cw_logging.AbstractLogger, delete_old_files: bool = False, root_dir: str = ""):
        self.exp_cls = exp_cls
        self.logger = logger
        self.delete_old_files = delete_old_files
        self.root_dir = root_dir

    def _divide_repetitions(self, exp_conf: attrdict.AttrDict) -> list:
        """internal function to divide experiment repetitions into sets of repetitions.
        Dependent on configured reps_per_job attribute. Each set of repetitions will be one job.

        Args:
            exp_conf (attrdict.AttrDict): single experiment configuration

        Returns:
            list: List of repetition indices.
        """
        reps = []
        max_rep = exp_conf.repetitions

        # Use 1 Repetition per job if not defined otherwise
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
        """creates a list of all jobs.

        Args:
            exp_configs (List[attrdict.AttrDict]): list of all defined experiment configurations.

        Returns:
            List[Job]: list of configured jobs.
        """
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
