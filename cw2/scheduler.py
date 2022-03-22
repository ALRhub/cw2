import abc
import os
from typing import List

from joblib import Parallel, delayed
import multiprocessing

from cw2 import cw_error, job
from cw2.cw_config import cw_config
from cw2.cw_slurm import cw_slurm


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
        """the scheduler begins to execute all assigned jobs

        Args:
            overwrite (bool, optional): overwrite flag. can be passed to the job. Defaults to False.
        """
        raise NotImplementedError


class GPUDistributingLocalScheduler(AbstractScheduler):

    def __init__(self, conf: cw_config.Config = None):

        super(GPUDistributingLocalScheduler, self).__init__(conf=conf)
        self._total_num_gpus = int(conf.slurm_config.sbatch_args["gres"][4:])
        self._gpus_per_rep = conf.slurm_config.gpus_per_rep
        self._queue_elements = self._total_num_gpus // self._gpus_per_rep

    def run(self, overwrite: bool = False):

        num_parallel = self.joblist[0].n_parallel
        for j in self.joblist:
            assert j.n_parallel == num_parallel, "All jobs in list must have same n_parallel"
            assert j.n_parallel == self._queue_elements, "Mismatch between GPUs Queue Elements and Jobs executed in" \
                                                         "parallel. Fix for optimal resource usage!!"

        with multiprocessing.Pool(processes=num_parallel) as pool:
            # setup gpu resource queue
            m = multiprocessing.Manager()
            gpu_queue = m.Queue(maxsize=self._queue_elements)
            for i in range(self._queue_elements):
                gpu_queue.put(i)

            for j in self.joblist:
                for c in j.tasks:
                    pool.apply_async(GPUDistributingLocalScheduler._execute_task, (j, c, gpu_queue,
                                                                                   self._gpus_per_rep,
                                                                                   overwrite))

            pool.close()
            pool.join()

    @staticmethod
    def _execute_task(j: job.Job,
                      c: dict,
                      q: multiprocessing.Queue,
                      gpus_per_job: int,
                      overwrite: bool = False):
        gpu_idx = q.get()
        s = ("{}," * gpus_per_job).format(*[gpu_idx * gpus_per_job + i for i in range(gpus_per_job)])[:-1]
        try:
            os.environ["CUDA_VISIBLE_DEVICES"] = s
            j.run_task(c, overwrite)
        except cw_error.ExperimentSurrender as _:
            return
        finally:
            q.put(gpu_idx)

    @staticmethod
    def use_distributed_gpu_scheduling(conf: cw_config.Config) -> bool:
        if conf.slurm_config is None:
            return False
        # Use if
        # 1.) GPUs Requested
        # 2.) Number of GPUs per rep specified
        # 3.) Number of GPUs per rep != total number of gpus requested
        return "gres" in conf.slurm_config.get("sbatch_args", "DUMMY_DEFAULT") and \
                "gpus_per_rep" in conf.slurm_config and \
               (int(conf.slurm_config.sbatch_args["gres"][4:]) != conf.slurm_config.gpus_per_rep)


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
