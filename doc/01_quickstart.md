# 1. Quickstart Guide
To deploy an existing project using **cw2**, the following highlevel steps are required:

1. Implement an [`AbstractExperiment`](../cw2/experiment.py)
2. Write a small Main() function
3. Write a simple YAML-file to configure your experiment.
4. Execute the python programm.


This quickstart guide is intended to help you quickly deploy your existing project. To develop a more robust understanding of the mechanisms behind **cw2**, please refer to the corresponding sections of the [User Guide](./).

You can find barebones templates in the [template folder](../cw2/../templates/).

## 1.1. Experiment Implementation
**cw2** requires that your program logic implements the [`cw2.experiment.AbstractExperiment`](../cw2/experiment.py) interface.

Lets assume you already have a working python project `existing_project.py`
```python
# existing_project.py
def project_main():
    # perform my program
    # ...

if __name__ == "__main__":
    project_main()
```

Create a new file to implement the `AbstractExperiment` interface, e.g. `MY_CW_MAIN.py`, and call your existing project's main (`project_main`) inside the experiments `run()` function:

```python
# MY_CW_MAIN.py
from cw2 import experiment

import existing_project

class MyExperiment(experiment.AbstractExperiment):
    # ...

    def initialize(self, config: dict, rep: int, logger: cw_logging.LoggerArray) -> None:
        # Skip for Quickguide
        pass

    def run(self, config: dict, rep: int, logger: cw_logging.LoggerArray) -> None:
        # Perform your existing task
        existing_project.project_main()
    
    def finalize(self, surrender: cw_error.ExperimentSurrender = None, crash: bool = False):
        # Skip for Quickguide
        pass
```
For more information on the experiment interface: [Experiment Class](02_experiment.md)
## 1.2. Main() Function

As with any Python program, you need to define a `__main__` function.

It creates a `ClusterWork` instance with your experiment. If you want to use any compatible [loggers](07_logging.md), you can also add them here. Finally it will start experiment:

```Python
from cw2 import cluster_work

if __name__ == "__main__":
    # Give the MyExperiment Class, not MyExperiment() Object!!
    cw = cluster_work.ClusterWork(MyExperiment)

    # Optional: Add loggers 
    cw.add_logger(...)

    # RUN!
    cw.run() 
```
The easiest location for this main function is in the same file as your experiment implementation, e.g. `MY_CW_MAIN.py`

For more information on Logging: [Logging Results](07_logging.md)

## 1.3. Config YAML
To qucikly deploy your first **cw2** experiment, create a simple YAML configuration file:

```yaml
---
# Experiment 1
name: "experiment_name"

# Required: Can also be set in DEFAULT
path: "path/to/output_dir/"   # location to save results in
repetitions: 1    # number of times one set of parameters is run

# Experiment Parameters:
params:
  key: 'value'
```

We strongly recommend you read the [Config Guide](03_config.md) to better understand what the different options mean, and how you can use this file to efficiently define hyperparameter grids.


## 1.4. Program Execution
To start an experiment locally, e.g. for testing:
```bash
python3 MY_CW_MAIN.py YOUR_CONFIG.yml
```

To start an experiment on a slurm cluster:
```bash
python3 MY_CW_MAIN.py YOUR_CONFIG.yml -s
```

For more information on slurm: [Slurm Guide](04_slurm.md) 

For more information on available CLI Arguments: [CLI at a Glance](10_cli_args.md)

[Back to Overview](./)