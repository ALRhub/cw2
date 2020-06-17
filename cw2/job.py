import os
import shutil
from typing import List

import attrdict

from . import experiment, logging


class Job():
    def __init__(self, exp_cls: experiment.AbstractExperiment.__class__, exp_config: attrdict, logger: logging.AbstractLogger, delete_old_files: bool = False, root_dir: str = ""):
        self.exp = exp_cls()
        self.config = exp_config
        self.__create_experiment_directory(delete_old_files, root_dir)
        self.logger = logger

    # TODO: save new path with root dir appended?

    def __create_experiment_directory(self, delete_old_files=False, root_dir=""):
        # FIXME: Will be called multiple times when used together with slurm -j cascade
        if delete_old_files:
            try:
                shutil.rmtree(os.path.join(root_dir,self.config.path))
            except:
                pass

        # create experiment path and subdir
        os.makedirs(os.path.join(root_dir, self.config.path), exist_ok=True)

        # create a directory for the log path
        os.makedirs(os.path.join(
            root_dir, self.config.log_path), exist_ok=True)

        # create log path for each repetition
        # FIXME: different handling for -j case
        rep_path_list = []
        for r in range(self.config.repetitions):
            rep_path = os.path.join(
                root_dir, self.config.log_path, 'rep_{:02d}'.format(r), '')
            os.makedirs(rep_path, exist_ok=True)

            rep_path_list.append(rep_path)
        self.config['rep_log_paths'] = rep_path_list

    def run(self, rep=None):
        c = self.config
        self.logger.configure(c)

        repetitions = range(c.repetitions)

        if rep is not None:
            repetitions = [rep]

        for r in repetitions:
            self.exp.initialize(c, r)
            self.logger.rep_setup(r)

            for n in range(c.iterations):
                res = self.exp.iterate(c, r, n)
                self.logger.log_raw_result(res, r, n)

                self.exp.save_state(c, r, n)
            self.exp.finalize()
            self.logger.rep_finalize()

        self.logger.global_finalize()
