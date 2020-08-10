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
    def run(self, job_idx: int = None, overwrite=False):
        raise NotImplementedError


class LocalScheduler(AbstractScheduler):
    def run(self, job_idx: int = None, overwrite: bool = False):
        joblist = self.joblist

        if job_idx is not None:
            joblist = [self.joblist[job_idx]]

        for j in joblist:
            for r in j.repetitions:
                j.run_rep(r, overwrite)


class SlurmScheduler(AbstractScheduler):
    def run(self, job_idx: int = None, overwrite: bool = False):
        cw_slurm.run_slurm(self.config, len(self.joblist))
