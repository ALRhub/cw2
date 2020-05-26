import abc
from typing import List

from workload import job


class AbstractScheduler(abc.ABC):
    def __init__(self):
        self.joblist = None

    def assign(self, joblist: List[job.AbstractJob]) -> None:
        """assigns the scheduler a list of jobs to execute

        Arguments:
            joblist {List[job.AbstractJob]} -- list of configured and implemented jobs
        """
        self.joblist = joblist

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError


class LocalScheduler(AbstractScheduler):
    def run(self):
        for j in self.joblist:
            c = j.config

            for r in range(c.repetitions):
                j.initialize(c, r)

                results = {}
                for n in range(c.iterations):
                    results = j.iterate(c, r, n)
                    j.save_state(c, r, n)

                j.finalize()
                print(results)
