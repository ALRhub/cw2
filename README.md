# CW2

A second iteration of a the software framework ClusterWork to easily deploy experiments on an computing cluster using SLURM.

## Installation
0. Creating a virtual environment with [virtualenv](https://virtualenv.pypa.io/en/stable/) or [conda](https://conda.io/miniconda.html) is recommended. Create and activate the environment before installing **CW2**:
    - Create a conda environment and activate it:
    ```bash
    conda create -n my_env python=3
    source activate my_env
    ```
    - Or create a virtualenv environment and activate it
    ```bash
    virtualenv -p python3 /path/to/my_env
    source /path/to/my_env/bin/activate
    ```
1. Clone or Download **CW2**
    ```bash
    git clone https://github.com/ALRhub/cw2.git
    ```

2. Install CW2:
    The `-e` option of pip makes the project editable, i.e., pip will only reference to the git directory and hence changes in the git will be directly available in your environment. If you install without the `-e` option, pip will copy the source to your python packages.
     ```bash
     cd /path/to/cw2
     pip install -e .
     ```

## Usage Guide (Iterative Experiment)
To run an iterative experiment on a computing cluster, the following highlevel steps are required:

1. Implement `cw2.experiment.AbstractIterativeExperiment()`:
2. Write a small Main() function
3. Write a simple YAML-file to configure your experiment.
4. Adopt a shell script that starts your experiment on your cluster.

You can find a barebones template in the `template` folder

### Implementing `cw2.experiment.AbstractIterativeExperiment()`
```Python
from cw2 import experiment

class MyExperiment(experiment.AbstractIterativeExperiment):
    # ...
    def iterate(self, config: dict, rep: int, n: int) -> dict:
        return {"Result": "Current Iteration is {}".format(n)}

    def save_state(self, config: dict, rep: int, n: int) -> None:
        if n % 50 == 0:
            self.write_to_disk()
```

### Main Function
```Python
from cw2 import cluster_work

if __name__ == "__main__":
    cw = cluster_work.ClusterWork(MyExperiment)
    cw.run()
```

### Configuration YAML
To configure the execution of the experiment, we need to write a small YAML-file. The YAML file consists several documents which are separated by a line of `---`. 
There are two special kind of optional documents:
1. By setting the key `name` to `"DEFAULT"`, a default document is defined. This default document will then form the basis for all following experiment documents.
2. By setting the key `name` to `"SLURM"`, special configuration parameters for the execution on a SLURM cluster can be defined.

Besides the optional default document, each document represents an experiment. However, experiments can be expanded by the _list_ __or__ _grid_ feature, which is explained below.

The required keys for each experiment are `name`, `repetitions`, and `path`. An iterative Experiment also nees the key `iterations`. The parameters found below the key `params` overwrite the default parameters defined in the experiment class. Since the `config` dictionary that is passed to the methods of the `cw2.experiment` subclasses is the full configuration generated from the YAML-file and the default parameters, additional keys can be used.

```
# default document denoted by the name "DEFAULT"
name: "DEFAULT"
repetitions: 20
iterations: 5
path: "/path/to/experiment/folder"

# Your implementation specific parameters
params:
    num_episodes: 150
    optimizer_options:
        maxiter: 50
---
# 1. experiment
name: "more_test_episodes"
params:
    num_test_episodes: False
---
# 2. experiment
name: "more_steps"
params:
    num_steps: 50
```