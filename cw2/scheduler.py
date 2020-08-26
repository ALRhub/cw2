import abc
from typing import List

from cw2 import config, cw_slurm, experiment, job


class AbstractScheduler(abc.ABC):
    def __init__(self, conf: config.Config = None):
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
            for c in j.tasks:
                j.run_task(c, overwrite)


class SlurmScheduler(AbstractScheduler):
    def run(self, overwrite: bool = False):
        cw_slurm.run_slurm(self.config, len(self.joblist))
