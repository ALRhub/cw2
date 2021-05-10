import abc
from typing import List

from joblib import Parallel, delayed

from cw2 import cw_config, cw_error, cw_slurm, experiment, job


class AbstractScheduler(abc.ABC):
    def __init__(self, conf: cw_config.Config = None):
        self.joblist = None
        self.config = conf

    def assign(self, joblist: List[job.Job]) -> None:
        """assigns the scheduler a list of jobs to execute

        Arguments:
            joblist {List[job.AbstractJob]} -- list of configured and implemented jobs
        """
        self.joblist = joblist

    @abc.abstractmethod
    def run(self, overwrite=False):
        raise NotImplementedError


class LocalScheduler(AbstractScheduler):
    def run(self, overwrite: bool = False):
        for j in self.joblist:
            Parallel(n_jobs=j.n_parallel)(delayed(self.execute_task)(j, c, overwrite)
                                          for c in j.tasks)

    def execute_task(self, j: job.Job, c: dict, overwrite: bool = False):
        try:
            j.run_task(c, overwrite)
        except cw_error.ExperimentSurrender as _:
            return


class SlurmScheduler(AbstractScheduler):
    def run(self, overwrite: bool = False):
        cw_slurm.run_slurm(self.config, len(self.joblist))
