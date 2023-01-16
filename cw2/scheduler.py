import abc
import concurrent.futures
import os
from typing import List

from joblib import Parallel, delayed
import multiprocessing
import socket
import warnings
from cw2 import cw_error, job
from cw2.cw_config import cw_config
from cw2.cw_slurm import cw_slurm
from cw2.cw_config import cw_conf_keys as KEYS


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
        self._total_num_gpus = int(conf.slurm_config['sbatch_args']['gres'][4:])
        self._gpus_per_rep = conf.slurm_config['gpus_per_rep']
        self._queue_elements = int(self._total_num_gpus / self._gpus_per_rep)

        print("GPUDistributingLocalScheduler: {} GPUs available, {} GPUs per rep, {} queue elements".format(
            self._total_num_gpus, self._gpus_per_rep, self._queue_elements))

        if self._gpus_per_rep >= 1.0:
            assert self._gpus_per_rep == int(self._gpus_per_rep), "gpus_per_rep must be integer"



    @staticmethod
    def use_distributed_gpu_scheduling(conf: cw_config.Config) -> bool:
        if conf.slurm_config is None:
            return False
        # Use if
        # 1.) GPUs Requested
        # 2.) Number of GPUs per rep specified
        # 3.) Number of GPUs per rep != total number of gpus requested
        gpus_requested = "gres" in conf.slurm_config.get("sbatch_args", "DUMMY_DEFAULT")
        gpus_per_rep_specified = "gpus_per_rep" in conf.slurm_config
        num_gpus_requested = int(conf.slurm_config["sbatch_args"]["gres"][4:]) if gpus_requested else 0

        use_distributed_gpu_scheduling = \
            gpus_requested and gpus_per_rep_specified and num_gpus_requested != conf.slurm_config["gpus_per_rep"]

        if not use_distributed_gpu_scheduling:
            on_horeka_gpu = "hkn" in socket.gethostname() and conf.slurm_config["partition"] == "accelerated"
            if on_horeka_gpu:
                assert num_gpus_requested == 4, "On HoreKA, you must request 4 GPUs (gres=gpu:4)"
            assert not on_horeka_gpu, "You are on HoreKA and not using the GPU scheduler, don't! "

        return use_distributed_gpu_scheduling

    @staticmethod
    def get_gpu_str(queue_idx: int, gpus_per_rep: float) -> str:
        if gpus_per_rep >= 1:
            assert int(gpus_per_rep) == gpus_per_rep, "gpus_per_rep must be integer if >= 1"
            gpus_per_rep = int(gpus_per_rep)
            return ("{}," * gpus_per_rep).format(*[queue_idx * gpus_per_rep + i for i in range(gpus_per_rep)])[:-1]
        else:
            return str(int(queue_idx * gpus_per_rep))


class MPGPUDistributingLocalScheduler(GPUDistributingLocalScheduler):

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
                    pool.apply_async(MPGPUDistributingLocalScheduler._execute_task, (j, c, gpu_queue,
                                                                                     self._gpus_per_rep,
                                                                                     overwrite))
            pool.close()
            pool.join()

    @staticmethod
    def _execute_task(j: job.Job,
                      c: dict,
                      q: multiprocessing.Queue,
                      gpus_per_rep: int,
                      overwrite: bool = False):
        queue_idx = q.get()
        gpu_str = MPGPUDistributingLocalScheduler.get_gpu_str(queue_idx, gpus_per_rep)
        try:
            os.environ["CUDA_VISIBLE_DEVICES"] = gpu_str
            j.run_task(c, overwrite)
        except cw_error.ExperimentSurrender as _:
            return
        finally:
            q.put(queue_idx)


class HOREKAAffinityGPUDistributingLocalScheduler(GPUDistributingLocalScheduler):

    def __init__(self, conf: cw_config.Config = None):
        super(HOREKAAffinityGPUDistributingLocalScheduler, self).__init__(conf=conf)

        total_cpus = conf.slurm_config['cpus-per-task'] * conf.slurm_config['ntasks']
        self._cpus_per_rep = total_cpus // self._queue_elements

        assert self._cpus_per_rep > 0, "Not enough CPUs for the number of GPUs requested"

    def run(self, overwrite: bool = False):
        print("Seeing CPUs:", os.sched_getaffinity(0))
        num_parallel = self.joblist[0].n_parallel
        for j in self.joblist:
            assert j.n_parallel == num_parallel, "All jobs in list must have same n_parallel"
            assert j.n_parallel == self._queue_elements, "Mismatch between GPUs Queue Elements and Jobs executed in" \
                                                         "parallel. Fix for optimal resource usage!!"

        with concurrent.futures.ProcessPoolExecutor(max_workers=num_parallel,
                                                    ) as pool:
            # setup gpu resource queue
            m = multiprocessing.Manager()
            gpu_queue = m.Queue(maxsize=self._queue_elements)
            for i in range(self._queue_elements):
                gpu_queue.put(i)

            for j in self.joblist:
                for c in j.tasks:
                    pool.submit(
                        HOREKAAffinityGPUDistributingLocalScheduler._execute_task,
                        j, c, gpu_queue, self._gpus_per_rep, self._cpus_per_rep,
                        overwrite)

    @staticmethod
    def _execute_task(j: job.Job,
                      c: dict,
                      q: multiprocessing.Queue,
                      gpus_per_rep: int,
                      cpus_per_rep: int,
                      overwrite: bool = False):
        print("Seeing CPUs:", os.sched_getaffinity(0))
        queue_idx = q.get()
        gpu_str = HOREKAAffinityGPUDistributingLocalScheduler.get_gpu_str(queue_idx, gpus_per_rep)
        cpus = set(range(queue_idx * cpus_per_rep, (queue_idx + 1) * cpus_per_rep))
        print("Job {}: Using GPUs: {} and CPUs: {}".format(queue_idx, gpu_str, cpus))
        try:
            os.sched_setaffinity(0, cpus)
            c[KEYS.i_CPU_CORES] = cpus
            os.environ["CUDA_VISIBLE_DEVICES"] = gpu_str
            j.run_task(c, overwrite)
        except cw_error.ExperimentSurrender as _:
            return
        finally:
            q.put(queue_idx)


class KlusterThreadLimitingScheduler(GPUDistributingLocalScheduler):

    def __init__(self, conf: cw_config.Config = None):
        super(KlusterThreadLimitingScheduler, self).__init__(conf=conf)
        total_cpus = conf.slurm_config['cpus-per-task'] * conf.slurm_config['ntasks']
        self._num_threads = total_cpus // self._queue_elements
        print("Using {} threads per Rep".format(self._num_threads))

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
                    args = (j, c, gpu_queue, self._gpus_per_rep, self._num_threads, overwrite)
                    pool.apply_async(KlusterThreadLimitingScheduler._execute_task, args)
            pool.close()
            pool.join()

    @staticmethod
    def _execute_task(j: job.Job,
                      c: dict,
                      q: multiprocessing.Queue,
                      gpus_per_rep: int,
                      num_threads: int,
                      overwrite: bool = False):
        queue_idx = q.get()
        gpu_str = KlusterThreadLimitingScheduler.get_gpu_str(queue_idx, gpus_per_rep)
        try:
            os.environ["MKL_NUM_THREADS"] = str(num_threads)
            os.environ["NUMEXPR_NUM_THREADS"] = str(num_threads)
            os.environ["OMP_NUM_THREADS"] = str(num_threads)
            # Ok, that's not so nice, but I did not find better way yet
            try:
                import torch
                torch.set_num_threads(num_threads)
            except ImportError:
                pass

            os.environ["CUDA_VISIBLE_DEVICES"] = gpu_str
            j.run_task(c, overwrite)
        except cw_error.ExperimentSurrender as _:
            return
        finally:
            q.put(queue_idx)


def get_gpu_scheduler_cls(scheduler: str):
    if scheduler == "mp":
        return MPGPUDistributingLocalScheduler
    elif scheduler == "horeka":
        return HOREKAAffinityGPUDistributingLocalScheduler
    elif scheduler == "kluster":
        return KlusterThreadLimitingScheduler
    else:
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
