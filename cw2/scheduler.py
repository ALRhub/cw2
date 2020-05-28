import abc
from typing import List

from . import experiment, job


class AbstractScheduler(abc.ABC):
    def __init__(self):
        self.joblist = None

    def assign(self, joblist: List[job.Job], exp_cls: experiment.AbstractExperiment) -> None:
        """assigns the scheduler a list of jobs to execute

        Arguments:
            joblist {List[job.AbstractJob]} -- list of configured and implemented jobs
        """
        self.joblist = joblist
        self.exp = exp_cls()

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError


class LocalScheduler(AbstractScheduler):
    def run(self):
        for j in self.joblist:
            j.run()
