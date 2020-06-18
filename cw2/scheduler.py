import abc
from typing import List

from . import experiment, job


class AbstractScheduler(abc.ABC):
    def __init__(self):
        self.joblist = None

    def assign(self, joblist: List[job.Job]) -> None:
        """assigns the scheduler a list of jobs to execute

        Arguments:
            joblist {List[job.AbstractJob]} -- list of configured and implemented jobs
        """
        self.joblist = joblist

    @abc.abstractmethod
    def run(self, rep=None):
        raise NotImplementedError


class LocalScheduler(AbstractScheduler):
    def run(self, job_idx=None):
        joblist = self.joblist
        
        if job_idx is not None:
            joblist = [self.joblist[job_idx]]

        for j in joblist:
            for r in j.repetitions:
                j.run_rep(r)
