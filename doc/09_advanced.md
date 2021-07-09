# 9. Advanced Features & Parallelization
- [9. Advanced Features & Parallelization](#9-advanced-features--parallelization)
  - [9.1. Error Handling](#91-error-handling)
  - [9.2. Parallelization](#92-parallelization)
    - [9.2.1 Parallelization Pitfalls](#921-parallelization-pitfalls)
  - [9.3. Custom Scheduler](#93-custom-scheduler)
  - [9.4. Linking External YAML Files](#94-linking-external-yaml-files)

## 9.1. Error Handling
Should any kind of exception be raised during an Experiment execution (`initialize()` or `run()`), **cw2** will abort this experiment run, log the error including stacktrace to a log file in the repetition directory and continue with the next task.

If you want to end an (iterative) experiment early, you can raise the `cw_error.ExperimentSurrender` exception to gracefully abort the experiment execution.

The `finalize()` function of you experiment has access to a raised `cw_error.ExperimentSurrender` exception and can access its payload. You can use this to "transmit" data to your finalziation procedure and react accordingly.

## 9.2. Parallelization
First, an attempt to establish a terminology:
- Experiment: A collection of hyperparameter runs, defined in the `config.yml` via the `name` key.
- Hyperparameter run: A combination of hyperparameters, as defined by `params` and combination keywords such as `grid`. Can be repeated multiple times
- Repetition: A singular repetition of a hyperparameter run. 
- Job (cw2): A computing job, resulting in its own, independend (computing) process. Per default a 1:1 mapping with repetitions. SLURM calls this "unit" of computation task (`cpu-per-task` keyword.)

The following config results in `2*2 (grid) * 5 (repetitions)` jobs.
```yaml
---
name: exp1
repetitions: 5
grid:
 a: [1, 2]
 b: [3, 4]
```

Often, a cluster has restrictions on how many SLURM tasks / cw2 jobs  can be submitted by a user at once. For this purpose, the 1:1 mapping of assign each repetition its own job can be changed with the `reps_per_job` config keyword. Multiple repetitions are bundled into one process, which are computed sequentially.

This can then be futher parallelized by using the `reps_in_parallel` config keyword. This starts a multi-threading parallelization within a job process.

### 9.2.1 Parallelization Pitfalls
Currently, we use joblib per default for the multi-threading parallelization. This can cause issues with GPU intensive tasks like Deep Learning or special third party libraries, e.g. Mujoco.


## 9.3. Custom Scheduler
In **cw2** a scheduler is an object responsible for executing a list of jobs (see [Slurm Introduction](04_slurm.md)). In some cases it might be necessary to built your own, custom scheduler. E.g., when the use of parallelization inside of a job is required, and your experiment is not compatible with the default joblib multiprocessing approach (for example through the use of GPU acceleration).

**cw2** does not offer such advanced schedulers on its own, as they might be highly dependend on your use case and applied libraries.

To build your custom scheduler, you need to at least implement the [`AbstractScheduler`](../cw2/scheduler.py) interface. 

You might want to use [`LocalScheduler`](../cw2/scheduler.py) as a reference implementation.

Remember: The Scheduler sees the `Job` objects, which itself might bundle multiple cw2 tasks / repetitions (NOT SLURM tasks).

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

## 9.4. Linking External YAML Files
It might be helpful to you, to organize your experiment configs into different yaml files which refer to each other.
Similiar to the merging behaviour with a `DEFAULT` configuration, you can now define a "parent" configuration with two new keywords:

```yaml
---
name: "child"
import_path: "some_path" # optional. can be an absolute path, or relative to this yaml file.
                         # if only import_exp is present, defaults to THIS file.
import_exp: "parent_exp" # optional. basically -e option which external experiment should be the basis.
                                       # The external experiment will be merged with its own default before importing.
                                       # Case Sensitive. Defaults to "DEFAULT".
```

Imported yaml files can be children with imports themselves. A child will always overwrite its parent. Relative paths will always be relative to the file they are written in, NOT to the root or main.py

Cyclic Linking should be detected and result in an error message.

The resolution order is:
1. A named experiment `child` gets merged with its internal `DEFAULT` configuration. Shared keys are "overwritten" by the more specific `child`.
2. Should after the merge an `import_` key be present in the configuration, the specified `parent_exp` gets loaded.
3. The `parent_exp` is merged with its internal "Parent"-`DEFAULT`.
4. Repeat Steps 2-4 for each parent.



[Back to Overview](./)