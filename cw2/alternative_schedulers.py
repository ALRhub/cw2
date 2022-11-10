import abc
import os
from typing import List

from joblib import Parallel, delayed
import multiprocessing

import concurrent.futures as con
import queue

from cw2 import cw_error, job
from cw2.cw_config import cw_config
from cw2.cw_slurm import cw_slurm

from cw2.scheduler import GPUDistributingLocalScheduler


class StarmapGPUDistributingLocalScheduler(GPUDistributingLocalScheduler):

    def run(self, overwrite: bool = False):
        print("Using StarmapGPUDistributingLocalScheduler")
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
                args = [(j, c, gpu_queue, self._gpus_per_rep, overwrite) for c in j.tasks]
                pool.starmap_async(StarmapGPUDistributingLocalScheduler._execute_task, args)
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


class ConcurrentGPUDistributingLocalScheduler(GPUDistributingLocalScheduler):

    def run(self, overwrite: bool = False):
        print("Using ConcurrentGPUDistributingLocalScheduler")
        num_parallel = self.joblist[0].n_parallel
        for j in self.joblist:
            assert j.n_parallel == num_parallel, "All jobs in list must have same n_parallel"
            assert j.n_parallel == self._queue_elements, "Mismatch between GPUs Queue Elements and Jobs executed in" \
                                                         "parallel. Fix for optimal resource usage!!"

        with con.ProcessPoolExecutor(max_workers=num_parallel) as pool:
            # setup gpu resource queue
            #gpu_queue = queue.Queue(maxsize=self._queue_elements)
            #for i in range(self._queue_elements):
            #    gpu_queue.put(i)

            results = []
            for j in self.joblist:
                for i, c in enumerate(j.tasks):
                    results.append(pool.submit(ConcurrentGPUDistributingLocalScheduler._execute_task, j, c, i,
                                               self._gpus_per_rep, overwrite))
            for r in results:
                r.result()

    @staticmethod
    def _execute_task(j: job.Job,
                      c: dict,
                      idx: int,
                      #q: multiprocessing.Queue,
                      gpus_per_job: int,
                      overwrite: bool = False):
        #gpu_idx = q.get()
        s = ("{}," * gpus_per_job).format(*[idx * gpus_per_job + i for i in range(gpus_per_job)])[:-1]
        try:
            os.environ["CUDA_VISIBLE_DEVICES"] = s
            j.run_task(c, overwrite)
        except cw_error.ExperimentSurrender as _:
            return
       # finally:
            #q.put(gpu_idx)


class JoblibGPUDistributingLocalScheduler(GPUDistributingLocalScheduler):

    def run(self, overwrite: bool = False):
        print("Using JoblibGPUDistributingLocalScheduler")
        for j in self.joblist:
            Parallel(n_jobs=j.n_parallel)(delayed(self.execute_task)(j, c, i, self._gpus_per_rep, overwrite)
                                          for i, c in enumerate(j.tasks))

    def execute_task(self, j: job.Job, c: dict, idx: int, gpus_per_job: int, overwrite: bool = False):
        s = ("{}," * gpus_per_job).format(*[idx * gpus_per_job + i for i in range(gpus_per_job)])[:-1]
        try:
            os.environ["CUDA_VISIBLE_DEVICES"] = s
            j.run_task(c, overwrite)
        except cw_error.ExperimentSurrender as _:
            return


class RayGPUDistributingLocalScheduler(GPUDistributingLocalScheduler):

    def run(self, overwrite: bool = False):
        print("Using RayGPUDistributingLocalScheduler")

        import ray
        from ray.util.queue import Queue

        @ray.remote
        def _execute_task(j: job.Job,
                          c: dict,
                          q,
                          gpus_per_job: int,
                          overwrite: bool = False):
            gpu_idx = q.get()
            print("I got gpu idx", gpu_idx)
            s = ("{}," * gpus_per_job).format(*[gpu_idx * gpus_per_job + i for i in range(gpus_per_job)])[:-1]
            try:
                os.environ["CUDA_VISIBLE_DEVICES"] = s
                j.run_task(c, overwrite)
            except cw_error.ExperimentSurrender as _:
                return
            finally:
                print("giving back gpu idx", gpu_idx)
                q.put(gpu_idx)

        ray.init()
        num_parallel = self.joblist[0].n_parallel
        for j in self.joblist:
            assert j.n_parallel == num_parallel, "All jobs in list must have same n_parallel"
            assert j.n_parallel == self._queue_elements, "Mismatch between GPUs Queue Elements and Jobs executed in" \
                                                         "parallel. Fix for optimal resource usage!!"
        gpu_queue = Queue(maxsize=self._queue_elements)

        for i in range(self._queue_elements):
            gpu_queue.put(i)
        results = []
        for j in self.joblist:
            for i, c in enumerate(j.tasks):
                results.append(_execute_task.remote(j, c, gpu_queue, self._gpus_per_rep, overwrite))
        ray.get(results)
