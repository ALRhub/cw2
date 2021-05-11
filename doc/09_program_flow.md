# 9. Advanced Program Flow & Parallelization
## Error Handling
Should any kind of exception be raised during an Experiment execution (`initialize()` or `run()`), `CW2` will abort this experiment run, log the error including stacktrace to a log file in the repetition directory and continue with the next task.

If you want to end an (iterative) experiment early, you can raise the `cw_error.ExperimentSurrender` exception to gracefully abort the experiment execution.

## Parallelization
under construction

## Custom Scheduler
In **cw2** a scheduler is an object responsible for executing a list of jobs (see [Slurm Introduction](04_slurm.md)). In some cases it might be necessary to built your own, custom scheduler. E.g., when the use of parallelization inside of a job is required, and your experiment is not compatible with the default joblib multiprocessing approach (for example through the use of GPU acceleration).

**cw2** does not offer such advanced schedulers on its own, as they might be highly dependend on your use case and applied libraries.

To build your custom scheduler, you need to at least implement the [`AbstractScheduler`](../cw2/scheduler.py) interface. 

You might want to use [`LocalScheduler`](../cw2/scheduler.py) as a reference implementation.

Remember: The Scheduler sees the `Job` objects, which itself might bundle multiple tasks.

This is a very abstract, non-working example how this might look like:

```python
import some_gpu_acc
from some_gpu_acc import some_multiproc_pool

from cw2.scheduler import LocalScheduler

class CustomScheduler(AbstractScheduler):
    def run(self, overwrite: bool = False):
        for job in self.joblist:
            for t in job.tasks:
                some_multiproc_pool(N_CORES).parallelize(
                    job.run_task(t, overwrite)
                )

```

To use your new custom scheduler, you have to give it to the [`ClusterWorks`](../cw2/cluster_work.py) instance in your `__main__` function:

```python
from cw2 import cluster_work

if __name__ == "__main__":
    # Give the MyExperiment Class, not MyExperiment() Object!!
    cw = cluster_work.ClusterWork(MyExperiment)

    # RUN WITH CUSTOM SCHEDULER!!!
    cw.run(s = CustomScheduler()) 
```



[Back to Overview](./)